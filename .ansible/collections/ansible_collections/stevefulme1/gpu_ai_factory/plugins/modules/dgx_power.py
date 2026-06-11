# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for control dgx system power state via redfish api."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_power
short_description: Manage DGX power state
description:
    - Control DGX system power state via Redfish API.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    node_id:
        description:
            - Node ID or BMC address.
        type: str
        required: true
    power_action:
        description:
            - Power action to perform.
        type: str
        required: true
        choices:
            - 'on'
            - 'off'
            - reset
            - cycle
            - nmi
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Execute dgx power action
  stevefulme1.gpu_ai_factory.dgx_power:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    node_id: "dgx-001"
"""

RETURN = r"""
power:
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
        power_action=dict(type="str", required=True, choices=['on', 'off', 'reset', 'cycle', 'nmi']),
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
    if params.get("power_action") is not None:
        payload["power_action"] = params["power_action"]

    url = f"{base_url}/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
    try:
        resp = call_with_retry(client.post, url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        module.exit_json(changed=True, power=to_dict(result))
    except requests_lib.exceptions.HTTPError as exc:
        module.fail_json(msg=f"API error: {exc}")


if __name__ == "__main__":
    main()
