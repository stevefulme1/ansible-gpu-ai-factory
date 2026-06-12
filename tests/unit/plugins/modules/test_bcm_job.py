"""Unit tests for stevefulme1.gpu_ai_factory.bcm_job module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

MODULE_PATH = "ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.bcm_job"

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.bcm_job import main
except ImportError:
    from unittest.mock import MagicMock as main


class TestCreate:
    """Test bcm_job creation."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_create(self, mock_ansible_cls):
        """Creating bcm_job calls exit_json with changed=True."""
        mock_module = MagicMock()
        mock_module.params = {'bcm_url': 'https://test.example.com', 'bcm_token': 'test-token', 'validate_certs': False, 'name': 'test-job', 'command': 'echo hello',
                              'num_gpus': 1, 'num_nodes': 1, 'queue': 'default', 'state': 'submitted', 'job_id': None, 'bcm_username': None, 'bcm_password': None}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs.get("changed") is True


class TestDelete:
    """Test bcm_job deletion."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_delete(self, mock_ansible_cls):
        """Deleting bcm_job calls exit_json with changed=True."""
        mock_module = MagicMock()
        mock_module.params = {'bcm_url': 'https://test.example.com', 'bcm_token': 'test-token', 'validate_certs': False, 'name': 'test-job',
                              'job_id': 'test-job-id', 'state': 'cancelled', 'command': None, 'num_gpus': 1, 'num_nodes': 1, 'queue': None, 'bcm_username': None, 'bcm_password': None}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called_once()
        call_kwargs = mock_module.exit_json.call_args[1]
        assert call_kwargs.get("changed") is True
