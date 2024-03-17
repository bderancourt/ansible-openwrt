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


class UciContext:

    module: AnsibleModule
    changes_before: list = []
    changes_after: list = []
    commands: list = []

    def __init__(self, module: AnsibleModule):
        self.module = module
        changes_before_cmd = [
            module.get_bin_path("uci", required=True),
            "changes",
            module.params["config"],
        ]
        rc, out, err = module.run_command(changes_before_cmd, check_rc=True)
        self.changes_before = out.splitlines()

    @property
    def state(self) -> str:
        return self.module.params["state"]

    @property
    def config(self) -> str:
        return self.module.params["config"]

    @property
    def section(self) -> str:
        return self.module.params["section"]

    @property
    def type(self) -> str:
        return self.module.params["type"]

    @property
    def options(self) -> dict:
        return self.module.params["options"]

    @property
    def position(self) -> int:
        return self.module.params["position"]

    @property
    def replace(self) -> bool:
        return self.module.params["replace"]

    @property
    def find(self) -> dict:
        return self.module.params["find"]

    @property
    def set_find(self) -> bool:
        return self.module.params["set_find"]

    @property
    def commit(self) -> bool:
        return self.module.params["commit"]

    @property
    def ucibin(self):
        return self.module.get_bin_path("uci", required=True)

    def has_changed(self) -> bool:
        changes_after_cmd = [self.ucibin, "changes", self.config]
        rc, out, err = self.module.run_command(changes_after_cmd, check_rc=True)
        self.changes_after = out.splitlines()

        return len(self.commands) > 0


def create_context():
    module = AnsibleModule(
        dict(
            state=dict(type="str", default=PRESENT, choices=[PRESENT, ABSENT]),
            config=dict(type="str", required=True),
            section=dict(type="str"),
            type=dict(type="str"),
            options=dict(type="dict"),
            position=dict(type="int"),
            replace=dict(type="bool", default=False),
            find=dict(type="dict", aliases=["find_by", "search"]),
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
    return UciContext(module=module)


def run_command(ctx: UciContext, *args: str):
    command_array = [ctx.ucibin, *args]
    ctx.commands.append(" ".join(command_array))
    if not ctx.module.check_mode:
        return ctx.module.run_command(command_array, check_rc=True)


def do_commit(ctx: UciContext):
    if ctx.commit:
        run_command(ctx, "commit", ctx.config)


def main():
    ctx = create_context()

    match ctx.state:
        case "present":
            run_command(ctx, "show", ctx.config)

        case "absent":
            run_command(ctx, "changes", ctx.config)

    changed = ctx.has_changed()
    do_commit(ctx)

    ctx.module.exit_json(
        changed=changed,
        changes_before=ctx.changes_before,
        changes_after=ctx.changes_after,
        uci_commands=ctx.commands,
    )


if __name__ == "__main__":
    main()
