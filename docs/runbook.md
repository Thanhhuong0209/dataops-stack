# Runbook

## Service health checks

```bash
docker ps
curl http://localhost:8428
curl http://localhost:3000
```

## Restart stack

```bash
docker compose down
docker compose up -d --build
```

## Rollback

- Restore previous image tag
- Re-run deployment playbook
- Validate health and logs
