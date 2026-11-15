# coupon 설계

## 발급 흐름

1. **Redis 문지기** (`CouponGate.admit`, Lua 한 번)
   - 캠페인 시작 전이거나 소진됐으면 거절한다.
   - 통과하면 입장 번호 `seq`(1..수량)를 준다. free 목록에 반납된 번호가 있으면 그것을 먼저 준다.
   - 거절된 요청은 PG에 닿지 않는다.
2. **PG 최종 판정** (`_ISSUE`)
   - `INSERT … SELECT … WHERE seq <= total_quantity AND starts_at <= now()`
   - 판정과 기록이 한 문장이라 동시성 문제가 없다.
   - `UNIQUE(campaign_id, seq)`, `UNIQUE(code)`가 걸려 있다.
3. **커밋 후 응답**. 실패하면 `seq`를 Redis free 목록에 반납해 다음 요청이 쓴다.

## 정합성 보장

| 요구사항 | 보장 방법 |
|---|---|
| 초과 발급 금지 | PG에는 1..수량 범위의 유일한 seq만 들어간다 |
| 코드 중복 금지 | 80bit 랜덤 코드(`CODE_RANDOM_BYTES = 10`, base32 16자) + PG `UNIQUE`. 충돌하면 다시 만든다 |
| 시작 전 발급 불가 | PG `now()` 한 시계로 판정한다. Redis의 시간 확인은 트래픽 차단용이다 |
| 응답받은 쿠폰 유실 없음 | PG 커밋 후에 응답한다. Redis가 유실돼도 상관없다 |

정합성은 PG가 책임진다. Redis는 유실되거나 역행해도 되는 앞단 필터다. 그래서 Redis는 AOF `everysec`로 충분하다.

## Redis 장애 시 동작

- **카운터 역행** (AOF everysec 유실)
  - 이미 쓰인 seq를 받으면 `SeqTakenError`(UNIQUE 위반)가 난다.
  - 그러면 다음 번호로 다시 시도한다. 초과 발급은 일어나지 않는다.
- **키 소실**
  - `admit`이 `MISSING`을 돌려준다.
  - 그러면 `_reseed`가 PG의 `max(seq)`로 키를 다시 채운다.

## 구현 선택의 이유

- **캠페인 row를 UPDATE하지 않는다.**
  - 발급 커밋끼리 row lock 경합이 생기지 않게 하기 위해서다.
  - 카운터를 PG row에 두던 첫 버전은 수량 5,000일 때 초당 약 575건이 한계였다.
- **`_ISSUE`는 모듈 로드 때 한 번만 만든다.**
  - 발급 성공마다 실행되는 문장이다.
  - 매번 만들면 문장 생성과 캐시 키 계산 비용으로 처리량이 절반으로 떨어졌다.
- **`insert_if_admissible`은 AUTOCOMMIT과 Core 연결로 실행한다.**
  - 한 문장이라 그 자체로 원자적이므로, AUTOCOMMIT으로 BEGIN/COMMIT 왕복을 아낀다. 그래서 트랜잭션의 첫 문장이어야 한다.
  - `Session.scalar(insert, dict)`는 ORM 벌크 insert로 해석된다. 그래서 Core 연결을 쓴다.
- **세션은 첫 쿼리 때 PG 연결을 잡는다.**
  - Redis에서 거절된 요청은 PG 연결을 쓰지 않는다.
- **REQUEST 스코프 세션은 쓴 경우에만 `close()`한다** (`di.py`).
  - `close()`는 쓰지 않은 세션에도 약 50µs가 든다. 거절 요청의 처리량을 깎는다.
  - 트랜잭션도 로드된 객체도 없으면 정리할 것이 없다.
- **Redis 풀은 `BlockingConnectionPool`을 쓴다.**
  - 기본 풀은 한도를 넘으면 즉시 에러를 낸다.
  - 버스트 때는 연결이 날 때까지 기다리게 한다.
- **Redis 키를 hash tag로 묶는다** (`campaign:{id}`, `campaign:{id}:free`).
  - Redis Cluster에서도 Lua가 두 키를 한 슬롯에서 다룰 수 있다.
- **`seed`는 키가 없을 때만 채운다.**
  - 캠페인 생성 직후의 seed가 실패해도 첫 발급 때 PG에서 다시 채운다.
- **실패하면 seq를 반납한다** (`issue`의 `BaseException` 분기).
  - 실제로는 커밋됐는데 응답 직전에 연결이 끊긴 경우에도 안전하다.
  - 다음 요청이 UNIQUE에 걸려 다시 시도할 뿐이기 때문이다.
- **`_insert`가 None을 받으면 캠페인 시작 여부를 다시 확인한다.**
  - 이것으로 `NotStarted`와 `SoldOut`을 구분한다.
  - 여기서 `SoldOut`이 나는 것은 Redis의 수량이 PG와 다를 때뿐이다.
- **`(campaign_id, seq)` UNIQUE 제약에만 이름을 직접 붙인다** (`SEQ_UNIQUE`).
  - 리포지토리는 이 이름으로 seq 충돌과 코드 충돌을 구분한다.
  - 나머지 제약은 PostgreSQL이 자동으로 이름을 붙인다. 예: `coupons_code_key`, `coupons_pkey`
- **캠페인 조회와 쿠폰 목록을 분리한다.**
  - `GetCampaign`의 `issued_count`는 `count(*)`로 센다. `(campaign_id, seq)` UNIQUE 인덱스를 타므로 쿠폰 row를 메모리에 올리지 않는다.
  - 쿠폰 목록은 `ListCoupons`로 페이지 단위로 읽는다. 페이지 크기는 기본 100, 최대 1000이다.
    - offset 대신 seq 기준 keyset으로 나눈다. `page_token`은 이전 페이지 마지막 seq다.
    - 같은 인덱스로 `seq > token`부터 읽으므로 뒤쪽 페이지도 느려지지 않는다.
  - `Campaign`에 쿠폰 관계(relationship)를 두지 않는다. 한 번에 전부 로드하는 경로를 아예 만들지 않기 위해서다.

## `admit` 반환값

| 값 | 의미 |
|---|---|
| 양수 | 입장 번호 seq |
| `MISSING(-1)` | 캠페인 없음 또는 키 소실 |
| `NOT_STARTED(-2)` | 시작 전 |
| `SOLD_OUT(-3)` | 소진 |

## gRPC 상태 코드

| 상황 | gRPC | gateway 경유 HTTP |
|---|---|---|
| 캠페인 없음 | `NOT_FOUND` | 404 |
| 시작 전 | `FAILED_PRECONDITION` | 400 |
| 소진 | `RESOURCE_EXHAUSTED` | 429 |
| 잘못된 입력 | `INVALID_ARGUMENT` | 400 |

## 알려진 한계

- **없는 캠페인 id로 온 요청은 Redis 문지기를 통과해 PG에 닿는다.**
  - `MISSING`이 키 소실인지 없는 캠페인인지 구분할 수 없어서, 매번 PG를 조회한다.
  - 공격자가 id를 바꿔 가며 보내면 "없음"을 캐시해도 막지 못한다.
  - 그래서 방어는 gateway의 클라이언트별 rate limit에 맡긴다. 이 rate limit 없이 `IssueCoupon`을 외부에 열지 않는다.
- Redis 키와 free 목록이 함께 사라지면, free 목록에 있던 번호는 다시 쓰이지 않는다.
- 그 결과 몇 장 덜 발급될 수 있다.
- 문제가 되면 `_reseed`에서 PG의 빈 seq를 찾아 free 목록을 채운다.
