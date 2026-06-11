# Changelog

## 1.1.1 (2026-05-18)

### Security

- Added `secret: true` to `bcm_token` and `bcm_password` options in lookup
  plugins (`dgx_images`, `dgx_categories`, `bcm_nodes`) and the
  `nvidia_bcm_inventory` inventory plugin.

## 1.1.0 (2026-05-18)

### New Features

- **AMD MI300X modules**: `amd_gpu_info`, `amd_gpu_config`, `amd_rocm_driver`,
  `amd_rocm_driver_info` for AMD GPU management via ROCm SMI
- **Intel Gaudi modules**: `gaudi_device_info`, `gaudi_device_config`,
  `gaudi_firmware`, `gaudi_firmware_info`, `habana_workload`,
  `habana_workload_info` for Intel Gaudi accelerator management
- **Credential management modules**: `credential_store`,
  `credential_store_info` for HashiCorp Vault integration
- **Subscription calculator modules**: `ai_factory_inventory_report`,
  `ai_factory_inventory_report_info` for AAP subscription sizing
- **Security compliance roles**: `stig_dgx` (DISA STIG hardening),
  `cis_ai_cluster` (CIS benchmark hardening)
- **Vault integration role**: `vault_integration` for HashiCorp Vault
  configuration with KV engine, policies, AppRole auth, and audit logging
- **PS bundle roles**: `ps_lab_setup` (demo environment),
  `reference_deployment` (reference architecture deployment)
- **Multi-vendor GPU support**: Collection renamed from `nvidia_ai_factory`
  to `gpu_ai_factory` to reflect AMD and Intel Gaudi support
- **Unit tests**: Added tests for all new modules

### Changes

- Renamed collection from `nvidia_ai_factory` to `gpu_ai_factory`
- Updated repository URLs from `ansible-nvidia-ai-factory` to
  `ansible-gpu-ai-factory`
- Added tags: `amd`, `intel`, `gaudi`, `rocm`, `compliance`, `stig`, `vault`

## 1.0.0 (2026-05-18)

### New Features

- **BCM Infrastructure modules**: `bcm_cluster`, `bcm_cluster_info`, `bcm_node`,
  `bcm_node_info`, `bcm_tenant`, `bcm_tenant_info`, `bcm_gpu_allocation`,
  `bcm_gpu_allocation_info`, `bcm_job`, `bcm_job_info`
- **DGX Hardware modules**: `dgx_firmware`, `dgx_firmware_info`, `dgx_health`,
  `dgx_power`, `dgx_bios`
- **NVIDIA AI Software modules**: `nemo_model`, `nemo_model_info`,
  `triton_server`, `triton_model`, `ngc_image`
- **Network modules**: `infiniband_port`, `infiniband_partition`,
  `infiniband_info`, `nvlink_info`, `rdma_config`
- **Inventory plugin**: `nvidia_bcm_inventory` dynamic inventory from BCM API
- **Roles**: `dgx_provision`, `gpu_allocation`, `tenant_isolation`,
  `infiniband_rdma`, `virtual_media_boot`, `nemo_deploy`
- **EDA event sources**: `dgx_telemetry`, `infiniband_fabric`, `ngc_catalog`
- **EDA rulebooks**: `dgx_health`, `infiniband_monitor`, `gpu_utilization`
