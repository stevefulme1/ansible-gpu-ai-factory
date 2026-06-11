# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying NVIDIA Bcm Job resources."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_job_info
short_description: List or get BCM job details
description:
    - Retrieve job status and details from BCM.
    - This module is read-only and does not modify any resources.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    job_id:
        description:
            - The ID of a specific resource to retrieve.
        type: str
    name:
        description:
            - Filter resources by name.
        type: str
    cluster_id:
        description:
            - Filter by cluster.
        type: str
    tenant_id:
        description:
            - Filter by tenant.
        type: str
    status:
        description:
            - Filter by job status.
        type: str
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.nvidia
requirements:
    - "python >= 3.12"
    - "requests"
"""

EXAMPLES = r"""
- name: List all resources
  stevefulme1.gpu_ai_factory.bcm_job_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"

- name: Get a specific resource
  stevefulme1.gpu_ai_factory.bcm_job_info:
    bcm_url: "https://bcm.example.com"
    bcm_token: "{{ bcm_token }}"
    job_id: "example-id"
"""

RETURN = r"""
jobs:
    description: List of resources or a single resource dict.
    returned: always
    type: list
    elements: dict
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
        job_id=dict(type="str"),
        name=dict(type="str"),
        cluster_id=dict(type="str"),
        tenant_id=dict(type="str"),
        status=dict(type="str"),
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

    client = create_bcm_client(module)
    params = module.params
    base_url = client.base_url

    if params.get("job_id"):
        url = f"{base_url}/api/v1/jobs/{params['job_id']}"
        try:
            resp = call_with_retry(client.get, url, timeout=30)
            resp.raise_for_status()
            resource = resp.json()
            module.exit_json(changed=False, jobs=[to_dict(resource)])
        except requests_lib.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                module.exit_json(changed=False, jobs=[])
            module.fail_json(msg=f"API error: {exc}")
    else:
        url = f"{base_url}/api/v1/jobs"
        query = {}
        if params.get("name"):
            query["name"] = params["name"]
        if params.get("cluster_id"):
            query["cluster_id"] = params["cluster_id"]
        if params.get("tenant_id"):
            query["tenant_id"] = params["tenant_id"]
        if params.get("status"):
            query["status"] = params["status"]
        try:
            resp = call_with_retry(client.get, url, params=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                items = data
            else:
                items = data.get("items", data.get("results", [data]))
            module.exit_json(changed=False, jobs=[to_dict(i) for i in items])
        except requests_lib.exceptions.HTTPError as exc:
            module.fail_json(msg=f"API error: {exc}")


if __name__ == "__main__":
    main()
