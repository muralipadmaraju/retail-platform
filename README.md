# Retail Platform — DevOps Assessment Task 1

This repository implements Task 1: enterprise release, emergency payment hotfix, Jenkins deployment validation, and automatic rollback.

## Versions
- `v4.2.0`: initial production baseline
- `v4.2.1`: payment hotfix and production release
- `v4.2.2`: temporary failure-injection release; starts but intentionally fails `/health`

## Branches
- `main` — production-ready code
- `develop` — ongoing development
- `release/4.3.0` — release preparation
- `hotfix/payment-4.2.1` — emergency production fix

## Application
- Flask API on port `8081`
- `/` exposes application/version/environment
- `/payment` demonstrates the payment defect fix
- `/health` is used by Docker and Jenkins
- `FAIL_HEALTH=true` intentionally makes the health endpoint return HTTP 500

## Docker
Build examples:

```text
docker build -t retail-app:4.2.1 .
docker run -d --name retail-app-4.2.1 -p 8081:8081 --network retail-network -e APP_VERSION=4.2.1 -e ENVIRONMENT=PRODUCTION -e PAYMENT_MODE=fixed retail-app:4.2.1
```

The Dockerfile runs as a non-root user and contains a HEALTHCHECK.

## Jenkins
The `Jenkinsfile` accepts:
- `DEPLOYMENT_ACTION`: DEPLOY / ROLLBACK
- `ENVIRONMENT`: UAT / PRODUCTION
- `VERSION`: free-text semantic version
- `CONFIRM_PROD`: YES / NO

Production deployment requires `CONFIRM_PROD=YES`. The pipeline validates the Git tag, records the current production image, builds a unique image tag using Jenkins `BUILD_NUMBER`, starts a candidate, checks `/health`, and only then promotes it. A failed deployment removes the candidate and attempts to restore the previous production image. The build remains failed when rollback was required.

## Required evidence commands
```text
git branch -a
git log --oneline --graph --decorate --all
git tag -n
docker images retail-app
docker ps -a
docker inspect retail-app-prod
docker network inspect retail-network
```

## Feature A
Customer-friendly release metadata added during development.

## Feature B
<<<<<<< HEAD
Prepare payment monitoring notes for development.
=======
Prepare payment monitoring notes for release 4.3.0.
>>>>>>> release/4.3.0
