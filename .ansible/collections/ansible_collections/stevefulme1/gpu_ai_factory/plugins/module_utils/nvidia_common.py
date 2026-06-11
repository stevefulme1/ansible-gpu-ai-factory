"""Common NVIDIA argument specs and constants used across all modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module_utils: nvidia_common
short_description: Shared NVIDIA argument specs and lifecycle constants
description:
  - Defines NVIDIA_COMMON_ARGS, the common argument spec shared by all
    NVIDIA AI Factory modules, covering BCM authentication, wait behavior,
    and certificate validation parameters.
  - Provides lifecycle state constants and frozen sets (WAIT_STATES,
    READY_STATES, DEAD_STATES) used for resource state management.
author:
  - Steve Fulmer (@stevefulme1)
"""


NVIDIA_COMMON_ARGS = dict(
    bcm_url=dict(type="str", required=True, fallback=(lambda: None,)),
    bcm_username=dict(type="str"),
    bcm_password=dict(type="str", no_log=True),
    bcm_token=dict(type="str", no_log=True),
    validate_certs=dict(type="bool", default=True),
    wait=dict(type="bool", default=True),
    wait_timeout=dict(type="int", default=600),
    wait_interval=dict(type="int", default=10),
)

LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_RUNNING = "RUNNING"
LIFECYCLE_PROVISIONING = "PROVISIONING"
LIFECYCLE_CREATING = "CREATING"
LIFECYCLE_UPDATING = "UPDATING"
LIFECYCLE_DELETED = "DELETED"
LIFECYCLE_DELETING = "DELETING"
LIFECYCLE_FAILED = "FAILED"
LIFECYCLE_STOPPED = "STOPPED"
LIFECYCLE_COMPLETED = "COMPLETED"
LIFECYCLE_PENDING = "PENDING"
LIFECYCLE_QUEUED = "QUEUED"

WAIT_STATES = frozenset({
    LIFECYCLE_PROVISIONING,
    LIFECYCLE_CREATING,
    LIFECYCLE_UPDATING,
    LIFECYCLE_DELETING,
    LIFECYCLE_PENDING,
    LIFECYCLE_QUEUED,
})

READY_STATES = frozenset({
    LIFECYCLE_ACTIVE,
    LIFECYCLE_RUNNING,
    LIFECYCLE_COMPLETED,
})

DEAD_STATES = frozenset({
    LIFECYCLE_DELETED,
})


def to_dict(resource):
    """Convert an API response object to a plain dictionary."""
    if resource is None:
        return {}
    if isinstance(resource, dict):
        return {k: to_dict(v) for k, v in resource.items()}
    if isinstance(resource, list):
        return [to_dict(i) for i in resource]
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            result[key] = to_dict(value)
        return result
    return resource
