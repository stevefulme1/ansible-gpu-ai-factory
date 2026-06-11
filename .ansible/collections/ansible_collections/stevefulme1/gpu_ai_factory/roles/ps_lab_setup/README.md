# ps_lab_setup

Stands up a Professional Services demo environment with GPU-accelerated models, monitoring, and sample notebooks.

## Requirements

- `stevefulme1.gpu_ai_factory` collection
- Kubernetes/OpenShift cluster with GPU nodes

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `lab_namespace` | `ai-factory-demo` | Namespace for the demo environment |
| `demo_models` | See defaults | Models to deploy (name, framework, replicas) |
| `monitoring_enabled` | `true` | Deploy GPU monitoring stack |
| `monitoring_namespace` | `monitoring` | Namespace for monitoring |
| `demo_users` | See defaults | Demo user accounts to create |

See `defaults/main.yml` for all variables.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.gpu_ai_factory.ps_lab_setup
      vars:
        lab_namespace: customer-demo
```

## License

GPL-3.0-or-later
