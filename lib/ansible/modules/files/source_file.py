#!/usr/bin/python

# Copyright: (c) 2019, Nicolas Karolak <nicolas.karolak@ubicast.eu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}


DOCUMENTATION = """
module: source_file
short_description: Source remote bash/dotenv file
description:
    - This module is used to register host variables from a remote bash/dotenv-like file.
    - It handles boolean value (`MY_VAR=1`) and has a basic handling of list (`MY_VAR=one,two,three`) and dictionnary (`MY_VAR=a=1;b=2;c=3`).
version_added: "2.8"
author: "Nicolas Karolak (@nikaro)"
options:
    path:
        description:
            - Path to the file to source.
        required: true
        type: path
    prefix:
        description:
            - Prefix to add to the registred variable name.
        required: false
        default: ""
        type: str
    lower:
        description:
            - Wether to lower or not the variable name.
        required: false
        default: false
        type: bool
notes:
    - The `check_mode` is supported.
"""

EXAMPLES = """
- name: source envsetup file
  source_file:
    prefix: envsetup_
    path: /root/envsetup/conf.sh
    lower: true
"""

RETURN = """
ansible_facts:
    description: Registred vairales.
    returned: on success
    type: dict
    sample:
        key: value
"""

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS, boolean
from ansible.module_utils.six import integer_types, string_types


def run_module():
    module_args = {
        "path": {"type": "path", "required": True},
        "prefix": {"type": "str", "required": False, "default": ""},
        "lower": {"type": "bool", "required": False, "default": False},
    }

    result = {"changed": False}

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    path = module.params["path"]
    prefix = module.params["prefix"]
    lower = boolean(module.params["lower"])
    variables = {}
    regex_valid_name = re.compile("^[a-zA-Z][a-zA-Z0-9_-]*$")
    regex_key_value = re.compile("^(?P<key>[a-zA-Z][a-zA-Z0-9_-]*)=(?P<value>.*)")

    if not os.path.isfile(path):
        module.fail_json(msg="'%s' does not exist or is not a file" % path, **result)

    if prefix and not regex_valid_name.match(prefix):
        module.fail_json(
            msg="'%s' is not a valid prefix it must starts with a letter or underscore"
            " character, and contains only letters, numbers and underscores" % prefix,
            **result
        )

    with open(path) as file:
        for line in file:
            match = regex_key_value.match(line)

            # skip lines that are not assignation (comments, blank, code, etc.)
            if not match:
                continue

            # get key and value
            k = str(match.group("key")).strip()
            v = str(match.group("value")).strip()

            # merge prefix + key
            if prefix:
                k = "%s%s" % (prefix, k)

            # lower key
            if lower:
                k = k.lower()

            # check key validity
            if not regex_valid_name.match(k):
                module.fail_json(
                    msg="'%s' is not a valid variable name it must starts with a letter or "
                    "underscore character, and contains only letters, numbers and underscores"
                    % k,
                    **result
                )

            # remove value surrounding quotes
            if (v.startswith("'") and v.endswith("'")) or (
                v.startswith('"') and v.endswith('"')
            ):
                v = v[1:-1]

            # handle list value
            if "," in v:
                v = v.split(",")

            # handle dict value
            if ";" in v and "=" in v:
                v = {i.split("=")[0]: i.split("=")[1] for i in v.split(";")}

            # handle bool value
            if isinstance(v, string_types) and v.lower() in BOOLEANS:
                v = boolean(v)

            variables[k] = v

            result["changed"] = True

            if not module.check_mode:
                result["ansible_facts"] = variables

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
