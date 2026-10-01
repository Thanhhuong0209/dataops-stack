# Secrets Management

## Recommended approach

- Store passwords and tokens in environment variables
- Use Ansible Vault for infrastructure secrets
- Use GitHub repository secrets for CI/CD pipelines
- Keep local `.env` files ignored by git

## Example

```bash
export DOCKERHUB_USERNAME="your-user"
export DOCKERHUB_TOKEN="your-token"
```

## Ansible Vault example

```bash
ansible-vault create ansible/vault/secrets.yml
```
