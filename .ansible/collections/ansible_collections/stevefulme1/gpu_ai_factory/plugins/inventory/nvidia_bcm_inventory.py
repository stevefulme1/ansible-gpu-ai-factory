# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Dynamic inventory plugin for NVIDIA Base Command Manager."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
name: nvidia_bcm_inventory
short_description: Dynamic inventory from NVIDIA Base Command Manager
description:
    - Generates a dynamic inventory from the NVIDIA BCM REST API.
    - Automatically groups nodes by type (dgx, hgx) and GPU model.
    - Provides GPU details, tenant assignment, and fabric topology as host vars.
version_added: "1.0.0"
author:
    - Steve Fulmer (@stevefulme1)
options:
    plugin:
        description: Name of the plugin.
        required: true
        choices: ["stevefulme1.gpu_ai_factory.nvidia_bcm_inventory"]
    bcm_url:
        description: URL of the BCM API endpoint.
        required: true
        env:
            - name: NVIDIA_BCM_URL
    bcm_username:
        description: Username for BCM API authentication.
        env:
            - name: NVIDIA_BCM_USERNAME
    bcm_password:
        description: Password for BCM API authentication.
        env:
            - name: NVIDIA_BCM_PASSWORD
    bcm_token:
        description: API token for BCM authentication.
        env:
            - name: NVIDIA_BCM_TOKEN
    validate_certs:
        description: Whether to validate SSL certificates.
        type: bool
        default: true
    cluster_id:
        description: Limit inventory to a specific cluster.
        type: str
    compose:
        description: Create vars from Jinja2 expressions.
        type: dict
        default: {}
    groups:
        description: Add hosts to groups based on Jinja2 conditionals.
        type: dict
        default: {}
    keyed_groups:
        description: Add hosts to groups based on the value of a variable.
        type: list
        default: []
        elements: dict
extends_documentation_fragment:
    - constructed
    - inventory_cache
"""

EXAMPLES = r"""
# Basic usage — nvidia_bcm.yml
plugin: stevefulme1.gpu_ai_factory.nvidia_bcm_inventory
bcm_url: https://bcm.example.com
bcm_token: "{{ lookup('env', 'NVIDIA_BCM_TOKEN') }}"
# Optional: filter to specific cluster with cluster_id: "cluster-001"
# Optional: add keyed_groups for GPU type grouping
"""

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """Dynamic inventory plugin for NVIDIA BCM."""

    NAME = "stevefulme1.gpu_ai_factory.nvidia_bcm_inventory"

    def verify_file(self, path):
        """Verify the inventory source file."""
        valid = False
        if super().verify_file(path):
            if path.endswith(("nvidia_bcm.yml", "nvidia_bcm.yaml",
                              "bcm_inventory.yml", "bcm_inventory.yaml")):
                valid = True
        return valid

    def _get_session(self):
        """Create an authenticated requests session."""
        session = requests.Session()
        session.verify = self.get_option("validate_certs")
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        token = self.get_option("bcm_token")
        if token:
            session.headers["Authorization"] = f"Bearer {token}"
            return session

        username = self.get_option("bcm_username")
        password = self.get_option("bcm_password")
        if username and password:
            bcm_url = self.get_option("bcm_url").rstrip("/")
            try:
                resp = session.post(
                    f"{bcm_url}/api/v1/auth/login",
                    json={"username": username, "password": password},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                access_token = data.get("access_token") or data.get("token")
                if access_token:
                    session.headers["Authorization"] = f"Bearer {access_token}"
                else:
                    session.auth = (username, password)
            except requests.exceptions.RequestException:
                session.auth = (username, password)

        return session

    def _fetch_nodes(self, session):
        """Fetch nodes from BCM API."""
        bcm_url = self.get_option("bcm_url").rstrip("/")
        url = f"{bcm_url}/api/v1/nodes"
        params = {}

        cluster_id = self.get_option("cluster_id")
        if cluster_id:
            params["cluster_id"] = cluster_id

        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get(
                "items", data.get("results", []))
        except requests.exceptions.RequestException as exc:
            raise AnsibleError(f"Failed to fetch nodes from BCM: {exc}")

    def _populate(self, nodes):
        """Populate inventory from BCM node data."""
        # Create standard groups
        gpu_groups = {
            "a100": "gpu_a100",
            "h100": "gpu_h100",
            "h200": "gpu_h200",
            "b200": "gpu_b200",
            "gb200": "gpu_gb200",
        }

        self.inventory.add_group("dgx_nodes")
        self.inventory.add_group("hgx_nodes")
        for group_name in gpu_groups.values():
            self.inventory.add_group(group_name)

        for node in nodes:
            hostname = node.get("hostname") or node.get("name", "unknown")
            self.inventory.add_host(hostname)

            # Set host variables
            node_type = (node.get("node_type") or "dgx").lower()
            gpu_type = (node.get("gpu_type") or "unknown").lower()
            gpu_count = node.get("gpu_count", 0)
            gpu_memory = node.get("gpu_memory", "")
            tenant = node.get("tenant", "")
            fabric_topology = node.get("fabric_topology", "")
            cluster = node.get("cluster_id", "")
            bmc_address = node.get("bmc_address", "")
            state = node.get("state", "unknown")

            self.inventory.set_variable(hostname, "node_type", node_type)
            self.inventory.set_variable(hostname, "gpu_type", gpu_type)
            self.inventory.set_variable(hostname, "gpu_count", gpu_count)
            self.inventory.set_variable(hostname, "gpu_memory", gpu_memory)
            self.inventory.set_variable(hostname, "tenant", tenant)
            self.inventory.set_variable(hostname, "fabric_topology", fabric_topology)
            self.inventory.set_variable(hostname, "cluster_id", cluster)
            self.inventory.set_variable(hostname, "bmc_address", bmc_address)
            self.inventory.set_variable(hostname, "node_state", state)

            # Add to type groups
            if node_type == "dgx":
                self.inventory.add_child("dgx_nodes", hostname)
            elif node_type == "hgx":
                self.inventory.add_child("hgx_nodes", hostname)

            # Add to GPU groups
            gpu_group = gpu_groups.get(gpu_type)
            if gpu_group:
                self.inventory.add_child(gpu_group, hostname)

            # Use constructed features
            strict = self.get_option("strict")
            self._set_composite_vars(
                self.get_option("compose"), node, hostname, strict=strict,
            )
            self._add_host_to_composed_groups(
                self.get_option("groups"), node, hostname, strict=strict,
            )
            self._add_host_to_keyed_groups(
                self.get_option("keyed_groups"), node, hostname, strict=strict,
            )

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory source."""
        super().parse(inventory, loader, path, cache)

        if not HAS_REQUESTS:
            raise AnsibleError(
                "The 'requests' Python library is required for the "
                "nvidia_bcm_inventory plugin."
            )

        self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        use_cache = self.get_option("cache") and cache
        update_cache = self.get_option("cache") and not cache

        nodes = None
        if use_cache:
            try:
                nodes = self._cache[cache_key]
            except KeyError:
                update_cache = True

        if nodes is None:
            session = self._get_session()
            nodes = self._fetch_nodes(session)

        if update_cache:
            self._cache[cache_key] = nodes

        self._populate(nodes)
