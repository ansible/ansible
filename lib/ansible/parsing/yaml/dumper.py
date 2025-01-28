# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from __future__ import annotations

import collections.abc as c
import typing as t

from yaml.representer import SafeRepresenter

from ansible.module_utils.datatag import AnsibleTaggedObject, Tripwire, AnsibleTagHelper
from ansible.parsing.vault import VaultHelper
from ansible.module_utils.common.yaml import HAS_LIBYAML

if HAS_LIBYAML:
    from yaml.cyaml import CSafeDumper as SafeDumper
else:
    from yaml import SafeDumper  # type: ignore[assignment]


class AnsibleDumper(SafeDumper):
    """A simple stub class that allows us to add representers for our custom types."""

    # DTFIX-MERGE: need a better way to handle serialization controls during YAML dumping
    def __init__(self, *args, dump_vault_tags: bool | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._dump_vault_tags = dump_vault_tags


def represent_ansible_tagged_object(self, data):
    if self._dump_vault_tags is not False and (ciphertext := VaultHelper.get_ciphertext(data, with_tags=False)):
        # deprecated: description='enable the deprecation warning below' core_version='2.21'
        # if self._dump_vault_tags is None:
        #     Display().deprecated(
        #         msg="Implicit YAML dumping of vaulted value ciphertext is deprecated. Set `dump_vault_tags` to explicitly specify the desired behavior",
        #         version="2.25",
        #     )

        return self.represent_scalar('!vault', ciphertext, style='|')

    return self.represent_data(AnsibleTagHelper.as_native_type(data))  # automatically decrypts encrypted strings


def represent_tripwire(self, data: Tripwire) -> t.NoReturn:
    data.trip()


AnsibleDumper.add_multi_representer(AnsibleTaggedObject, represent_ansible_tagged_object)

AnsibleDumper.add_multi_representer(Tripwire, represent_tripwire)
AnsibleDumper.add_multi_representer(c.Mapping, SafeRepresenter.represent_dict)
AnsibleDumper.add_multi_representer(c.Sequence, SafeRepresenter.represent_list)
