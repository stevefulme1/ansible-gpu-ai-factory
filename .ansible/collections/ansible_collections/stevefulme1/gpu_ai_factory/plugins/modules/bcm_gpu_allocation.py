# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing NVIDIA Bcm Gpu Allocation resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_gpu_allocation
short_description: Allocate or deallocate GPU slices
description:
    - Manage GPU allocations for tenants in BCM.
    - This module is idempotent and supports check mode.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    tenant_id:
        description:
            - Tenant ID to allocate GPUs to.
        type: str
        required: true
    cluster_id:
        description:
            - BCM cluster ID.
        type: str
        required: true
    node_id:
        description:
            - Specific node to allocate from.
        type: str
    gpu_count:
        description:
            - Number of GPU slices.
        type: int
        required: true
    gpu_type:
        description:
            - GPU model to allocate.
        type: str
    mig_profile:
        description:
            - MIG profile for partitioning.
        type: str
    priority:
        description:
            - Allocation priority.
        type: str
        choices:
            - low
            - normal
            - high
    allocation_id:
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
- name: Create a bcm gpu allocation
  stevefulme1.gpu_ai_factory.bcm_gpu_allocation:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    state: present

- name: Delete a bcm gpu allocation
  stevefulme1.gpu_ai_factory.bcm_gpu_allocation:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    allocation_id: "example-id"
    state: absent
"""

RETURN = r"""
gpu_allocation:
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
        tenant_id=dict(type="str", required=True),
        cluster_id=dict(type="str", required=True),
        node_id=dict(type="str"),
        gpu_count=dict(type="int", required=True),
        gpu_type=dict(type="str"),
        mig_profile=dict(type="str"),
        priority=dict(type="str", choices=['low', 'normal', 'high']),
        allocation_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/gpu-allocations/{resource_id}"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests_lib.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def find_resource(client, base_url, params):
    """No name-based lookup available."""
    return None


def create_resource(module, client, base_url):
    """Create a new resource."""
    params = module.params
    payload = {}
    if params.get("tenant_id") is not None:
        payload["tenant_id"] = params["tenant_id"]
    if params.get("cluster_id") is not None:
        payload["cluster_id"] = params["cluster_id"]
    if params.get("node_id") is not None:
        payload["node_id"] = params["node_id"]
    if params.get("gpu_count") is not None:
        payload["gpu_count"] = params["gpu_count"]
    if params.get("gpu_type") is not None:
        payload["gpu_type"] = params["gpu_type"]
    if params.get("mig_profile") is not None:
        payload["mig_profile"] = params["mig_profile"]
    if params.get("priority") is not None:
        payload["priority"] = params["priority"]

    url = f"{base_url}/api/v1/gpu-allocations"
    resp = call_with_retry(client.post, url, json=payload, timeout=60)
    resp.raise_for_status()
    resource = resp.json()

    resource_id = resource.get("id") or resource.get("allocation_id")
    if resource_id and module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        resource = wait_for_resource(module, _get, resource_id, target_states=READY_STATES)
    return resource


def update_resource(module, client, base_url, existing):
    """Update an existing resource."""
    params = module.params
    resource_id = existing.get("id") or existing.get("allocation_id")
    payload = {}
    if params.get("tenant_id") is not None:
        payload["tenant_id"] = params["tenant_id"]
    if params.get("cluster_id") is not None:
        payload["cluster_id"] = params["cluster_id"]
    if params.get("node_id") is not None:
        payload["node_id"] = params["node_id"]
    if params.get("gpu_count") is not None:
        payload["gpu_count"] = params["gpu_count"]
    if params.get("gpu_type") is not None:
        payload["gpu_type"] = params["gpu_type"]
    if params.get("mig_profile") is not None:
        payload["mig_profile"] = params["mig_profile"]
    if params.get("priority") is not None:
        payload["priority"] = params["priority"]

    url = f"{base_url}/api/v1/gpu-allocations/{resource_id}"
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
    resource_id = existing.get("id") or existing.get("allocation_id")
    url = f"{base_url}/api/v1/gpu-allocations/{resource_id}"
    call_with_retry(client.delete, url, timeout=60)

    if module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        wait_for_resource(module, _get, resource_id, target_states=DEAD_STATES)


def needs_update(params, existing):
    """Check if the existing resource needs updating."""
    desired = params.get("gpu_count")
    if desired is not None:
        current = existing.get("gpu_count")
        if current != desired:
            return True
    desired = params.get("priority")
    if desired is not None:
        current = existing.get("priority")
        if current != desired:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[("state", "present", ("tenant_id", "cluster_id", "gpu_count",), True)],
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url
    state = params["state"]

    existing = None
    if params.get("allocation_id"):
        existing = get_resource(client, base_url, params["allocation_id"])
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
        module.exit_json(changed=True, gpu_allocation=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, base_url, existing)
        module.exit_json(changed=True, gpu_allocation=to_dict(resource))
        return

    module.exit_json(changed=False, gpu_allocation=to_dict(existing))


if __name__ == "__main__":
    main()
