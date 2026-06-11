# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying NVIDIA Triton Server resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: triton_server_info
short_description: Query Triton Inference Server instances
description:
    - Retrieve information about Triton Inference Server instances.
    - This module is read-only and does not modify any resources.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    name:
        description:
            - Name of the Triton server to query. If omitted, all servers are returned.
        type: str
    cluster_id:
        description:
            - Filter servers by BCM cluster ID.
        type: str
    server_id:
        description:
            - Specific Triton server ID to query.
        type: str
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all Triton servers
  stevefulme1.gpu_ai_factory.triton_server_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"

- name: Get a specific Triton server by name
  stevefulme1.gpu_ai_factory.triton_server_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    name: "inference-01"

- name: Get servers for a specific cluster
  stevefulme1.gpu_ai_factory.triton_server_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    cluster_id: "cluster-prod"

- name: Get a specific server by ID
  stevefulme1.gpu_ai_factory.triton_server_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    server_id: "server-12345"
"""

RETURN = r"""
triton_servers:
    description: List of Triton server information dictionaries.
    returned: always
    type: list
    elements: dict
    contains:
        server_id:
            description: Triton server identifier.
            type: str
        name:
            description: Name of the Triton server instance.
            type: str
        cluster_id:
            description: BCM cluster ID.
            type: str
        model_repository:
            description: Path to the model repository.
            type: str
        gpu_count:
            description: Number of GPUs.
            type: int
        http_port:
            description: HTTP port for inference.
            type: int
        grpc_port:
            description: gRPC port for inference.
            type: int
        metrics_port:
            description: Prometheus metrics port.
            type: int
        state:
            description: Current state of the server.
            type: str
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
        name=dict(type="str"),
        cluster_id=dict(type="str"),
        server_id=dict(type="str"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/triton-servers/{resource_id}"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests_lib.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_resources(client, base_url, name=None, cluster_id=None):
    """List all resources or filter by name/cluster."""
    url = f"{base_url}/api/v1/triton-servers"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))

        if name:
            items = [item for item in items if item.get("name") == name]
        if cluster_id:
            items = [item for item in items if item.get("cluster_id") == cluster_id]

        return items
    except requests_lib.exceptions.HTTPError:
        return []


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url

    if params.get("server_id"):
        resource = get_resource(client, base_url, params["server_id"])
        if resource:
            module.exit_json(changed=False, triton_servers=[to_dict(resource)])
        else:
            module.exit_json(changed=False, triton_servers=[])
    else:
        resources = list_resources(
            client,
            base_url,
            params.get("name"),
            params.get("cluster_id")
        )
        module.exit_json(changed=False, triton_servers=[to_dict(r) for r in resources])


if __name__ == "__main__":
    main()
