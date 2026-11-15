# 0002. 서비스는 gRPC만 열고, 외부 HTTP/JSON은 Envoy Gateway가 변환한다

- 상태: 채택
- 날짜: 2026-11-15

## 맥락

외부 클라이언트(브라우저 등)는 HTTP/JSON을 써야 한다. 서비스 간 호출은 빠르고 계약이 엄격해야 한다. 처음 쿠폰 앱은 REST(FastAPI)와 gRPC를 한 프로세스에서 함께 열었다. 그래서 같은 기능을 두 번 노출하고 에러 매핑도 두 벌 관리했다.

## 결정

- 서비스는 gRPC만 연다.
- 외부 요청은 전부 Envoy Gateway(Gateway API)를 거친다.
  - JSON ↔ gRPC 변환은 Envoy의 gRPC-JSON transcoder가 한다.
  - REST 경로는 proto의 `google.api.http` 옵션으로만 선언한다.
- 서비스는 gRPC 상태 코드만 고른다. HTTP 상태 코드는 transcoder의 표준 매핑을 따른다.
- gateway가 맡는 일은 다음뿐이다.
  - 라우팅
  - TLS, CORS
  - JWT 검증
  - 일반 rate limit
  - trace 시작
- 비즈니스 로직, 응답 조합, 권한 판단은 gateway에 넣지 않는다.
- 인증은 gateway가 JWT를 검증하고 사용자 id를 `x-user-id` 메타데이터로 넘긴다. 서비스는 이를 신뢰하고 권한 판단만 한다.
- 서비스 간 호출은 headless Service와 클라이언트 `round_robin`을 쓴다. 일반 k8s Service는 연결 단위로 분산해 gRPC 요청이 한 pod에 몰린다.
- 헬스체크는 gRPC health checking 프로토콜을 쓴다.

## 결과

- proto 파일 하나가 서비스 간 계약이자 외부 API 명세가 된다.
- 엔드포인트를 추가할 때 gateway 코드는 필요 없고, proto 주석 한 줄이면 된다.
- 기존 HTTP 상태 코드가 바뀐다: 시작 전 403 → 400, 소진 409 → 429.
- Envoy Gateway에는 transcoding 전용 API가 없다. `EnvoyPatchPolicy`로 필터를 주입해야 하는데, 이 기능은 문서가 보안 위험을 경고한다. 너무 번거로우면 일반 Envoy Deployment로 바꾼다.

## 검토한 대안

- **직접 만든 FastAPI gateway**: 서비스가 늘수록 핸들러 코드가 늘고, 선착순 트래픽에서 Python 홉이 병목이 된다.
- **Kong, APISIX**: 별도 저장소(etcd, DB)가 필요해 지금 규모에는 무겁다.
