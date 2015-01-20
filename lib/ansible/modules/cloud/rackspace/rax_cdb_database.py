#!/usr/bin/python -tt
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

# This is a DOCUMENTATION stub specific to this module, it extends
# a documentation fragment located in ansible.utils.module_docs_fragments
DOCUMENTATION = '''
module: rax_cdb_database
short_description: 'create / delete a database in the Cloud Databases'
description:
  - create / delete a database in the Cloud Databases.
version_added: "1.8"
options:
  cdb_id:
    description:
      - The databases server UUID
    default: null
  name:
    description:
      - Name to give to the database
    default: null
  character_set:
    description:
      - Set of symbols and encodings
    default: 'utf8'
  collate:
    description:
      - Set of rules for comparing characters in a character set
    default: 'utf8_general_ci'
  state:
    description:
      - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
author: Simon JAILLET
extends_documentation_fragment: rackspace
'''

EXAMPLES = '''
- name: Build a database in Cloud Databases
  tasks:
    - name: Database build request
      local_action:
        module: rax_cdb_database
        credentials: ~/.raxpub
        region: IAD
        cdb_id: 323e7ce0-9cb0-11e3-a5e2-0800200c9a66
        name: db1
        state: present
      register: rax_db_database
'''

try:
    import pyrax
    HAS_PYRAX = True
except ImportError:
    HAS_PYRAX = False


def find_database(instance, name):
    try:
        database = instance.get_database(name)
    except Exception:
        return False

    return database


def save_database(module, cdb_id, name, character_set, collate):
    cdb = pyrax.cloud_databases

    try:
        instance = cdb.get(cdb_id)
    except Exception, e:
        module.fail_json(msg='%s' % e.message)

    changed = False

    database = find_database(instance, name)

    if not database:
        try:
            database = instance.create_database(name=name,
                                                character_set=character_set,
                                                collate=collate)
        except Exception, e:
            module.fail_json(msg='%s' % e.message)
        else:
            changed = True

    module.exit_json(changed=changed, action='create',
                     database=rax_to_dict(database))


def delete_database(module, cdb_id, name):
    cdb = pyrax.cloud_databases

    try:
        instance = cdb.get(cdb_id)
    except Exception, e:
        module.fail_json(msg='%s' % e.message)

    changed = False

    database = find_database(instance, name)

    if database:
        try:
            database.delete()
        except Exception, e:
            module.fail_json(msg='%s' % e.message)
        else:
            changed = True

    module.exit_json(changed=changed, action='delete',
                     database=rax_to_dict(database))


def rax_cdb_database(module, state, cdb_id, name, character_set, collate):

    # act on the state
    if state == 'present':
        save_database(module, cdb_id, name, character_set, collate)
    elif state == 'absent':
        delete_database(module, cdb_id, name)


def main():
    argument_spec = rax_argument_spec()
    argument_spec.update(
        dict(
            cdb_id=dict(type='str', required=True),
            name=dict(type='str', required=True),
            character_set=dict(type='str', default='utf8'),
            collate=dict(type='str', default='utf8_general_ci'),
            state=dict(default='present', choices=['present', 'absent'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=rax_required_together(),
    )

    if not HAS_PYRAX:
        module.fail_json(msg='pyrax is required for this module')

    cdb_id = module.params.get('cdb_id')
    name = module.params.get('name')
    character_set = module.params.get('character_set')
    collate = module.params.get('collate')
    state = module.params.get('state')

    setup_rax_module(module, pyrax)
    rax_cdb_database(module, state, cdb_id, name, character_set, collate)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.rax import *

# invoke the module
main()
