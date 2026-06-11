# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for read and configure bios settings on dgx systems via redfish api."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_bios
short_description: Configure DGX BIOS settings
description:
    - Read and configure BIOS settings on DGX systems via Redfish API.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    node_id:
        description:
            - Node ID or BMC address.
        type: str
        required: true
    settings:
        description:
            - BIOS settings as key-value pairs.
        type: dict
        required: true
    reset_after:
        description:
            - Reset system after BIOS update.
        type: bool
        default: false
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Execute dgx bios action
  stevefulme1.gpu_ai_factory.dgx_bios:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    node_id: "dgx-001"
"""

RETURN = r"""
bios:
    description: Result of the operation.
    returned: on success
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import requests as requests_lib
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_common import (
    NVIDIA_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_auth import create_bcm_client
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_wait import call_with_retry


def get_module_args():
    module_args = dict(
        node_id=dict(type="str", required=True),
        settings=dict(type="dict", required=True),
        reset_after=dict(type="bool", default=False),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    if module.check_mode:
        module.exit_json(changed=True)

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url

    payload = {}
    if params.get("node_id") is not None:
        payload["node_id"] = params["node_id"]
    if params.get("settings") is not None:
        payload["settings"] = params["settings"]
    if params.get("reset_after") is not None:
        payload["reset_after"] = params["reset_after"]

    url = f"{base_url}/redfish/v1/Systems/1/Bios"
    try:
        resp = call_with_retry(client.post, url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        module.exit_json(changed=True, bios=to_dict(result))
    except requests_lib.exceptions.HTTPError as exc:
        module.fail_json(msg=f"API error: {exc}")


if __name__ == "__main__":
    main()
