# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for nvidia_common module utility."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_common import (
    NVIDIA_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
    WAIT_STATES,
    READY_STATES,
    DEAD_STATES,
    to_dict,
)


class TestNvidiaCommonArgs:
    """Tests for NVIDIA_COMMON_ARGS."""

    def test_common_args_has_required_keys(self):
        required = [
            "bcm_url", "bcm_username", "bcm_password",
            "validate_certs", "wait", "wait_timeout",
        ]
        for key in required:
            assert key in NVIDIA_COMMON_ARGS, f"Missing key: {key}"

    def test_bcm_password_is_no_log(self):
        assert NVIDIA_COMMON_ARGS["bcm_password"]["no_log"] is True

    def test_bcm_token_is_no_log(self):
        assert NVIDIA_COMMON_ARGS["bcm_token"]["no_log"] is True

    def test_validate_certs_default(self):
        assert NVIDIA_COMMON_ARGS["validate_certs"]["default"] is True

    def test_wait_default(self):
        assert NVIDIA_COMMON_ARGS["wait"]["default"] is True


class TestLifecycleStates:
    """Tests for lifecycle state constants."""

    def test_ready_states_contain_active(self):
        assert LIFECYCLE_ACTIVE in READY_STATES

    def test_dead_states_contain_deleted(self):
        assert LIFECYCLE_DELETED in DEAD_STATES

    def test_states_are_disjoint(self):
        assert READY_STATES.isdisjoint(DEAD_STATES)
        assert READY_STATES.isdisjoint(WAIT_STATES)
        assert DEAD_STATES.isdisjoint(WAIT_STATES)


class TestToDict:
    """Tests for to_dict helper."""

    def test_none_returns_empty_dict(self):
        assert to_dict(None) == {}

    def test_dict_passthrough(self):
        data = {"id": "123", "name": "test"}
        assert to_dict(data) == data

    def test_nested_dict(self):
        data = {"outer": {"inner": "value"}}
        assert to_dict(data) == {"outer": {"inner": "value"}}

    def test_list_conversion(self):
        data = [{"id": "1"}, {"id": "2"}]
        result = to_dict(data)
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_primitive_passthrough(self):
        assert to_dict("string") == "string"
        assert to_dict(42) == 42
        assert to_dict(True) is True
