# (c) 2014, Tristan Fisher <tfisher@singleplatform.com>; <code@tristanfisher.com>

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


DOCUMENTATION = '''
module: fileglob_to_dict
short_description: Fileglob a directory and get back a list of dictionaries
description:
  - This works exactly like fileglob, but instead of returning a list of files,
    this module looks into the files, parses JSON or YAML, and returns it to the list.

    The end result is a fileglob that returns a list of dictionaries that can be used in a task.
version_added: "1.0"
options: {}
notes:
    - The fileglob directory must contain valid only JSON or YAML files.
requirements: []
author: Tristan Fisher
'''

EXAMPLES = '''
#Example use in a task:
- name: create ops users
  user:
    name="{{item.username}}"
    comment="{{item.comment}}"
    uid="{{ item.uid }}"
    groups="{{ item.groups }}"
    generate_ssh_key=no
    shell="{{item.shell|default("/bin/bash")}}"
    state=present
  fileglob_to_dict:
    - "{{ 'ops/*' }}"
'''

import os
import glob
from ansible import utils

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        ret = []

        for term in terms:

            dwimmed = utils.path_dwim(self.basedir, term)
            globbed = glob.glob(dwimmed)
            ret.extend(g for g in globbed if os.path.isfile(g))

        parsed_ret = []

        # go through filename list, turning each into parsed objects
        for _record in ret:

            _record_parsed = utils.parse_yaml_from_file(path=_record, vault_password=None)
            parsed_ret.append(_record_parsed)

        return parsed_ret