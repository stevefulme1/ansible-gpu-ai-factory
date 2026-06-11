# -*- coding: utf-8 -*-
# Copyright (c) 2026, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for nvidia_wait module utility."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from unittest.mock import MagicMock, patch
from ansible_collections.stevefulme1.gpu_ai_factory.plugins.module_utils.nvidia_wait import (
    call_with_retry,
)


class TestCallWithRetry:
    """Tests for call_with_retry."""

    def test_success_on_first_try(self):
        fn = MagicMock(return_value="success")
        result = call_with_retry(fn, "arg1")
        assert result == "success"
        fn.assert_called_once_with("arg1")

    def test_retry_on_500(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        import requests
        exc = requests.exceptions.HTTPError(response=mock_response)

        fn = MagicMock(side_effect=[exc, "success"])
        with patch("time.sleep"):
            result = call_with_retry(fn, "arg1", max_retries=1)
        assert result == "success"
        assert fn.call_count == 2

    def test_raises_after_max_retries(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        import requests
        exc = requests.exceptions.HTTPError(response=mock_response)

        fn = MagicMock(side_effect=exc)
        with patch("time.sleep"):
            with pytest.raises(requests.exceptions.HTTPError):
                call_with_retry(fn, "arg1", max_retries=2)
        assert fn.call_count == 3

    def test_no_retry_on_400(self):
        mock_response = MagicMock()
        mock_response.status_code = 400

        import requests
        exc = requests.exceptions.HTTPError(response=mock_response)

        fn = MagicMock(side_effect=exc)
        with pytest.raises(requests.exceptions.HTTPError):
            call_with_retry(fn, "arg1")
        fn.assert_called_once()
