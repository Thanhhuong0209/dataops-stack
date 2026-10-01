# Architecture

This project is designed as a lightweight but production-oriented DevOps platform.

## Components

- Ansible: infrastructure provisioning
- Docker Compose: service orchestration
- Jenkins: CI/CD pipeline
- Dagster: data orchestration
- VictoriaMetrics: metric storage
- Grafana: visualization
- Traefik: reverse proxy and routing

## Deployment flow

1. Developer pushes code
2. Jenkins triggers build pipeline
3. Docker image is built and pushed
4. Ansible or Compose deploys the new release
5. Monitoring observes service behavior

## Target topology

```text
GitHub
  -> Jenkins
    -> Docker Build
      -> Deploy to VM / server
        -> Docker Compose
          -> Dagster
          -> VictoriaMetrics
          -> Grafana
          -> Traefik
```
