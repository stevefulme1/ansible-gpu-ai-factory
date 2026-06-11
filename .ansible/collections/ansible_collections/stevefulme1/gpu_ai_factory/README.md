# stevefulme1.gpu_ai_factory

Ansible Collection for multi-vendor GPU AI Factory automation.

Provides comprehensive automation for NVIDIA Base Command Manager (BCM),
DGX/HGX systems, GPU allocation, tenant isolation, InfiniBand/RDMA networking,
NeMo model deployment, Triton Inference Server, NGC catalog management,
AMD MI300X GPU management via ROCm SMI, Intel Gaudi accelerator management
via Habana Labs API, DISA STIG and CIS benchmark security compliance,
HashiCorp Vault credential integration, AAP subscription sizing,
and Professional Services deployment bundles.

## Requirements

- Ansible >= 2.16.0
- Python >= 3.12
- `requests` Python library

## Installation

```bash
ansible-galaxy collection install stevefulme1.gpu_ai_factory
```

## Modules

### BCM Infrastructure
| Module | Description |
|--------|-------------|
| `bcm_cluster` | Manage BCM clusters |
| `bcm_cluster_info` | List/get BCM clusters |
| `bcm_node` | Manage DGX/HGX nodes |
| `bcm_node_info` | List/get nodes with GPU details |
| `bcm_tenant` | Manage BCM tenants |
| `bcm_tenant_info` | List tenants |
| `bcm_gpu_allocation` | Allocate/deallocate GPU slices |
| `bcm_gpu_allocation_info` | List GPU allocations |
| `bcm_job` | Submit/manage BCM jobs |
| `bcm_job_info` | List/get job status |

### DGX Hardware
| Module | Description |
|--------|-------------|
| `dgx_firmware` | Manage DGX firmware updates |
| `dgx_firmware_info` | Get firmware versions |
| `dgx_health` | Query DGX health via Redfish |
| `dgx_power` | Manage DGX power state |
| `dgx_bios` | Configure DGX BIOS settings |

### NVIDIA AI Software
| Module | Description |
|--------|-------------|
| `nemo_model` | Deploy/manage NeMo models |
| `nemo_model_info` | List deployed NeMo models |
| `triton_server` | Manage Triton Inference Server |
| `triton_model` | Load/unload Triton models |
| `ngc_image` | Pull/manage NGC container images |

### Network
| Module | Description |
|--------|-------------|
| `infiniband_port` | Configure InfiniBand ports |
| `infiniband_partition` | Manage IB partitions |
| `infiniband_info` | Query IB fabric status |
| `nvlink_info` | Query NVLink topology |
| `rdma_config` | Configure RDMA settings |

### AMD MI300X (new in 1.1.0)
| Module | Description |
|--------|-------------|
| `amd_gpu_info` | Query AMD GPU status via ROCm SMI |
| `amd_gpu_config` | Configure AMD MI300X GPU settings |
| `amd_rocm_driver` | Manage ROCm driver installation/updates |
| `amd_rocm_driver_info` | Query ROCm driver and version info |

### Intel Gaudi (new in 1.1.0)
| Module | Description |
|--------|-------------|
| `gaudi_device_info` | Query Intel Gaudi accelerator status |
| `gaudi_device_config` | Configure Intel Gaudi device settings |
| `gaudi_firmware` | Manage Intel Gaudi firmware updates |
| `gaudi_firmware_info` | Query Gaudi firmware versions |
| `habana_workload` | Manage Habana workload submissions |
| `habana_workload_info` | Query workload status |

### Credential Management (new in 1.1.0)
| Module | Description |
|--------|-------------|
| `credential_store` | Manage AI platform credentials in HashiCorp Vault |
| `credential_store_info` | List/query stored credential metadata |

### Subscription Calculator (new in 1.1.0)
| Module | Description |
|--------|-------------|
| `ai_factory_inventory_report` | Generate AAP subscription sizing report |
| `ai_factory_inventory_report_info` | Query existing inventory reports |

## Inventory Plugin

`nvidia_bcm_inventory` -- Dynamic inventory from BCM API with automatic
grouping by node type and GPU model.

## Roles

| Role | Description |
|------|-------------|
| `dgx_provision` | Full DGX node provisioning |
| `gpu_allocation` | Allocate GPU slices to tenant |
| `tenant_isolation` | Configure tenant isolation |
| `infiniband_rdma` | Configure IB RDMA for multi-node training |
| `virtual_media_boot` | DGX provisioning via virtual media |
| `nemo_deploy` | Deploy NeMo models with Triton |
| `stig_dgx` | DISA STIG hardening for DGX nodes (new in 1.1.0) |
| `cis_ai_cluster` | CIS benchmark hardening for AI clusters (new in 1.1.0) |
| `vault_integration` | Configure HashiCorp Vault for AI Factory (new in 1.1.0) |
| `ps_lab_setup` | Stand up a PS demo environment (new in 1.1.0) |
| `reference_deployment` | Deploy AI Factory reference architecture (new in 1.1.0) |

## EDA Event Sources

| Plugin | Description |
|--------|-------------|
| `dgx_telemetry` | Stream DGX health via Redfish/IPMI |
| `infiniband_fabric` | Monitor IB fabric events |
| `ngc_catalog` | Watch NGC catalog for new releases |

## License

GPL-3.0-or-later
