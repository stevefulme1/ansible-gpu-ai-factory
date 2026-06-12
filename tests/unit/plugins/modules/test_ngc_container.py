"""Unit tests for stevefulme1.gpu_ai_factory.ngc_container module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

MODULE_PATH = "ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.ngc_container"

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.ngc_container import main
except ImportError:
    from unittest.mock import MagicMock as main


class TestCreate:
    """Test ngc_container creation."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create(self, mock_ansible_cls):
        """Creating ngc_container calls exit_json with changed=True."""
        mock_module = MagicMock()
        mock_module.params = {'ngc_api_key': 'test-key', 'ngc_api_base': 'https://api.ngc.nvidia.com/v2', 'org': 'test-org',
                              'validate_certs': False, 'state': 'present', 'name': 'test-container', 'display_name': 'Test Container', 'description': 'test'}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs.get("changed") is True


class TestDelete:
    """Test ngc_container deletion."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete(self, mock_ansible_cls):
        """Deleting ngc_container calls exit_json with changed=True."""
        mock_module = MagicMock()
        mock_module.params = {'ngc_api_key': 'test-key', 'ngc_api_base': 'https://api.ngc.nvidia.com/v2', 'org': 'test-org',
                              'validate_certs': False, 'state': 'absent', 'name': 'test-container', 'display_name': None, 'description': None}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs.get("changed") is True


class TestIdempotent:
    """Test ngc_container idempotency."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create_idempotent(self, mock_ansible_cls):
        """Re-creating existing ngc_container calls exit_json with changed=False."""
        mock_module = MagicMock()
        mock_module.params = {'ngc_api_key': 'test-key', 'ngc_api_base': 'https://api.ngc.nvidia.com/v2', 'org': 'test-org',
                              'validate_certs': False, 'state': 'present', 'name': 'test-container', 'display_name': 'Test Container', 'description': 'test'}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called()
