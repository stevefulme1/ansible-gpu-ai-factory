"""NVIDIA BCM authentication utilities."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module_utils: nvidia_auth
short_description: NVIDIA BCM authentication and client creation
description:
  - Provides helpers for authenticating to NVIDIA Base Command Manager
    using username/password basic auth or token-based auth.
  - Exports create_bcm_client to build an authenticated requests.Session.
author:
  - Steve Fulmer (@stevefulme1)
"""

import os

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def create_bcm_client(module):
    """Create an authenticated requests.Session for the BCM REST API."""
    if not HAS_REQUESTS:
        module.fail_json(
            msg="The 'requests' Python library is required. "
            "Install with: pip install requests",
        )
        return None

    params = module.params
    bcm_url = params.get("bcm_url") or os.environ.get("NVIDIA_BCM_URL")
    if not bcm_url:
        module.fail_json(msg="bcm_url is required (param or NVIDIA_BCM_URL env var)")

    bcm_url = bcm_url.rstrip("/")
    validate_certs = params.get("validate_certs", True)

    session = requests.Session()
    session.verify = validate_certs
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })

    # Token auth takes precedence
    token = params.get("bcm_token") or os.environ.get("NVIDIA_BCM_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
        session.base_url = bcm_url
        return session

    # Fall back to basic auth
    username = params.get("bcm_username") or os.environ.get("NVIDIA_BCM_USERNAME")
    password = params.get("bcm_password") or os.environ.get("NVIDIA_BCM_PASSWORD")

    if not username or not password:
        module.fail_json(
            msg="Either bcm_token or bcm_username/bcm_password is required "
            "for BCM authentication.",
        )

    # Authenticate and obtain a session token
    auth_url = f"{bcm_url}/api/v1/auth/login"
    try:
        resp = session.post(
            auth_url,
            json={"username": username, "password": password},
            timeout=30,
        )
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("access_token") or token_data.get("token")
        if access_token:
            session.headers["Authorization"] = f"Bearer {access_token}"
        else:
            # Fall back to basic auth if no token endpoint
            session.auth = (username, password)
    except requests.exceptions.RequestException:
        # Fall back to basic auth
        session.auth = (username, password)

    session.base_url = bcm_url
    return session
