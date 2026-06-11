# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for bcm_cluster module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


def set_module_args(args):
    """Prepare arguments for AnsibleModule."""
    if "_ansible_remote_tmp" not in args:
        args["_ansible_remote_tmp"] = "/tmp"
    if "_ansible_keep_remote_files" not in args:
        args["_ansible_keep_remote_files"] = False
    args_json = json.dumps({"ANSIBLE_MODULE_ARGS": args})
    basic._ANSIBLE_ARGS = to_bytes(args_json)


class AnsibleExitJson(Exception):
    """Exception for module exit_json calls."""

    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__()


class AnsibleFailJson(Exception):
    """Exception for module fail_json calls."""

    def __init__(self, kwargs):
        self.kwargs = kwargs
        super().__init__()


@pytest.fixture
def mock_module(monkeypatch):
    """Patch AnsibleModule exit/fail for testing."""
    monkeypatch.setattr(
        basic.AnsibleModule, "exit_json",
        lambda self, **kwargs: (__x for __x in ()).throw(AnsibleExitJson(kwargs)),
    )
    monkeypatch.setattr(
        basic.AnsibleModule, "fail_json",
        lambda self, **kwargs: (__x for __x in ()).throw(AnsibleFailJson(kwargs)),
    )


class TestBcmCluster:
    """Tests for bcm_cluster module."""

    @patch(
        "ansible_collections.stevefulme1.gpu_ai_factory."
        "plugins.modules.bcm_cluster.create_bcm_client"
    )
    def test_missing_requests_fails(self, mock_client, mock_module):
        set_module_args({
            "bcm_url": "https://bcm.example.com",
            "bcm_token": "test-token",
            "name": "test-cluster",
            "state": "present",
        })

        with patch(
            "ansible_collections.stevefulme1.gpu_ai_factory."
            "plugins.modules.bcm_cluster.HAS_REQUESTS",
            False,
        ):
            from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules import bcm_cluster
            with pytest.raises(AnsibleFailJson) as exc_info:
                bcm_cluster.main()
            assert "requests" in exc_info.value.kwargs["msg"]
