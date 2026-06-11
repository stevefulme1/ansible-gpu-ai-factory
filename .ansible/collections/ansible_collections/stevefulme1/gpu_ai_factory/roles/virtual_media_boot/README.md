# virtual_media_boot

Provisions DGX systems using virtual media boot instead of PXE. Mounts ISO via Redfish, sets boot order, and initiates installation.

## Requirements

- `stevefulme1.nvidia_ai_factory` collection
- BCM API access credentials

## Role Variables

See `defaults/main.yml` for available variables and their defaults.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.nvidia_ai_factory.virtual_media_boot
      vars:
        bcm_url: "https://bcm.example.com"
        bcm_token: "{{ vault_bcm_token }}"
```

## License

GPL-3.0-or-later
