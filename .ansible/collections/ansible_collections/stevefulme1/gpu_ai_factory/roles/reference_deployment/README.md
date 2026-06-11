# reference_deployment

Deploys the AI Factory reference architecture including GPU operator, model serving, observability, networking, and storage.

## Requirements

- `stevefulme1.gpu_ai_factory` collection
- Kubernetes/OpenShift cluster with GPU-capable nodes

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cluster_size` | `4` | Number of GPU nodes |
| `gpu_type` | `nvidia_a100` | GPU model for the deployment |
| `network_type` | `infiniband` | Network interconnect type |
| `storage_backend` | `ceph` | Storage backend |
| `model_serving_enabled` | `true` | Deploy model serving stack |
| `model_serving_framework` | `triton` | Serving framework |
| `observability_enabled` | `true` | Deploy observability stack |
| `observability_stack` | `prometheus` | Observability platform |

See `defaults/main.yml` for all variables.

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.gpu_ai_factory.reference_deployment
      vars:
        cluster_size: 8
        gpu_type: nvidia_h100
```

## License

GPL-3.0-or-later
