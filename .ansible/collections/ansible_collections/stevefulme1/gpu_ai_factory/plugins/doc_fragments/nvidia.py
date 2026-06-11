# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Common documentation fragment for NVIDIA AI Factory modules."""

    DOCUMENTATION = r"""
options:
  bcm_url:
    description:
      - The URL of the NVIDIA Base Command Manager API endpoint.
      - Can also be set via the C(NVIDIA_BCM_URL) environment variable.
    type: str
    required: true
  bcm_username:
    description:
      - The username for BCM API authentication.
      - Can also be set via the C(NVIDIA_BCM_USERNAME) environment variable.
    type: str
  bcm_password:
    description:
      - The password for BCM API authentication.
      - Can also be set via the C(NVIDIA_BCM_PASSWORD) environment variable.
    type: str
  bcm_token:
    description:
      - An API token for BCM authentication (alternative to username/password).
      - Can also be set via the C(NVIDIA_BCM_TOKEN) environment variable.
    type: str
  validate_certs:
    description:
      - Whether to validate SSL certificates when connecting to the BCM API.
    type: bool
    default: true
  wait:
    description:
      - Whether to wait for the resource to reach the desired state.
    type: bool
    default: true
  wait_timeout:
    description:
      - Maximum time in seconds to wait for resource state changes.
    type: int
    default: 600
  wait_interval:
    description:
      - Time in seconds between polling attempts when waiting.
    type: int
    default: 10
"""
