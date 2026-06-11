# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying AMD GPU status via ROCm SMI."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: amd_gpu_info
short_description: Query AMD GPU status via ROCm SMI
description:
    - Retrieve AMD GPU information including model, temperature,
      utilization, memory usage, and driver version via ROCm SMI API.
    - This module is read-only and does not modify any resources.
version_added: "1.1.0"
author:
    - Steve Fulmer (@sfulmer)
options:
    host:
        description:
            - ROCm SMI API endpoint host.
        type: str
        required: true
    api_key:
        description:
            - API authentication key.
        type: str
        required: true
    gpu_id:
        description:
            - Specific GPU ID to query. If omitted, all GPUs are returned.
        type: str
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all AMD GPUs
  stevefulme1.gpu_ai_factory.amd_gpu_info:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"

- name: Get a specific AMD GPU
  stevefulme1.gpu_ai_factory.amd_gpu_info:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
    gpu_id: "0"
"""

RETURN = r"""
gpus:
    description: List of AMD GPU information dictionaries.
    returned: always
    type: list
    elements: dict
    contains:
        gpu_id:
            description: GPU identifier.
            type: str
        model:
            description: GPU model name.
            type: str
        temperature:
            description: Current GPU temperature in Celsius.
            type: int
        utilization:
            description: GPU utilization percentage.
            type: int
        memory_used:
            description: Memory used in MiB.
            type: int
        memory_total:
            description: Total memory in MiB.
            type: int
        driver_version:
            description: ROCm driver version.
            type: str
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def main():
    argument_spec = dict(
        host=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True),
        gpu_id=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    gpu_id = module.params.get('gpu_id')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        if gpu_id:
            url = f"{host}/api/v1/gpus/{gpu_id}"
        else:
            url = f"{host}/api/v1/gpus"

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if gpu_id:
            gpus = [data] if isinstance(data, dict) else data
        else:
            gpus = data if isinstance(data, list) else data.get('gpus', [])

    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, gpus=gpus)


if __name__ == '__main__':
    main()
