# 0003. 계약은 protobuf + buf, 생성 코드는 커밋한다

- 상태: 채택
- 날짜: 2026-11-15

## 맥락

언어가 섞일 수 있고, 같은 계약을 서비스 코드 생성, Envoy transcoder, k6 부하 테스트가 함께 쓴다. `grpcio-tools`는 Python 전용이고 breaking 검사가 없다.

## 결정

- 계약 원본은 `proto/<서비스>/v1/`뿐이다. RPC와 이벤트 메시지를 모두 여기에 둔다.
- buf로 lint, breaking 검사, 코드 생성, descriptor 빌드를 한다.
  - buf는 도커 이미지로 실행해 로컬 설치를 요구하지 않는다.
  - 원격 플러그인 버전은 서비스 런타임(protobuf, grpcio) 버전과 맞춰 고정한다.
- 생성 코드는 `gen/<언어>/`에, 전체 descriptor set은 `gen/descriptor.binpb`에 두고 커밋한다.
- lint는 `STANDARD`에서 `RPC_REQUEST_RESPONSE_UNIQUE`, `RPC_RESPONSE_STANDARD_NAME`만 뺀다. Get과 Create가 리소스 메시지를 그대로 반환하는 AIP 스타일을 쓰기 위해서다.
- 호환이 깨지는 변경은 `v2` 패키지를 새로 만든다.

## 결과

- 생성 코드를 커밋하므로 서비스 빌드와 테스트에 buf가 필요 없다.
- Python 서비스는 `gen/python`을 `PYTHONPATH`로 참조한다. 생성 코드가 `google.api.annotations_pb2`를 import하므로 `googleapis-common-protos`가 필요하다.
- 원격 플러그인을 쓰므로 생성할 때 BSR에 네트워크로 접근해야 한다.
