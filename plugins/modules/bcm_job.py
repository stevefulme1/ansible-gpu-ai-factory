#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: bcm_job
short_description: Submit and manage workload jobs on NVIDIA BCM
version_added: "1.0.0"
description:
    - Submits, cancels, or manages workload jobs on NVIDIA Base
      Command Manager (BCM) via the CMDaemon REST API.
author:
    - Steve Fulmer (@stevefulme1)
extends_documentation_fragment:
    - stevefulme1.gpu_ai_factory.bcm
options:
    bcm_url:
        required: true
    name:
        description:
            - Name for the job.
        type: str
        required: true
    job_id:
        description:
            - ID of an existing job.
            - Required when O(state=cancelled).
        type: str
    command:
        description:
            - Command to execute.
            - Required when O(state=submitted).
        type: str
    num_gpus:
        description:
            - Number of GPUs to allocate for the job.
        type: int
        default: 1
    num_nodes:
        description:
            - Number of nodes to allocate.
        type: int
        default: 1
    queue:
        description:
            - Workload queue to submit the job to.
        type: str
    state:
        description:
            - Desired state of the job.
            - C(submitted) creates a new job.
            - C(cancelled) cancels an existing job.
        type: str
        default: submitted
        choices:
            - submitted
            - cancelled
requirements:
    - requests
"""

EXAMPLES = r"""
- name: Submit a training job
  stevefulme1.gpu_ai_factory.bcm_job:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
    name: llm-training-run-1
    command: "/opt/train/run.sh --epochs 10"
    num_gpus: 8
    num_nodes: 2
    queue: gpu-high
  register: job

- name: Cancel a running job
  stevefulme1.gpu_ai_factory.bcm_job:
    bcm_url: https://bcm-head:8081
    bcm_username: admin
    bcm_password: "{{ vault_bcm_password }}"
    name: llm-training-run-1
    job_id: "{{ job.job.id }}"
    state: cancelled
"""

RETURN = r"""
job:
    description: Job details after the operation.
    type: dict
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
        name=dict(type="str", required=True),
        job_id=dict(type="str"),
        command=dict(type="str"),
        num_gpus=dict(type="int", default=1),
        num_nodes=dict(type="int", default=1),
        queue=dict(type="str"),
        state=dict(
            type="str", default="submitted",
            choices=["submitted", "cancelled"],
        ),
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
        required_if=[
            ("state", "submitted", ("command",)),
            ("state", "cancelled", ("job_id",)),
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

    if p["state"] == "cancelled":
        if module.check_mode:
            module.exit_json(changed=True, msg="Would cancel job")
        try:
            client.cancel_job(p["job_id"])
        except Exception as exc:
            module.fail_json(msg="Failed to cancel job: {0}".format(exc))
        module.exit_json(
            changed=True,
            job=dict(id=p["job_id"], state="cancelled"),
        )

    # state == submitted
    payload = dict(
        name=p["name"],
        command=p["command"],
        numGpus=p["num_gpus"],
        numNodes=p["num_nodes"],
    )
    if p["queue"]:
        payload["queue"] = p["queue"]

    if module.check_mode:
        module.exit_json(changed=True, msg="Would submit job")

    try:
        data = client.submit_job(payload)
    except Exception as exc:
        module.fail_json(msg="Failed to submit job: {0}".format(exc))

    job = data.get("job", data)
    module.exit_json(changed=True, job=job)


if __name__ == "__main__":
    main()
