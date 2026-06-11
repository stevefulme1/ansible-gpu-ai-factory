# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email the maintainer at sfulmer@redhat.com with details.
3. Include steps to reproduce the issue.
4. Allow reasonable time for a fix before public disclosure.

## Security Considerations

- BCM credentials are marked `no_log` in all modules.
- Redfish/IPMI credentials should be stored in Ansible Vault.
- `validate_certs` defaults to `true` for all HTTPS connections.
- InfiniBand partition keys are treated as sensitive data.
