# DevOps Data Platform

A practical DevOps and data platform project built around Dagster, Docker, Ansible, Jenkins, VictoriaMetrics, and Traefik.

## Why this project matters

This repository is designed to demonstrate a real-world engineering workflow instead of a simple toy example.

It covers:
- infrastructure provisioning with Ansible
- service deployment with Docker Compose
- CI/CD automation with Jenkins and GitHub Actions
- workflow orchestration with Dagster
- data collection and metric ingestion with VictoriaMetrics
- reverse proxy and route management with Traefik
- monitoring and alert readiness with Grafana

## Architecture

```text
+------------------+
| Developer / GitHub |
+---------+--------+
          |
          v
+------------------+
| CI / CD          |
| - GitHub Actions |
| - Jenkins        |
+---------+--------+
          |
          v
+------------------+
| App / Data Layer |
| - Dagster        |
| - Python jobs    |
| - Time-series    |
|   ingestion      |
+---------+--------+
          |
          v
+------------------+
| Runtime / Infra  |
| - Docker/Podman  |
| - Traefik        |
| - Ansible        |
| - Compose        |
+---------+--------+
          |
          v
+------------------+
| Observability    |
| - VictoriaMetrics|
| - Grafana        |
+------------------+
```

This project follows a layered architecture:
- application logic: Dagster and Python workloads
- platform automation: Ansible and Docker/Podman orchestration
- delivery pipeline: CI/CD through GitHub Actions and Jenkins
- observability: metrics collection and monitoring via VictoriaMetrics and Grafana

## Main capabilities

- automated server bootstrap with Ansible
- environment separation for dev / staging / production
- compose-based service orchestration
- deployment workflow with rollback readiness
- metric generation and ingestion pipeline
- CI validation using real business smoke checks

## Repository structure

```text
.
├── apps/
│   ├── dagster/
│   └── sample-app/
├── infra/
│   ├── ansible/
│   │   ├── ansible.cfg
│   │   ├── requirements.yml
│   │   ├── inventory/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   ├── group_vars/
│   │   │   └── all/
│   │   ├── playbooks/
│   │   │   ├── bootstrap.yml
│   │   │   ├── deploy.yml
│   │   │   └── rollback.yml
│   │   └── roles/
│   │       ├── common/
│   │       ├── docker/
│   │       ├── traefik/
│   │       ├── jenkins/
│   │       ├── grafana/
│   │       ├── victoriametrics/
│   │       └── dagster/
│   └── docker/
│       └── .env.example
├── monitoring/
│   └── README.md
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   ├── secrets.md
│   └── runbook.md
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── .gitignore
├── .dockerignore
├── Dockerfile
├── Jenkinsfile
├── LICENSE
├── README.md
├── docker-compose.yml
├── docker-compose.override.yml
├── dagster_pipeline.py
├── vm_ingestion_test.py
├── requirements.txt
├── pyproject.toml
├── REPORT.md
└── .env.example
```

## Quick start

### 1. Create the local environment

```bash
make venv
```

### 2. Install dependencies

```bash
make install
```

### 3. Run a real smoke test

```bash
make smoke
```

This validates the actual business behavior: generating time-series data for multiple sensor streams without requiring a live VictoriaMetrics service.

### 4. Start the platform stack

```bash
make up
```

### 5. Validate endpoints

- Dagster UI: http://localhost:3030
- VictoriaMetrics: http://localhost:8428
- Jenkins: http://localhost:8080

### Common developer commands

```bash
make help
make logs
make down
make clean
```

### Local environment template

Copy the runtime template before starting services:

```bash
cp docker/.env.example docker/.env
```

The template is stored in [docker/.env.example](docker/.env.example).

## CI/CD

The repository includes:
- GitHub Actions smoke validation on push and pull requests
- release workflow triggered by version tags
- Jenkins pipeline entry point for deployment automation

## Deployment model

This project is designed for:
- dev environment
- staging environment
- production environment

The deployment flow is:

```text
code commit -> pipeline -> build -> deploy -> health validation -> rollback if needed
```

## Observability

The service is ready to produce and monitor telemetry for:
- temperature
- humidity
- application health
- infrastructure metrics

## Roadmap

Planned improvements:
- stronger secret management with Ansible Vault and GitHub Secrets
- full Traefik routing rules
- Grafana dashboard provisioning
- production rollback automation
- Kubernetes or cloud deployment variants

## License

This project is intended for learning, portfolio demonstration, and further DevOps platform development.
