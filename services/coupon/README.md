# coupon: 선착순 쿠폰 발급

gRPC 서비스(50051). 외부 HTTP/JSON은 gateway가 transcoding한다. 저장소는 Redis(문지기)와 PostgreSQL(최종 판정)이다. 설계와 정합성 보장은 [docs/design.md](docs/design.md)에 있다.

## 실행

```sh
cp .env.example .env                                # 접속 정보 (환경 변수가 있으면 그쪽이 우선)
docker compose up -d --wait                         # PG, Redis
uv sync
uv run pytest                                       # 정합성 테스트
uv run lint-imports                                 # 레이어 규칙
PYTHONPATH=../../gen/python uv run python -m app.main   # 로컬 실행 (먼저 alembic upgrade head)
```

설정:

| 환경 변수 | 필수 | 기본값 |
|---|---|---|
| `DATABASE_URL` | 예 | |
| `REDIS_URL` | 예 | |
| `PG_POOL_SIZE` | | 20 |
| `REDIS_POOL_SIZE` | | 64 |
| `GRPC_PORT` | | 50051 |

이미지는 저장소 루트에서 빌드한다: `docker build -f services/coupon/Dockerfile .`

## API

| 기능 | gRPC (`coupon.v1.CouponService`) | gateway REST |
|---|---|---|
| 캠페인 생성 | `CreateCampaign` | 없음 (클러스터 내부 전용) |
| 캠페인 + 발급 수 | `GetCampaign` | 없음 (클러스터 내부 전용) |
| 쿠폰 목록 (페이지) | `ListCoupons` `{campaign_id, page_size, page_token}` | 없음 (클러스터 내부 전용) |
| 쿠폰 발급 | `IssueCoupon` | `POST /v1/campaigns/{campaign_id}/coupons` |

다음 RPC는 외부에 열지 않는다.
- `ListCoupons`: 발급된 쿠폰 코드를 돌려준다.
- `CreateCampaign`: 권한 확인이 없다.
- `GetCampaign`: 운영용 조회다.

발급 실패: 없음 `NOT_FOUND`(404), 시작 전 `FAILED_PRECONDITION`(400), 소진 `RESOURCE_EXHAUSTED`(429).

## 부하 테스트 (k6)

캠페인을 `START_DELAY`(기본 3초) 뒤에 시작하도록 만들고, 시작 전부터 `RATE` rps로 발급 요청을 보낸 뒤 PG 결과를 검증한다.

통과 조건:
- 성공 응답 수 == 수량
- 예상 밖 응답 0
- PG 발급 수 == 수량
- 코드 중복 0
- 시작 시각 전 발급 0

스크립트는 `loadtest/k6.js`이고 `/gen/descriptor.binpb`를 읽는다. k3d 배포 후 다시 측정한다.

이전 구조의 측정치(uvicorn 6워커 한 컨테이너, REST와 gRPC 직접 노출, MacBook 10코어 한 대에 k6·앱·PG·Redis 전부, 10초):

| 프로토콜 | 수량 | 처리 rps | p50 | p99 | 전량 발급 소요 | 검증 |
|---|---|---|---|---|---|---|
| gRPC | 1,000 | 9,983 | 0.96ms | 51ms | 0.13s | 통과 |
| gRPC | 5,000 | 9,955 | 0.84ms | 32ms | 0.50s | 통과 |
| HTTP | 1,000 | 9,939 | 0.87ms | 83ms | 0.23s | 통과 |
| HTTP | 5,000 | 9,929 | 1.00ms | 93ms | 0.50s | 통과 |
