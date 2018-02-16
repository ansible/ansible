#!/usr/bin/python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_blueprint
author: jeremy@apstra.com (@jeremyschulman)
version_added: "2.3"
short_description: Manage AOS blueprint instance
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
    - Apstra AOS Blueprint module let you manage your Blueprint easily. You can create
      create and delete Blueprint by Name or ID. You can also use it to retrieve
      all data from a blueprint. This module is idempotent
      and support the I(check) mode. It's using the AOS REST API.
requirements:
  - "aos-pyez >= 0.6.0"
options:
  session:
    description:
      - An existing AOS session as obtained by M(aos_login) module.
    required: true
  name:
    description:
      - Name of the Blueprint to manage.
        Only one of I(name) or I(id) can be set.
  id:
    description:
      - AOS Id of the IP Pool to manage (can't be used to create a new IP Pool).
        Only one of I(name) or I(id) can be set.
  state:
    description:
      - Indicate what is the expected state of the Blueprint.
    choices: ['present', 'absent', 'build-ready']
    default: present
  timeout:
    description:
      - When I(state=build-ready), this timeout identifies timeout in seconds to wait before
        declaring a failure.
    default: 5
  template:
    description:
      - When creating a blueprint, this value identifies, by name, an existing engineering
        design template within the AOS-server.
  reference_arch:
     description:
        - When creating a blueprint, this value identifies a known AOS reference
          architecture value. I(Refer to AOS-server documentation for available values).
'''

EXAMPLES = '''
- name: Creating blueprint
  aos_blueprint:
    session: "{{ aos_session }}"
    name: "my-blueprint"
    template: "my-template"
    reference_arch: two_stage_l3clos
    state: present

- name: Access a blueprint and get content
  aos_blueprint:
    session: "{{ aos_session }}"
    name: "{{ blueprint_name }}"
    template: "{{ blueprint_template }}"
    state: present
  register: bp

- name: Delete a blueprint
  aos_blueprint:
    session: "{{ aos_session }}"
    name: "my-blueprint"
    state: absent

- name: Await blueprint build-ready, and obtain contents
  aos_blueprint:
    session: "{{ aos_session }}"
    name: "{{ blueprint_name }}"
    state: build-ready
  register: bp
'''

RETURNS = '''
name:
  description: Name of the Blueprint
  returned: always
  type: str
  sample: My-Blueprint

id:
  description: AOS unique ID assigned to the Blueprint
  returned: always
  type: str
  sample: fcc4ac1c-e249-4fe7-b458-2138bfb44c06

value:
  description: Information about the Blueprint
  returned: always
  type: dict
  sample: {'...'}

contents:
  description: Blueprint contents data-dictionary
  returned: always
  type: dict
  sample: { ... }

build_errors:
  description: When state='build-ready', and build errors exist, this contains list of errors
  returned: only when build-ready returns fail
  type: list
  sample: [{...}, {...}]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import get_aos_session, check_aos_version, find_collection_item


def create_blueprint(module, aos, name):

    margs = module.params

    try:

        template_id = aos.DesignTemplates[margs['template']].id

        # Create a new Object based on the name
        blueprint = aos.Blueprints[name]
        blueprint.create(template_id, reference_arch=margs['reference_arch'])

    except Exception as exc:
        msg = "Unable to create blueprint: %s" % exc.message
        if 'UNPROCESSABLE ENTITY' in exc.message:
            msg += ' (likely missing dependencies)'

        module.fail_json(msg=msg)

    return blueprint


def ensure_absent(module, aos, blueprint):

    if blueprint.exists is False:
        module.exit_json(changed=False)

    else:

        if not module.check_mode:
            try:
                blueprint.delete()
            except Exception as exc:
                module.fail_json(msg='Unable to delete blueprint, %s' % exc.message)

        module.exit_json(changed=True,
                         id=blueprint.id,
                         name=blueprint.name)


def ensure_present(module, aos, blueprint):
    margs = module.params

    if blueprint.exists:
        module.exit_json(changed=False,
                         id=blueprint.id,
                         name=blueprint.name,
                         value=blueprint.value,
                         contents=blueprint.contents)

    else:

        # Check if template is defined and is valid
        if margs['template'] is None:
            module.fail_json(msg="You must define a 'template' name to create a new blueprint, currently missing")

        elif aos.DesignTemplates.find(label=margs['template']) is None:
            module.fail_json(msg="You must define a Valid 'template' name to create a new blueprint, %s is not valid" % margs['template'])

        # Check if reference_arch
        if margs['reference_arch'] is None:
            module.fail_json(msg="You must define a 'reference_arch' to create a new blueprint, currently missing")

        if not module.check_mode:
            blueprint = create_blueprint(module, aos, margs['name'])
            module.exit_json(changed=True,
                             id=blueprint.id,
                             name=blueprint.name,
                             value=blueprint.value,
                             contents=blueprint.contents)
        else:
            module.exit_json(changed=True,
                             name=margs['name'])


def ensure_build_ready(module, aos, blueprint):
    margs = module.params

    if not blueprint.exists:
        module.fail_json(msg='blueprint %s does not exist' % blueprint.name)

    if blueprint.await_build_ready(timeout=margs['timeout'] * 1000):
        module.exit_json(contents=blueprint.contents)
    else:
        module.fail_json(msg='blueprint %s has build errors',
                         build_erros=blueprint.build_errors)


def aos_blueprint(module):

    margs = module.params

    try:
        aos = get_aos_session(module, margs['session'])
    except:
        module.fail_json(msg="Unable to login to the AOS server")

    item_name = False
    item_id = False

    if margs['name'] is not None:
        item_name = margs['name']

    elif margs['id'] is not None:
        item_id = margs['id']

    # ----------------------------------------------------
    # Find Object if available based on ID or Name
    # ----------------------------------------------------
    try:
        my_blueprint = find_collection_item(aos.Blueprints,
                                            item_name=item_name,
                                            item_id=item_id)
    except:
        module.fail_json(msg="Unable to find the Blueprint based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        ensure_absent(module, aos, my_blueprint)

    elif margs['state'] == 'present':

        ensure_present(module, aos, my_blueprint)

    elif margs['state'] == 'build-ready':

        ensure_build_ready(module, aos, my_blueprint)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False),
            id=dict(required=False),
            state=dict(choices=[
                'present', 'absent', 'build-ready'],
                default='present'),
            timeout=dict(type="int", default=5),
            template=dict(required=False),
            reference_arch=dict(required=False)
        ),
        mutually_exclusive=[('name', 'id')],
        required_one_of=[('name', 'id')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    aos_blueprint(module)


if __name__ == '__main__':
    main()
