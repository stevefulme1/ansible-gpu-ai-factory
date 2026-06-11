# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying Habana workload status."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: habana_workload_info
short_description: Query Habana workload status
description:
    - Retrieve workload status information from Intel Gaudi accelerators.
    - This module is read-only and does not modify any resources.
version_added: "1.1.0"
author:
    - Steve Fulmer (@sfulmer)
options:
    host:
        description:
            - Habana Labs API endpoint host.
        type: str
        required: true
    api_key:
        description:
            - API authentication key.
        type: str
        required: true
    name:
        description:
            - Filter by workload name.
        type: str
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all workloads
  stevefulme1.gpu_ai_factory.habana_workload_info:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"

- name: Get specific workload
  stevefulme1.gpu_ai_factory.habana_workload_info:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    name: "llama-inference"
"""

RETURN = r"""
workloads:
    description: List of workload information.
    returned: always
    type: list
    elements: dict
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
        name=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    name = module.params.get('name')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        params = {}
        if name:
            params['name'] = name
        response = requests.get(
            f"{host}/api/v1/workloads",
            headers=headers, params=params, timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        workloads = data if isinstance(data, list) else data.get('workloads', [])
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, workloads=workloads)


if __name__ == '__main__':
    main()
