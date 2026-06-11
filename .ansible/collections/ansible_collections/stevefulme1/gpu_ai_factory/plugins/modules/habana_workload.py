# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing Habana workload submissions."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: habana_workload
short_description: Manage Habana workload submissions
description:
    - Submit, manage, or cancel workloads on Intel Gaudi accelerators
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
    name:
        description:
            - Workload name.
        type: str
        required: true
    state:
        description:
            - Desired state of the workload.
        type: str
        choices: [present, absent]
        default: present
    model_path:
        description:
            - Path to the model to run.
        type: str
    batch_size:
        description:
            - Batch size for inference or training.
        type: int
        default: 1
    num_workers:
        description:
            - Number of worker processes.
        type: int
        default: 1
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Submit a workload
  stevefulme1.gpu_ai_factory.habana_workload:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    name: "llama-inference"
    model_path: "/models/llama-70b"
    batch_size: 8
    num_workers: 4

- name: Cancel a workload
  stevefulme1.gpu_ai_factory.habana_workload:
    host: "https://gaudi.example.com"
    api_key: "{{ gaudi_api_key }}"
    name: "llama-inference"
    state: absent
"""

RETURN = r"""
workload:
    description: Workload details.
    returned: always
    type: dict
    contains:
        name:
            description: Workload name.
            type: str
        status:
            description: Workload status.
            type: str
        model_path:
            description: Model path.
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
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        model_path=dict(type='str'),
        batch_size=dict(type='int', default=1),
        num_workers=dict(type='int', default=1),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    name = module.params['name']
    state = module.params['state']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Check if workload exists
    existing = None
    try:
        response = requests.get(
            f"{host}/api/v1/workloads",
            headers=headers, params={'name': name}, timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        workloads = data if isinstance(data, list) else data.get('workloads', [])
        for w in workloads:
            if w.get('name') == name:
                existing = w
                break
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to query workloads: {e}")

    if state == 'absent':
        if not existing:
            module.exit_json(changed=False, workload={})
        if module.check_mode:
            module.exit_json(changed=True, workload={})
        try:
            response = requests.delete(
                f"{host}/api/v1/workloads/{existing['id']}",
                headers=headers, timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to cancel workload: {e}")
        module.exit_json(changed=True, workload={})

    # state == present
    desired = {
        'name': name,
        'model_path': module.params.get('model_path'),
        'batch_size': module.params['batch_size'],
        'num_workers': module.params['num_workers'],
    }

    if existing:
        changes_needed = any(
            existing.get(k) != v for k, v in desired.items() if v is not None
        )
        if not changes_needed:
            module.exit_json(changed=False, workload=existing)
        if module.check_mode:
            module.exit_json(changed=True, workload=desired)
        try:
            response = requests.put(
                f"{host}/api/v1/workloads/{existing['id']}",
                headers=headers, json=desired, timeout=30,
            )
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to update workload: {e}")
        module.exit_json(changed=True, workload=result)

    # Create new
    if module.check_mode:
        module.exit_json(changed=True, workload=desired)
    try:
        response = requests.post(
            f"{host}/api/v1/workloads",
            headers=headers, json=desired, timeout=30,
        )
        response.raise_for_status()
        result = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to create workload: {e}")

    module.exit_json(changed=True, workload=result)


if __name__ == '__main__':
    main()
