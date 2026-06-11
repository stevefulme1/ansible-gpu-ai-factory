# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying stored credentials metadata."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: credential_store_info
short_description: List and query stored credential metadata
description:
    - Retrieve metadata for credentials stored in HashiCorp Vault.
    - Returns metadata only, never secret values.
    - This module is read-only and does not modify any resources.
version_added: "1.1.0"
author:
    - Steve Fulmer (@sfulmer)
options:
    host:
        description:
            - HashiCorp Vault API endpoint.
        type: str
        required: true
    api_key:
        description:
            - Vault authentication token.
        type: str
        required: true
    vault_path:
        description:
            - Path in Vault to list credentials from.
        type: str
        default: secret/metadata/ai-factory
    credential_name:
        description:
            - Filter by specific credential name.
        type: str
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all credentials
  stevefulme1.gpu_ai_factory.credential_store_info:
    host: "https://vault.example.com"
    api_key: "{{ vault_token }}"

- name: Get specific credential metadata
  stevefulme1.gpu_ai_factory.credential_store_info:
    host: "https://vault.example.com"
    api_key: "{{ vault_token }}"
    credential_name: "ngc-prod"
"""

RETURN = r"""
credentials:
    description: List of credential metadata (never includes secret values).
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
        vault_path=dict(type='str', default='secret/metadata/ai-factory'),
        credential_name=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    vault_path = module.params['vault_path']
    credential_name = module.params.get('credential_name')

    headers = {
        'X-Vault-Token': api_key,
        'Accept': 'application/json',
    }

    try:
        if credential_name:
            url = f"{host}/v1/{vault_path}/{credential_name}"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json().get('data', {})
            credentials = [data]
        else:
            url = f"{host}/v1/{vault_path}"
            response = requests.request('LIST', url, headers=headers, timeout=30)
            response.raise_for_status()
            keys = response.json().get('data', {}).get('keys', [])
            credentials = [{'name': k} for k in keys]
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"API request failed: {e}")

    module.exit_json(changed=False, credentials=credentials)


if __name__ == '__main__':
    main()
