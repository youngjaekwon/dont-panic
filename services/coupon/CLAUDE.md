# coupon 서비스

선착순 쿠폰 발급. 계약은 `proto/coupon/v1/coupon.proto`. 발급 흐름, 정합성 보장, 각 구현 선택의 이유는 `docs/design.md`에 있다. 아래 항목을 바꾸기 전에 그 문서를 먼저 읽는다.

## 깨면 안 되는 불변식

- 발급 판정의 최종 권한은 PG의 `_ISSUE` 한 문장에 있다. Redis 결과만으로 발급을 확정하지 않는다.
- 응답은 PG 커밋 후에만 보낸다.
- `campaigns` row를 발급 경로에서 UPDATE하지 않는다.
- Redis 실패나 유실이 초과 발급으로 이어지면 안 된다. 새 경로를 추가하면 `test_redis_*` 테스트와 같은 장애 시나리오로 검증한다.

## 성능 때문에 유지하는 것

다음은 측정으로 확인한 선택이니 단순화하지 않는다.

- `_ISSUE`를 미리 만들어 두는 것
- AUTOCOMMIT + Core 연결
- 세션의 지연 연결과 조건부 `close()`
- `BlockingConnectionPool`

## 연결된 이름

- `SEQ_UNIQUE` 제약 이름은 리포지토리의 예외 분기와 연결되어 있다. 바꾸면 마이그레이션도 함께 바꾼다.
- Redis 키는 `campaign:{id}` hash tag 형식을 유지한다.

## 문서 갱신

- 설계나 알려진 한계가 바뀌면 `docs/design.md`를 같은 커밋에서 고친다.
- 실행법이나 API가 바뀌면 `README.md`를 같은 커밋에서 고친다.
