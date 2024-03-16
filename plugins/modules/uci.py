#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Benoit DE RANCOURT <benoit2r@gmail.com>
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: uci

short_description: OpenWRT UCI module

version_added: "1.0.0"

description:
  - Manipulate OpenWRT UCI configuration https://openwrt.org/docs/guide-user/base-system/uci
  - Inspired by Markus Weippert (@gekmihesg) openwrt role from https://github.com/gekmihesg/ansible-openwrt
  - This module is designed to be declarative rather than imperative like Markus's module.

options:
  state:
    description:
      - uci config state, present or absent
    type: str
    choices: [ present, absent ]
    default: present
  config:
    description:
      - uci config
    type: str
    required: true
  section:
    description:
      - uci section. If section is unnamed, use type and position instead
    type: str
  type:
    description:
      - uci type
    type: str
  options:
    description:
      - list of uci options to add/update/remove. If your option is an uci list
      - write it simply as a list.
    type: dict
  position:
    description:
      - section position. Use it to reorder the section
    type: int
  find:
    description:
      - Value(s) to match sections against.
      - Option value to find if I(option) is set. May be list.
      - Dict of options/values if I(option) is not set. Values may be list.
      - Lists are compared in order.
    type: dict
    aliases:
      - find_by
      - search
  replace:
    description:
      - whether to delete all options not mentioned in I(keep_keys), I(value) or find when
        I(set_find=true).
    type: bool
    default: false
  set_find:
    description:
      - When I(command=section) whether to set the options used to search
        a matching section in the newly created section when no match was
        found.
    type: bool
    default: false
  commit:
    description:
      - Whether to commit changes
    type: bool
    default: false

author:
    - Benoit DE RANCOURT (@bderancourt)
"""

EXAMPLES = r"""
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.uci:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.uci:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.uci:
    name: fail me
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
"""

from ansible.module_utils.basic import AnsibleModule

PRESENT = "present"
ABSENT = "absent"


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default=PRESENT, choices=[PRESENT, ABSENT]),
            config=dict(type="str", required=True),
            section=dict(type="str"),
            type=dict(type="str"),
            options=dict(type="dict"),
            position=dict(type="int"),
            replace=dict(type="bool", default=False),
            find=dict(type="dict", aliases=['find_by', 'search']),
            set_find=dict(type="bool", default=False),
            commit=dict(type="bool", default=False),
        ),
        # mutually_exclusive = [],
        # required_together = [],
        # required_one_of = [],
        # required_if = [],
        # required_by = [],
        supports_check_mode=True,
    )
    ucibin = module.get_bin_path("uci", required=True)
    state = module.params["state"]
    config = module.params["config"]
    section = module.params["section"]
    type = module.params["section"]
    options = module.params["options"]
    position = module.params["position"]
    replace = module.params["replace"]
    commit = module.params["commit"]

    ucibin = module.get_bin_path("uci", required=True)
    commands = []
    changed = False

    match state:
        case "present":
            commands.append([ucibin, "show", config])
            if not module.check_mode:
                rc, out, err = module.run_command(commands[0], check_rc=True)

        case "absent":
            commands.append([ucibin, "changes", config])
            if not module.check_mode:
                rc, out, err = module.run_command(commands[0], check_rc=True)

    module.exit_json(
        changed=changed,
        state=state,
        config=config,
        section=section,
        type=type,
        options=options,
        position=position,
        replace=replace,
        commit=commit,
        uci_commands=commands,
    )


if __name__ == "__main__":
    main()
