# cis_ai_cluster

CIS benchmark hardening for AI clusters. Applies Level 1 or Level 2 controls including password policies, account lockout, network hardening, and audit logging.

## Requirements

- `stevefulme1.gpu_ai_factory` collection

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cis_level` | `1` | CIS benchmark level (1 or 2) |
| `remediate` | `true` | Apply remediation or audit only |
| `cis_password_max_days` | `365` | Maximum password age |
| `cis_password_min_days` | `7` | Minimum password age |
| `cis_password_min_length` | `14` | Minimum password length |
| `cis_account_lockout_attempts` | `5` | Failed login attempts before lockout |
| `cis_account_lockout_time` | `900` | Lockout duration in seconds |
| `cis_log_retention_days` | `90` | Audit log retention in days |

See `defaults/main.yml` for all variables.

## Example Playbook

```yaml
- hosts: ai_cluster
  roles:
    - role: stevefulme1.gpu_ai_factory.cis_ai_cluster
      vars:
        cis_level: 2
        remediate: false
```

## License

GPL-3.0-or-later
