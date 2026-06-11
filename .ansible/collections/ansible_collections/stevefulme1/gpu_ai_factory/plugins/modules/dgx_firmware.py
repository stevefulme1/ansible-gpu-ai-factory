# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for apply firmware updates to dgx systems via redfish api."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: dgx_firmware
short_description: Manage DGX firmware updates
description:
    - Apply firmware updates to DGX systems via Redfish API.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    node_id:
        description:
            - Node ID or BMC address.
        type: str
        required: true
    firmware_url:
        description:
            - URL to firmware update package.
        type: str
        required: true
    component:
        description:
            - Firmware component to update.
        type: str
    force:
        description:
            - Force update even if version matches.
        type: bool
        default: false
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Execute dgx firmware action
  stevefulme1.gpu_ai_factory.dgx_firmware:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    node_id: "dgx-001"
"""

RETURN = r"""
firmware_update:
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
        firmware_url=dict(type="str", required=True),
        component=dict(type="str"),
        force=dict(type="bool", default=False),
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
    if params.get("firmware_url") is not None:
        payload["firmware_url"] = params["firmware_url"]
    if params.get("component") is not None:
        payload["component"] = params["component"]
    if params.get("force") is not None:
        payload["force"] = params["force"]

    url = f"{base_url}/redfish/v1/UpdateService"
    try:
        resp = call_with_retry(client.post, url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        module.exit_json(changed=True, firmware_update=to_dict(result))
    except requests_lib.exceptions.HTTPError as exc:
        module.fail_json(msg=f"API error: {exc}")


if __name__ == "__main__":
    main()
