#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_node_info
short_description: List cluster nodes from NVIDIA BCM
version_added: "1.0.0"
description:
    - Retrieves node information from NVIDIA Base Command Manager
      (BCM) via the CMDaemon REST API.
    - Can list all nodes or filter by category.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.bcm
options:
    bcm_url:
        required: true
    name:
        description:
            - Name of a specific node to retrieve.
            - If omitted, all nodes are listed.
        type: str
    category:
        description:
            - Filter nodes by category (e.g. C(gpu), C(cpu), C(storage)).
        type: str
requirements:
    - requests
"""

EXAMPLES = r"""
- name: List all BCM cluster nodes
  stevefulme1.gpu_ai_factory.bcm_node_info:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
  register: nodes

- name: List GPU nodes only
  stevefulme1.gpu_ai_factory.bcm_node_info:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
    category: gpu
  register: gpu_nodes
"""

RETURN = r"""
nodes:
    description: List of cluster node details.
    type: list
    elements: dict
    returned: always
node_count:
    description: Total number of nodes returned.
    type: int
    returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.bcm_client import (
        BcmClient,
    )
    HAS_BCM = True
except ImportError:
    HAS_BCM = False


def main():
    argument_spec = dict(
        bcm_url=dict(type="str", required=True),
        bcm_username=dict(type="str"),
        bcm_password=dict(type="str", no_log=True),
        bcm_token=dict(type="str", no_log=True),
        validate_certs=dict(type="bool", default=True),
        name=dict(type="str"),
        category=dict(type="str"),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[
            ("bcm_username", "bcm_token"),
        ],
        required_together=[
            ("bcm_username", "bcm_password"),
        ],
    )

    if not HAS_BCM:
        module.fail_json(msg="The 'requests' library is required.")

    p = module.params
    try:
        client = BcmClient(
            base_url=p["bcm_url"],
            username=p.get("bcm_username"),
            password=p.get("bcm_password"),
            token=p.get("bcm_token"),
            validate_certs=p["validate_certs"],
        )
    except Exception as exc:
        module.fail_json(msg="Failed to connect to BCM: {0}".format(exc))

    try:
        if p["name"]:
            data = client.get_node(p["name"])
            nodes = [data] if isinstance(data, dict) else data
        else:
            data = client.list_nodes(category=p.get("category"))
            nodes = data.get("nodes", data) if isinstance(data, dict) else data
    except Exception as exc:
        module.fail_json(msg="Failed to query BCM nodes: {0}".format(exc))

    if not isinstance(nodes, list):
        nodes = [nodes]

    module.exit_json(changed=False, nodes=nodes, node_count=len(nodes))


if __name__ == "__main__":
    main()
