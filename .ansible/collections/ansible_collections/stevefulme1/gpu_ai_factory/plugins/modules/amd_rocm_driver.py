# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing ROCm driver installation and updates."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: amd_rocm_driver
short_description: Manage ROCm driver installation and updates
description:
    - Install, update, or remove ROCm drivers on AMD GPU systems.
    - Uses idempotent get-before-write pattern.
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
    state:
        description:
            - Desired state of the ROCm driver.
        type: str
        choices: [present, absent]
        default: present
    version:
        description:
            - ROCm driver version to install or update to.
        type: str
    packages:
        description:
            - List of ROCm packages to manage.
        type: list
        elements: str
        default: [rocm-dev]
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Install ROCm driver
  stevefulme1.gpu_ai_factory.amd_rocm_driver:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
    state: present
    version: "6.2.0"
    packages:
      - rocm-dev
      - rocm-smi-lib

- name: Remove ROCm driver
  stevefulme1.gpu_ai_factory.amd_rocm_driver:
    host: "https://rocm.example.com"
    api_key: "{{ rocm_api_key }}"
    state: absent
"""

RETURN = r"""
driver:
    description: Driver installation details.
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
            description: Installation status.
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
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        version=dict(type='str'),
        packages=dict(type='list', elements='str', default=['rocm-dev']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    state = module.params['state']
    version = module.params.get('version')
    packages = module.params['packages']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Get current driver state
    try:
        response = requests.get(
            f"{host}/api/v1/drivers/rocm",
            headers=headers, timeout=30,
        )
        response.raise_for_status()
        current = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to query driver state: {e}")

    current_version = current.get('version')
    current_packages = current.get('packages', [])
    is_installed = current.get('status') == 'installed'

    if state == 'absent':
        if not is_installed:
            module.exit_json(changed=False, driver=current)
        if module.check_mode:
            module.exit_json(changed=True, driver={'status': 'removed'})
        try:
            response = requests.delete(
                f"{host}/api/v1/drivers/rocm",
                headers=headers, timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to remove driver: {e}")
        module.exit_json(changed=True, driver={'status': 'removed'})

    # state == present
    needs_change = (
        not is_installed
        or (version and current_version != version)
        or set(packages) != set(current_packages)
    )

    if not needs_change:
        module.exit_json(changed=False, driver=current)

    if module.check_mode:
        module.exit_json(changed=True, driver={'version': version, 'packages': packages})

    payload = {'packages': packages}
    if version:
        payload['version'] = version

    try:
        response = requests.put(
            f"{host}/api/v1/drivers/rocm",
            headers=headers, json=payload, timeout=300,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to install/update driver: {e}")

    module.exit_json(changed=True, driver=result)


if __name__ == '__main__':
    main()
