# 플랫폼 모노레포

한 제품의 도메인 서비스들을 담는 MSA 저장소. 서비스는 gRPC만 열고, 외부 HTTP/JSON은 Envoy Gateway가 gRPC로 변환한다. 규칙과 방향은 [CLAUDE.md](CLAUDE.md)에 있다.

## 서비스

| 서비스 | 설명 | 계약 |
|---|---|---|
| 아직 없음 | | |

## 로드맵

1. ~~모노레포 구조, REST 제거, buf 도입~~ (완료)
2. k3d + Envoy Gateway에 coupon 배포(`IssueCoupon`의 클라이언트별 rate limit 포함), 부하 테스트 재측정 ([ADR 0002](docs/adr/0002-grpc-only-services-envoy-gateway.md), [0006](docs/adr/0006-k8s-k3d-kustomize.md))
3. OpenTelemetry 계측 + otel-lgtm ([ADR 0005](docs/adr/0005-opentelemetry-otel-lgtm.md))
4. 두 번째 서비스 + Kafka + outbox ([ADR 0004](docs/adr/0004-kafka-outbox-events.md))

## 문서

- [docs/adr/](docs/adr): 스택과 구조를 이렇게 정한 이유
- `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`: Claude Code용 작업 지침

## 계약 코드 생성

buf는 도커 이미지로 실행하므로 따로 설치하지 않아도 된다.

```sh
make proto      # lint → gen/python 생성 → gen/descriptor.binpb 빌드
make breaking   # main 브랜치 대비 호환성 검사
```

## 서비스 테스트

각 서비스 폴더의 README를 따른다. Python 서비스는 다음과 같다.

```sh
cd services/<서비스>
cp .env.example .env
docker compose up -d --wait
uv sync && uv run pytest
```
