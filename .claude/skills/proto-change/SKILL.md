---
name: proto-change
description: proto/ 아래 계약(RPC, 메시지, 이벤트, REST 매핑)을 추가하거나 바꿀 때 따르는 절차. 코드 생성, 호환성 검사, 서비스 반영까지 포함한다.
---

# proto 변경 절차

1. `proto/<서비스>/v1/*.proto`를 고친다. 규칙은 `.claude/rules/proto.md`에 있다.
2. 저장소 루트에서 `make proto`를 실행한다. buf lint를 통과해야 하고, 다음이 갱신된다.
   - `gen/python/<서비스>/v1/`
   - `gen/descriptor.binpb`
3. `make breaking`을 실행한다. 실패하면 둘 중 하나를 택한다.
   - 변경을 호환되게 바꾼다. 예: 새 필드 추가, 지운 필드는 `reserved`.
   - `v2` 패키지를 새로 만든다.
   - 단, main에 아직 없는 새 proto는 비교 대상이 없으므로 이 검사가 의미 없다.
   - 첫 릴리스 전이라면 실패를 그대로 둘 수 있다. 조건은 `.claude/rules/proto.md`를 따른다.
4. 이 계약을 쓰는 모든 서비스를 고친다.
   - servicer와 클라이언트 코드
   - 테스트
   - REST 매핑이 바뀌었다면 서비스 `README.md`의 API 표
5. 영향받는 각 서비스 폴더에서 테스트를 통과시킨다.
6. `proto/`, `gen/`, 서비스 변경을 한 커밋에 담는다.

`gen/`은 읽기와 수정이 막혀 있다. 생성 결과는 proto와 `make proto` 출력으로 판단한다.
