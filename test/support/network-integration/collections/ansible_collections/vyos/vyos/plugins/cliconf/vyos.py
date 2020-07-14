#
# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
cliconf: vyos
short_description: Use vyos cliconf to run command on VyOS platform
description:
  - This vyos plugin provides low level abstraction apis for
    sending and receiving CLI commands from VyOS network devices.
version_added: "2.4"
"""

import re
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    NetworkConfig,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    to_list,
)
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):
    def get_device_info(self):
        device_info = {}

        device_info["network_os"] = "vyos"
        reply = self.get("show version")
        data = to_text(reply, errors="surrogate_or_strict").strip()

        match = re.search(r"Version:\s*(.*)", data)
        if match:
            device_info["network_os_version"] = match.group(1)

        match = re.search(r"HW model:\s*(\S+)", data)
        if match:
            device_info["network_os_model"] = match.group(1)

        reply = self.get("show host name")
        device_info["network_os_hostname"] = to_text(
            reply, errors="surrogate_or_strict"
        ).strip()

        return device_info

    def get_config(self, flags=None, format=None):
        if format:
            option_values = self.get_option_values()
            if format not in option_values["format"]:
                raise ValueError(
                    "'format' value %s is invalid. Valid values of format are %s"
                    % (format, ", ".join(option_values["format"]))
                )

        if not flags:
            flags = []

        if format == "text":
            command = "show configuration"
        else:
            command = "show configuration commands"

        command += " ".join(to_list(flags))
        command = command.strip()

        out = self.send_command(command)
        return out

    def edit_config(
        self, candidate=None, commit=True, replace=None, comment=None
    ):
        resp = {}
        operations = self.get_device_operations()
        self.check_edit_config_capability(
            operations, candidate, commit, replace, comment
        )

        results = []
        requests = []
        self.send_command("configure")
        for cmd in to_list(candidate):
            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            results.append(self.send_command(**cmd))
            requests.append(cmd["command"])
        out = self.get("compare")
        out = to_text(out, errors="surrogate_or_strict")
        diff_config = out if not out.startswith("No changes") else None

        if diff_config:
            if commit:
                try:
                    self.commit(comment)
                except AnsibleConnectionFailure as e:
                    msg = "commit failed: %s" % e.message
                    self.discard_changes()
                    raise AnsibleConnectionFailure(msg)
                else:
                    self.send_command("exit")
            else:
                self.discard_changes()
        else:
            self.send_command("exit")
            if (
                to_text(
                    self._connection.get_prompt(), errors="surrogate_or_strict"
                )
                .strip()
                .endswith("#")
            ):
                self.discard_changes()

        if diff_config:
            resp["diff"] = diff_config
        resp["response"] = results
        resp["request"] = requests
        return resp

    def get(
        self,
        command=None,
        prompt=None,
        answer=None,
        sendonly=False,
        output=None,
        newline=True,
        check_all=False,
    ):
        if not command:
            raise ValueError("must provide value of command to execute")
        if output:
            raise ValueError(
                "'output' value %s is not supported for get" % output
            )

        return self.send_command(
            command=command,
            prompt=prompt,
            answer=answer,
            sendonly=sendonly,
            newline=newline,
            check_all=check_all,
        )

    def commit(self, comment=None):
        if comment:
            command = 'commit comment "{0}"'.format(comment)
        else:
            command = "commit"
        self.send_command(command)

    def discard_changes(self):
        self.send_command("exit discard")

    def get_diff(
        self,
        candidate=None,
        running=None,
        diff_match="line",
        diff_ignore_lines=None,
        path=None,
        diff_replace=None,
    ):
        diff = {}
        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if candidate is None and device_operations["supports_generate_diff"]:
            raise ValueError(
                "candidate configuration is required to generate diff"
            )

        if diff_match not in option_values["diff_match"]:
            raise ValueError(
                "'match' value %s in invalid, valid values are %s"
                % (diff_match, ", ".join(option_values["diff_match"]))
            )

        if diff_replace:
            raise ValueError("'replace' in diff is not supported")

        if diff_ignore_lines:
            raise ValueError("'diff_ignore_lines' in diff is not supported")

        if path:
            raise ValueError("'path' in diff is not supported")

        set_format = candidate.startswith("set") or candidate.startswith(
            "delete"
        )
        candidate_obj = NetworkConfig(indent=4, contents=candidate)
        if not set_format:
            config = [c.line for c in candidate_obj.items]
            commands = list()
            # this filters out less specific lines
            for item in config:
                for index, entry in enumerate(commands):
                    if item.startswith(entry):
                        del commands[index]
                        break
                commands.append(item)

            candidate_commands = [
                "set %s" % cmd.replace(" {", "") for cmd in commands
            ]

        else:
            candidate_commands = str(candidate).strip().split("\n")

        if diff_match == "none":
            diff["config_diff"] = list(candidate_commands)
            return diff

        running_commands = [
            str(c).replace("'", "") for c in running.splitlines()
        ]

        updates = list()
        visited = set()

        for line in candidate_commands:
            item = str(line).replace("'", "")

            if not item.startswith("set") and not item.startswith("delete"):
                raise ValueError(
                    "line must start with either `set` or `delete`"
                )

            elif item.startswith("set") and item not in running_commands:
                updates.append(line)

            elif item.startswith("delete"):
                if not running_commands:
                    updates.append(line)
                else:
                    item = re.sub(r"delete", "set", item)
                    for entry in running_commands:
                        if entry.startswith(item) and line not in visited:
                            updates.append(line)
                            visited.add(line)

        diff["config_diff"] = list(updates)
        return diff

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            output = cmd.pop("output", None)
            if output:
                raise ValueError(
                    "'output' value %s is not supported for run_commands"
                    % output
                )

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, "err", e)

            responses.append(out)

        return responses

    def get_device_operations(self):
        return {
            "supports_diff_replace": False,
            "supports_commit": True,
            "supports_rollback": False,
            "supports_defaults": False,
            "supports_onbox_diff": True,
            "supports_commit_comment": True,
            "supports_multiline_delimiter": False,
            "supports_diff_match": True,
            "supports_diff_ignore_lines": False,
            "supports_generate_diff": False,
            "supports_replace": False,
        }

    def get_option_values(self):
        return {
            "format": ["text", "set"],
            "diff_match": ["line", "none"],
            "diff_replace": [],
            "output": [],
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result["rpc"] += [
            "commit",
            "discard_changes",
            "get_diff",
            "run_commands",
        ]
        result["device_operations"] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def set_cli_prompt_context(self):
        """
        Make sure we are in the operational cli mode
        :return: None
        """
        if self._connection.connected:
            self._update_cli_prompt_context(
                config_context="#", exit_command="exit discard"
            )
