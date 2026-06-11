# vault_integration

Configures HashiCorp Vault for AI Factory credential management including KV secrets engine, policies, AppRole authentication, and audit logging.

## Requirements

- `stevefulme1.gpu_ai_factory` collection
- HashiCorp Vault instance (unsealed)

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `vault_addr` | `https://vault.example.com:8200` | Vault server address |
| `vault_engine_path` | `secret` | Secrets engine mount path |
| `vault_engine_type` | `kv-v2` | Secrets engine type |
| `vault_policies` | See defaults | Vault policies to create |

See `defaults/main.yml` for all variables.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.gpu_ai_factory.vault_integration
      vars:
        vault_addr: "https://vault.internal:8200"
        vault_token: "{{ vault_root_token }}"
```

## License

GPL-3.0-or-later
