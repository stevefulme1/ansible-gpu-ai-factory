# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for configuring Intel Gaudi device settings."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: gaudi_device_config
short_description: Configure Intel Gaudi device settings
description:
    - Configure Intel Gaudi device settings including power mode
      and clock frequency via Habana Labs API.
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
            - Gaudi device ID to configure.
        type: str
        required: true
    state:
        description:
            - Desired state of the device configuration.
        type: str
        choices: [present, absent]
        default: present
    power_mode:
        description:
            - Power mode setting.
        type: str
        choices: [performance, balanced, efficiency]
    clock_frequency:
        description:
            - Clock frequency in MHz.
        type: int
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Configure Gaudi device
  stevefulme1.gpu_ai_factory.gaudi_device_config:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    device_id: "0"
    power_mode: performance
    clock_frequency: 1500

- name: Reset device to defaults
  stevefulme1.gpu_ai_factory.gaudi_device_config:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    device_id: "0"
    state: absent
"""

RETURN = r"""
config:
    description: Current device configuration after changes.
    returned: always
    type: dict
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
        power_mode=dict(type='str', choices=['performance', 'balanced', 'efficiency']),
        clock_frequency=dict(type='int'),
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

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Get current config
    try:
        response = requests.get(
            f"{host}/api/v1/devices/{device_id}/config",
            headers=headers, timeout=30,
        )
        response.raise_for_status()
        current = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to get current config: {e}")

    if state == 'absent':
        if current.get('power_mode') != 'balanced' or current.get('clock_frequency'):
            if module.check_mode:
                module.exit_json(changed=True, config={})
            try:
                response = requests.delete(
                    f"{host}/api/v1/devices/{device_id}/config",
                    headers=headers, timeout=30,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                module.fail_json(msg=f"Failed to reset config: {e}")
            module.exit_json(changed=True, config={})
        module.exit_json(changed=False, config=current)

    desired = {}
    for param in ('power_mode', 'clock_frequency'):
        value = module.params.get(param)
        if value is not None:
            desired[param] = value

    changes_needed = any(current.get(k) != v for k, v in desired.items())

    if not changes_needed:
        module.exit_json(changed=False, config=current)

    if module.check_mode:
        module.exit_json(changed=True, config=desired)

    try:
        response = requests.put(
            f"{host}/api/v1/devices/{device_id}/config",
            headers=headers, json=desired, timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to apply config: {e}")

    module.exit_json(changed=True, config=result)


if __name__ == '__main__':
    main()
