# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
name: dgx_categories
author: Steve Fulmer (@stevefulme1)
short_description: Lookup DGX software categories from BCM
version_added: "1.0.0"
description:
  - Queries the NVIDIA Base Command Manager API to retrieve DGX software
    categories such as disk setup, kernel modules, kernel parameters,
    and software images.
  - Returns a list of category dictionaries with name, type, and items.
  - Useful for discovering available configuration categories before
    applying software images or kernel settings to nodes.
options:
  _terms:
    description:
      - Category type to filter by (e.g., C(disk_setup), C(kernel_modules),
        C(kernel_params), C(software_images)).
      - If not specified, all categories are returned.
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
extends_documentation_fragment:
  - stevefulme1.gpu_ai_factory.nvidia
"""

EXAMPLES = r"""
- name: Get all DGX software categories
  ansible.builtin.debug:
    msg: "{{ lookup('stevefulme1.gpu_ai_factory.dgx_categories') }}"

- name: Get only kernel module categories
  ansible.builtin.debug:
    msg: >-
      {{ lookup('stevefulme1.gpu_ai_factory.dgx_categories',
                'kernel_modules') }}

- name: List available disk setup configurations
  vars:
    disk_cats: >-
      {{ lookup('stevefulme1.gpu_ai_factory.dgx_categories', 'disk_setup') }}
  ansible.builtin.debug:
    msg: "Disk setup options: {{ disk_cats | map(attribute='name') | list }}"
"""

RETURN = r"""
_raw:
  description:
    - List of category dictionaries matching the filter criteria.
  type: list
  elements: dict
  contains:
    name:
      description: The category name.
      type: str
    type:
      description: The category type (disk_setup, kernel_modules, etc.).
      type: str
    description:
      description: Human-readable description of the category.
      type: str
    category_items:
      description: List of items within this category.
      type: list
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
    """Lookup DGX software categories from BCM."""

    def run(self, terms, variables=None, **kwargs):
        if not HAS_REQUESTS:
            raise AnsibleError(
                "The 'requests' Python library is required for the "
                "dgx_categories lookup. Install with: pip install requests"
            )

        self.set_options(var_options=variables, direct=kwargs)

        bcm_url = self.get_option("bcm_url") or os.environ.get("NVIDIA_BCM_URL")
        if not bcm_url:
            raise AnsibleError(
                "bcm_url is required (option or NVIDIA_BCM_URL env var)"
            )
        bcm_url = bcm_url.rstrip("/")

        validate_certs = self.get_option("validate_certs")

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

        url = "{0}/api/v1/categories".format(bcm_url)
        category_filter = terms[0] if terms else None

        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            categories = resp.json()
        except requests.exceptions.RequestException as exc:
            raise AnsibleError(
                "Failed to query DGX categories from BCM: {0}".format(exc)
            )

        if not isinstance(categories, list):
            categories = categories.get("data", categories.get("categories", []))

        if category_filter:
            categories = [
                cat for cat in categories
                if cat.get("type", "").lower() == category_filter.lower()
            ]

        return [categories]
