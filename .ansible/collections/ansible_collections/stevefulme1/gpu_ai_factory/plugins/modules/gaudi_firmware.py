# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing Intel Gaudi firmware updates."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: gaudi_firmware
short_description: Manage Intel Gaudi firmware updates
description:
    - Install, update, or manage firmware on Intel Gaudi accelerators
      via Habana Labs API.
    - Uses idempotent get-before-write pattern.
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
            - Gaudi device ID to update firmware on.
        type: str
        required: true
    state:
        description:
            - Desired state of the firmware.
        type: str
        choices: [present, absent]
        default: present
    firmware_version:
        description:
            - Target firmware version.
        type: str
    force:
        description:
            - Force firmware update even if version matches.
        type: bool
        default: false
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Update Gaudi firmware
  stevefulme1.gpu_ai_factory.gaudi_firmware:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    device_id: "0"
    firmware_version: "1.18.0"

- name: Force firmware update
  stevefulme1.gpu_ai_factory.gaudi_firmware:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    device_id: "0"
    firmware_version: "1.18.0"
    force: true
"""

RETURN = r"""
firmware:
    description: Firmware update result.
    returned: always
    type: dict
    contains:
        version:
            description: Current firmware version.
            type: str
        status:
            description: Update status.
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
        device_id=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        firmware_version=dict(type='str'),
        force=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    device_id = module.params['device_id']
    state = module.params['state']
    firmware_version = module.params.get('firmware_version')
    force = module.params['force']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Get current firmware
    try:
        response = requests.get(
            f"{host}/api/v1/devices/{device_id}/firmware",
            headers=headers, timeout=30,
        )
        response.raise_for_status()
        current = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to query firmware: {e}")

    current_version = current.get('version')

    if state == 'absent':
        module.exit_json(changed=False, firmware=current,
                         msg="Firmware cannot be removed, only updated.")

    if not firmware_version:
        module.exit_json(changed=False, firmware=current)

    if current_version == firmware_version and not force:
        module.exit_json(changed=False, firmware=current)

    if module.check_mode:
        module.exit_json(changed=True, firmware={'version': firmware_version, 'status': 'pending'})

    try:
        payload = {'version': firmware_version, 'force': force}
        response = requests.post(
            f"{host}/api/v1/devices/{device_id}/firmware",
            headers=headers, json=payload, timeout=300,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Firmware update failed: {e}")

    module.exit_json(changed=True, firmware=result)


if __name__ == '__main__':
    main()
