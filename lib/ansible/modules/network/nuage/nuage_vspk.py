#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Nokia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: nuage_vspk
short_description: Manage Nuage VSP environments
description:
    - Manage or find Nuage VSP entities, this includes create, update, delete, assign, unassign and find, with all supported properties.
version_added: "2.4"
author: Philippe Dellaert (@pdellaert)
options:
    auth:
        description:
            - Dict with the authentication information required to connect to a Nuage VSP environment.
            - Requires a I(api_username) parameter (example csproot).
            - Requires either a I(api_password) parameter (example csproot) or a I(api_certificate) and I(api_key) parameters,
              which point to the certificate and key files for certificate based authentication.
            - Requires a I(api_enterprise) parameter (example csp).
            - Requires a I(api_url) parameter (example https://10.0.0.10:8443).
            - Requires a I(api_version) parameter (example v4_0).
        required: true
        default: null
    type:
        description:
            - The type of entity you want to work on (example Enterprise).
            - This should match the objects CamelCase class name in VSPK-Python.
            - This Class name can be found on U(https://nuagenetworks.github.io/vspkdoc/html/index.html).
        required: true
        default: null
    id:
        description:
            - The ID of the entity you want to work on.
            - In combination with I(command=find), it will only return the single entity.
            - In combination with I(state), it will either update or delete this entity.
            - Will take precedence over I(match_filter) and I(properties) whenever an entity needs to be found.
        required: false
        default: null
    parent_id:
        description:
            - The ID of the parent of the entity you want to work on.
            - When I(state) is specified, the entity will be gathered from this parent, if it exists, unless an I(id) is specified.
            - When I(command=find) is specified, the entity will be searched for in this parent, unless an I(id) is specified.
            - If specified, I(parent_type) also needs to be specified.
        required: false
        default: null
    parent_type:
        description:
            - The type of parent the ID is specified for (example Enterprise).
            - This should match the objects CamelCase class name in VSPK-Python.
            - This Class name can be found on U(https://nuagenetworks.github.io/vspkdoc/html/index.html).
            - If specified, I(parent_id) also needs to be specified.
        required: false
        default: null
    state:
        description:
            - Specifies the desired state of the entity.
            - If I(state=present), in case the entity already exists, will update the entity if it is needed.
            - If I(state=present), in case the relationship with the parent is a member relationship, will assign the entity as a member of the parent.
            - If I(state=absent), in case the relationship with the parent is a member relationship, will unassign the entity as a member of the parent.
            - Either I(state) or I(command) needs to be defined, both can not be defined at the same time.
        required: false
        default: null
        choices:
            - present
            - absent
    command:
        description:
            - Specifies a command to be executed.
            - With I(command=find), if I(parent_id) and I(parent_type) are defined, it will only search within the parent. Otherwise, if allowed,
              will search in the root object.
            - With I(command=find), if I(id) is specified, it will only return the single entity matching the id.
            - With I(command=find), otherwise, if I(match_filter) is define, it will use that filter to search.
            - With I(command=find), otherwise, if I(properties) are defined, it will do an AND search using all properties.
            - With I(command=change_password), a password of a user can be changed. Warning - In case the password is the same as the existing,
              it will throw an error.
            - With I(command=wait_for_job), the module will wait for a job to either have a status of SUCCESS or ERROR. In case an ERROR status is found,
              the module will exit with an error.
            - With I(command=wait_for_job), the job will always be returned, even if the state is ERROR situation.
            - Either I(state) or I(command) needs to be defined, both can not be defined at the same time.
        required: false
        default: null
        choices:
            - find
            - change_password
            - wait_for_job
            - get_csp_enterprise
    match_filter:
        description:
            - A filter used when looking (both in I(command) and I(state) for entities, in the format the Nuage VSP API expects.
            - If I(match_filter) is defined, it will take precedence over the I(properties), but not on the I(id)
        required: false
        default: null
    properties:
        description:
            - Properties are the key, value pairs of the different properties an entity has.
            - If no I(id) and no I(match_filter) is specified, these are used to find or determine if the entity exists.
        required: false
        default: null
    children:
        description:
            - Can be used to specify a set of child entities.
            - A mandatory property of each child is the I(type).
            - Supported optional properties of each child are I(id), I(properties) and I(match_filter).
            - The function of each of these properties is the same as in the general task definition.
            - This can be used recursively
            - Only useable in case I(state=present).
        required: false
        default: null
notes:
    - Check mode is supported, but with some caveats. It will not do any changes, and if possible try to determine if it is able do what is requested.
    - In case a parent id is provided from a previous task, it might be empty and if a search is possible on root, it will do so, which can impact performance.
requirements:
    - Python 2.7
    - Supports Nuage VSP 4.0Rx & 5.x.y
    - Proper VSPK-Python installed for your Nuage version
    - Tested with NuageX U(https://nuagex.io)
'''

EXAMPLES = '''
# This can be executed as a single role, with the following vars
# vars:
#   auth:
#     api_username: csproot
#     api_password: csproot
#     api_enterprise: csp
#     api_url: https://10.0.0.10:8443
#     api_version: v5_0
#   enterprise_name: Ansible-Enterprise
#   enterprise_new_name: Ansible-Updated-Enterprise
#
# or, for certificate based authentication
# vars:
#   auth:
#     api_username: csproot
#     api_certificate: /path/to/user-certificate.pem
#     api_key: /path/to/user-Key.pem
#     api_enterprise: csp
#     api_url: https://10.0.0.10:8443
#     api_version: v5_0
#   enterprise_name: Ansible-Enterprise
#   enterprise_new_name: Ansible-Updated-Enterprise

# Creating a new enterprise
- name: Create Enterprise
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Enterprise
    state: present
    properties:
      name: "{{ enterprise_name }}-basic"
  register: nuage_enterprise

# Checking if an Enterprise with the new name already exists
- name: Check if an Enterprise exists with the new name
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Enterprise
    command: find
    properties:
      name: "{{ enterprise_new_name }}-basic"
  ignore_errors: yes
  register: nuage_check_enterprise

# Updating an enterprise's name
- name: Update Enterprise name
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Enterprise
    id: "{{ nuage_enterprise.id }}"
    state: present
    properties:
      name: "{{ enterprise_new_name }}-basic"
  when: nuage_check_enterprise | failed

# Creating a User in an Enterprise
- name: Create admin user
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: User
    parent_id: "{{ nuage_enterprise.id }}"
    parent_type: Enterprise
    state: present
    match_filter: "userName == 'ansible-admin'"
    properties:
      email: "ansible@localhost.local"
      first_name: "Ansible"
      last_name: "Admin"
      password: "ansible-password"
      user_name: "ansible-admin"
  register: nuage_user

# Updating password for User
- name: Update admin password
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: User
    id: "{{ nuage_user.id }}"
    command: change_password
    properties:
      password: "ansible-new-password"
  ignore_errors: yes

# Finding a group in an enterprise
- name: Find Administrators group in Enterprise
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Group
    parent_id: "{{ nuage_enterprise.id }}"
    parent_type: Enterprise
    command: find
    properties:
      name: "Administrators"
  register: nuage_group

# Assign the user to the group
- name: Assign admin user to administrators
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: User
    id: "{{ nuage_user.id }}"
    parent_id: "{{ nuage_group.id }}"
    parent_type: Group
    state: present

# Creating multiple DomainTemplates
- name: Create multiple DomainTemplates
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: DomainTemplate
    parent_id: "{{ nuage_enterprise.id }}"
    parent_type: Enterprise
    state: present
    properties:
      name: "{{ item }}"
      description: "Created by Ansible"
  with_items:
    - "Template-1"
    - "Template-2"

# Finding all DomainTemplates
- name: Fetching all DomainTemplates
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: DomainTemplate
    parent_id: "{{ nuage_enterprise.id }}"
    parent_type: Enterprise
    command: find
  register: nuage_domain_templates

# Deleting all DomainTemplates
- name: Deleting all found DomainTemplates
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: DomainTemplate
    state: absent
    id: "{{ item.ID }}"
  with_items: "{{ nuage_domain_templates.entities }}"
  when: nuage_domain_templates.entities is defined

# Unassign user from group
- name: Unassign admin user to administrators
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: User
    id: "{{ nuage_user.id }}"
    parent_id: "{{ nuage_group.id }}"
    parent_type: Group
    state: absent

# Deleting an enterprise
- name: Delete Enterprise
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Enterprise
    id: "{{ nuage_enterprise.id }}"
    state: absent

# Setup an enterprise with Children
- name: Setup Enterprise and domain structure
  connection: local
  nuage_vspk:
    auth: "{{ nuage_auth }}"
    type: Enterprise
    state: present
    properties:
      name: "Child-based-Enterprise"
    children:
    - type: L2DomainTemplate
      properties:
        name: "Unmanaged-Template"
      children:
      - type: EgressACLTemplate
        match_filter: "name == 'Allow All'"
        properties:
          name: "Allow All"
          active: true
          default_allow_ip: true
          default_allow_non_ip: true
          default_install_acl_implicit_rules: true
          description: "Created by Ansible"
          priority_type: "TOP"
      - type: IngressACLTemplate
        match_filter: "name == 'Allow All'"
        properties:
          name: "Allow All"
          active: true
          default_allow_ip: true
          default_allow_non_ip: true
          description: "Created by Ansible"
          priority_type: "TOP"
'''

RETURN = '''
id:
    description: The id of the entity that was found, created, updated or assigned.
    returned: On state=present and command=find in case one entity was found.
    type: string
    sample: bae07d8d-d29c-4e2b-b6ba-621b4807a333
entities:
    description: A list of entities handled. Each element is the to_dict() of the entity.
    returned: On state=present and find, with only one element in case of state=present or find=one.
    type: list
    sample: [{
        "ID": acabc435-3946-4117-a719-b8895a335830",
        "assocEntityType": "DOMAIN",
        "command": "BEGIN_POLICY_CHANGES",
        "creationDate": 1487515656000,
        "entityScope": "ENTERPRISE",
        "externalID": null,
        "lastUpdatedBy": "8a6f0e20-a4db-4878-ad84-9cc61756cd5e",
        "lastUpdatedDate": 1487515656000,
        "owner": "8a6f0e20-a4db-4878-ad84-9cc61756cd5e",
        "parameters": null,
        "parentID": "a22fddb9-3da4-4945-bd2e-9d27fe3d62e0",
        "parentType": "domain",
        "progress": 0.0,
        "result": null,
        "status": "RUNNING"
        }]
'''

import time

try:
    import importlib
    HAS_IMPORTLIB = True
except ImportError:
    HAS_IMPORTLIB = False

try:
    from bambou.exceptions import BambouHTTPError
    HAS_BAMBOU = True
except ImportError:
    HAS_BAMBOU = False

from ansible.module_utils.basic import AnsibleModule


SUPPORTED_COMMANDS = ['find', 'change_password', 'wait_for_job', 'get_csp_enterprise']
VSPK = None


class NuageEntityManager(object):
    """
    This module is meant to manage an entity in a Nuage VSP Platform
    """

    def __init__(self, module):
        self.module = module
        self.auth = module.params['auth']
        self.api_username = None
        self.api_password = None
        self.api_enterprise = None
        self.api_url = None
        self.api_version = None
        self.api_certificate = None
        self.api_key = None
        self.type = module.params['type']

        self.state = module.params['state']
        self.command = module.params['command']
        self.match_filter = module.params['match_filter']
        self.entity_id = module.params['id']
        self.parent_id = module.params['parent_id']
        self.parent_type = module.params['parent_type']
        self.properties = module.params['properties']
        self.children = module.params['children']

        self.entity = None
        self.entity_class = None
        self.parent = None
        self.parent_class = None
        self.entity_fetcher = None

        self.result = {
            'state': self.state,
            'id': self.entity_id,
            'entities': []
        }
        self.nuage_connection = None

        self._verify_api()
        self._verify_input()
        self._connect_vspk()
        self._find_parent()

    def _connect_vspk(self):
        """
        Connects to a Nuage API endpoint
        """
        try:
            # Connecting to Nuage
            if self.api_certificate and self.api_key:
                self.nuage_connection = VSPK.NUVSDSession(username=self.api_username, enterprise=self.api_enterprise, api_url=self.api_url,
                                                          certificate=(self.api_certificate, self.api_key))
            else:
                self.nuage_connection = VSPK.NUVSDSession(username=self.api_username, password=self.api_password, enterprise=self.api_enterprise,
                                                          api_url=self.api_url)
            self.nuage_connection.start()
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to connect to the API URL with given username, password and enterprise: {0}'.format(error))

    def _verify_api(self):
        """
        Verifies the API and loads the proper VSPK version
        """
        # Checking auth parameters
        if ('api_password' not in list(self.auth.keys()) or not self.auth['api_password']) and ('api_certificate' not in list(self.auth.keys()) or
                                                                                                'api_key' not in list(self.auth.keys()) or
                                                                                                not self.auth['api_certificate'] or not self.auth['api_key']):
            self.module.fail_json(msg='Missing api_password or api_certificate and api_key parameter in auth')

        self.api_username = self.auth['api_username']
        if 'api_password' in list(self.auth.keys()) and self.auth['api_password']:
            self.api_password = self.auth['api_password']
        if 'api_certificate' in list(self.auth.keys()) and 'api_key' in list(self.auth.keys()) and self.auth['api_certificate'] and self.auth['api_key']:
            self.api_certificate = self.auth['api_certificate']
            self.api_key = self.auth['api_key']
        self.api_enterprise = self.auth['api_enterprise']
        self.api_url = self.auth['api_url']
        self.api_version = self.auth['api_version']

        try:
            global VSPK
            VSPK = importlib.import_module('vspk.{0:s}'.format(self.api_version))
        except ImportError:
            self.module.fail_json(msg='vspk is required for this module, or the API version specified does not exist.')

    def _verify_input(self):
        """
        Verifies the parameter input for types and parent correctness and necessary parameters
        """

        # Checking if type exists
        try:
            self.entity_class = getattr(VSPK, 'NU{0:s}'.format(self.type))
        except AttributeError:
            self.module.fail_json(msg='Unrecognised type specified')

        if self.module.check_mode:
            return

        if self.parent_type:
            # Checking if parent type exists
            try:
                self.parent_class = getattr(VSPK, 'NU{0:s}'.format(self.parent_type))
            except AttributeError:
                # The parent type does not exist, fail
                self.module.fail_json(msg='Unrecognised parent type specified')

            fetcher = self.parent_class().fetcher_for_rest_name(self.entity_class.rest_name)
            if fetcher is None:
                # The parent has no fetcher, fail
                self.module.fail_json(msg='Specified parent is not a valid parent for the specified type')
        elif not self.entity_id:
            # If there is an id, we do not need a parent because we'll interact directly with the entity
            # If an assign needs to happen, a parent will have to be provided
            # Root object is the parent
            self.parent_class = VSPK.NUMe
            fetcher = self.parent_class().fetcher_for_rest_name(self.entity_class.rest_name)
            if fetcher is None:
                self.module.fail_json(msg='No parent specified and root object is not a parent for the type')

        # Verifying if a password is provided in case of the change_password command:
        if self.command and self.command == 'change_password' and 'password' not in self.properties.keys():
            self.module.fail_json(msg='command is change_password but the following are missing: password property')

    def _find_parent(self):
        """
        Fetches the parent if needed, otherwise configures the root object as parent. Also configures the entity fetcher
        Important notes:
        - If the parent is not set, the parent is automatically set to the root object
        - It the root object does not hold a fetcher for the entity, you have to provide an ID
        - If you want to assign/unassign, you have to provide a valid parent
        """
        self.parent = self.nuage_connection.user

        if self.parent_id:
            self.parent = self.parent_class(id=self.parent_id)
            try:
                self.parent.fetch()
            except BambouHTTPError as error:
                self.module.fail_json(msg='Failed to fetch the specified parent: {0}'.format(error))

        self.entity_fetcher = self.parent.fetcher_for_rest_name(self.entity_class.rest_name)

    def _find_entities(self, entity_id=None, entity_class=None, match_filter=None, properties=None, entity_fetcher=None):
        """
        Will return a set of entities matching a filter or set of properties if the match_filter is unset. If the
        entity_id is set, it will return only the entity matching that ID as the single element of the list.
        :param entity_id: Optional ID of the entity which should be returned
        :param entity_class: Optional class of the entity which needs to be found
        :param match_filter: Optional search filter
        :param properties: Optional set of properties the entities should contain
        :param entity_fetcher: The fetcher for the entity type
        :return: List of matching entities
        """
        search_filter = ''

        if entity_id:
            found_entity = entity_class(id=entity_id)
            try:
                found_entity.fetch()
            except BambouHTTPError as error:
                self.module.fail_json(msg='Failed to fetch the specified entity by ID: {0}'.format(error))

            return [found_entity]

        elif match_filter:
            search_filter = match_filter
        elif properties:
            # Building filter
            for num, property_name in enumerate(properties):
                if num > 0:
                    search_filter += ' and '
                search_filter += '{0:s} == "{1}"'.format(property_name, properties[property_name])

        if entity_fetcher is not None:
            try:
                return entity_fetcher.get(filter=search_filter)
            except BambouHTTPError:
                pass
        return []

    def _find_entity(self, entity_id=None, entity_class=None, match_filter=None, properties=None, entity_fetcher=None):
        """
        Finds a single matching entity that matches all the provided properties, unless an ID is specified, in which
        case it just fetches the one item
        :param entity_id: Optional ID of the entity which should be returned
        :param entity_class: Optional class of the entity which needs to be found
        :param match_filter: Optional search filter
        :param properties: Optional set of properties the entities should contain
        :param entity_fetcher: The fetcher for the entity type
        :return: The first entity matching the criteria, or None if none was found
        """
        search_filter = ''
        if entity_id:
            found_entity = entity_class(id=entity_id)
            try:
                found_entity.fetch()
            except BambouHTTPError as error:
                self.module.fail_json(msg='Failed to fetch the specified entity by ID: {0}'.format(error))

            return found_entity

        elif match_filter:
            search_filter = match_filter
        elif properties:
            # Building filter
            for num, property_name in enumerate(properties):
                if num > 0:
                    search_filter += ' and '
                search_filter += '{0:s} == "{1}"'.format(property_name, properties[property_name])

        if entity_fetcher is not None:
            try:
                return entity_fetcher.get_first(filter=search_filter)
            except BambouHTTPError:
                pass
        return None

    def handle_main_entity(self):
        """
        Handles the Ansible task
        """
        if self.command and self.command == 'find':
            self._handle_find()
        elif self.command and self.command == 'change_password':
            self._handle_change_password()
        elif self.command and self.command == 'wait_for_job':
            self._handle_wait_for_job()
        elif self.command and self.command == 'get_csp_enterprise':
            self._handle_get_csp_enterprise()
        elif self.state == 'present':
            self._handle_present()
        elif self.state == 'absent':
            self._handle_absent()
        self.module.exit_json(**self.result)

    def _handle_absent(self):
        """
        Handles the Ansible task when the state is set to absent
        """
        # Absent state
        self.entity = self._find_entity(entity_id=self.entity_id, entity_class=self.entity_class, match_filter=self.match_filter, properties=self.properties,
                                        entity_fetcher=self.entity_fetcher)
        if self.entity and (self.entity_fetcher is None or self.entity_fetcher.relationship in ['child', 'root']):
            # Entity is present, deleting
            if self.module.check_mode:
                self.result['changed'] = True
            else:
                self._delete_entity(self.entity)
                self.result['id'] = None
        elif self.entity and self.entity_fetcher.relationship == 'member':
            # Entity is a member, need to check if already present
            if self._is_member(entity_fetcher=self.entity_fetcher, entity=self.entity):
                # Entity is not a member yet
                if self.module.check_mode:
                    self.result['changed'] = True
                else:
                    self._unassign_member(entity_fetcher=self.entity_fetcher, entity=self.entity, entity_class=self.entity_class, parent=self.parent,
                                          set_output=True)

    def _handle_present(self):
        """
        Handles the Ansible task when the state is set to present
        """
        # Present state
        self.entity = self._find_entity(entity_id=self.entity_id, entity_class=self.entity_class, match_filter=self.match_filter, properties=self.properties,
                                        entity_fetcher=self.entity_fetcher)
        # Determining action to take
        if self.entity_fetcher is not None and self.entity_fetcher.relationship == 'member' and not self.entity:
            self.module.fail_json(msg='Trying to assign an entity that does not exist')
        elif self.entity_fetcher is not None and self.entity_fetcher.relationship == 'member' and self.entity:
            # Entity is a member, need to check if already present
            if not self._is_member(entity_fetcher=self.entity_fetcher, entity=self.entity):
                # Entity is not a member yet
                if self.module.check_mode:
                    self.result['changed'] = True
                else:
                    self._assign_member(entity_fetcher=self.entity_fetcher, entity=self.entity, entity_class=self.entity_class, parent=self.parent,
                                        set_output=True)
        elif self.entity_fetcher is not None and self.entity_fetcher.relationship in ['child', 'root'] and not self.entity:
            # Entity is not present as a child, creating
            if self.module.check_mode:
                self.result['changed'] = True
            else:
                self.entity = self._create_entity(entity_class=self.entity_class, parent=self.parent, properties=self.properties)
                self.result['id'] = self.entity.id
                self.result['entities'].append(self.entity.to_dict())

            # Checking children
            if self.children:
                for child in self.children:
                    self._handle_child(child=child, parent=self.entity)
        elif self.entity:
            # Need to compare properties in entity and found entity
            changed = self._has_changed(entity=self.entity, properties=self.properties)

            if self.module.check_mode:
                self.result['changed'] = changed
            elif changed:
                self.entity = self._save_entity(entity=self.entity)
                self.result['id'] = self.entity.id
                self.result['entities'].append(self.entity.to_dict())
            else:
                self.result['id'] = self.entity.id
                self.result['entities'].append(self.entity.to_dict())

            # Checking children
            if self.children:
                for child in self.children:
                    self._handle_child(child=child, parent=self.entity)
        elif not self.module.check_mode:
            self.module.fail_json(msg='Invalid situation, verify parameters')

    def _handle_get_csp_enterprise(self):
        """
        Handles the Ansible task when the command is to get the csp enterprise
        """
        self.entity_id = self.parent.enterprise_id
        self.entity = VSPK.NUEnterprise(id=self.entity_id)
        try:
            self.entity.fetch()
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to fetch CSP enterprise: {0}'.format(error))
        self.result['id'] = self.entity_id
        self.result['entities'].append(self.entity.to_dict())

    def _handle_wait_for_job(self):
        """
        Handles the Ansible task when the command is to wait for a job
        """
        # Command wait_for_job
        self.entity = self._find_entity(entity_id=self.entity_id, entity_class=self.entity_class, match_filter=self.match_filter, properties=self.properties,
                                        entity_fetcher=self.entity_fetcher)
        if self.module.check_mode:
            self.result['changed'] = True
        else:
            self._wait_for_job(self.entity)

    def _handle_change_password(self):
        """
        Handles the Ansible task when the command is to change a password
        """
        # Command change_password
        self.entity = self._find_entity(entity_id=self.entity_id, entity_class=self.entity_class, match_filter=self.match_filter, properties=self.properties,
                                        entity_fetcher=self.entity_fetcher)
        if self.module.check_mode:
            self.result['changed'] = True
        else:
            try:
                getattr(self.entity, 'password')
            except AttributeError:
                self.module.fail_json(msg='Entity does not have a password property')

            try:
                setattr(self.entity, 'password', self.properties['password'])
            except AttributeError:
                self.module.fail_json(msg='Password can not be changed for entity')

            self.entity = self._save_entity(entity=self.entity)
            self.result['id'] = self.entity.id
            self.result['entities'].append(self.entity.to_dict())

    def _handle_find(self):
        """
        Handles the Ansible task when the command is to find an entity
        """
        # Command find
        entities = self._find_entities(entity_id=self.entity_id, entity_class=self.entity_class, match_filter=self.match_filter, properties=self.properties,
                                       entity_fetcher=self.entity_fetcher)
        self.result['changed'] = False
        if entities:
            if len(entities) == 1:
                self.result['id'] = entities[0].id
            for entity in entities:
                self.result['entities'].append(entity.to_dict())
        elif not self.module.check_mode:
            self.module.fail_json(msg='Unable to find matching entries')

    def _handle_child(self, child, parent):
        """
        Handles children of a main entity. Fields are similar to the normal fields
        Currently only supported state: present
        """
        if 'type' not in list(child.keys()):
            self.module.fail_json(msg='Child type unspecified')
        elif 'id' not in list(child.keys()) and 'properties' not in list(child.keys()):
            self.module.fail_json(msg='Child ID or properties unspecified')

        # Setting intern variables
        child_id = None
        if 'id' in list(child.keys()):
            child_id = child['id']
        child_properties = None
        if 'properties' in list(child.keys()):
            child_properties = child['properties']
        child_filter = None
        if 'match_filter' in list(child.keys()):
            child_filter = child['match_filter']

        # Checking if type exists
        entity_class = None
        try:
            entity_class = getattr(VSPK, 'NU{0:s}'.format(child['type']))
        except AttributeError:
            self.module.fail_json(msg='Unrecognised child type specified')

        entity_fetcher = parent.fetcher_for_rest_name(entity_class.rest_name)
        if entity_fetcher is None and not child_id and not self.module.check_mode:
            self.module.fail_json(msg='Unable to find a fetcher for child, and no ID specified.')

        # Try and find the child
        entity = self._find_entity(entity_id=child_id, entity_class=entity_class, match_filter=child_filter, properties=child_properties,
                                   entity_fetcher=entity_fetcher)

        # Determining action to take
        if entity_fetcher.relationship == 'member' and not entity:
            self.module.fail_json(msg='Trying to assign a child that does not exist')
        elif entity_fetcher.relationship == 'member' and entity:
            # Entity is a member, need to check if already present
            if not self._is_member(entity_fetcher=entity_fetcher, entity=entity):
                # Entity is not a member yet
                if self.module.check_mode:
                    self.result['changed'] = True
                else:
                    self._assign_member(entity_fetcher=entity_fetcher, entity=entity, entity_class=entity_class, parent=parent, set_output=False)
        elif entity_fetcher.relationship in ['child', 'root'] and not entity:
            # Entity is not present as a child, creating
            if self.module.check_mode:
                self.result['changed'] = True
            else:
                entity = self._create_entity(entity_class=entity_class, parent=parent, properties=child_properties)
        elif entity_fetcher.relationship in ['child', 'root'] and entity:
            changed = self._has_changed(entity=entity, properties=child_properties)

            if self.module.check_mode:
                self.result['changed'] = changed
            elif changed:
                entity = self._save_entity(entity=entity)

        if entity:
            self.result['entities'].append(entity.to_dict())

        # Checking children
        if 'children' in list(child.keys()) and not self.module.check_mode:
            for subchild in child['children']:
                self._handle_child(child=subchild, parent=entity)

    def _has_changed(self, entity, properties):
        """
        Compares a set of properties with a given entity, returns True in case the properties are different from the
        values in the entity
        :param entity: The entity to check
        :param properties: The properties to check
        :return: boolean
        """
        # Need to compare properties in entity and found entity
        changed = False
        if properties:
            for property_name in list(properties.keys()):
                if property_name == 'password':
                    continue
                entity_value = ''
                try:
                    entity_value = getattr(entity, property_name)
                except AttributeError:
                    self.module.fail_json(msg='Property {0:s} is not valid for this type of entity'.format(property_name))

                if entity_value != properties[property_name]:
                    # Difference in values changing property
                    changed = True
                    try:
                        setattr(entity, property_name, properties[property_name])
                    except AttributeError:
                        self.module.fail_json(msg='Property {0:s} can not be changed for this type of entity'.format(property_name))
        return changed

    def _is_member(self, entity_fetcher, entity):
        """
        Verifies if the entity is a member of the parent in the fetcher
        :param entity_fetcher: The fetcher for the entity type
        :param entity: The entity to look for as a member in the entity fetcher
        :return: boolean
        """
        members = entity_fetcher.get()
        for member in members:
            if member.id == entity.id:
                return True
        return False

    def _assign_member(self, entity_fetcher, entity, entity_class, parent, set_output):
        """
        Adds the entity as a member to a parent
        :param entity_fetcher: The fetcher of the entity type
        :param entity: The entity to add as a member
        :param entity_class: The class of the entity
        :param parent: The parent on which to add the entity as a member
        :param set_output: If set to True, sets the Ansible result variables
        """
        members = entity_fetcher.get()
        members.append(entity)
        try:
            parent.assign(members, entity_class)
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to assign entity as a member: {0}'.format(error))
        self.result['changed'] = True
        if set_output:
            self.result['id'] = entity.id
            self.result['entities'].append(entity.to_dict())

    def _unassign_member(self, entity_fetcher, entity, entity_class, parent, set_output):
        """
        Removes the entity as a member of a parent
        :param entity_fetcher: The fetcher of the entity type
        :param entity: The entity to remove as a member
        :param entity_class: The class of the entity
        :param parent: The parent on which to add the entity as a member
        :param set_output: If set to True, sets the Ansible result variables
        """
        members = []
        for member in entity_fetcher.get():
            if member.id != entity.id:
                members.append(member)
        try:
            parent.assign(members, entity_class)
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to remove entity as a member: {0}'.format(error))
        self.result['changed'] = True
        if set_output:
            self.result['id'] = entity.id
            self.result['entities'].append(entity.to_dict())

    def _create_entity(self, entity_class, parent, properties):
        """
        Creates a new entity in the parent, with all properties configured as in the file
        :param entity_class: The class of the entity
        :param parent: The parent of the entity
        :param properties: The set of properties of the entity
        :return: The entity
        """
        entity = entity_class(**properties)
        try:
            parent.create_child(entity)
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to create entity: {0}'.format(error))
        self.result['changed'] = True
        return entity

    def _save_entity(self, entity):
        """
        Updates an existing entity
        :param entity: The entity to save
        :return: The updated entity
        """
        try:
            entity.save()
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to update entity: {0}'.format(error))
        self.result['changed'] = True
        return entity

    def _delete_entity(self, entity):
        """
        Deletes an entity
        :param entity: The entity to delete
        """
        try:
            entity.delete()
        except BambouHTTPError as error:
            self.module.fail_json(msg='Unable to delete entity: {0}'.format(error))
        self.result['changed'] = True

    def _wait_for_job(self, entity):
        """
        Waits for a job to finish
        :param entity: The job to wait for
        """
        running = False
        if entity.status == 'RUNNING':
            self.result['changed'] = True
            running = True

        while running:
            time.sleep(1)
            entity.fetch()

            if entity.status != 'RUNNING':
                running = False

        self.result['entities'].append(entity.to_dict())
        if entity.status == 'ERROR':
            self.module.fail_json(msg='Job ended in an error')


def main():
    """
    Main method
    """
    module = AnsibleModule(
        argument_spec=dict(
            auth=dict(
                required=True,
                type='dict',
                options=dict(
                    api_username=dict(required=True, type='str'),
                    api_enterprise=dict(required=True, type='str'),
                    api_url=dict(required=True, type='str'),
                    api_version=dict(required=True, type='str'),
                    api_password=dict(default=None, required=False, type='str', no_log=True),
                    api_certificate=dict(default=None, required=False, type='str', no_log=True),
                    api_key=dict(default=None, required=False, type='str', no_log=True)
                )
            ),
            type=dict(required=True, type='str'),
            id=dict(default=None, required=False, type='str'),
            parent_id=dict(default=None, required=False, type='str'),
            parent_type=dict(default=None, required=False, type='str'),
            state=dict(default=None, choices=['present', 'absent'], type='str'),
            command=dict(default=None, choices=SUPPORTED_COMMANDS, type='str'),
            match_filter=dict(default=None, required=False, type='str'),
            properties=dict(default=None, required=False, type='dict'),
            children=dict(default=None, required=False, type='list')
        ),
        mutually_exclusive=[
            ['command', 'state']
        ],
        required_together=[
            ['parent_id', 'parent_type']
        ],
        required_one_of=[
            ['command', 'state']
        ],
        required_if=[
            ['state', 'present', ['id', 'properties', 'match_filter'], True],
            ['state', 'absent', ['id', 'properties', 'match_filter'], True],
            ['command', 'change_password', ['id', 'properties']],
            ['command', 'wait_for_job', ['id']]
        ],
        supports_check_mode=True
    )

    if not HAS_BAMBOU:
        module.fail_json(msg='bambou is required for this module')

    if not HAS_IMPORTLIB:
        module.fail_json(msg='importlib (python 2.7) is required for this module')

    entity_manager = NuageEntityManager(module)
    entity_manager.handle_main_entity()


if __name__ == '__main__':
    main()
