# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for amd_gpu_config module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import pytest
from unittest.mock import patch, MagicMock

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


class TestMissingRequests:
    """Test behavior when requests library is missing."""

    def test_missing_requests_fails(self, mock_module):
        set_module_args({"host": "https://rocm.example.com", "api_key": "test-key", "gpu_id": "0", "state": "present"})

        with patch(
            "ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.amd_gpu_config.HAS_REQUESTS",
            False,
        ):
            from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules import amd_gpu_config
            import importlib
            importlib.reload(amd_gpu_config)
            with patch("ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.amd_gpu_config.HAS_REQUESTS", False):
                with pytest.raises(AnsibleFailJson) as exc_info:
                    amd_gpu_config.main()
                assert "requests" in exc_info.value.kwargs["msg"]


class TestGet:
    """Test GET / list operations."""

    @patch("ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.amd_gpu_config.requests")
    def test_get_success(self, mock_requests, mock_module):
        set_module_args({"host": "https://rocm.example.com", "api_key": "test-key", "gpu_id": "0", "state": "present"})

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response
        mock_requests.post.return_value = mock_response
        mock_requests.put.return_value = mock_response
        mock_requests.delete.return_value = mock_response

        from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules import amd_gpu_config
        import importlib
        importlib.reload(amd_gpu_config)

        with pytest.raises(AnsibleExitJson):
            amd_gpu_config.main()

    @patch("ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.amd_gpu_config.requests")
    def test_api_error(self, mock_requests, mock_module):
        set_module_args({"host": "https://rocm.example.com", "api_key": "test-key", "gpu_id": "0", "state": "present"})

        import requests as real_requests
        mock_requests.get.side_effect = real_requests.exceptions.ConnectionError("connection failed")
        mock_requests.exceptions = real_requests.exceptions

        from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules import amd_gpu_config
        import importlib
        importlib.reload(amd_gpu_config)

        with pytest.raises(AnsibleFailJson) as exc_info:
            amd_gpu_config.main()
        msg = exc_info.value.kwargs["msg"].lower()
        assert "fail" in msg or "error" in msg or "connection" in msg


class TestCheckMode:
    """Test check_mode behavior."""

    @patch("ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.amd_gpu_config.requests")
    def test_check_mode(self, mock_requests, mock_module):
        args = {"host": "https://rocm.example.com", "api_key": "test-key", "gpu_id": "0", "state": "present"}
        args["_ansible_check_mode"] = True
        set_module_args(args)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules import amd_gpu_config
        import importlib
        importlib.reload(amd_gpu_config)

        with pytest.raises(AnsibleExitJson):
            amd_gpu_config.main()
