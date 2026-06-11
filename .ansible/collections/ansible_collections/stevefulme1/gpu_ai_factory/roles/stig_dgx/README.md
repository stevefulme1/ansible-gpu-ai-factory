# stig_dgx

DISA STIG hardening for DGX nodes. Applies security controls including service hardening, SSH configuration, audit logging, and filesystem protections.

## Requirements

- `stevefulme1.gpu_ai_factory` collection

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `stig_profile` | `high` | STIG profile: high, medium, or low |
| `remediate` | `true` | Apply remediation or report only |
| `audit_only` | `false` | Report findings without changes |
| `stig_disabled_services` | See defaults | Services to disable (bluetooth, cups, etc.) |
| `stig_ssh_permit_root_login` | `no` | SSH PermitRootLogin setting |
| `stig_ssh_max_auth_tries` | `3` | SSH MaxAuthTries setting |

See `defaults/main.yml` for all variables.

## Example Playbook

```yaml
- hosts: dgx_nodes
  roles:
    - role: stevefulme1.gpu_ai_factory.stig_dgx
      vars:
        stig_profile: high
        audit_only: true
```

## License

GPL-3.0-or-later
