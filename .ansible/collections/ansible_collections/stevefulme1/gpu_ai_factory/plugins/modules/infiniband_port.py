# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing NVIDIA Infiniband Port resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: infiniband_port
short_description: Configure InfiniBand ports
description:
    - Configure InfiniBand port settings on DGX/HGX systems.
    - This module is idempotent and supports check mode.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    port_name:
        description:
            - InfiniBand port identifier.
        type: str
        required: true
    node_id:
        description:
            - Node ID of the DGX/HGX system.
        type: str
        required: true
    speed:
        description:
            - Port speed.
        type: str
        choices:
            - hdr
            - hdr100
            - ndr
            - ndr200
            - xdr
    mtu:
        description:
            - Maximum Transmission Unit size.
        type: int
    partition_key:
        description:
            - InfiniBand partition key.
        type: str
    enabled:
        description:
            - Whether the port is enabled.
        type: bool
        default: false
    port_id:
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
- name: Create a infiniband port
  stevefulme1.gpu_ai_factory.infiniband_port:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    state: present

- name: Delete a infiniband port
  stevefulme1.gpu_ai_factory.infiniband_port:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    port_id: "example-id"
    state: absent
"""

RETURN = r"""
ib_port:
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
        port_name=dict(type="str", required=True),
        node_id=dict(type="str", required=True),
        speed=dict(type="str", choices=['hdr', 'hdr100', 'ndr', 'ndr200', 'xdr']),
        mtu=dict(type="int"),
        partition_key=dict(type="str", no_log=True),
        enabled=dict(type="bool", default=False),
        port_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/infiniband/ports/{resource_id}"
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
    name_val = params.get("port_name")
    if not name_val:
        return None
    url = f"{base_url}/api/v1/infiniband/ports"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))
        for item in items:
            if item.get("state", "").upper() in DEAD_STATES:
                continue
            if item.get("port_name") == name_val:
                return item
    except requests_lib.exceptions.HTTPError:
        pass
    return None


def create_resource(module, client, base_url):
    """Create a new resource."""
    params = module.params
    payload = {}
    if params.get("port_name") is not None:
        payload["port_name"] = params["port_name"]
    if params.get("node_id") is not None:
        payload["node_id"] = params["node_id"]
    if params.get("speed") is not None:
        payload["speed"] = params["speed"]
    if params.get("mtu") is not None:
        payload["mtu"] = params["mtu"]
    if params.get("partition_key") is not None:
        payload["partition_key"] = params["partition_key"]
    if params.get("enabled") is not None:
        payload["enabled"] = params["enabled"]

    url = f"{base_url}/api/v1/infiniband/ports"
    resp = call_with_retry(client.post, url, json=payload, timeout=60)
    resp.raise_for_status()
    resource = resp.json()

    resource_id = resource.get("id") or resource.get("port_id")
    if resource_id and module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        resource = wait_for_resource(module, _get, resource_id, target_states=READY_STATES)
    return resource


def update_resource(module, client, base_url, existing):
    """Update an existing resource."""
    params = module.params
    resource_id = existing.get("id") or existing.get("port_id")
    payload = {}
    if params.get("port_name") is not None:
        payload["port_name"] = params["port_name"]
    if params.get("node_id") is not None:
        payload["node_id"] = params["node_id"]
    if params.get("speed") is not None:
        payload["speed"] = params["speed"]
    if params.get("mtu") is not None:
        payload["mtu"] = params["mtu"]
    if params.get("partition_key") is not None:
        payload["partition_key"] = params["partition_key"]
    if params.get("enabled") is not None:
        payload["enabled"] = params["enabled"]

    url = f"{base_url}/api/v1/infiniband/ports/{resource_id}"
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
    resource_id = existing.get("id") or existing.get("port_id")
    url = f"{base_url}/api/v1/infiniband/ports/{resource_id}"
    call_with_retry(client.delete, url, timeout=60)

    if module.params.get("wait", True):
        def _get(rid):
            return get_resource(client, base_url, rid)
        wait_for_resource(module, _get, resource_id, target_states=DEAD_STATES)


def needs_update(params, existing):
    """Check if the existing resource needs updating."""
    desired = params.get("speed")
    if desired is not None:
        current = existing.get("speed")
        if current != desired:
            return True
    desired = params.get("mtu")
    if desired is not None:
        current = existing.get("mtu")
        if current != desired:
            return True
    desired = params.get("partition_key")
    if desired is not None:
        current = existing.get("partition_key")
        if current != desired:
            return True
    desired = params.get("enabled")
    if desired is not None:
        current = existing.get("enabled")
        if current != desired:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[("state", "present", ("port_name", "node_id",), True)],
    )

    if not HAS_REQUESTS:
        module.fail_json(msg="The 'requests' Python library is required.")

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url
    state = params["state"]

    existing = None
    if params.get("port_id"):
        existing = get_resource(client, base_url, params["port_id"])
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
        module.exit_json(changed=True, ib_port=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, base_url, existing)
        module.exit_json(changed=True, ib_port=to_dict(resource))
        return

    module.exit_json(changed=False, ib_port=to_dict(existing))


if __name__ == "__main__":
    main()
