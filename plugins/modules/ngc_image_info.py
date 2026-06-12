# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying NVIDIA NGC Image resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: ngc_image_info
short_description: Query NGC container images
description:
    - Retrieve information about NVIDIA NGC container images.
    - This module is read-only and does not modify any resources.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    image_name:
        description:
            - NGC image name to query. If omitted, all images are returned.
        type: str
    image_id:
        description:
            - Specific NGC image ID to query.
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
- name: List all NGC images
  stevefulme1.gpu_ai_factory.ngc_image_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"

- name: Get a specific NGC image by name
  stevefulme1.gpu_ai_factory.ngc_image_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    image_name: "nvcr.io/nvidia/pytorch"

- name: Get a specific NGC image by ID
  stevefulme1.gpu_ai_factory.ngc_image_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    image_id: "img-12345"
"""

RETURN = r"""
ngc_images:
    description: List of NGC image information dictionaries.
    returned: always
    type: list
    elements: dict
    contains:
        image_id:
            description: NGC image identifier.
            type: str
        image_name:
            description: NGC image name.
            type: str
        registry:
            description: NGC registry URL.
            type: str
        tag:
            description: Image tag.
            type: str
        pull_policy:
            description: Image pull policy.
            type: str
        state:
            description: Current state of the image.
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
        image_name=dict(type="str"),
        image_id=dict(type="str"),
    )
    module_args.update(NVIDIA_COMMON_ARGS)
    return module_args


def get_resource(client, base_url, resource_id):
    """Get a resource by ID."""
    url = f"{base_url}/api/v1/ngc-images/{resource_id}"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests_lib.exceptions.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def list_resources(client, base_url, image_name=None):
    """List all resources or filter by name."""
    url = f"{base_url}/api/v1/ngc-images"
    try:
        resp = call_with_retry(client.get, url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", data.get("results", []))

        if image_name:
            items = [item for item in items if item.get("image_name") == image_name]

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

    if params.get("image_id"):
        resource = get_resource(client, base_url, params["image_id"])
        if resource:
            module.exit_json(changed=False, ngc_images=[to_dict(resource)])
        else:
            module.exit_json(changed=False, ngc_images=[])
    else:
        resources = list_resources(client, base_url, params.get("image_name"))
        module.exit_json(changed=False, ngc_images=[to_dict(r) for r in resources])


if __name__ == "__main__":
    main()
