"""Unit tests for stevefulme1.gpu_ai_factory.dgx_power module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

MODULE_PATH = "ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.dgx_power"

try:
    from ansible_collections.stevefulme1.gpu_ai_factory.plugins.modules.dgx_power import main
except ImportError:
    from unittest.mock import MagicMock as main


class TestAction:
    """Test dgx_power action execution."""

    @patch(f"{MODULE_PATH}.AnsibleModule")
    def test_execute(self, mock_ansible_cls):
        """Executing dgx_power returns a result."""
        mock_module = MagicMock()
        mock_module.params = {'bmc_host': '192.168.1.100', 'bmc_username': 'admin',
                              'bmc_password': 'test-pass', 'validate_certs': False, 'system_id': '1', 'state': 'on'}
        mock_module.check_mode = False
        mock_ansible_cls.return_value = mock_module
        main()
        mock_module.exit_json.assert_called_once()
