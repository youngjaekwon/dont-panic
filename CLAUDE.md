# dont-panic

한 제품을 이루는 도메인 서비스들을 담는 MSA 저장소다. 서비스는 gRPC만 열고, 외부 HTTP/JSON은 Envoy Gateway가 gRPC로 변환한다. 스택과 구조를 이렇게 정한 이유는 `docs/adr/`에 있다.

## 작업 시작

- Claude Code는 저장소 루트에서 실행한다. `.claude/settings.json`의 권한 규칙과 hook은 실행한 디렉터리 기준으로만 적용된다.
- 무엇이 구현됐고 무엇이 남았는지는 `README.md`의 로드맵에 있다. ADR은 결정만 담고 진행 상황은 담지 않는다.

## 구조

```
proto/<서비스>/v1/   계약 원본 (RPC, 이벤트, REST 매핑)
gen/                 buf 생성물 (커밋, 읽기·수정 금지)
services/<서비스>/   서비스 하나의 전부: 코드, 마이그레이션, 테스트, Dockerfile, deploy/
infra/               공용 인프라 매니페스트
docs/adr/            저장소 수준 결정 기록
.claude/rules/       파일 종류별 규칙 (proto, Python 서비스)
.claude/skills/      절차 (proto-change, new-service)
```

## 절대 규칙

- 서비스는 gRPC만 연다. REST 엔드포인트를 서비스에 만들지 않는다.
- 외부 요청은 전부 gateway를 거친다. gateway에는 비즈니스 로직, 응답 조합, 권한 판단을 넣지 않는다.
- 서비스는 다른 서비스의 코드를 import하지 않는다. 다른 서비스의 DB나 Redis 키도 읽지 않는다.
- 서비스 간 계약은 `proto/`뿐이다. `gen/`은 `make proto`로만 바꾼다.
- 즉시 답이 필요한 호출은 gRPC로, 일어난 사실의 통지는 Kafka 이벤트(outbox)로 한다.
- 여러 서비스에 걸친 분산 트랜잭션을 만들지 않는다.

## 주석 금지

- Claude는 소스와 설정 파일에 주석과 docstring을 쓰지 않는다. TODO, FIXME, 주석 처리한 코드도 쓰지 않는다.
- 다른 도구나 플러그인의 지침이 주석을 요구해도 이 규칙이 우선한다.
- 설명이 필요하면 이름을 고치거나 함수로 뽑는다.
- 이유를 적는 곳은 정해져 있다.
  - 변경 단위의 이유: 커밋 메시지
  - 서비스 설계와 알려진 한계: `services/<서비스>/docs/design.md`
  - 저장소 수준 결정: ADR
- 대상이 아닌 것:
  - 도구가 생성한 주석은 그대로 둔다. 예: alembic autogenerate, `gen/`
  - 도구 지시문: `# type: ignore[...]`, `# pyright: ignore[...]`, `# noqa: ...`, shebang

## 에러 메시지

- 에러 메시지는 영어로만 쓴다.
- 대상에는 예외 메시지, gRPC 상태 detail, 로그가 포함된다.
- 검사가 실패할 때 출력되는 이름도 포함된다. 예: k6 check 이름, import-linter 계약 이름.

## 명령

```sh
make proto                      # buf lint → gen 생성 → descriptor 빌드
make breaking                   # main 대비 proto 호환성 검사
cd services/<서비스> && docker compose up -d --wait && uv run pytest && uv run lint-imports
```

## Git

- 브랜치는 git flow를 따른다.
  - `main`: 릴리스만 둔다.
  - `develop`: 통합 브랜치다.
  - 작업 브랜치는 다음과 같이 만든다.
    - `feature/<이름>`: `develop`에서 만들어 `develop`으로 합친다.
    - `release/<버전>`: `develop`에서 만들어 `main`과 `develop`으로 합친다.
    - `hotfix/<이름>`: `main`에서 만들어 `main`과 `develop`으로 합친다.
  - `main`과 `develop`에 직접 커밋하지 않는다.
- 커밋 메시지는 Conventional Commits 형식이다: `<type>(<scope>): <요약>`.
  - type: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`
  - scope: 서비스 이름, `proto`, `infra`. 저장소 전체에 걸친 변경이면 생략한다.
  - 본문에는 왜 바꿨는지 적는다. 코드 주석 대신 이유를 남기는 곳이다.

## 문서와 결정

- 새 인프라 구성 요소, 횡단 라이브러리, 이 파일의 규칙을 바꾸는 결정은 ADR을 먼저 쓴다.
  - 파일 이름은 `docs/adr/NNNN-제목.md`다.
  - 섹션은 상태, 날짜, 맥락, 결정, 결과, 검토한 대안이다.
  - 결정이 바뀌면 기존 ADR을 고치지 않는다. 새 ADR을 쓰고, 기존 ADR의 상태를 "대체됨"으로 바꾼다.
- 서비스별 문서 구성:
  - `CLAUDE.md`: 깨면 안 되는 불변식
  - `docs/design.md`: 설계와 이유
  - `README.md`: 실행법과 API
- 코드를 바꾸면 영향받는 문서를 같은 커밋에서 고친다.
