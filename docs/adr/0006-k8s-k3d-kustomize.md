# 0006. 배포는 k8s/k3s, 로컬은 k3d, 매니페스트는 Kustomize

- 상태: 채택
- 날짜: 2026-11-15

## 맥락

배포 대상은 k8s 또는 k3s다. gateway 설정을 docker compose용과 k8s용으로 두 벌 관리하고 싶지 않다.

## 결정

- 로컬 전체 실행도 k3d(도커 위의 k3s)로 하고, 배포 대상과 같은 매니페스트를 쓴다.
- 매니페스트는 kubectl에 내장된 Kustomize로 관리한다.
  - 서비스의 것은 `services/<서비스>/deploy/`에 둔다: Deployment, headless Service, GRPCRoute, migrate Job.
  - 공용 인프라는 `infra/`에 둔다: cluster, gateway, postgres, redis, kafka, observability.
- 마이그레이션은 배포마다 k8s Job으로 실행한다.
- 서비스 프로세스는 컨테이너당 하나이고, replica 수로 확장한다.
- docker compose는 서비스 단위 테스트에 필요한 PG와 Redis만 띄운다.

## 결과

- 로컬과 배포 환경의 차이가 줄어든다.
- 개발 루프가 compose보다 느리다. 이미지를 빌드하고 k3d에 올려야 한다. 이 루프가 고통스러워지면 Skaffold나 Tilt를 검토한다.

## 검토한 대안

- **Helm**: 템플릿 문법이 필요할 만큼 변형이 많지 않다.
- **ArgoCD 같은 GitOps**: 원격 클러스터가 생기면 검토한다.
