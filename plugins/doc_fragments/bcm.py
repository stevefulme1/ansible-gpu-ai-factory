# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    """Doc fragment for BCM CMDaemon API modules."""

    DOCUMENTATION = r"""
options:
    bcm_url:
        description:
            - URL of the BCM CMDaemon REST API.
            - Typically runs on port 8081 of the head node.
        type: str
        required: true
    bcm_username:
        description:
            - CMDaemon username for authentication.
            - Required unless O(bcm_token) is provided.
        type: str
    bcm_password:
        description:
            - CMDaemon password for authentication.
            - Required unless O(bcm_token) is provided.
        type: str
    bcm_token:
        description:
            - Pre-existing authentication token for CMDaemon.
            - If provided, O(bcm_username) and O(bcm_password) are ignored.
        type: str
    validate_certs:
        description:
            - Whether to validate TLS certificates.
        type: bool
        default: true
"""
