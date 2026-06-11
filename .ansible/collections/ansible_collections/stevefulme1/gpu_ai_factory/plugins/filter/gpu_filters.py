# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: gpu_filters
author: Steve Fulmer (@stevefulme1)
short_description: Filters for GPU-related data in NVIDIA AI Factory
version_added: "1.0.0"
description:
  - Provides Jinja2 filters for working with GPU node data returned
    by the NVIDIA AI Factory collection.
  - Includes filters for summing GPU memory, counting GPUs, filtering
    nodes by GPU type, and averaging GPU utilization from telemetry data.
extends_documentation_fragment:
  - stevefulme1.gpu_ai_factory.nvidia
"""

EXAMPLES = r"""
# Sum total GPU memory across all nodes
- name: Calculate total GPU memory
  ansible.builtin.debug:
    msg: "Total GPU memory: {{ nodes | stevefulme1.gpu_ai_factory.gpu_memory_total }} GB"

# Count GPUs across nodes
- name: Count all GPUs
  ansible.builtin.debug:
    msg: "Total GPUs: {{ nodes | stevefulme1.gpu_ai_factory.gpu_count }}"

# Filter nodes to only those with H100 GPUs
- name: Get H100 nodes
  ansible.builtin.debug:
    msg: "H100 nodes: {{ nodes | stevefulme1.gpu_ai_factory.filter_by_gpu_type('H100') }}"

# Calculate average GPU utilization
- name: Average GPU utilization
  ansible.builtin.debug:
    msg: >-
      Average utilization:
      {{ telemetry | stevefulme1.gpu_ai_factory.gpu_utilization_avg }}%
"""

from ansible.errors import AnsibleFilterError


def gpu_memory_total(nodes, memory_key="gpu_memory_gb"):
    """Sum total GPU memory across a list of nodes.

    Args:
        nodes: List of node dictionaries, each containing a GPU memory field.
        memory_key: The dictionary key for GPU memory per node (default: gpu_memory_gb).

    Returns:
        Total GPU memory in GB as a float.
    """
    if not isinstance(nodes, list):
        raise AnsibleFilterError(
            "gpu_memory_total expects a list of node dicts, got {0}".format(
                type(nodes).__name__
            )
        )
    total = 0.0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        mem = node.get(memory_key, 0)
        try:
            total += float(mem)
        except (TypeError, ValueError):
            continue
    return total


def gpu_count(nodes, count_key="gpu_count"):
    """Count total GPUs across a list of nodes.

    Args:
        nodes: List of node dictionaries, each containing a GPU count field.
        count_key: The dictionary key for GPU count per node (default: gpu_count).

    Returns:
        Total number of GPUs as an integer.
    """
    if not isinstance(nodes, list):
        raise AnsibleFilterError(
            "gpu_count expects a list of node dicts, got {0}".format(
                type(nodes).__name__
            )
        )
    total = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        count = node.get(count_key, 0)
        try:
            total += int(count)
        except (TypeError, ValueError):
            continue
    return total


def filter_by_gpu_type(nodes, gpu_type, type_key="gpu_type"):
    """Filter nodes by GPU model type.

    Args:
        nodes: List of node dictionaries.
        gpu_type: GPU model to filter by (e.g., 'A100', 'H100', 'B200').
        type_key: The dictionary key for GPU type (default: gpu_type).

    Returns:
        Filtered list of node dictionaries matching the GPU type.
    """
    if not isinstance(nodes, list):
        raise AnsibleFilterError(
            "filter_by_gpu_type expects a list of node dicts, got {0}".format(
                type(nodes).__name__
            )
        )
    if not gpu_type:
        raise AnsibleFilterError("filter_by_gpu_type requires a gpu_type argument")

    gpu_type_lower = gpu_type.lower()
    return [
        node for node in nodes
        if isinstance(node, dict)
        and gpu_type_lower in node.get(type_key, "").lower()
    ]


def gpu_utilization_avg(telemetry_data, util_key="gpu_utilization"):
    """Calculate average GPU utilization from telemetry data.

    Args:
        telemetry_data: List of telemetry dictionaries, each with a utilization field.
        util_key: The dictionary key for GPU utilization percentage
                  (default: gpu_utilization).

    Returns:
        Average GPU utilization as a float (0-100).
    """
    if not isinstance(telemetry_data, list):
        raise AnsibleFilterError(
            "gpu_utilization_avg expects a list of telemetry dicts, got {0}".format(
                type(telemetry_data).__name__
            )
        )
    values = []
    for entry in telemetry_data:
        if not isinstance(entry, dict):
            continue
        util = entry.get(util_key)
        if util is not None:
            try:
                values.append(float(util))
            except (TypeError, ValueError):
                continue
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


class FilterModule(object):
    """GPU-related filters for NVIDIA AI Factory."""

    def filters(self):
        return {
            "gpu_memory_total": gpu_memory_total,
            "gpu_count": gpu_count,
            "filter_by_gpu_type": filter_by_gpu_type,
            "gpu_utilization_avg": gpu_utilization_avg,
        }
