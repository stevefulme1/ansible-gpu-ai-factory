# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for configuring AMD MI300X GPU settings."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: amd_gpu_config
short_description: Configure AMD MI300X GPU settings
description:
    - Configure AMD MI300X GPU settings including power limit,
      clock profile, and memory mode via ROCm SMI API.
    - Uses idempotent get-before-write pattern.
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
            - GPU ID to configure.
        type: str
        required: true
    state:
        description:
            - Desired state of the GPU configuration.
        type: str
        choices: [present, absent]
        default: present
    power_limit:
        description:
            - Power limit in watts.
        type: int
    clock_profile:
        description:
            - Clock profile to apply.
        type: str
        choices: [default, high, low, manual]
    memory_mode:
        description:
            - Memory mode setting.
        type: str
        choices: [auto, hbm, unified]
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Configure AMD GPU power limit
  stevefulme1.gpu_ai_factory.amd_gpu_config:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
    gpu_id: "0"
    power_limit: 560
    clock_profile: high

- name: Reset GPU to defaults
  stevefulme1.gpu_ai_factory.amd_gpu_config:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
    gpu_id: "0"
    state: absent
"""

RETURN = r"""
config:
    description: Current GPU configuration after changes.
    returned: always
    type: dict
changed:
    description: Whether the configuration was modified.
    returned: always
    type: bool
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
        gpu_id=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        power_limit=dict(type='int'),
        clock_profile=dict(type='str', choices=['default', 'high', 'low', 'manual']),
        memory_mode=dict(type='str', choices=['auto', 'hbm', 'unified']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    gpu_id = module.params['gpu_id']
    state = module.params['state']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Get current config
    try:
        response = requests.get(
            f"{host}/api/v1/gpus/{gpu_id}/config",
            headers=headers, timeout=30,
        )
        response.raise_for_status()
        current = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to get current config: {e}")

    if state == 'absent':
        if current.get('power_limit') or current.get('clock_profile') != 'default':
            if module.check_mode:
                module.exit_json(changed=True, config={})
            try:
                response = requests.delete(
                    f"{host}/api/v1/gpus/{gpu_id}/config",
                    headers=headers, timeout=30,
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                module.fail_json(msg=f"Failed to reset config: {e}")
            module.exit_json(changed=True, config={})
        module.exit_json(changed=False, config=current)

    # Build desired config
    desired = {}
    for param in ('power_limit', 'clock_profile', 'memory_mode'):
        value = module.params.get(param)
        if value is not None:
            desired[param] = value

    # Compare with current
    changes_needed = False
    for key, value in desired.items():
        if current.get(key) != value:
            changes_needed = True
            break

    if not changes_needed:
        module.exit_json(changed=False, config=current)

    if module.check_mode:
        module.exit_json(changed=True, config=desired)

    try:
        response = requests.put(
            f"{host}/api/v1/gpus/{gpu_id}/config",
            headers=headers, json=desired, timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to apply config: {e}")

    module.exit_json(changed=True, config=result)


if __name__ == '__main__':
    main()
