# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying ROCm driver and version info."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: amd_rocm_driver_info
short_description: Query ROCm driver and version info
description:
    - Retrieve ROCm driver version, installed packages, and status.
    - This module is read-only and does not modify any resources.
version_added: "1.1.0"
author:
    - Steve Fulmer (@sfulmer)
options:
    host:
        description:
            - ROCm management API endpoint host.
        type: str
        required: true
    api_key:
        description:
            - API authentication key.
        type: str
        required: true
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Get ROCm driver info
  stevefulme1.gpu_ai_factory.amd_rocm_driver_info:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
"""

RETURN = r"""
driver:
    description: ROCm driver information.
    returned: always
    type: dict
    contains:
        version:
            description: Installed driver version.
            type: str
        packages:
            description: Installed packages.
            type: list
        status:
            description: Driver status.
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
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        response = requests.get(
            f"{host}/api/v1/drivers/rocm",
            headers=headers, timeout=30,
        )
        response.raise_for_status()
        driver = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, driver=driver)


if __name__ == '__main__':
    main()
