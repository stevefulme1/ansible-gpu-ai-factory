# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing NVIDIA Nemo Model resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: nemo_model
short_description: Deploy and manage NeMo models
description:
    - Deploy, update, and remove NeMo models on NVIDIA AI infrastructure.
    - This module is idempotent and supports check mode.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    name:
        description:
            - Name of the model deployment.
        type: str
        required: true
    model_path:
        description:
            - Path or NGC URI of the NeMo model.
        type: str
        required: true
    cluster_id:
        description:
            - BCM cluster to deploy on.
        type: str
        required: true
    gpu_count:
        description:
            - Number of GPUs for inference.
        type: int
    replica_count:
        description:
            - Number of model replicas.
        type: int
    max_batch_size:
        description:
            - Maximum batch size.
        type: int
    tensor_parallel:
        description:
            - Tensor parallelism degree.
        type: int
    pipeline_parallel:
        description:
            - Pipeline parallelism degree.
        type: int
    model_id:
        description:
            - The ID of an existing resource.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the resource.
        type: str
        choices:
            - present
            - absent
        default: present
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: Create a nemo model
  stevefulme1.gpu_ai_factory.nemo_model:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    state: present

- name: Delete a nemo model
  stevefulme1.gpu_ai_factory.nemo_model:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    model_id: "example-id"
    state: absent
"""

RETURN = r"""
model:
    description: Details of the resource.
    returned: on success when state is present
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
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_auth import create_bcm_client
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        name=dict(type="str", required=True),
        model_path=dict(type="str", required=True),
        cluster_id=dict(type="str", required=True),
        gpu_count=dict(type="int"),
        replica_count=dict(type="int"),
        max_batch_size=dict(type="int"),
        tensor_parallel=dict(type="int"),
        pipeline_parallel=dict(type="int"),
        model_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/models/{resource_id}"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests_lib.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def find_resource(client, base_url, params):
    """Find a resource by name."""
    name_val = params.get("name")
    if not name_val:
        return None
    url = f"{base_url}/api/v1/models"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))
        for item in items:
            if item.get("state", "").upper() in DEAD_STATES:
                continue
            if item.get("name") == name_val:
                return item
    except requests_lib.exceptions.HTTPError:
        pass
    return None


def create_resource(module, client, base_url):
    """Create a new resource."""
    params = module.params
    payload = {}
    if params.get("name") is not None:
        payload["name"] = params["name"]
    if params.get("model_path") is not None:
        payload["model_path"] = params["model_path"]
    if params.get("cluster_id") is not None:
        payload["cluster_id"] = params["cluster_id"]
    if params.get("gpu_count") is not None:
        payload["gpu_count"] = params["gpu_count"]
    if params.get("replica_count") is not None:
        payload["replica_count"] = params["replica_count"]
    if params.get("max_batch_size") is not None:
        payload["max_batch_size"] = params["max_batch_size"]
    if params.get("tensor_parallel") is not None:
        payload["tensor_parallel"] = params["tensor_parallel"]
    if params.get("pipeline_parallel") is not None:
        payload["pipeline_parallel"] = params["pipeline_parallel"]

    url = f"{base_url}/api/v1/models"
    resp = call_with_retry(client.post, url, json=payload, timeout=60)
    resp.raise_for_status()
    resource = resp.json()

    resource_id = resource.get("id") or resource.get("model_id")
    if resource_id and module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        resource = wait_for_resource(module, _get, resource_id, target_states=READY_STATES)
    return resource


def update_resource(module, client, base_url, existing):
    """Update an existing resource."""
    params = module.params
    resource_id = existing.get("id") or existing.get("model_id")
    payload = {}
    if params.get("name") is not None:
        payload["name"] = params["name"]
    if params.get("model_path") is not None:
        payload["model_path"] = params["model_path"]
    if params.get("cluster_id") is not None:
        payload["cluster_id"] = params["cluster_id"]
    if params.get("gpu_count") is not None:
        payload["gpu_count"] = params["gpu_count"]
    if params.get("replica_count") is not None:
        payload["replica_count"] = params["replica_count"]
    if params.get("max_batch_size") is not None:
        payload["max_batch_size"] = params["max_batch_size"]
    if params.get("tensor_parallel") is not None:
        payload["tensor_parallel"] = params["tensor_parallel"]
    if params.get("pipeline_parallel") is not None:
        payload["pipeline_parallel"] = params["pipeline_parallel"]

    url = f"{base_url}/api/v1/models/{resource_id}"
    resp = call_with_retry(client.put, url, json=payload, timeout=60)
    resp.raise_for_status()
    resource = resp.json()

    if module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        resource = wait_for_resource(module, _get, resource_id, target_states=READY_STATES)
    return resource


def delete_resource(module, client, base_url, existing):
    """Delete a resource."""
    resource_id = existing.get("id") or existing.get("model_id")
    url = f"{base_url}/api/v1/models/{resource_id}"
    call_with_retry(client.delete, url, timeout=60)

    if module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        wait_for_resource(module, _get, resource_id, target_states=DEAD_STATES)


def needs_update(params, existing):
    """Check if the existing resource needs updating."""
    desired = params.get("replica_count")
    if desired is not None:
        current = existing.get("replica_count")
        if current != desired:
            return True
    desired = params.get("max_batch_size")
    if desired is not None:
        current = existing.get("max_batch_size")
        if current != desired:
            return True
    desired = params.get("gpu_count")
    if desired is not None:
        current = existing.get("gpu_count")
        if current != desired:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[("state", "present", ("name", "model_path", "cluster_id",), True)],
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url
    state = params["state"]

    existing = None
    if params.get("model_id"):
        existing = get_resource(client, base_url, params["model_id"])
    else:
        existing = find_resource(client, base_url, params)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, base_url, existing)
        module.exit_json(changed=True)
        return

    # state == "present"
    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client, base_url)
        module.exit_json(changed=True, model=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, base_url, existing)
        module.exit_json(changed=True, model=to_dict(resource))
        return

    module.exit_json(changed=False, model=to_dict(existing))


if __name__ == "__main__":
    main()
