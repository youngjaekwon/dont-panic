---
paths:
  - "services/**/*.py"
---

# Python 서비스 규칙

## 구조

- 레이어는 위에서 아래로만 import한다: `main → di → api → services → repositories → models → core`. 서비스 폴더의 `pyproject.toml` import-linter 계약이 이를 강제한다.
- 각 레이어의 역할:
  - `api/`: gRPC servicer와 서버 기동만 둔다. 도메인 예외를 gRPC 상태 코드로 바꾸는 일은 여기서 한다.
  - `services/`: 트랜잭션 경계를 정한다.
  - `repositories/`: SQL과 Redis를 다룬다.
- 의존성 조립은 `di.py`(dishka)에서만 한다.
  - APP 스코프: 엔진, 풀, 클라이언트
  - REQUEST 스코프: 세션, 리포지토리, 서비스. gRPC 호출 하나가 REQUEST 스코프 하나다.
- 진입점은 `python -m app.main`이다. 컨테이너당 프로세스 하나로 띄우고, replica 수로 확장한다.

## 설정과 의존성

- 설정은 `core/config.py`의 `Settings`(pydantic-settings)로 읽는다.
  - 접속 정보처럼 환경마다 다른 값은 기본값을 두지 않는다. 튜닝 값만 기본값을 둔다.
  - 새 설정을 추가하면 `.env.example`에도 추가한다.
- 생성 코드는 `from <서비스>.v1 import <서비스>_pb2`로 import한다. `gen/python`은 `PYTHONPATH`로 들어온다. pytest는 `pythonpath`, Dockerfile은 `ENV`에서 지정한다.
- 의존성은 `uv add`로 추가한다. `uv.lock`은 직접 고치지 않는다.

## 마이그레이션

- 스키마 변경은 alembic 마이그레이션을 새로 만든다. 이미 커밋된 마이그레이션은 고치지 않는다.

## 검증

서비스 폴더에서 실행한다.

```sh
docker compose up -d --wait
uv run pytest
uv run lint-imports
```
