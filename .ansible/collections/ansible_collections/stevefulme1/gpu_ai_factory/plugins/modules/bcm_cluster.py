# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing NVIDIA Bcm Cluster resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_cluster
short_description: Manage BCM clusters
description:
    - Create, update, and delete NVIDIA Base Command Manager clusters.
    - This module is idempotent and supports check mode.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    name:
        description:
            - The name of the BCM cluster.
        type: str
        required: true
    description:
        description:
            - Description of the cluster.
        type: str
    cluster_type:
        description:
            - Type of cluster.
        type: str
        choices:
            - slurm
            - kubernetes
    max_nodes:
        description:
            - Maximum number of nodes.
        type: int
    cluster_id:
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
- name: Create a bcm cluster
  stevefulme1.gpu_ai_factory.bcm_cluster:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    state: present

- name: Delete a bcm cluster
  stevefulme1.gpu_ai_factory.bcm_cluster:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    cluster_id: "example-id"
    state: absent
"""

RETURN = r"""
cluster:
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
        description=dict(type="str"),
        cluster_type=dict(type="str", choices=['slurm', 'kubernetes']),
        max_nodes=dict(type="int"),
        cluster_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/clusters/{resource_id}"
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
    url = f"{base_url}/api/v1/clusters"
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
    if params.get("description") is not None:
        payload["description"] = params["description"]
    if params.get("cluster_type") is not None:
        payload["cluster_type"] = params["cluster_type"]
    if params.get("max_nodes") is not None:
        payload["max_nodes"] = params["max_nodes"]

    url = f"{base_url}/api/v1/clusters"
    resp = call_with_retry(client.post, url, json=payload, timeout=60)
    resp.raise_for_status()
    resource = resp.json()

    resource_id = resource.get("id") or resource.get("cluster_id")
    if resource_id and module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        resource = wait_for_resource(module, _get, resource_id, target_states=READY_STATES)
    return resource


def update_resource(module, client, base_url, existing):
    """Update an existing resource."""
    params = module.params
    resource_id = existing.get("id") or existing.get("cluster_id")
    payload = {}
    if params.get("name") is not None:
        payload["name"] = params["name"]
    if params.get("description") is not None:
        payload["description"] = params["description"]
    if params.get("cluster_type") is not None:
        payload["cluster_type"] = params["cluster_type"]
    if params.get("max_nodes") is not None:
        payload["max_nodes"] = params["max_nodes"]

    url = f"{base_url}/api/v1/clusters/{resource_id}"
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
    resource_id = existing.get("id") or existing.get("cluster_id")
    url = f"{base_url}/api/v1/clusters/{resource_id}"
    call_with_retry(client.delete, url, timeout=60)

    if module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        wait_for_resource(module, _get, resource_id, target_states=DEAD_STATES)


def needs_update(params, existing):
    """Check if the existing resource needs updating."""
    desired = params.get("name")
    if desired is not None:
        current = existing.get("name")
        if current != desired:
            return True
    desired = params.get("description")
    if desired is not None:
        current = existing.get("description")
        if current != desired:
            return True
    desired = params.get("max_nodes")
    if desired is not None:
        current = existing.get("max_nodes")
        if current != desired:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[("state", "present", ("name",), True)],
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url
    state = params["state"]

    existing = None
    if params.get("cluster_id"):
        existing = get_resource(client, base_url, params["cluster_id"])
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
        module.exit_json(changed=True, cluster=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, base_url, existing)
        module.exit_json(changed=True, cluster=to_dict(resource))
        return

    module.exit_json(changed=False, cluster=to_dict(existing))


if __name__ == "__main__":
    main()
