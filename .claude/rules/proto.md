---
paths:
  - "proto/**"
---

# proto 규칙

- 패키지는 `<서비스>.v1`, 파일 위치는 `proto/<서비스>/v1/`. 디렉터리와 패키지가 일치해야 lint를 통과한다.
- 외부 REST 경로는 `google.api.http` 옵션으로만 선언한다. 형식은 `/v1/<리소스>`, 생성은 `post` + `body: "*"`.
- 이벤트 메시지는 같은 패키지의 `events.proto`에 둔다. 토픽 이름은 `<서비스>.<이벤트>.v1`.
- 실패는 gRPC 상태 코드로 표현한다. HTTP 코드는 transcoder 표준 매핑이 정하므로 그 매핑을 보고 고른다. 예: `FAILED_PRECONDITION`은 400, `RESOURCE_EXHAUSTED`는 429, `ABORTED`는 409.
- 필드 번호는 재사용하지 않는다. 지운 필드는 `reserved`로 막는다.
- 호환이 깨지는 변경은 `v1`을 고치지 않고 `v2` 패키지를 새로 만든다.
  - 예외: 첫 릴리스 전에는 `v1`을 직접 바꿀 수 있다. 첫 릴리스는 `main`에 버전 태그가 붙은 시점이다.
  - 이 경우에도 지운 필드는 `reserved`로 막는다. `make breaking` 실패는 예상된 결과다.
- 고친 뒤에는 `proto-change` 스킬 절차를 따른다. `gen/`은 직접 고치지 않는다.
- 근거: `docs/adr/0002-grpc-only-services-envoy-gateway.md`, `docs/adr/0003-protobuf-buf-contracts.md`
