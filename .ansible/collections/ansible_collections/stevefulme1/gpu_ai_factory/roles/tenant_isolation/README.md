# tenant_isolation

Sets up multi-tenant isolation including network segmentation via InfiniBand partitions, RBAC configuration, and GPU fencing.

## Requirements

- `stevefulme1.nvidia_ai_factory` collection
- BCM API access credentials

## Role Variables

See `defaults/main.yml` for available variables and their defaults.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.nvidia_ai_factory.tenant_isolation
      vars:
        bcm_url: "https://bcm.example.com"
        bcm_token: "{{ vault_bcm_token }}"
```

## License

GPL-3.0-or-later
