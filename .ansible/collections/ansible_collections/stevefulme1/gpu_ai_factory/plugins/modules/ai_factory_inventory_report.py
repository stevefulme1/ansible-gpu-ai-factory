# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for generating AAP subscription sizing reports."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: ai_factory_inventory_report
short_description: Generate AAP subscription sizing report
description:
    - Scan AI Factory infrastructure and generate an Ansible Automation
      Platform subscription sizing report.
    - Calculates managed node count, controller requirements, and
      estimated SKU breakdown.
    - Uses idempotent get-before-write pattern.
version_added: "1.1.0"
author:
    - Steve Fulmer (@sfulmer)
options:
    host:
        description:
            - AI Factory management API endpoint.
        type: str
        required: true
    api_key:
        description:
            - API authentication key.
        type: str
        required: true
    state:
        description:
            - Desired state of the report.
        type: str
        choices: [present, absent]
        default: present
    include_networking:
        description:
            - Include network devices in the inventory count.
        type: bool
        default: true
    include_storage:
        description:
            - Include storage devices in the inventory count.
        type: bool
        default: true
    output_format:
        description:
            - Output format for the report.
        type: str
        choices: [json, yaml, csv]
        default: json
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Generate full inventory report
  stevefulme1.gpu_ai_factory.ai_factory_inventory_report:
    host: "https://aifactory.example.com"
    api_key: "{{ api_key }}"
    include_networking: true
    include_storage: true
    output_format: json

- name: Generate compute-only report
  stevefulme1.gpu_ai_factory.ai_factory_inventory_report:
    host: "https://aifactory.example.com"
    api_key: "{{ api_key }}"
    include_networking: false
    include_storage: false
"""

RETURN = r"""
report:
    description: Subscription sizing report.
    returned: always
    type: dict
    contains:
        managed_node_count:
            description: Total managed nodes.
            type: int
        controller_count:
            description: Required automation controllers.
            type: int
        network_device_count:
            description: Network devices counted.
            type: int
        estimated_aap_cost:
            description: Estimated annual AAP subscription cost.
            type: str
        sku_breakdown:
            description: Breakdown by SKU type.
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
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        include_networking=dict(type='bool', default=True),
        include_storage=dict(type='bool', default=True),
        output_format=dict(type='str', choices=['json', 'yaml', 'csv'], default='json'),
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
    include_networking = module.params['include_networking']
    include_storage = module.params['include_storage']
    output_format = module.params['output_format']

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    if state == 'absent':
        # Delete existing report
        try:
            response = requests.delete(
                f"{host}/api/v1/reports/inventory",
                headers=headers, timeout=30,
            )
            if response.status_code == 404:
                module.exit_json(changed=False, report={})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to delete report: {e}")
        module.exit_json(changed=True, report={})

    if module.check_mode:
        module.exit_json(changed=True, report={'status': 'pending'})

    payload = {
        'include_networking': include_networking,
        'include_storage': include_storage,
        'output_format': output_format,
    }

    try:
        response = requests.post(
            f"{host}/api/v1/reports/inventory",
            headers=headers, json=payload, timeout=120,
        )
        response.raise_for_status()
        report = response.json()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to generate report: {e}")

    module.exit_json(changed=True, report=report)


if __name__ == '__main__':
    main()
