---
name: new-service
description: services/ 아래에 새 도메인 서비스를 만들 때 따르는 절차. 기존 서비스 복사, 계약 작성, 데이터 분리, 문서까지 포함한다.
disable-model-invocation: true
---

# 새 서비스 추가 절차

`<name>`은 새 서비스 이름이다. 소문자 한 단어로 짓고, proto 패키지명으로도 쓴다.

1. **골격 복사**
   - `services/coupon`을 `services/<name>`으로 복사한다.
   - 쿠폰 도메인 코드, 마이그레이션, 테스트, `loadtest/`, `docs/design.md`를 지운다.
   - 그 뒤 `pyproject.toml`의 `name`과 `description`을 바꾸고 `uv lock`을 실행한다.
2. **계약**
   - `proto/<name>/v1/<name>.proto`를 쓴다.
   - `proto-change` 스킬 절차로 코드를 생성한다.
3. **서버 연결**
   - `app/api/server.py`에서 새 servicer를 등록한다.
   - 다른 서비스를 호출해야 하면 그 서비스의 생성 stub을 쓴다. 다른 서비스의 `app` 코드는 import하지 않는다.
4. **데이터**
   - PG database와 계정을 `<name>`으로 정한다.
   - Redis를 쓰면 키 prefix를 `<name>:`으로 정한다.
   - 다른 서비스의 database나 키에 접근하지 않는다.
5. **로컬 테스트 환경**
   - `docker-compose.yml`의 `POSTGRES_*` 기본값과 `.env.example`의 `POSTGRES_*` 값을 새 서비스 이름으로 바꾼다.
   - 사용자에게 `cp .env.example .env` 실행을 요청한다. Claude는 `.env`를 만들 수 없다.
   - 포트가 다른 서비스와 겹치면 바꾼다.
6. **배포**: 기존 서비스에 `deploy/`가 있으면 매니페스트와 GRPCRoute를 복사해 이름을 바꾼다.
7. **문서**
   - `services/<name>/CLAUDE.md`에는 깨면 안 되는 불변식만 쓴다.
   - `docs/design.md`에는 설계와 이유를 쓴다.
   - `README.md`에는 실행법과 API를 쓴다.
   - 루트 `README.md`의 서비스 표에 한 줄 추가한다.
8. **검증**
   - `make -C services/<name> lint test`를 통과시킨다. 의존성이 쿠폰과 다르면 `Makefile`의 `test` 타깃을 고친다. CI 파일은 고치지 않는다.
   - 새 인프라 구성 요소가 필요했다면 ADR을 먼저 쓴다.
