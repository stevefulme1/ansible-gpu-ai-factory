#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_job_info
short_description: Get workload job information from NVIDIA BCM
version_added: "1.0.0"
description:
    - Retrieves workload job information from NVIDIA Base Command
      Manager (BCM) via the CMDaemon REST API.
    - Can list all jobs, filter by state, or get a specific job.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.bcm
options:
    bcm_url:
        required: true
    job_id:
        description:
            - ID of a specific job to retrieve.
            - If omitted, all jobs are listed.
        type: str
    state_filter:
        description:
            - Filter jobs by state (e.g. C(running), C(pending), C(completed)).
        type: str
requirements:
    - requests
"""

EXAMPLES = r"""
- name: List all BCM jobs
  stevefulme1.gpu_ai_factory.bcm_job_info:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
  register: jobs

- name: Get specific job details
  stevefulme1.gpu_ai_factory.bcm_job_info:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
    job_id: "12345"
  register: job
"""

RETURN = r"""
jobs:
    description: List of workload job details.
    type: list
    elements: dict
    returned: always
job_count:
    description: Total number of jobs returned.
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
        job_id=dict(type="str"),
        state_filter=dict(type="str"),
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
        if p["job_id"]:
            data = client.get_job(p["job_id"])
            jobs = [data] if isinstance(data, dict) else data
        else:
            data = client.list_jobs(state=p.get("state_filter"))
            jobs = data.get("jobs", data) if isinstance(data, dict) else data
    except Exception as exc:
        module.fail_json(msg="Failed to query BCM jobs: {0}".format(exc))

    if not isinstance(jobs, list):
        jobs = [jobs]

    module.exit_json(changed=False, jobs=jobs, job_count=len(jobs))


if __name__ == "__main__":
    main()
