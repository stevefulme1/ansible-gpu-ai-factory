# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: dgx_images
author: Steve Fulmer (@stevefulme1)
short_description: Lookup available DGX OS images from BCM
version_added: "1.0.0"
description:
  - Queries the NVIDIA Base Command Manager API to retrieve available DGX OS
    images for the specified architecture and distribution.
  - Returns a list of image dictionaries including name, version, architecture,
    distribution, and image path.
  - Useful for dynamically selecting the correct OS image during provisioning.
options:
  _terms:
    description:
      - Architecture to filter images by (e.g., C(x86_64), C(aarch64)).
      - If not specified, all architectures are returned.
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
  distro:
    description:
      - Filter images by distribution name (e.g., C(ubuntu22.04), C(rhel9)).
    type: str
    required: false
  validate_certs:
    description:
      - Whether to validate SSL certificates when connecting to the BCM API.
    type: bool
    default: true
extends_documentation_fragment:
  - stevefulme1.gpu_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Get all available DGX images
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.gpu_ai_factory.dgx_images') }}"

- name: Get x86_64 images only
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.gpu_ai_factory.dgx_images', 'x86_64') }}"

- name: Get RHEL 9 images for x86_64
  ansible.builtin.debug:
    msg: >-
      {{ lookup('stevefulme1.gpu_ai_factory.dgx_images', 'x86_64',
                distro='rhel9') }}

- name: Use in a loop to provision nodes with latest image
  vars:
    images: "{{ lookup('stevefulme1.gpu_ai_factory.dgx_images', 'x86_64',
                        distro='ubuntu22.04') }}"
  ansible.builtin.debug:
    msg: "Latest image: {{ images | sort(attribute='version') | last }}"
"""

RETURN = r"""
_raw:
  description:
    - List of image dictionaries matching the filter criteria.
  type: list
  elements: dict
  contains:
    name:
      description: The image name.
      type: str
    version:
      description: The image version string.
      type: str
    architecture:
      description: The CPU architecture (e.g., x86_64).
      type: str
    distro:
      description: The Linux distribution.
      type: str
    path:
      description: The image file path or URI on the BCM server.
      type: str
    status:
      description: The image status (e.g., available, deprecated).
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
    """Lookup available DGX OS images from BCM."""

    def run(self, terms, variables=None, **kwargs):
        if not HAS_REQUESTS:
            raise AnsibleError(
                "The 'requests' Python library is required for the dgx_images "
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
        distro = self.get_option("distro")

        # Build authenticated session
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

        # Query the BCM software images endpoint
        url = "{0}/api/v1/software-images".format(bcm_url)
        params = {}
        if distro:
            params["distro"] = distro

        arch_filter = terms[0] if terms else None

        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            images = resp.json()
        except requests.exceptions.RequestException as exc:
            raise AnsibleError(
                "Failed to query DGX images from BCM: {0}".format(exc)
            )

        if not isinstance(images, list):
            images = images.get("data", images.get("images", []))

        # Filter by architecture if specified
        if arch_filter:
            images = [
                img for img in images
                if img.get("architecture", "").lower() == arch_filter.lower()
            ]

        return [images]
