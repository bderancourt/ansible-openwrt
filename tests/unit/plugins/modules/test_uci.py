# Copyright: (c) 2024, Benoit DE RANCOURT <benoit2r@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import unittest
from unittest.mock import call, patch

# Adjust the import paths to match your collection's structure
# Assuming your module is in a collection named 'my_namespace.my_collection'
from my_namespace.my_collection.plugins.modules.uci import main as uci_main, UciContext
from my_namespace.my_collection.plugins.modules.uci import AnsibleModule # Used for patching

# Mock the AnsibleModule and its methods
class MockAnsibleModule:
    def __init__(self, argument_spec, supports_check_mode):
        self.params = {}
        self.check_mode = False
        self.exit_json = Mock()
        self.run_command = Mock(return_value=(0, "", ""))
        self.get_bin_path = Mock(return_value="/usr/bin/uci")

    def __call__(self, *args, **kwargs):
        return self

# Helper function to set module arguments for a test case
def set_module_args(args):
    # This simulates how Ansible sets module parameters
    os.environ['ANSIBLE_MODULE_ARGS'] = str(args)

class AnsibleExitJson(Exception):
    """Exception to be raised instead of AnsibleModule.exit_json"""
    pass

class UciModuleTestCase(unittest.TestCase):
    def setUp(self):
        super(UciModuleTestCase, self).setUp()
        self.mock_ansible_module = MockAnsibleModule(argument_spec={}, supports_check_mode=True)
        self.mock_ansible_module.exit_json.side_effect = AnsibleExitJson

        # Patch the AnsibleModule class in the uci module file
        self.module_path = "my_namespace.my_collection.plugins.modules.uci.AnsibleModule"
        self.patcher = patch(self.module_path, return_value=self.mock_ansible_module)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        super(UciModuleTestCase, self).tearDown()

    def module_main(self, exit_exc):
        # This function runs the main function of your module and catches the exit exception
        with self.assertRaises(exit_exc) as exc:
            uci_main()
        return exc.exception.args[0]

    # --- Test Cases ---

    def test_present_new_section(self):
        """
        Test adding a new section and its options.
        """
        with set_module_args({
            'state': 'present',
            'config': 'network',
            'type': 'interface',
            'options': {'proto': 'static', 'ipaddr': '192.168.1.1'},
            'commit': True
        }):
            # Mock the output of `uci changes` before and after
            self.mock_ansible_module.run_command.side_effect = [
                # First uci changes returns no changes
                (0, "", ""),
                # uci add returns the new section name
                (0, "cfg12345", ""),
                # All other commands return success
                (0, "", ""),
                (0, "", ""),
                (0, "", ""),
                (0, "", ""),
                (0, "", ""),
            ]

            result = self.module_main(AnsibleExitJson)

        self.assertTrue(result['changed'])
        self.mock_ansible_module.run_command.assert_has_calls([
            call(['/usr/bin/uci', 'changes', 'network'], check_rc=True),
            call(['/usr/bin/uci', 'add', 'network', 'interface'], check_rc=True),
            call(['/usr/bin/uci', 'set', 'network.cfg12345.proto=static'], check_rc=True),
            call(['/usr/bin/uci', 'set', 'network.cfg12345.ipaddr=192.168.1.1'], check_rc=True),
            call(['/usr/bin/uci', 'changes', 'network'], check_rc=True),
            call(['/usr/bin/uci', 'commit', 'network'], check_rc=True),
        ])

    def test_absent_existing_section(self):
        """
        Test removing an existing section.
        """
        with set_module_args({
            'state': 'absent',
            'config': 'wireless',
            'section': 'radio0',
            'commit': True
        }):
            # Mock the output of uci changes and delete
            self.mock_ansible_module.run_command.side_effect = [
                (0, "", ""), # uci changes
                (0, "", ""), # uci delete
                (0, "", ""), # uci changes
                (0, "", ""), # uci commit
            ]

            result = self.module_main(AnsibleExitJson)

        self.assertTrue(result['changed'])
        self.mock_ansible_module.run_command.assert_has_calls([
            call(['/usr/bin/uci', 'changes', 'wireless'], check_rc=True),
            call(['/usr/bin/uci', 'delete', 'wireless.radio0'], check_rc=True),
            call(['/usr/bin/uci', 'changes', 'wireless'], check_rc=True),
            call(['/usr/bin/uci', 'commit', 'wireless'], check_rc=True),
        ])

    def test_present_modify_existing_section(self):
        """
        Test modifying options in an existing section.
        """
        with set_module_args({
            'state': 'present',
            'config': 'wireless',
            'section': 'radio0',
            'options': {'channel': '11'},
            'commit': False
        }):
            # Mock the output
            self.mock_ansible_module.run_command.side_effect = [
                (0, "", ""), # uci changes
                (0, "", ""), # uci set
                (0, "", ""), # uci changes
            ]

            result = self.module_main(AnsibleExitJson)

        self.assertTrue(result['changed'])
        self.mock_ansible_module.run_command.assert_has_calls([
            call(['/usr/bin/uci', 'changes', 'wireless'], check_rc=True),
            call(['/usr/bin/uci', 'set', 'wireless.radio0.channel=11'], check_rc=True),
            call(['/usr/bin/uci', 'changes', 'wireless'], check_rc=True),
        ])
    
if __name__ == '__main__':
    unittest.main()