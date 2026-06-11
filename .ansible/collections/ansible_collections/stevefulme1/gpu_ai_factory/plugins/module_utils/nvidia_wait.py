"""Waiter and retry utilities for NVIDIA BCM resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module_utils: nvidia_wait
short_description: Waiter and retry utilities for NVIDIA BCM API operations
description:
  - Provides wait_for_resource to poll a BCM resource until it reaches a
    target state, with configurable timeout and failure state detection.
  - Includes call_with_retry for exponential backoff retries on transient
    API errors (429, 500, 503).
author:
  - Steve Fulmer (@stevefulme1)
"""

import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def wait_for_resource(
    module,
    get_fn,
    resource_id,
    target_states,
    failure_states=None,
):
    """Poll a resource until it reaches a target state."""
    wait = module.params.get("wait", True)
    if not wait:
        return get_fn(resource_id)

    timeout = module.params.get("wait_timeout", 600)
    interval = module.params.get("wait_interval", 10)

    if failure_states is None:
        failure_states = frozenset({"FAILED", "ERROR"})

    start = time.monotonic()
    while True:
        resource = get_fn(resource_id)
        if resource is None:
            if "DELETED" in target_states:
                return None
            # Resource disappeared unexpectedly; keep polling briefly
            elapsed = time.monotonic() - start
            if elapsed >= timeout:
                module.fail_json(
                    msg=f"Resource {resource_id} not found while waiting "
                    f"for states {target_states}.",
                )
            time.sleep(min(interval, timeout - elapsed))
            continue

        state = resource.get("state") or resource.get("status", "")
        state = state.upper()

        if state in target_states:
            return resource
        if state in failure_states:
            module.fail_json(
                msg=f"Resource {resource_id} entered failure state: {state}",
            )

        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            module.fail_json(
                msg=f"Timed out waiting for resource {resource_id} to reach "
                f"state {target_states}. Current state: {state}",
            )
        time.sleep(min(interval, timeout - elapsed))


def call_with_retry(fn, *args, max_retries=3, retry_on=(429, 500, 503), **kwargs):
    """Call a BCM API function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            status = getattr(exc.response, "status_code", None)
            if status not in retry_on or attempt == max_retries:
                raise
            time.sleep(2 ** attempt)
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)
    raise last_error  # pragma: no cover
