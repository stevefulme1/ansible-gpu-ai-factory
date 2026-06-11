# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying Intel Gaudi firmware versions."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: gaudi_firmware_info
short_description: Query Intel Gaudi firmware versions
description:
    - Retrieve firmware version information for Intel Gaudi accelerators.
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
    device_id:
        description:
            - Specific device ID to query firmware for.
        type: str
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Get all Gaudi firmware versions
  stevefulme1.gpu_ai_factory.gaudi_firmware_info:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"

- name: Get firmware for specific device
  stevefulme1.gpu_ai_factory.gaudi_firmware_info:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    device_id: "0"
"""

RETURN = r"""
firmware:
    description: Firmware version information.
    returned: always
    type: list
    elements: dict
    contains:
        device_id:
            description: Device identifier.
            type: str
        version:
            description: Firmware version.
            type: str
        status:
            description: Firmware status.
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
        device_id=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    device_id = module.params.get('device_id')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        if device_id:
            url = f"{host}/api/v1/devices/{device_id}/firmware"
        else:
            url = f"{host}/api/v1/devices/firmware"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        firmware = [data] if isinstance(data, dict) else data if isinstance(data, list) else data.get('firmware', [])
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, firmware=firmware)


if __name__ == '__main__':
    main()
