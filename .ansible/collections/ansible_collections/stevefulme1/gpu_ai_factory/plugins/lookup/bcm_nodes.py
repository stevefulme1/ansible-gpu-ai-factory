# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: bcm_nodes
author: Steve Fulmer (@stevefulme1)
short_description: Lookup BCM-registered nodes by cluster or tenant
version_added: "1.0.0"
description:
  - Queries the NVIDIA Base Command Manager API to retrieve nodes
    registered in a specific cluster or tenant.
  - Returns a list of node dictionaries with hostname, IP, GPU info,
    status, and other host details suitable for dynamic use in playbooks.
  - Can be used to build dynamic inventories or target specific nodes
    for GPU workload deployment.
options:
  _terms:
    description:
      - Cluster name or tenant name to filter nodes by.
      - If not specified, all nodes in the BCM instance are returned.
    type: str
    required: false
  bcm_url:
    description:
      - The URL of the NVIDIA Base Command Manager API endpoint.
      - Can also be set via the C(NVIDIA_BCM_URL) environment variable.
    type: str
    required: true
    env:
      - name: NVIDIA_BCM_URL
  bcm_token:
    description:
      - An API token for BCM authentication.
      - Can also be set via the C(NVIDIA_BCM_TOKEN) environment variable.
    type: str
    env:
      - name: NVIDIA_BCM_TOKEN
  bcm_username:
    description:
      - The username for BCM API authentication.
      - Can also be set via the C(NVIDIA_BCM_USERNAME) environment variable.
    type: str
    env:
      - name: NVIDIA_BCM_USERNAME
  bcm_password:
    description:
      - The password for BCM API authentication.
      - Can also be set via the C(NVIDIA_BCM_PASSWORD) environment variable.
    type: str
    env:
      - name: NVIDIA_BCM_PASSWORD
  validate_certs:
    description:
      - Whether to validate SSL certificates when connecting to the BCM API.
    type: bool
    default: true
  status:
    description:
      - Filter nodes by their operational status (e.g., C(UP), C(DOWN),
        C(PROVISIONING)).
    type: str
    required: false
extends_documentation_fragment:
  - stevefulme1.gpu_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Get all BCM-registered nodes
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.gpu_ai_factory.bcm_nodes') }}"

- name: Get nodes in a specific cluster
  ansible.builtin.debug:
    msg: >-
      {{ lookup('stevefulme1.gpu_ai_factory.bcm_nodes', 'gpu-cluster-01') }}

- name: Get only active nodes in a tenant
  ansible.builtin.debug:
    msg: >-
      {{ lookup('stevefulme1.gpu_ai_factory.bcm_nodes', 'tenant-ml',
                status='UP') }}

- name: Use nodes in a play for dynamic targeting
  hosts: localhost
  tasks:
    - name: Gather GPU nodes
      ansible.builtin.set_fact:
        gpu_hosts: >-
          {{ lookup('stevefulme1.gpu_ai_factory.bcm_nodes',
                    'gpu-cluster-01') | map(attribute='hostname') | list }}
"""

RETURN = r"""
_raw:
  description:
    - List of node dictionaries matching the filter criteria.
  type: list
  elements: dict
  contains:
    hostname:
      description: The fully qualified hostname of the node.
      type: str
    ip_address:
      description: The management IP address of the node.
      type: str
    mac_address:
      description: The management MAC address.
      type: str
    status:
      description: Current operational status (UP, DOWN, etc.).
      type: str
    gpu_count:
      description: Number of GPUs installed in the node.
      type: int
    gpu_type:
      description: The GPU model (e.g., A100, H100, B200).
      type: str
    cluster:
      description: The cluster the node belongs to.
      type: str
    tenant:
      description: The tenant the node is assigned to, if any.
      type: str
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

display = Display()


class LookupModule(LookupBase):
    """Lookup BCM-registered nodes by cluster or tenant."""

    def run(self, terms, variables=None, **kwargs):
        if not HAS_REQUESTS:
            raise AnsibleError(
                "The 'requests' Python library is required for the bcm_nodes "
                "lookup. Install with: pip install requests"
            )

        self.set_options(var_options=variables, direct=kwargs)

        bcm_url = self.get_option("bcm_url") or os.environ.get("NVIDIA_BCM_URL")
        if not bcm_url:
            raise AnsibleError(
                "bcm_url is required (option or NVIDIA_BCM_URL env var)"
            )
        bcm_url = bcm_url.rstrip("/")

        validate_certs = self.get_option("validate_certs")
        status_filter = self.get_option("status")

        session = requests.Session()
        session.verify = validate_certs
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        token = self.get_option("bcm_token") or os.environ.get("NVIDIA_BCM_TOKEN")
        if token:
            session.headers["Authorization"] = "Bearer {0}".format(token)
        else:
            username = (
                self.get_option("bcm_username")
                or os.environ.get("NVIDIA_BCM_USERNAME")
            )
            password = (
                self.get_option("bcm_password")
                or os.environ.get("NVIDIA_BCM_PASSWORD")
            )
            if username and password:
                session.auth = (username, password)
            else:
                raise AnsibleError(
                    "Either bcm_token or bcm_username/bcm_password is required."
                )

        cluster_or_tenant = terms[0] if terms else None

        url = "{0}/api/v1/nodes".format(bcm_url)
        params = {}
        if cluster_or_tenant:
            params["cluster"] = cluster_or_tenant

        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            nodes = resp.json()
        except requests.exceptions.RequestException as exc:
            raise AnsibleError(
                "Failed to query BCM nodes: {0}".format(exc)
            )

        if not isinstance(nodes, list):
            nodes = nodes.get("data", nodes.get("nodes", []))

        # If cluster filter didn't match, try tenant filter
        if cluster_or_tenant and not nodes:
            params = {"tenant": cluster_or_tenant}
            try:
                resp = session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                nodes = resp.json()
            except requests.exceptions.RequestException as exc:
                raise AnsibleError(
                    "Failed to query BCM nodes: {0}".format(exc)
                )
            if not isinstance(nodes, list):
                nodes = nodes.get("data", nodes.get("nodes", []))

        if status_filter:
            nodes = [
                n for n in nodes
                if n.get("status", "").upper() == status_filter.upper()
            ]

        return [nodes]
