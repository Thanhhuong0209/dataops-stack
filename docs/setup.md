# Setup Guide

## 1. Clone repository

```bash
git clone <your-repo-url>
cd <repo-folder>
```

## 2. Create environment file

```bash
cp docker/.env.example docker/.env
```

## 3. Run locally

```bash
docker compose up -d --build
```

## 4. Deploy via Ansible

```bash
cd ansible
ansible-playbook -i inventory/dev/hosts.yml playbooks/bootstrap.yml
```

## 5. Validate services

- Dagster: http://localhost:3000
- VictoriaMetrics: http://localhost:8428
- Jenkins: http://localhost:8080
