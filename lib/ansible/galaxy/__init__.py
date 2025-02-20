########################################################################
#
# (C) 2015, Brian Coca <bcoca@ansible.com>
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
########################################################################
""" This manages remote shared Ansible objects, mainly roles"""

from __future__ import annotations

import shutil
import os

import ansible.constants as C
from ansible import context
from ansible.utils.display import Display
from ansible.module_utils.common.text.converters import to_bytes
from ansible.module_utils.common.yaml import yaml_load

#      default_readme_template
#      default_meta_template

display = Display()


def _ask_uninstall(label: str, paths: list[str], collection: bool = True, skip_prompt: bool = False) -> bool:
    """Confirm whether the list of paths should be removed and return a boolean."""
    if skip_prompt:
        return True

    prompt = f"Uninstalling {'collection' if collection else 'role'} {label}:"
    prompt += (
        "\n  Would remove:\n    " +
        "\n    ".join(paths)
    )
    display.display(prompt)
    while (response := input("Proceed (y/n)? ").lower()) not in ("y", "n"):
        display.display(f"Your response ('{response}') was not one of the expected responses: y, n,")
    return response == "y"


def _uninstall_paths(label: str, paths: list[str], collection: bool = True) -> int:
    """Remove a list of paths, depth first."""
    rc = 0
    for path in reversed(sorted(paths)):
        try:
            if os.path.islink(path):
                os.unlink(path)
            else:
                shutil.rmtree(path)
        except OSError as e:
            display.error(f"Unable to remove {'collection' if collection else 'role'} {label} path {path}: {e}")
            rc = 1
        else:
            display.vvvv(f"Removed {path}")
    if rc == 0:
        display.display(f"Uninstalled {'collection' if collection else 'role'} {label}")

    return rc


def get_collections_galaxy_meta_info():
    meta_path = os.path.join(os.path.dirname(__file__), 'data', 'collections_galaxy_meta.yml')
    with open(to_bytes(meta_path, errors='surrogate_or_strict'), 'rb') as galaxy_obj:
        return yaml_load(galaxy_obj)


class Galaxy(object):
    """ Keeps global galaxy info """

    def __init__(self):
        # TODO: eventually remove this as it contains a mismash of properties that aren't really global

        # roles_path needs to be a list and will be by default
        roles_path = context.CLIARGS.get('roles_path', C.DEFAULT_ROLES_PATH)
        # cli option handling is responsible for splitting roles_path
        self.roles_paths = roles_path

        self.roles = {}

        # load data path for resource usage
        this_dir, this_filename = os.path.split(__file__)
        type_path = context.CLIARGS.get('role_type', 'default')
        if type_path == 'default':
            type_path = os.path.join(type_path, context.CLIARGS.get('type'))

        self.DATA_PATH = os.path.join(this_dir, 'data', type_path)

    @property
    def default_role_skeleton_path(self):
        return self.DATA_PATH

    def add_role(self, role):
        self.roles[role.name] = role

    def remove_role(self, role_name):
        del self.roles[role_name]
