#!/usr/bin/python
#
# PubNub Real-time Cloud-Hosted Push API and Push Notification Client Frameworks
# Copyright (C) 2016 PubNub Inc.
# http://www.pubnub.com/
# http://www.pubnub.com/terms
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'commiter',
                    'version': '1.0'}


DOCUMENTATION = '''
---
module: pubnub_blocks
version_added: '1.0'
short_description: PubNub blocks management module.
description:
  - This module allow to manage existing blocks by managing event handlers and starting/stopping block.
author:
  - PubNub <support@pubnub.com> (@pubnub)
  - Sergey Mamontov <sergey@pubnub.com> (@parfeon)
requirements:
  - "python >= 2.7"
options:
  email:
    description:
      - Email from account for which new session should be started.
      - Not required if C(cache) contains result of previous module call (in same play).
    required: false
  pwd:
    description:
      - Password which match to account to which specified C(email) belong.
      - Not required if C(cache) contains result of previous module call (in same play).
    required: false
  cache:
    description:
      - In case if single play use blocks management module few times it is preferred to enabled 'caching' by making \
        previous module to share gathered artifacts and pass them to this parameter.
    required: false
    default: {}
  application:
    description:
      - Name of target PubNub application for which blocks configuration on specific C(keyset) will be done.
    required: true
  keyset:
    description:
      - Name of application's keys set which is bound to managed blocks.
    required: true
  state:
    description:
      - Intended block state after event handlers creation / update process will be completed.
    required: false
    default: 'start'
    choices: ['start', 'stop', 'present', 'absent']
  block:
    description:
      - Name of managed block which will be later visible on admin.pubnub.com.
    required: true
  description:
    description:
      - Short block description which will be later visible on admin.pubnub.com. Used only if block doesn't exists and \
        won't change description for existing block.
    required: false
    default: 'New block'
  event_handlers:
    description:
      - List of event handlers which should be updated for specified C(block).
      - 'Each entry for new event handler should contain: C(name), C(src), C(channels), C(event). C(name) used as event' \
        handler name which can be used later to make changes to it. C(src) is full path to file with event handler \
        code. C(channels) is name of channel from which event handler is waiting for events. C(event) is type of event \
        'which is able to trigger event handler: I(js-before-publish), I(js-after-publish), I(js-after-presence).'
      - Each entry for existing handlers should contain C(name) (so target handler can be identified). Rest parameters \
        (C(src), C(channels) and C(event)) can be added if changes required for them.
      - It is possible to rename event handler by adding C(changes) key to event handler payload and pass dictionary, \
        which will contain single key C(name), where new name should be passed.
      - To remove particular event handler it is possible to set C(state) for it to C(absent) and it will be removed.
    required: false
    default: []
  changes:
    description:
      - List of fields which should be changed by block itself (doesn't affect any event handlers).
      - Possible options for change is C(name) and C(description).
    required: false
    default: {}
  validate_certs:
    description:
      - This key allow to try skip certificates check when performing REST API calls. Sometimes host may have issues \
        with certificates on it and this will cause problems to call PubNub REST API.
      - If check should be ignored C(False) should be passed to this parameter.
    required: false
    default: true
'''

EXAMPLES = '''
# Event handler create example.
- name: Create single event handler
  pubnub_blocks:
    email: '{{ email }}'
    pwd: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    block: '{{ block_name }}'
    event_handlers:
      -
        src: '{{ path_to_handler_source }}'
        name: '{{ handler_name }}'
        event: 'js-before-publish'
        channels: '{{ handler_channel }}'

# Change event handler trigger event type.
- name: Change event handler 'event'
  pubnub_blocks:
    email: '{{ email }}'
    pwd: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    block: '{{ block_name }}'
    event_handlers:
      -
        name: '{{ handler_name }}'
        event: 'js-after-publish'

# Stop block and event handlers.
- name: Stopping block
  pubnub_blocks:
    email: '{{ email }}'
    pwd: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    block: '{{ block_name }}'
    state: stop

# Multiple module calls with cached result passing
- name: Create '{{ block_name }}' block
      register: module_cache
      pubnub_blocks:
        email: '{{ email }}'
        pwd: '{{ password }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        block: '{{ block_name }}'
        state: present
    - name: Add '{{ event_handler_1_name }}' event handler to '{{ block_name }}'
      register: module_cache
      pubnub_blocks:
        cache: '{{ module_cache }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        block: '{{ block_name }}'
        state: present
        event_handlers:
          -
            src: '{{ path_to_handler_1_source }}'
            name: '{{ event_handler_1_name }}'
            channels: '{{ event_handler_1_channel }}'
            event: 'js-before-publish'
    - name: Add '{{ event_handler_2_name }}' event handler to '{{ block_name }}'
      register: module_cache
      pubnub_blocks:
        cache: '{{ module_cache }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        block: '{{ block_name }}'
        state: present
        event_handlers:
          -
            src: '{{ path_to_handler_2_source }}'
            name: '{{ event_handler_2_name }}'
            channels: '{{ event_handler_2_channel }}'
            event: 'js-before-publish'
    - name: Start '{{ block_name }}' block
      register: module_cache
      pubnub_blocks:
        cache: '{{ module_cache }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        block: '{{ block_name }}'
        state: start
'''

RETURN = '''
module_cache:
  description: Cached account information. In case if with single play module used few times it is better to pass \
               cached data to next module calls to speed up process.
  type: dict
'''

PUBNUB_API_URL = "https://admin.pubnub.com/api"
PN_BLOCK_STATE_CHECK_INTERVAL = 1
PN_BLOCK_STATE_CHECK_MAX_COUNT = 30
# Import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import *
from ansible.module_utils.urls import *
PN_URLENCODE = None
try:
    import urllib.parse
    PN_URLENCODE = urllib.parse.urlencode
except ImportError:
    import urllib
    PN_URLENCODE = urllib.urlencode
try:
    import zlib
    ZLIB_AVAILABLE = True
except ImportError:
    ZLIB_AVAILABLE = False
import traceback
import random
import copy
import time


class PubNubAccount(object):
    """PubNub account representation model."""

    def __init__(self, module, cache=None):
        """Construct account model using service response.

        :type module:   AnsibleModule
        :param module:  Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type cache:    dict
        :param cache:   Reference on dictionary which represent previously exported account model (previous model run).
                        'None' can be passed in case if this is first module run or cached data not provided (maybe
                        single module call).
        :rtype:  PubNubAccount
        :return: Initialized account data model.
        """
        super(PubNubAccount, self).__init__()
        self._module = module
        self._api = PubNubAPIClient(module=module, account=self)
        self._orig_service_data = None
        self._applications = dict()
        if not _is_empty(cache):
            self._restore(cache)

    @property
    def uid(self):
        """Stores reference on unique account identifier.

        :rtype:  int
        :return: Reference on unique user identifier or 'None' in case if account model configuration not completed.
        """
        uid = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('user')):
            uid = self._orig_service_data['user']['id']

        return uid

    @property
    def email(self):
        """Stores reference on account's owner email address.

        :rtype:  str
        :return: Reference on account's owner email address or 'None' in case if account model configuration not
                 completed.
        """
        email = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('user')):
            email = self._orig_service_data['user']['email']

        return email

    def changed(self):
        """Check whether something changed in account's data.

        Whether something in account has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if account or application data has been modified.
        """
        applications_changed = False
        for application_name in self._applications:
            applications_changed = self.application_by_name(application_name).changed()
            if applications_changed:
                break

        return applications_changed

    def export(self):
        """Export account model.

        Export allow to receive object which can be used to re-use it with other pubnub modules call which will follow
        after this.
        :rtype:  dict
        :return: Dictionary which represent account model with all it fields and values.
        """
        export_data = copy.deepcopy(self._orig_service_data)
        if not _is_empty(self._applications):
            exported_applications = list()
            for application_name in self._applications:
                application = self.application_by_name(application_name)
                exported_applications.append(application.export())
            export_data['pnm_applications'] = exported_applications

        return export_data

    def current_application(self):
        """Retrieve reference on application which has been specified for this module run.

        Check module properties to find out name of application with which module should work at this moment.
        :rtype:  PubNubApplication
        :return: Reference on registered application model or 'None' in case if there is no application with specified
                 name.
        """
        return self.application_by_name(self._module.params['application'])

    def application_by_name(self, application):
        """Retrieve reference on application by it't name.

        :type application:  str
        :param application: Reference on name of application to which reference should be retrieved.
        :rtype:  PubNubApplication
        :return: Reference on registered application model or 'None' in case if there is no application with specified
                 name.
        """
        app = self._applications.get(application)
        if _is_empty(app):
            error_fmt = "There is no '%s' application for %s. Make sure what correct application name has " + \
                        "been passed. If application doesn't exist you can create it on admin.pubnub.com."
            error_args = (application, self.email)
            self._module.fail_json(changed=self.changed(), msg=error_fmt % error_args)

        return app

    def login(self, email, pwd):
        """Start new PubNub block management API access session using provided account credentials.

        :type email:  str
        :param email: Email of account for which REST API calls should be authorized.
        :type pwd:    str
        :param pwd:   Account's password.
        """
        # Authorize with account's credentials and complete account model configuration.
        self._process_account_data(self._api.start_session(email=email, pwd=pwd))
        # Fetch and process list of registered applications.
        self._process_applications_data(self._api.fetch_applications(account_id=self.uid))

    def save(self):
        """Store any changes to account and related data structures.

        If account or any related to current module run component has been changed it should be saved using REST API.
        """
        for application_name in self._applications:
            self.application_by_name(application_name).save()

    def _restore(self, cache):
        """Restore account data model.

        Module allow to export cached results and their re-usage with next module call. Restore allow to speed up module
        execution, because some REST API calls is pretty slow.
        :type cache:  dict
        :param cache: Reference on dictionary which contain information from previous module run and allow to restore
                      account model to it's latest state.
        """
        if not _is_empty(cache.get('pnm_applications')):
            self._process_applications_data(cache.pop('pnm_applications'))
        self._process_account_data(cache)

        # Update session information for API.
        self._api.session = self._session = cache['token']

    def _process_account_data(self, account):
        """Process service data to configure account data model.

        Configure or restore account model from previous module run using exported data. Restore allow to speed up
        module execution, because some REST API calls is pretty slow.
        :type account:  dict
        :param account: Reference on dictionary which contain information for account data model configuration.
        """
        # Store account information.
        self._orig_service_data = copy.deepcopy(account)

    def _process_applications_data(self, applications):
        """Process list of applications which is registered for account.

        :type applications:  list
        :param applications: Reference on list of dictionaries which describe every application which is registered for
                             authorized account.
        """
        for application in applications:
            application_model = PubNubApplication(self._module, account=self, api_client=self._api,
                                                  application=application)
            self._applications[application_model.name] = application_model


class PubNubApplication(object):
    """PubNub application representation model."""

    def __init__(self, module, account, api_client, application):
        """Construct application model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type account:      PubNubAccount
        :param account:     Reference on user account where this application has been registered.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client.
        :type application:  dict
        :param application: PubNub service response with information about particular application.
        :rtype:  PubNubApplication
        :return: Initialized application data model.
        """
        super(PubNubApplication, self).__init__()
        self._module = module
        self._account = account
        self._api = api_client
        self._orig_service_data = None
        self._keysets = dict()
        self._active_keyset = None
        self._process_application_data(application)

    @property
    def uid(self):
        """Stores reference on unique application identifier.

        :rtype:  int
        :return: Reference on unique application identifier or 'None' in case if application model configuration not
                 completed.
        """
        uid = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('id')):
            uid = self._orig_service_data['id']

        return uid

    @property
    def name(self):
        """Stores reference on registered application name.

        :rtype:  str
        :return: Reference on application name or 'None' in case if application model configuration not completed.
        """
        name = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('name')):
            name = self._orig_service_data['name']

        return name

    def changed(self):
        """Check whether application's data has been changed or not.

        Whether something in application has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if application or keysets data has been modified.
        """
        keysets_changed = False
        for keyset_name in self._keysets:
            keysets_changed = self.keyset_by_name(keyset_name).changed()
            if keysets_changed:
                break

        return keysets_changed

    def export(self):
        """Export application model.

        Export allow to receive object which can be used to re-use it with other pubnub modules call which will follow
        after this.
        :rtype:  dict
        :return: Dictionary which represent application model with all it fields and values.
        """
        export_data = copy.deepcopy(self._orig_service_data)
        if not _is_empty(self._keysets):
            exported_keysets = list()
            for keyset_name in self._keysets:
                keyset = self.keyset_by_name(keyset_name)
                exported_keysets.append(keyset.export())
            export_data['keys'] = exported_keysets

        return export_data

    def current_keyset(self):
        """Retrieve reference on application's keyset which has been specified for this module run.

        Check module properties to find out name of keyset with which module should work at this moment.
        :rtype:  PubNubKeyset
        :return: Reference on application's keyset model or 'None' in case if there is no keysets with specified name.
        """
        return self.keyset_by_name(self._module.params['keyset'])

    def keyset_by_name(self, keyset):
        """Retrieve reference on application's keyset by it't name.

        :type keyset:  str
        :param keyset: Reference on name of keyset to which reference should be retrieved.
        :rtype:  PubNubKeyset
        :return: Reference on application's keyset model or 'None' in case if there is no keysets with specified name.
        """
        ks = self._keysets.get(keyset)
        if _is_empty(ks):
            error_fmt = "There is no '%s' keyset for '%s' application. Make sure what correct keyset name has " + \
                        "been passed. If keyset doesn't exist you can create it on admin.pubnub.com."
            error_args = (keyset, self.name)
            self._module.fail_json(changed=self.changed(), msg=error_fmt % error_args)

        return ks

    def save(self):
        """Store any changes to application and/or keyset."""
        for keyset_name in self._keysets:
            self.keyset_by_name(keyset_name).save()

    def _process_application_data(self, application):
        """Process fetched application data.

        Process received application data to complete model configuration.
        :type application:  dict
        :param application: Reference on dictionary which describe application which is registered for authorized
                            account.
        """
        if not _is_empty(application.get('keys')):
            keysets = application.pop('keys')
            for keyset in keysets:
                keyset_model = PubNubKeyset(self._module, application=self, api_client=self._api, keyset=keyset)
                self._keysets[keyset_model.name] = keyset_model
        self._orig_service_data = copy.deepcopy(application)


class PubNubKeyset(object):
    """PubNub application's keyset representation model."""

    def __init__(self, module, application, api_client, keyset):
        """Construct application's keyset model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type application:  PubNubApplication
        :param application: Reference on application model to which keyset belong.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client.
        :type keyset:       dict
        :param keyset:      PubNub service response with information about particular application's keyset.
        :rtype:  PubNubKeyset
        :return: Initialized keyset model.
        """
        super(PubNubKeyset, self).__init__()
        self._module = module
        self._changed = False
        self._api = api_client
        self._application = application
        self._orig_service_data = None
        self._blocks = None
        self._process_keyset_data(keyset)

    @property
    def uid(self):
        """Stores reference on unique keyset identifier.

        :rtype:  int
        :return: Reference on unique keyset identifier or 'None' in case if keyset model configuration not completed.
        """
        uid = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('id')):
            uid = self._orig_service_data['id']

        return uid

    @property
    def name(self):
        """Stores reference on keyset name.

        :rtype:  str
        :return: Reference on keyset name or 'None' in case if keyset model configuration not completed.
        """
        name = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('properties')):
            name = self._orig_service_data['properties']['name']

        return name

    def changed(self):
        """Check whether keyset's data has been changed or not.

        Whether something in keyset has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if keyset or block data has been modified.
        """
        blocks_changed = False
        if not self._changed:
            blocks = self._blocks if not _is_empty(self._blocks) else dict()
            for block_name in blocks:
                blocks_changed = self.block_by_name(block_name).changed()
                if blocks_changed:
                    break

        return self._changed or blocks_changed

    def export(self):
        """Export keyset model.

        Export allow to receive object which can be used to re-use it with other pubnub modules call which will follow
        after this.
        :rtype:  dict
        :return: Dictionary which keyset application model with all it fields and values.
        """
        export_data = copy.deepcopy(self._orig_service_data)
        if not _is_empty(self._blocks):
            exported_blocks = list()
            for block_name in self._blocks:
                block = self.block_by_name(block_name)
                exported_blocks.append(block.export())
            export_data['pnm_blocks'] = exported_blocks

        return export_data

    def current_block(self, ignore_missing_block=False):
        """Retrieve reference on block which has been specified for this module run.

        Check module properties to find out name of block with which module should work at this moment.
        :type ignore_missing_block:  bool
        :param ignore_missing_block: Whether it is possible to ignore missing block or not.
        :rtype:  PubNubBlock
        :return: Reference on block model or 'None' in case if there is no block with specified name.
        """
        return self.block_by_name(block=self._module.params['block'], ignore_missing_block=ignore_missing_block)

    def block_by_name(self, block, ignore_missing_block=False):
        """Retrieve reference on one of keyset's block by it't name.

        :type block:                 str
        :param block:                Reference on name of block to which reference should be retrieved.
        :type ignore_missing_block:  bool
        :param ignore_missing_block: Whether it is possible to ignore missing block or not.
        :rtype:  PubNubBlock
        :return: Reference on one of keyset's block model or 'None' in case if there is no block with specified name.
        """
        self._fetch_blocks_if_required()
        block_model = self._blocks.get(block)
        if _is_empty(block_model) and not ignore_missing_block:
            self._module.fail_json(changed=self.changed(), msg="'{}' block doesn't exists.".format(block))

        return block_model

    def add_block(self, new_block):
        """Add new block to keyset.

        Create new block by user request and store it in keyset model.
        :type new_block:  PubNubBlock
        :param new_block: Reference on initialized new block which should be created.
        """
        self._fetch_blocks_if_required()
        created_block = self.block_by_name(block=new_block.name, ignore_missing_block=_is_empty(new_block.uid))
        if created_block is None:
            new_block.set_api_client(self._api)
            self._blocks[new_block.name] = new_block

    def replace_block(self, old_name, block, new_name=None):
        """Update block which is stored under specified keys.

        :type old_name:  str
        :param old_name: Reference on name under which 'block' should be stored.
        :type block:     PubNubBlock
        :param block:    Reference on PubNubBlock model instance which should be placed under specified 'old_name' or
                         'new_name' (if specified).
        :type new_name:  str
        :param new_name: Reference on name under which 'block' should be stored. If specified, block which is stored
                         under 'old_name' will be removed.
        """
        self._fetch_blocks_if_required()
        if not _is_empty(self._blocks):
            target_key = new_name if not _is_empty(new_name) else old_name
            if not _is_empty(new_name) and not _is_empty(old_name) and not _is_empty(self._blocks.get(old_name)):
                del self._blocks[old_name]
            self._blocks[target_key] = block

    def remove_block(self, block):
        """Remove block from keyset.

        Stop and remove target block if it exists.
        :type block:  PubNubBlock
        :param block: Reference on PubNubBlock model instance which should be removed.
        """
        self._fetch_blocks_if_required()
        if self.block_by_name(block=block.name, ignore_missing_block=True) is not None:
            block.delete()

    def save(self):
        """Store any changes to keyset and/or blocks."""
        if not _is_empty(self._blocks):
            blocks_for_removal = list()
            for block_name in self._blocks:
                block = self.block_by_name(block_name)
                if block.should_delete:
                    blocks_for_removal.append(block.name)
                block.save()
            for block_name in blocks_for_removal:
                del self._blocks[block_name]
            if not _is_empty(blocks_for_removal):
                self._changed = True

    def _fetch_blocks_if_required(self):
        """Fetch keyset's blocks if required.

        In case if this is first time when keyset is used blocks should be retrieved.
        """
        if self._blocks is None:
            self._process_blocks_data(blocks=self._api.fetch_blocks(self.uid))

    def _process_keyset_data(self, keyset):
        """Process fetched keyset data.

        Process received keyset data to complete model configuration.
        :type keyset:  dict
        :param keyset: Reference on dictionary which contain information about application's keyset.
        """
        if not _is_empty(keyset.get('pnm_blocks')):
            self._process_blocks_data(keyset.pop('pnm_blocks'))
        self._orig_service_data = copy.deepcopy(keyset)

    def _process_blocks_data(self, blocks, block_name=None):
        """Process fetched list of blocks.

        Process received blocks data to complete blocks models configuration.
        :type blocks:      list
        :param blocks:     Reference on list of dictionaries each of which represent block with event handlers.
        :type block_name:  str
        :param block_name: Reference on name of the only one block which should be parsed. If 'None' then all blocks
                           will be parsed.
        """
        if _is_empty(self._blocks):
            self._blocks = dict()

        for block in blocks:
            if block_name is None or PubNubBlock.name_from_payload(block) == block_name:
                block_model = PubNubBlock(self._module, keyset=self, api_client=self._api, block=block)
                self._blocks[block_model.name] = block_model
                if not _is_empty(block_name):
                    break


class PubNubBlock(object):
    """PubNub block representation model."""

    def __init__(self, module, keyset, api_client=None, block=None, name=None, description=None):
        """Construct block model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type keyset:       PubNubKeyset
        :param keyset:      Reference on keyset model to which block belong.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client. 'None' can be in case if block has been just created.
        :type block:        dict
        :param block:       PubNub service response with information about particular block. 'None' possible in case if
                            there is request to create new block.
        :type name:         str
        :param name:        Reference on name of block which should be created.
        :type description:  str
        :param description: Reference on bew block description.
        :rtype:  PubNubBlock
        :return: Initialized block model.
        """
        super(PubNubBlock, self).__init__()
        self._module = module
        self._changed = False
        self._api = api_client
        self._keyset = keyset
        self._orig_service_data = None
        self._block_data = None
        self._event_handlers = dict()
        self._should_delete = False
        if not _is_empty(block):
            self._process_block_data(block)
        else:
            self.name = name
            self.description = description

    @property
    def keyset(self):
        """Stores reference on keyset for which block has been created.

        :rtype:  PubNubKeyset
        :return: Reference on keyset model.
        """
        return self._keyset

    @property
    def payload(self):
        """Stores reference on block data structured as it required by PubNub service.

        :rtype:  dict
        :return: Block information in format which is known to PubNub service.
        """
        payload = dict()
        if not _is_empty(self._orig_service_data):
            payload.update(key_id=self.keyset.uid, block_id=self.uid, name=self.name, description=self.description)
        if not _is_empty(self._block_data):
            if not _is_empty(self._block_data.get('name')):
                payload['name'] = self._block_data['name']
            if not _is_empty(self._block_data.get('description')):
                payload['description'] = self._block_data['description']
        if _is_empty(payload.get('description')):
            payload['description'] = 'New block'

        return payload

    @property
    def uid(self):
        """Stores reference on unique block's identifier.

        :rtype:  int
        :return: Reference on unique block's identifier or 'None' in case if block model configuration not completed.
        """
        uid = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('id')):
            uid = self._orig_service_data['id']

        return uid

    @property
    def name(self):
        """Stores reference on block's name.

        :rtype:  str
        :return: Reference on block's name or 'None' in case if block model configuration not completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._block_data

        return data['name'] if not _is_empty(data) and not _is_empty(data.get('name')) else None

    @name.setter
    def name(self, name):
        """Update block's name.

        :type name:  str
        :param name: Reference on new block name.
        """
        if self._block_data is None:
            self._block_data = dict()
        self._block_data['name'] = name

    @property
    def description(self):
        """Stores reference on block's description.

        :rtype:  str
        :return: Reference on block's description or 'None' in case if block model configuration not completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._block_data

        return data['description'] if not _is_empty(data) and not _is_empty(data.get('description')) else None

    @description.setter
    def description(self, description):
        """Update block's description.

        :type description:  str
        :param description: Reference on new block's description.
        """
        if self._block_data is None:
            self._block_data = dict()
        self._block_data['description'] = description

    @property
    def state(self):
        """Stores reference on current block's state.

        :rtype:  str
        :return: Reference on block's state or 'None' in case if block model configuration not completed.
        """
        state = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('state')):
            state = self._orig_service_data['state']

        return state

    @property
    def target_state(self):
        """Stores reference on target block's state.

        :rtype:  str
        :return: Reference on block's state or 'None' in case if block model configuration not completed.
        """
        state = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('intended_state')):
            state = self._orig_service_data['intended_state']

        return state

    @target_state.setter
    def target_state(self, target_state):
        """Update block's target state.

        :type target_state:  str
        :param target_state: Reference on new block's target state.
        """
        if self._block_data is None:
            self._block_data = dict()
        self._block_data['intended_state'] = target_state

    @property
    def should_delete(self):
        """Stores whether block should be removed during save operation or not.

        Block removal will happen at the same moment when account will be asked to 'save' changes.
        """
        return self._should_delete

    @staticmethod
    def name_from_payload(payload):
        """Retrieve block's name from raw payload.

        :rtype:  str
        :return: Reference on block's name or 'None' in case if block model configuration not completed.
        """
        name = None
        if not _is_empty(payload) and not _is_empty(payload.get('name')):
            name = payload['name']

        return name

    def changed(self):
        """Check whether block's data has been changed or not.

        Whether something in block has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if block or event handlers data has been modified.
        """
        event_handlers_changed = False
        if not self._changed:
            for event_handler_name in self._event_handlers:
                event_handlers_changed = self.event_handler_by_name(event_handler_name).changed()
                if event_handlers_changed:
                    break

        return self._changed or event_handlers_changed

    def set_api_client(self, api_client):
        """Update information about API client which should be used by block.

        :type api_client:  PubNubAPIClient
        :param: api_client Reference on API access client. 'None' can be in case if block has been just created.
        """
        self._api = api_client
        for event_handler_name in self._event_handlers:
            self.event_handler_by_name(event_handler_name).set_api_client(api_client)

    def export(self):
        """Export block model.

        Export allow to receive object which can be used to re-use it with other pubnub modules call which will follow
        after this.
        :rtype:  dict
        :return: Dictionary which keyset application model with all it fields and values.
        """
        export_data = dict()
        if not _is_empty(self._orig_service_data):
            export_data.update(self._orig_service_data)
        if not _is_empty(self._block_data):
            export_data.update(self._block_data)
        if not _is_empty(self._event_handlers):
            exported_event_handlers = list()
            for event_handler_name in self._event_handlers:
                event_handler = self.event_handler_by_name(event_handler_name)
                exported_event_handlers.append(event_handler.export())
            export_data['event_handlers'] = exported_event_handlers

        return export_data

    def event_handler_by_name(self, event_handler):
        """Retrieve reference on event handler by it't name.

        :type event_handler:  str
        :param event_handler: Reference on name of event handler to which reference should be retrieved.
        :rtype:  PubNubEventHandler
        :return: Reference on block's event handler model or 'None' in case if there is no event handler with specified
                 name.
        """
        return self._event_handlers.get(event_handler)

    def apply_changes(self):
        """Update block information if required."""
        # Check whether block name should be changed or not.
        changes = self._module.params['changes']
        if not _is_empty(changes) and not _is_empty(changes.get('name')):
            self.name = changes['name']
            self._module.params['block'] = changes['name']
            self.keyset.replace_block(old_name=self.name, block=self, new_name=changes['name'])

    def start(self):
        """Start block if possible.

        Block start request will be sent only if target state not equal to 'running'.
        """
        self.target_state = 'running'

    def stop(self):
        """Stop block if possible.

        Block stop request will be sent only if target state not equal to 'stopped'.
        """
        self.target_state = 'stopped'

    def delete(self):
        """Remove block from keyset."""
        self._should_delete = True

    def update_event_handlers(self, event_handlers):
        """Update event handlers information if required.

        Use user-provided information to update event handlers.
        :type event_handlers:  list
        :param event_handlers: Reference on list of dictionaries which represent event handlers changes.
        """
        if self._will_change_event_handlers(event_handlers):
            for event_handler in event_handlers:
                event_handler_model = self.event_handler_by_name(PubNubEventHandler.name_from_payload(event_handler))
                # Create event handler if required.
                if event_handler_model is None:
                    event_handler_model = PubNubEventHandler(module=self._module, block=self, api_client=self._api,
                                                             event_handler=event_handler)
                    if not event_handler_model.should_delete:
                        self._event_handlers[event_handler_model.name] = event_handler_model
                elif event_handler_model.will_change_with_data(event_handler):
                    event_handler_model.update_with_data(event_handler)

    def save(self):
        """Save block changes.

        Depending on whether block existed before or not it may be created and updated if required.
        """
        will_change = self._should_create() or self.should_delete or self._should_save()
        block_data = self.payload
        if self._should_create():
            if not self._module.check_mode:
                block_data.update(self._api.create_block(keyset_id=self.keyset.uid, block_payload=block_data))
                block_data['block_id'] = block_data['id']
            else:
                block_data['id'] = 1616
        elif self.should_delete:
            self._change_block_state(state='stopped', update_cached_state=False)
            if not self._module.check_mode:
                self._api.delete_block(keyset_id=self.keyset.uid, block_id=self.uid)
        elif self._should_save():
            # Update block own information.
            if not self._module.check_mode:
                self._api.update_block(keyset_id=self.keyset.uid, block_id=self.uid, block_payload=block_data)
            block_data = self._orig_service_data
            block_data.update(self.payload)
            # Stop block in case if event_handlers modification is required.
            if self._will_change_event_handlers():
                self._change_block_state(state='stopped', update_cached_state=False)
            else:
                # Change block operation state as it has been requested during module call.
                self._change_block_state(state=self._block_data['intended_state'])

        if will_change:
            self._changed = True
            if not self.should_delete:
                if self._should_create():
                    block_data.update(dict(intended_state='stopped', state='stopped'))
                self._process_block_data(block_data)

        if self._will_change_event_handlers():
            event_handlers_for_removal = list()
            for event_handler_name in self._event_handlers:
                event_handler = self.event_handler_by_name(event_handler_name)
                if event_handler.should_delete:
                    event_handlers_for_removal.append(event_handler.name)
                event_handler.save()
            if not _is_empty(event_handlers_for_removal):
                self._changed = True

        if self._will_change_event_handlers():
            self._change_block_state(state=self._block_data['intended_state'])

    def _should_create(self):
        """Check whether block should be created or not.

        :rtype:  bool
        :return: 'True' in case if there is no raw data from PubNub service about this block.
        """
        return _is_empty(self._orig_service_data)

    def _should_save(self):
        """Check whether there is block changes which should be saved.

        :rtype:  bool
        :return: 'True' in case if there is unsaved changes.
        """
        should_save = self._should_create()
        if not should_save and not _is_empty(self._orig_service_data) and not _is_empty(self._block_data):
            should_save = cmp(self._orig_service_data, self._block_data) != 0

        return should_save

    def _will_change_event_handlers(self, event_handlers=None):
        """Check whether any block's event handler will change.

        Check whether any user-provided event handlers' data will cause their modification or not.
        :type event_handlers:  list
        :param event_handlers: Reference on list of dictionaries which represent event handlers changes.
        :rtype:  bool
        :return: 'True' in case if any portion of event blocks should be modified.
        """
        will_change = False
        if not _is_empty(event_handlers):
            for event_handler in event_handlers:
                eh = self.event_handler_by_name(PubNubEventHandler.name_from_payload(event_handler))
                will_change = eh.will_change_with_data(event_handler) if eh else eh is None
                if will_change:
                    break
        else:
            for event_handler_name in self._event_handlers:
                will_change = self.event_handler_by_name(event_handler_name).will_change_with_data()
                if will_change:
                    break

        return will_change

    def _change_block_state(self, state, update_cached_state=True):
        """Update actual block state.

        Perform block operation state change request and process service response.
        :type state:  str
        :param state: Reference on expected block operation state (running or stopped).
        :type update_cached_state:  bool
        :param update_cached_state: Whether desired block state should be modified as well (the one which is asked by
                                    user during module configuration).
        """
        if self._orig_service_data['intended_state'] != state or self._orig_service_data['state'] != state:
            current_state = state if self._orig_service_data['intended_state'] == state else None
            if not self._module.check_mode:
                operation = dict(running=self._api.start_block, stopped=self._api.stop_block)
                (timeout, error_reason, stack) = operation[state](keyset_id=self.keyset.uid, block_id=self.uid,
                                                                  current_state=current_state)
                self._handle_block_state_change(state='start' if state == 'running' else 'stop', timeout=timeout,
                                                error_reason=error_reason, stack=stack)
            self._orig_service_data['intended_state'] = state
            self._orig_service_data['state'] = state
            self._block_data['state'] = state
            if update_cached_state:
                self._block_data['intended_state'] = state

            if _is_empty(current_state):
                self._changed = True

    def _process_block_data(self, block):
        """Process fetched block data.

        Process received block data to complete model configuration.
        :type block:  dict
        :param block: Reference on dictionary which contain information about specific block.
        """
        if not _is_empty(block.get('event_handlers')):
            event_handlers = block.pop('event_handlers')
            for event_handler in event_handlers:
                event_handler_model = PubNubEventHandler(self._module, block=self, api_client=self._api,
                                                         event_handler=event_handler)
                self._event_handlers[event_handler_model.name] = event_handler_model
        self._orig_service_data = copy.deepcopy(block)
        self._block_data = copy.deepcopy(block)

    def _handle_block_state_change(self, state, timeout, error_reason, stack):
        """Handle block operation state change.

        :type state:         str
        :param state:        Target block state.
        :type timeout:       bool
        :param timeout:      Whether block state change failed by timeout or not.
        :type error_reason:  str
        :param error_reason: Field contain error reason description (if provided by PubNub service).
        :type stack:         str
        :param stack:        Reference on string which represent event handler execution stack trace.
        """
        error_message = None
        if timeout:
            delay = PN_BLOCK_STATE_CHECK_MAX_COUNT * PN_BLOCK_STATE_CHECK_INTERVAL
            error_message = '\'{}\' block not {}\'ed in {} seconds'.format(self.name, state, delay)
        elif not _is_empty(stack):
            error_message = 'Unable to {} \'{}\' block because of error: {}'.format(state, self.name, error_reason)

        if error_message:
            self._module.fail_json(changed=self.changed(), msg=error_message, stack=stack)


class PubNubEventHandler(object):
    """PubNub event handler representation model."""

    def __init__(self, module, block, api_client, event_handler):
        """Construct block model using service response.

        :type module:         AnsibleModule
        :param module:        Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type block:          PubNubBlock
        :param block:         Reference on block model to which event handler belong.
        :type api_client:     PubNubAPIClient
        :param: api_client    Reference on API access client.
        :type event_handler:  dict
        :param event_handler: PubNub service response with information about particular event handler.
        :rtype:  PubNubEventHandler
        :return: Initialized event handler model.
        """
        super(PubNubEventHandler, self).__init__()
        self._module = module
        self._changed = False
        self._api = api_client
        self._block = block
        self._orig_service_data = None
        self._event_handler_data = None
        self._state = 'present'
        self._should_delete = False
        self._process_event_handler_data(event_handler)

    @property
    def payload(self):
        """Stores reference on event handler data structured as it required by PubNub service.

        :rtype:  dict
        :return: Event handler information in format which is known to PubNub service.
        """
        payload = dict()
        if not _is_empty(self._orig_service_data):
            payload.update(key_id=self._block.keyset.uid, block_id=self._block.uid, name=self.name,
                           channels=self.channels, code=self.code, event=self.event,
                           type=self._orig_service_data['type'], output=self._orig_service_data['output'],
                           log_level=self._orig_service_data['log_level'])
        payload.update(self._event_handler_data)

        return payload

    @property
    def uid(self):
        """Stores reference on unique block's identifier.

        :rtype:  int
        :return: Reference on unique block's identifier or 'None' in case if event handler model configuration not
                 completed.
        """
        uid = None
        if not _is_empty(self._orig_service_data) and not _is_empty(self._orig_service_data.get('id')):
            uid = self._orig_service_data['id']

        return uid

    @property
    def name(self):
        """Stores reference on event handler's name.

        :rtype:  str
        :return: Reference on event handler's name or 'None' in case if event handler model configuration not completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._event_handler_data

        return data['name'] if not _is_empty(data) and not _is_empty(data.get('name')) else None

    @name.setter
    def name(self, name):
        """Update event handler's name.

        :type name:  str
        :param name: Reference on new event handler name.
        """
        if self._event_handler_data is None:
            self._event_handler_data = dict()
        self._event_handler_data['name'] = name

    @property
    def code(self):
        """Stores reference on event handler's code.

        :rtype:  str
        :return: Reference on event handler's code or 'None' in case if event handler model configuration not completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._event_handler_data

        return data['code'] if not _is_empty(data) and not _is_empty(data.get('code')) else None

    @code.setter
    def code(self, name):
        """Update event handler's code.

        :type name:  str
        :param name: Reference on new event handler code.
        """
        if self._event_handler_data is None:
            self._event_handler_data = dict()
        self._event_handler_data['code'] = name

    @property
    def channels(self):
        """Stores reference on event handler's trigger channel.

        :rtype:  str
        :return: Reference on event handler's trigger channel or 'None' in case if event handler model configuration not
                 completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._event_handler_data

        return data['channels'] if not _is_empty(data) and not _is_empty(data.get('channels')) else None

    @channels.setter
    def channels(self, channels):
        """Update event handler's trigger channel.

        :type channels:  str
        :param channels: Reference on new event handler trigger channel.
        """
        if self._event_handler_data is None:
            self._event_handler_data = dict()
        self._event_handler_data['channels'] = channels

    @property
    def event(self):
        """Stores reference on event handler's trigger event.

        :rtype:  str
        :return: Reference on event handler's trigger event or 'None' in case if event handler model configuration not
                 completed.
        """
        data = self._orig_service_data if not _is_empty(self._orig_service_data) else self._event_handler_data

        return data['event'] if not _is_empty(data) and not _is_empty(data.get('event')) else None

    @event.setter
    def event(self, event):
        """Update event handler's trigger event.

        :type event:  str
        :param event: Reference on new event handler trigger event.
        """
        if self._event_handler_data is None:
            self._event_handler_data = dict()
        self._event_handler_data['event'] = event

    @staticmethod
    def name_from_payload(payload):
        """Retrieve event handler's name from raw payload.

        :rtype:  str
        :return: Reference on event handler's name or 'None' in case if block model configuration not completed.
        """
        name = None
        if not _is_empty(payload) and not _is_empty(payload.get('name')):
            name = payload['name']

        return name

    @property
    def should_delete(self):
        """Stores whether event handler should be removed during save operation or not.

        Block removal will happen at the same moment when block will be asked to 'save' changes.
        """
        return self._should_delete

    def changed(self):
        """Check whether event handler's data has been changed or not.

        Whether something in block has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if event handler data has been modified.
        """
        return self._changed

    def set_api_client(self, api_client):
        """Update information about API client which should be used by event handler.

        :type api_client:  PubNubAPIClient
        :param: api_client Reference on API access client..
        """
        self._api = api_client

    def export(self):
        """Export event handler model.

        Export allow to receive object which can be used to re-use it with other pubnub modules call which will follow
        after this.
        :rtype:  dict
        :return: Dictionary which keyset application model with all it fields and values.
        """
        export_data = dict()
        if not _is_empty(self._orig_service_data):
            export_data.update(self._orig_service_data)
        export_data.update(self._event_handler_data)

        return export_data

    def will_change_with_data(self, event_handler=None):
        """Check whether receiver handler can be updated with provided data.

        Check whether any portion of event handler can be updated with user-provided information or not.
        :type event_handler:  dict
        :param event_handler: Reference on dictionary which represent event handler changes.
        :rtype:  bool
        :return: 'True' in case if any portion of event handler require modification.
        """
        should_update = _is_empty(self._orig_service_data) and not _is_empty(self._event_handler_data)
        if not should_update and not _is_empty(event_handler):
            # Retrieve user-provided handler information.
            fields = ['name', 'src', 'channels', 'event']
            (name, src_path, channels, event) = tuple(_values_for_keys(event_handler, keys=fields))
            if not _is_empty(event_handler.get('changes')) and not _is_empty(event_handler['changes'].get('name')):
                name = event_handler['changes']['name']
            should_update = name != self.name or not _is_empty(event) and event != self.event
            should_update = should_update or not _is_empty(channels) and channels != self.channels
            if not should_update:
                code = _content_of_file_at_path(src_path)
                should_update = not _is_empty(code) and code != self.code
            handler_state = event_handler['state'] if not _is_empty(event_handler.get('state')) else 'present'
            should_update = should_update or handler_state == 'absent'
        elif not should_update and not _is_empty(self._orig_service_data) and not _is_empty(self._event_handler_data):
            should_update = cmp(self._orig_service_data, self._event_handler_data) != 0

        return should_update

    def update_with_data(self, event_handler):
        """Update handler data.

        :type event_handler:  dict
        :param event_handler: Reference on dictionary which represent event handler changes.
        """
        handler_state = event_handler['state'] if not _is_empty(event_handler.get('state')) else 'present'
        if handler_state != 'absent':
            # Retrieve user-provided handler information.
            fields = ['name', 'src', 'channels', 'event']
            (name, src_path, channels, event) = tuple(_values_for_keys(event_handler, keys=fields))
            if not _is_empty(event_handler.get('changes')) and not _is_empty(event_handler['changes'].get('name')):
                name = event_handler['changes']['name']
            self.name = name
            if not _is_empty(channels):
                self.channels = channels
            if not _is_empty(event):
                self.event = event
            code = _content_of_file_at_path(src_path)
            if not _is_empty(code):
                self.code = code
        else:
            self._should_delete = True

    def save(self):
        """Save event handler's changes.

        Depending on whether event handler existed before or not it may be created and updated if required.
        """
        will_change = self._should_create() or self.should_delete or self.will_change_with_data()
        handler_data = self.payload
        # Create new event handler if required.
        if self._should_create():
            fields = ['name', 'channels', 'event', 'code']
            handler_data.update(self._default_handler_payload())
            (name, channels, event, code) = _values_for_keys(handler_data, fields)
            if not _is_empty(name) and not _is_empty(channels) and not _is_empty(event) and not _is_empty(code):
                if not self._module.check_mode:
                    handler_data.update(self._api.create_event_handler(keyset_id=self._block.keyset.uid,
                                                                       payload=handler_data))
                else:
                    handler_data['id'] = 1617
                self._changed = True
            else:
                missed_fields = list()
                missed_fields.append('name') if _is_empty(name) else None
                missed_fields.append('channels') if _is_empty(channels) else None
                missed_fields.append('code') if _is_empty(code) else None
                missed_fields.append('event') if _is_empty(event) else None
                error_message = 'Unable create event handler w/o following fields: {}.'.format(', '.join(missed_fields))
                self._module.fail_json(changed=self.changed(), msg=error_message)
        elif self.should_delete:
            if not self._module.check_mode:
                self._api.delete_event_handler(keyset_id=self._block.keyset.uid, handler_id=self.uid)
            self._changed = True
        elif self.will_change_with_data():
            if not self._module.check_mode:
                self._api.update_event_handler(keyset_id=self._block.keyset.uid, handler_id=self.uid,
                                               payload=handler_data)
            handler_data = self._orig_service_data
            handler_data.update(self.payload)

        if will_change:
            self._changed = True
            if not self.should_delete:
                self._process_event_handler_data(handler_data)

    def _should_create(self):
        """Check whether event handler should be created or not.

        :rtype:  bool
        :return: 'True' in case if this is new event handler (doesn't have unique identifier assigned by PubNub
                 service).
        """
        return _is_empty(self._orig_service_data)

    def _process_event_handler_data(self, event_handler):
        # Check whether event handler payload belong to new handler or not.
        event_handler_exists = not _is_empty(event_handler.get('id'))
        handler_state = event_handler['state'] if not _is_empty(event_handler.get('state')) else 'present'
        if not event_handler_exists and handler_state == 'present':
            (name, channels, event, src_path) = _values_for_keys(event_handler, ['name', 'channels', 'event', 'src'])
            if not _is_empty(event_handler.get('changes')) and not _is_empty(event_handler['changes'].get('name')):
                name = event_handler['changes']['name']
            code = _content_of_file_at_path(src_path)
            if not _is_empty(name) and not _is_empty(channels) and not _is_empty(event) and not _is_empty(code):
                self._state = 'present'
                self._event_handler_data = dict(name=name, channels=channels, event=event, code=code)
        elif event_handler_exists:
            self._state = handler_state
            self._should_delete = True if self._state == 'absent' else False
            self._orig_service_data = copy.deepcopy(event_handler)
            self._event_handler_data = copy.deepcopy(event_handler)

    def _default_handler_payload(self):
        """Compose default payload for event handler create / update.

        Payload include application-wide information and doesn't depend from particular event handler configuration.
        :rtype:  dict
        :return: Initial payload dictionary which can be used for event handler manipulation requests.
        """
        return dict(key_id=self._block.keyset.uid, block_id=self._block.uid,
                    log_level='debug', output="output-{}".format(random.random()), type='js')


class PubNubEndpoint(object):
    """Endpoint path constructor.

    Instance allow to build relative REST API endpoint path.
    """

    @staticmethod
    def account():
        """Provide endpoint to get account information."""
        return '/me'

    @staticmethod
    def applications(identifier):
        """Provide endpoint to get list of registered applications.

        :type identifier:  int
        :param identifier: Reference on unique identifier of authorized user for which applications should be retrieved.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        return PubNubEndpoint._endpoint_with_query(endpoint='/apps', query=dict(owner_id=identifier))

    @staticmethod
    def block(keyset_id, block_id=None):
        """Provide endpoint to get block information.

        Endpoint allow to retrieve information about specific block or all blocks registered for keyset (if 'block_id'
        is 'None').
        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which list of blocks should be
                          retrieved.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block for which information should be retrieved.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        endpoint = '/v1/blocks/key/{}/block'.format(keyset_id)
        if not _is_empty(block_id):
            endpoint = '{}/{}'.format(endpoint, block_id)

        return endpoint

    @staticmethod
    def block_state(keyset_id, block_id, state):
        """Provide endpoint which will allow change current block operation mode.

        Endpoint allow to retrieve information about specific block or all blocks registered for keyset (if 'block_id'
        is 'None').
        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which block state should be
                          changed.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block for which operation state should be changed.
        :type state:      str
        :param state:     Reference to one of possible block operation states: start, stop.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        return '{}/{}'.format(PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id), state)

    @staticmethod
    def event_handler(keyset_id, handler_id=None):
        """Provide endpoint which allow block's event handlers manipulation.

        :type keyset_id:   int
        :param keyset_id:  Reference on unique identifier of application's keyset for which event handler access
                           required.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of block's event handler.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        endpoint = '/v1/blocks/key/{}/event_handler'.format(keyset_id)
        if not _is_empty(handler_id):
            endpoint = '{}/{}'.format(endpoint, handler_id)

        return endpoint

    @staticmethod
    def _endpoint_with_query(endpoint, query):
        """Add if required list of query parameters to API endpoint

        :type endpoint:  str
        :param endpoint: Reference on REST API endpoint to which list of query parameters should be appended.
        :type query:     dict
        :param query:    Reference on dictionary which represent key/value pairs for query string which will be
                         appended to API endpoint string.
        :rtype:  str
        :return: Reference on string which is composed from API endpoint path components and query string.
        """
        return '{}?{}'.format(endpoint, PN_URLENCODE(query))


class PubNubAPIClient(object):
    """PubNub REST API access client.

    Class provide access to set of API endpoints which allow to manage blocks.
    """

    def __init__(self, module, account):
        """Client provide entry point to interact with PubNub REST API by performing authorized requests.

        :type module:   AnsibleModule
        :param module:  Reference on initialized AnsibleModule which provide some initial functionality to module.
        :type account:  PubNubAccount
        :param account: Reference on model which is used along with API client to get access to REST API.
        :rtype:  PubNubAPIClient
        :return: Configured and ready to use REST API client.
        """
        super(PubNubAPIClient, self).__init__()
        self.module = module
        self.account = account
        self.state_changed = False
        self._session = None
        self.application = dict()

    @staticmethod
    def authorization_fields():
        """List of fields which is required to authorize API call and start new session.

        :rtype: dict
        :return: Dictionary with expected module arguments requirements.
        """
        return dict(email=dict(default='', required=False, type='str'),
                    pwd=dict(default='', required=False, type='str', no_log=True))

    @property
    def session(self):
        """Stores reference on started session identifier.
        :rtype:  str
        :return: Reference on started session identifier or 'None' if there is no registered session.
        """
        return self._session

    @session.setter
    def session(self, session):
        """Update active session identifier

        :type session:  str
        :param session: Reference on started session identifier.
        """
        self._session = session

    def start_session(self, email, pwd):
        """Start new PubNub block management API access session using provided account credentials.
        :type email:  str
        :param email: Email of account for which REST API calls should be authorized.
        :type pwd:    str
        :param pwd:   Account's password.
        :rtype:  dict
        :return: Reference on dictionary which contain information about authorized account.
        """
        response = self.request(api_endpoint=PubNubEndpoint.account(), http_method='POST',
                                data=dict(email=email, password=pwd))
        self._session = response['result']['token']

        return response['result']

    def fetch_applications(self, account_id):
        """Fetch information about list of applications / keys which has been created.

        :type account_id:  int
        :param account_id: Reference on uniquie authorized account identifier for which list if registered applications
                           should be received.
        :rtype:  list
        :return: Reference on list of dictionaries which represent list of registered applications for authorized
                 account.
        """
        # Send account information audit request.
        response = self.request(api_endpoint=PubNubEndpoint.applications(account_id), http_method='GET')

        return response['result'] if not _is_empty(response.get('result')) else list()

    def fetch_blocks(self, keyset_id):
        """Retrieve list of blocks created for keyset.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which list of blocks should be
                          retrieved.
        :rtype:  list
        :return: Reference on list of dictionaries each represent particular block with event handlers information.
        """
        # Send blocks information audit request.
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id), http_method='GET')

        return response['payload']

    def fetch_block(self, keyset_id, block_id):
        """Retrieve information about specific block.

        Request allow to get smaller amount of information with request performed against concrete block using it's ID.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be retrieved.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be retrieved.
        :rtype:  dict
        :return: Reference on dictionary which represent particular block with event handlers information.
        """
        # Send block audit request.
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id),
                                http_method='GET')
        block = response['payload']

        return block[0] if not _is_empty(block) else list()

    def create_block(self, keyset_id, block_payload):
        """Create new block using initial payload.

        New block can be created with minimal block information (name and/ description).
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which new block should be created.
        :type block_payload:  dict
        :param block_payload: Reference on payload which should be pushed to PubNub REST API to create new block.
        :rtype:  dict
        :return: Reference on dictionary which contain block information provided by PubNub service.
        """
        # Prepare new block payload
        payload = dict(key_id=keyset_id)
        payload.update(block_payload)
        # Create new block
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id), http_method='POST',
                                data=payload)

        return response['payload']

    def update_block(self, keyset_id, block_id, block_payload):
        """Update block information using data from payload.

        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be updated.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block for which changes should be done.
        :type block_payload:  dict
        :param block_payload: Reference on payload which contain changed for block.
        """
        # Prepare new block payload
        payload = dict(key_id=keyset_id, block_id=block_id)
        payload.update(block_payload)
        payload['id'] = block_id
        # Update block information
        self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id), http_method='PUT',
                     data=payload)

    def delete_block(self, keyset_id, block_id):
        """Remove block from keyset.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of keyset from which block should be removed.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block which should be removed.
        """
        # Remove block from keyset.
        self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id), http_method='DELETE')

    def start_block(self, keyset_id, block_id, current_state=None):
        """Start target block.

        Client will try to start specific block and verify operation success by requesting updated block information.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be started.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be started.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if it reached, change
                              request won't be sent and only wait for transition to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block starting results.
        """
        return self._set_block_operation_state(keyset_id=keyset_id, block_id=block_id, state='start',
                                               current_state=current_state)

    def stop_block(self, keyset_id, block_id, current_state=None):
        """Start target block.

        Client will try to start specific block and verify operation success by requesting updated block information.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset from which block should be stopped.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be stopped.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if it reached, change
                              request won't be sent and only wait for transition to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block stopping results.
        """
        return self._set_block_operation_state(keyset_id=keyset_id, block_id=block_id, state='stop',
                                               current_state=current_state)

    def _set_block_operation_state(self, keyset_id, block_id, state, current_state=None):
        """Update current block's operation state.

        Depending from requested state block can be stopped or started.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset from which block should be removed.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be removed.
        :type state:          str
        :param state:         Reference on new block state to which it should be switched.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if it reached, change
                              request won't be sent and only wait for transition to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block operation state change.
        """
        timeout = False
        in_transition = current_state is not None and current_state == ('running' if state == 'start' else 'stopped')
        error_reason = None
        stack = None
        if not in_transition:
            response = self.request(api_endpoint=PubNubEndpoint.block_state(keyset_id=keyset_id, block_id=block_id,
                                                                            state=state),
                                    http_method='POST', ignored_status_codes=[409])
        else:
            response = None

        if in_transition or response['status'] != 409:
            check_count = 0
            block = self.fetch_block(keyset_id=keyset_id, block_id=block_id)
            # Block require some time to change it's state, so this while loop will check it few times after
            # specified interval. In case if after fixed iterations count state still won't be same as requested it
            # will report error.
            while block['state'] != block['intended_state']:
                check_count += 1
                if check_count != PN_BLOCK_STATE_CHECK_MAX_COUNT:
                    time.sleep(PN_BLOCK_STATE_CHECK_INTERVAL)
                    block = self.fetch_block(keyset_id=keyset_id, block_id=block_id)
                else:
                    timeout = True
                    break
        else:
            stack = 'Not available'
            if not _is_empty(response.get('message')):
                service_message = response['message']
                if not _is_empty(service_message.get('text')):
                    error_reason = service_message['text']
                if not _is_empty(service_message.get('stack')):
                    stack = service_message['stack']
        return timeout, error_reason, stack

    def create_event_handler(self, keyset_id, payload):
        """Create new event handler for block.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of keyset for which event handler should be created for target
                          block.
        :type payload:    dict
        :param payload:   Reference on new event handler payload.
        """
        # Send event handler creation request
        response = self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id), http_method='POST',
                                data=payload)

        return response['payload']

    def update_event_handler(self, keyset_id, handler_id, payload):
        """Update event handler's event data.

        Use provided information to update event handler behaviour and data processing flow (handler code).
        :type keyset_id:   int
        :param keyset_id:  Reference on unique identifier of keyset for which event handler data should be updated.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of event handler which should be updated.
        :type payload:     dict
        :param payload:    Reference on updated event handler payload.
        :rtype:  dict
        :return: Reference on dictionary which contain handler information provided by PubNub service.
        """
        # Append handler identifier to payload.
        payload['id'] = handler_id
        # Update event handler information.
        self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id, handler_id=handler_id),
                     http_method='PUT', data=payload)

    def delete_event_handler(self, keyset_id, handler_id):
        """Remove event handler from target block.

        :type keyset_id:   int
        :param keyset_id:  Reference on unique identifier of keyset from which event handler data should be removed.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of event handler which should be removed.
        """
        self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id, handler_id=handler_id),
                     http_method='DELETE')

    def request(self, api_endpoint, http_method='GET', data=None, ignored_status_codes=list()):
        """Construct request to get access to PubNub's REST API and pre-process service response.

        :type  api_endpoint:         str
        :param api_endpoint:         Represent URI path to REST API endpoint (relative to base API URL
                                     'PUBNUB_API_URL').
        :type  http_method:          str
        :param http_method:          Represent HTTP request method (GET, POST, PUT, DELETE).
        :type  data:                 dict
        :param data:                 Data which should be sent with in case if 'POST' has been passed to 'method'.
        :type  ignored_status_codes: list
        :param ignored_status_codes: Status code numbers which shouldn't be handled as error during initial request
                                     processing.
        :rtype:                      dict
        :return:                     PubNub API processing results.
        """
        url = "{}{}".format(PUBNUB_API_URL, api_endpoint)
        headers = {'Accept': 'application/json'}
        if ZLIB_AVAILABLE:
            headers.update({'Accept-Encoding': 'gzip,deflate'})
        if not _is_empty(data):
            headers.update({'Content-Type': 'application/json'})

        # Authorize request if required.
        if not _is_empty(self.session):
            headers['X-Session-Token'] = self.session

        # Prepare POST data if required (if provided).
        json_data = self.module.jsonify(data) if not _is_empty(headers.get('Content-Type')) else None

        response = None
        error_message = None
        res_stream, res_inf = fetch_url(self.module, url=url, data=json_data, headers=headers, method=http_method,
                                        force=True)
        if res_inf['status'] >= 400 and res_inf['status'] not in ignored_status_codes:
            # Process API call error.
            descr = None
            try:
                descr = self.module.from_json(res_inf.get('body')) if not _is_empty(res_inf.get('body')) else None
            except ValueError:
                error_message = res_inf.get('body')
            if not _is_empty(descr):
                error_message = descr.get('message')
        elif _is_empty(res_stream):
            error_message = '{} ({})'.format(res_inf['msg'], res_inf['url'])
        else:
            raw_response = _decompress_if_possible(res_stream.read(), res_inf)
            if _is_empty(raw_response):
                error_message = 'Unexpected response: Empty PubNub service response.'
            else:
                try:
                    response = self.module.from_json(raw_response)
                except ValueError:
                    error = sys.exc_info()[1]
                    error_message = "Unexpected response: %s. Received response: %s" % (error.message, raw_response)
        if not _is_empty(error_message):
                self.module.fail_json(changed=self.state_changed, msg=error_message, url=res_inf['url'],
                                      status=res_inf['status'], post_body=data, module_cache=self.account.export())

        return response


def _is_empty(val):
    """
    Check whether specified value is 'empty' (not set or doesn't contain any data).
    :param val: Reference on value against which check should be done.
    :rtype:  bool
    :return: 'True' in case if specified value is 'empty'
    """
    return val is None or not val


def _values_for_keys(dct, keys):
    """Extract values for specified list of fields.

    Try get from  passed 'dict' all values which is stored under specified 'keys'.
    :type dct:   dict
    :param dct:  Reference on dictionary from which values should be retrieved.
    :type keys:  list
    :param keys: Reference on list of
    :return:
    """
    values = list()
    for key in keys:
        values.append(dct.get(key))

    return values


def _content_of_file_at_path(path):
    """Read file content.

    Try read content of file at specified path.
    :type path:  str
    :param path: Full path to location of file which should be read'ed.
    :rtype:  content
    :return: File content or 'None'
    """
    content = None
    if not _is_empty(path) and os.path.exists(to_bytes(path)):
        with open(to_bytes(path), mode="r") as opened_file:
            b_content = opened_file.read()
            try:
                content = to_text(b_content, errors='surrogate_or_strict')
            except UnicodeError:
                pass

    return content


def _decompress_if_possible(data, information):
    """Try decompress provided data.

    Depending from whether 'zlib' module available or not provided data can be decompressed or returned as-is.
    :type  data:  str
    :param data: Reference on object which should be decompressed if possible.
    :type information:  dict
    :param information: Reference on dictionary which contain additional information about processed data.
    :rtype:  str
    :return: Decompressed object content or same object if 'zlib' not available.
    """
    data_compressed = information.get('content-encoding') in ['gzip', 'deflate']
    return zlib.decompress(data, 16 + zlib.MAX_WBITS) if data_compressed else data


def main():
    fields = PubNubAPIClient.authorization_fields()
    fields.update(dict(application=dict(required=True, type='str'), keyset=dict(required=True, type='str'),
                       state=dict(default='present', type='str', choices=['start', 'stop', 'present', 'absent']),
                       block=dict(required=True, type='str'), description=dict(type='str'),
                       event_handlers=dict(default=list(), type='list'), changes=dict(default=dict(), type='dict'),
                       cache=dict(default=dict(), type='dict'), validate_certs=dict(default=True, type='bool')))
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

    module_cache = None
    if not _is_empty(module.params.get('cache')) and not _is_empty(module.params['cache'].get('module_cache')):
        module_cache = copy.deepcopy(module.params['cache']['module_cache'])
    account = PubNubAccount(module, cache=module_cache)
    if _is_empty(module_cache):
        if not _is_empty(module.params['email']) and not _is_empty(module.params['pwd']):
            account.login(email=module.params['email'], pwd=module.params['pwd'])
        else:
            module.fail_json(msg='Missing account credentials.',
                             description='It looks like not account credentials has been passed or \'cache\' field ' +
                                         'doesn\'t have result of previous module call.')
    # Retrieve reference on target application (the one which user decided to manage).
    application = account.current_application()
    application.active_keyset = application.current_keyset()

    # Retrieve reference on target block (the one which used decided to manager).
    expect_block_to_exist = module.params['state'] in ['start', 'stop']
    block = application.active_keyset.current_block(not expect_block_to_exist)
    is_new_block = _is_empty(block) and module.params['state'] != 'absent'

    # Create new block if required.
    if is_new_block:
        description = module['description'] if not _is_empty(module.params.get('description')) else 'New block'
        block = PubNubBlock(module=module, keyset=application.active_keyset, name=module.params['block'],
                            description=description)
        application.active_keyset.add_block(block)

    # Remove block if required.
    if module.params['state'] == 'absent' and not _is_empty(block):
        application.active_keyset.remove_block(block)
        block = None

    if not _is_empty(block):
        # Apply block changed if required.
        block.apply_changes()

        # Update event-handlers if required.
        block.update_event_handlers(module.params['event_handlers'])

    # Update block operation state if required.
    if not _is_empty(block) and not is_new_block:
        if module.params['state'] == 'start':
            block.start()
        elif module.params['state'] == 'stop':
            block.stop()
    account.save()

    module.exit_json(changed=account.changed(), module_cache=account.export())


if __name__ == '__main__':
    main()
