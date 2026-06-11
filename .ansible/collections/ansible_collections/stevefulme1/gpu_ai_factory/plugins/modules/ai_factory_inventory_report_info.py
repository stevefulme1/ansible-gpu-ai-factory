# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying existing inventory reports."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: ai_factory_inventory_report_info
short_description: Query existing inventory reports
description:
    - Retrieve existing AI Factory inventory and subscription sizing reports.
    - This module is read-only and does not modify any resources.
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
    report_id:
        description:
            - Specific report ID to query.
        type: str
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all reports
  stevefulme1.gpu_ai_factory.ai_factory_inventory_report_info:
    host: "https://aifactory.example.com"
    api_key: "{{ api_key }}"

- name: Get specific report
  stevefulme1.gpu_ai_factory.ai_factory_inventory_report_info:
    host: "https://aifactory.example.com"
    api_key: "{{ api_key }}"
    report_id: "rpt-12345"
"""

RETURN = r"""
reports:
    description: List of inventory reports.
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
        report_id=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    report_id = module.params.get('report_id')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
    }

    try:
        if report_id:
            url = f"{host}/api/v1/reports/inventory/{report_id}"
        else:
            url = f"{host}/api/v1/reports/inventory"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if report_id:
            reports = [data] if isinstance(data, dict) else data
        else:
            reports = data if isinstance(data, list) else data.get('reports', [])
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, reports=reports)


if __name__ == '__main__':
    main()
