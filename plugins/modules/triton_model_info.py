# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying NVIDIA Triton Model resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: triton_model_info
short_description: Query Triton Inference Server models
description:
    - Retrieve information about models loaded in Triton Inference Server instances.
    - This module is read-only and does not modify any resources.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    model_name:
        description:
            - Name of the model to query. If omitted, all models are returned.
        type: str
    server_id:
        description:
            - Filter models by Triton server instance ID.
        type: str
    model_id:
        description:
            - Specific model ID to query.
        type: str
    wait:
        description:
            - Whether to wait for the resource to reach a stable state before returning.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach a stable state.
        type: int
        default: 600
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.bcm
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all Triton models
  stevefulme1.gpu_ai_factory.triton_model_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"

- name: Get a specific model by name
  stevefulme1.gpu_ai_factory.triton_model_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    model_name: "bert-base"

- name: Get models for a specific Triton server
  stevefulme1.gpu_ai_factory.triton_model_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    server_id: "triton-01"

- name: Get a specific model by ID
  stevefulme1.gpu_ai_factory.triton_model_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    model_id: "model-12345"
"""

RETURN = r"""
triton_models:
    description: List of Triton model information dictionaries.
    returned: always
    type: list
    elements: dict
    contains:
        model_id:
            description: Model identifier.
            type: str
        model_name:
            description: Name of the model.
            type: str
        server_id:
            description: Triton server instance ID.
            type: str
        model_path:
            description: Path to the model files.
            type: str
        model_version:
            description: Model version.
            type: str
        instance_count:
            description: Number of model instances per GPU.
            type: int
        max_batch_size:
            description: Maximum batch size.
            type: int
        state:
            description: Current state of the model.
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
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.bcm_client import BcmClient
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_wait import call_with_retry


def get_module_args():
    module_args = dict(
        model_name=dict(type="str"),
        server_id=dict(type="str"),
        model_id=dict(type="str"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/triton-models/{resource_id}"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests_lib.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_resources(client, base_url, model_name=None, server_id=None):
    """List all resources or filter by name/server."""
    url = f"{base_url}/api/v1/triton-models"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))

        if model_name:
            items = [item for item in items if item.get("model_name") == model_name]
        if server_id:
            items = [item for item in items if item.get("server_id") == server_id]

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

    params = module.params
    client = BcmClient(
        base_url=params["bcm_url"],
        username=params.get("bcm_username"),
        password=params.get("bcm_password"),
        token=params.get("bcm_token"),
        validate_certs=params["validate_certs"],
    )
    base_url = client.base_url

    if params.get("model_id"):
        resource = get_resource(client, base_url, params["model_id"])
        if resource:
            module.exit_json(changed=False, triton_models=[to_dict(resource)])
        else:
            module.exit_json(changed=False, triton_models=[])
    else:
        resources = list_resources(
            client,
            base_url,
            params.get("model_name"),
            params.get("server_id")
        )
        module.exit_json(changed=False, triton_models=[to_dict(r) for r in resources])


if __name__ == "__main__":
    main()
