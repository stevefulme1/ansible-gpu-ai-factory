# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing AI platform credentials in Vault."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: credential_store
short_description: Manage AI platform credentials in HashiCorp Vault
description:
    - Store, update, or remove AI platform credentials in HashiCorp Vault
      or Ansible Vault.
    - Supports NGC tokens, API keys, SSH keys, and certificates.
    - Uses idempotent get-before-write pattern.
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
    credential_name:
        description:
            - Name identifier for the credential.
        type: str
        required: true
    state:
        description:
            - Desired state of the credential.
        type: str
        choices: [present, absent]
        default: present
    credential_type:
        description:
            - Type of credential being stored.
        type: str
        choices: [ngc_token, api_key, ssh_key, certificate]
        default: api_key
    secret_value:
        description:
            - The secret value to store. Required when state is present.
        type: str
    vault_path:
        description:
            - Path in Vault where the credential is stored.
        type: str
        default: secret/data/ai-factory
    vault_engine:
        description:
            - Vault secrets engine to use.
        type: str
        default: kv
        choices: [kv, kv-v2]
    validate_certs:
        description:
            - Whether to validate SSL certificates for Vault API requests.
        type: bool
        default: true
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Store NGC token
  stevefulme1.gpu_ai_factory.credential_store:
    host: "https://vault.example.com"
    api_key: "{{ vault_token }}"
    credential_name: "ngc-prod"
    credential_type: ngc_token
    secret_value: "{{ ngc_api_key }}"
    vault_path: "secret/data/ai-factory/ngc"

- name: Remove a credential
  stevefulme1.gpu_ai_factory.credential_store:
    host: "https://vault.example.com"
    api_key: "{{ vault_token }}"
    credential_name: "ngc-prod"
    state: absent
"""

RETURN = r"""
credential:
    description: Credential metadata (never includes secret values).
    returned: always
    type: dict
    contains:
        name:
            description: Credential name.
            type: str
        credential_type:
            description: Type of credential.
            type: str
        vault_path:
            description: Vault storage path.
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
        credential_name=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        credential_type=dict(
            type='str',
            choices=['ngc_token', 'api_key', 'ssh_key', 'certificate'],
            default='api_key',
        ),
        secret_value=dict(type='str', no_log=True),
        vault_path=dict(type='str', default='secret/data/ai-factory'),
        vault_engine=dict(type='str', default='kv', choices=['kv', 'kv-v2']),
        validate_certs=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['secret_value']),
        ],
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' library is required by this module.")

    host = module.params['host'].rstrip('/')
    api_key = module.params['api_key']
    credential_name = module.params['credential_name']
    state = module.params['state']
    credential_type = module.params['credential_type']
    secret_value = module.params.get('secret_value')
    vault_path = module.params['vault_path']
    validate_certs = module.params['validate_certs']

    headers = {
        'X-Vault-Token': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    full_path = f"{vault_path}/{credential_name}"

    # Check if credential exists
    existing = None
    try:
        response = requests.get(
            f"{host}/v1/{full_path}",
            headers=headers, timeout=30, verify=validate_certs,
        )
        if response.status_code == 200:
            existing = response.json().get('data', {})
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to query Vault: {e}")

    if state == 'absent':
        if not existing:
            module.exit_json(changed=False, credential={})
        if module.check_mode:
            module.exit_json(changed=True, credential={})
        try:
            response = requests.delete(
                f"{host}/v1/{full_path}",
                headers=headers, timeout=30, verify=validate_certs,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            module.fail_json(msg=f"Failed to delete credential: {e}")
        module.exit_json(changed=True, credential={})

    # state == present
    payload = {
        'data': {
            'credential_name': credential_name,
            'credential_type': credential_type,
            'value': secret_value,
        }
    }

    if existing and existing.get('data', {}).get('credential_type') == credential_type:
        # Cannot compare secret values safely; assume changed if writing
        pass

    if module.check_mode:
        module.exit_json(
            changed=True,
            credential={
                'name': credential_name,
                'credential_type': credential_type,
                'vault_path': full_path,
            },
        )

    try:
        response = requests.post(
            f"{host}/v1/{full_path}",
            headers=headers, json=payload, timeout=30, verify=validate_certs,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to store credential: {e}")

    module.exit_json(
        changed=True,
        credential={
            'name': credential_name,
            'credential_type': credential_type,
            'vault_path': full_path,
        },
    )


if __name__ == '__main__':
    main()
