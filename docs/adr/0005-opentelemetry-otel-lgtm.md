# 0005. 관측은 OpenTelemetry → Collector → otel-lgtm

- 상태: 채택
- 날짜: 2026-11-15

## 맥락

서비스 간 호출과 이벤트가 생기면 요청 하나가 여러 서비스를 거친다. 로그만으로는 원인을 추적할 수 없다.

## 결정

- 모든 서비스는 다음을 OTel SDK로 계측하고 OTLP로 Collector에 보낸다.
  - gRPC 호출
  - DB 접근
  - Redis 접근
  - Kafka 송수신
- trace context는 gRPC 메타데이터와 Kafka 헤더로 전파한다.
- 로그는 stdout에 JSON으로 쓰고 trace id를 포함한다.
- 백엔드는 `grafana/otel-lgtm` 하나로 시작한다. 이 이미지 하나에 Tempo, Loki, Prometheus/Mimir, Grafana가 들어 있다.

## 결과

- 벤더 중립 계측이라 백엔드를 바꿔도 서비스 코드는 그대로다.
- otel-lgtm은 개발과 데모용이다. 운영 규모가 되면 구성 요소를 나눈다.
