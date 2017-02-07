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
                    'supported_by': 'committer',
                    'version': '1.0'}


DOCUMENTATION = '''
---
module: pubnub_blocks
version_added: '2.2'
short_description: PubNub blocks management module.
description:
  - "This module allows Ansible to interface with the PubNub BLOCKS infrastructure with functionality to create, remove, start, stop rename blocks and create,
  modify and remove event handlers"
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
  password:
    description:
      - Password which match to account to which specified C(email) belong.
      - Not required if C(cache) contains result of previous module call (in same play).
    required: false
  cache:
    description: >
       In case if single play use blocks management module few times it is preferred to enabled \'caching\' by making previous module to share gathered
       artifacts and pass them to this parameter.
    required: false
    default: {}
  application:
    description:
      - Name of target PubNub application for which blocks configuration on specific C(keyset) will be done.
    required: true
  keyset:
    description:
      - Name of application\'s keys set which is bound to managed blocks.
    required: true
  state:
    description:
      - Intended block state after event handlers creation / update process will be completed.
    required: false
    default: \'start\'
    choices: [\'start\', \'stop\', \'present\', \'absent\']
  name:
    description:
      - Name of managed block which will be later visible on admin.pubnub.com.
    required: true
  description:
    description:
        - "Short block description which will be later visible on admin.pubnub.com. Used only if block doesn\'t exists and won\'t change description for
        existing block."
    required: false
    default: \'New block\'
  event_handlers:
    description:
      - List of event handlers which should be updated for specified block C(name).
      - "Each entry for new event handler should contain: C(name), C(src), C(channels), C(event). C(name) used as event handler name which can be used later to
      make changes to it."
      - C(src) is full path to file with event handler code.
      - C(channels) is name of channel from which event handler is waiting for events.
      - "C(event) is type of event which is able to trigger event handler: I(js-before-publish), I(js-after-publish), I(js-after-presence)."
      - "Each entry for existing handlers should contain C(name) (so target handler can be identified). Rest parameters (C(src), C(channels) and C(event)) can
      be added if changes required for them."
      - "It is possible to rename event handler by adding C(changes) key to event handler payload and pass dictionary, which will contain single key C(name),
      where new name should be passed."
      - To remove particular event handler it is possible to set C(state) for it to C(absent) and it will be removed.
    required: false
    default: []
  changes:
    description:
      - List of fields which should be changed by block itself (doesn\'t affect any event handlers).
      - "Possible options for change is: C(name)."
    required: false
    default: {}
  validate_certs:
    description:
      - "This key allow to try skip certificates check when performing REST API calls. Sometimes host may have issues with certificates on it and this will
      cause problems to call PubNub REST API."
      - If check should be ignored C(False) should be passed to this parameter.
    required: false
    default: true
'''

EXAMPLES = '''
# Event handler create example.
- name: Create single event handler
  pubnub_blocks:
    email: '{{ email }}'
    password: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    name: '{{ block_name }}'
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
    password: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    name: '{{ block_name }}'
    event_handlers:
      -
        name: '{{ handler_name }}'
        event: 'js-after-publish'

# Stop block and event handlers.
- name: Stopping block
  pubnub_blocks:
    email: '{{ email }}'
    password: '{{ password }}'
    application: '{{ app_name }}'
    keyset: '{{ keyset_name }}'
    name: '{{ block_name }}'
    state: stop

# Multiple module calls with cached result passing
- name: Create '{{ block_name }}' block
      register: module_cache
      pubnub_blocks:
        email: '{{ email }}'
        password: '{{ password }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        name: '{{ block_name }}'
        state: present
    - name: Add '{{ event_handler_1_name }}' event handler to '{{ block_name }}'
      register: module_cache
      pubnub_blocks:
        cache: '{{ module_cache }}'
        application: '{{ app_name }}'
        keyset: '{{ keyset_name }}'
        name: '{{ block_name }}'
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
        name: '{{ block_name }}'
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
        name: '{{ block_name }}'
        state: start
'''

RETURN = '''
module_cache:
  description: "Cached account information. In case if with single play module used few times it is better to pass cached data to next module calls to speed up
  process."
  type: dict
'''

PUBNUB_API_URL = "https://admin.pubnub.com/api"
PN_BLOCK_STATE_CHECK_INTERVAL = 1
PN_BLOCK_STATE_CHECK_MAX_COUNT = 30
# Import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import *
from ansible.module_utils.urls import *
from ansible.module_utils.six.moves.urllib.parse import urlencode
try:
    import zlib
    ZLIB_AVAILABLE = True
except ImportError:
    ZLIB_AVAILABLE = False
import random
import copy
import time


class PubNubAccount(object):
    """PubNub account representation model."""

    def __init__(self, module, cache=None):
        """Construct account model using service response.

        :type module:   AnsibleModule
        :param module:  Reference on initialized AnsibleModule which provide some initial
                        functionality to module.
        :type cache:    dict
        :param cache:   Reference on dictionary which represent previously exported account model
                        (previous model run). 'None' can be passed in case if this is first module
                        run or cached data not provided (maybe single module call).
        :rtype:  PubNubAccount
        :return: Initialized account data model.
        """
        super(PubNubAccount, self).__init__()
        self._module = module
        self._api = PubNubAPIClient(module=module, account=self)
        self._service_data = None
        """:type : dict"""
        self._apps = dict()
        self._restore(cache)

    def keys(self):
        """Retrieve list of account fields.

        This method used to find out list of fields which should be inside of dict after account
        will be serialized to it.
        :rtype:  list
        :return: List of keys which represent account.
        """
        keys = list()
        if self._service_data:
            keys = list(self._service_data.keys()) + ['pnm_applications']

        return keys

    def __getitem__(self, item):
        """Retrieve value for requested item.

        Provide values which should be placed inside of dictionary which represent account. In case
        if applications list requested it will be additionally pre-processed to serialize
        application models.
        :type item:  str
        :param item: Reference on string which represent key under which stored value which should
                     be serialized as part of account entry.
        :return: One of fields which is stored for account.
        """
        if item != 'pnm_applications':
            value = self._service_data.get(item)
        else:
            value = list(dict(application) for application in self.applications)

        return value

    @property
    def uid(self):
        """Stores reference on unique account identifier.

        :rtype:  int | None
        :return: Reference on unique user identifier or 'None' in case if account model
                 configuration not completed.
        """
        uid = _object_value(obj=self._service_data, key='user.id')
        return int(uid) if uid is not None else uid

    @property
    def email(self):
        """Stores reference on account's owner email address.

        :rtype:  str
        :return: Reference on account's owner email address or 'None' in case if account model
                 configuration not completed.
        """
        return _object_value(obj=self._service_data, key='user.email')

    @property
    def applications(self):
        """Stores reference on list of application models.

        All applications which is registered for this account represented by models and stored in
        this property.
        :rtype:  list[PubNubApplication]
        :return: List of application models.
        """
        return list(self._apps[name] for name in self._apps if self._apps.get(name))

    @property
    def current_application(self):
        """Retrieve reference on application which has been specified for this module run.

        Check module properties to find out name of application with which module should work at
        this moment.
        :rtype:  PubNubApplication
        :return: Reference on registered application model or 'None' in case if there is no
                 application with specified name.
        """
        application = self._apps.get(self._module.params['application'])
        if application is None:
            error_fmt = 'There is no \'{0}\' application for {1}. Make sure what correct ' + \
                        'application name has been passed. If application doesn\'t exist you ' + \
                        'can create it on admin.pubnub.com.'
            self._module.fail_json(msg=error_fmt.format(application, self.email),
                                   changed=self.changed)

        return application

    @property
    def changed(self):
        """Stores whether something changed in account's data.

        :rtype:  bool
        :return: 'True' in case if account or application data has been modified.
        """
        changed = False
        for application in self.applications:
            changed = application.changed
            if changed:
                break

        return changed

    def login(self, email, password):
        """Start new PubNub block management API access session using provided account credentials.

        :type email:     str
        :param email:    Email of account for which REST API calls should be authorized.
        :type password:  str
        :param password: Account's password.
        """
        # Authorize with account's credentials and complete account model configuration.
        self._process_data(account=self._api.start_session(email=email, password=password))
        # Fetch and process list of registered applications.
        self._process_data(applications=self._api.fetch_applications(account_id=self.uid),
                           initial=True)

    def save(self):
        """Store any changes to account and related data structures.

        If account or any related to current module run component has been changed it should be
        saved using REST API.
        """
        for application in self.applications:
            application.save()

    def _restore(self, cache):
        """Restore account data model.

        Module allow to export cached results and their re-usage with next module call. Restore
        allow to speed up module execution, because some REST API calls is pretty slow.
        :type cache:  dict
        :param cache: Reference on dictionary which contain information from previous module run and
                      allow to restore account model to it's latest state.
        """
        if cache:
            cached_apps = cache.get('pnm_applications')
            apps = cache.pop('pnm_applications') if cached_apps is not None else list()
            self._process_data(account=cache, applications=apps)

            # Update session information for API.
            self._api.session = self._session = _object_value(obj=cache, key='token')

    def _process_data(self, account=None, applications=None, initial=False):
        """Process service / cached data to condfigure account data model.

        Configure or restore account model from previous module run using exported data. Restore
        allow to speed up module execution, because some REST API calls is pretty slow.
        :type account:       dict
        :param account:      Reference on dictionary which contain information for account data
                             model configuration.
        :type applications:  list
        :param applications: Reference on list of dictionaries which describe every application
                             which is registered for authorized account.
        :type initial:       bool
        :param initial:      Whether applications list processed on account initialization from the
                             scratch (not from cache).
        """
        # Store account information if passed.
        if account is not None:
            self._service_data = copy.deepcopy(account)
        # Create models from list of account's applications.
        if applications is not None:
            for app in applications:
                application = PubNubApplication(self._module, account=self, api_client=self._api,
                                                application=app, initial=initial)
                self._apps[application.name] = application


class PubNubApplication(object):
    """PubNub application representation model."""

    def __init__(self, module, account, api_client, application, initial=False):
        """Construct application model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial
                            functionality to module.
        :type account:      PubNubAccount
        :param account:     Reference on user account where this application has been registered.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client.
        :type application:  dict
        :param application: PubNub service response with information about particular application.
        :type initial:      bool
        :param initial:     Whether application created during account initialization from the
                            scratch (not from cache).
        :rtype:  PubNubApplication
        :return: Initialized application data model.
        """
        super(PubNubApplication, self).__init__()
        self._module = module
        self._account = account
        self._api = api_client
        self._service_data = None
        """:type : dict"""
        self._keysets = dict()
        self._active_keyset = None
        """:type : PubNubKeyset"""
        self._process_data(application=application, initial=initial)

    def keys(self):
        """Retrieve list of application fields.

        This method used to find out list of fields which should be inside of dict after application
        will be serialized to it.
        :rtype:  list
        :return: List of keys which represent application.
        """
        return list(self._service_data.keys()) + ['keys'] if self._service_data else list()

    def __getitem__(self, item):
        """Retrieve value for requested item.

        Provide values which should be placed inside of dictionary which represent application. In
        case if keysets list requested it will be additionally pre-processed to serialize keyset
        models.
        :type item:  str
        :param item: Reference on string which represent key under which stored value which should
                     be serialized as part of application entry.
        :return: One of fields which is stored for application.
        """
        if item != 'keys':
            value = self._service_data.get(item)
        else:
            value = list(dict(keyset) for keyset in self.keysets)

        return value

    @property
    def uid(self):
        """Stores reference on unique application identifier.

        :rtype:  int | None
        :return: Reference on unique application identifier or 'None' in case if application model
                 configuration not completed.
        """
        uid = _object_value(obj=self._service_data, key='id')
        return int(uid) if uid is not None else uid

    @property
    def name(self):
        """Stores reference on registered application name.

        :rtype:  str
        :return: Reference on application name or 'None' in case if application model configuration
                 not completed.
        """
        return _object_value(obj=self._service_data, key='name')

    @property
    def keysets(self):
        """Stores reference on list of keyset models.

        All keysets which is registered for this application represented by models and stored in
        this property.
        :rtype:  list[PubNubKeyset]
        :return: List of keyset models.
        """
        return list(self._keysets[name] for name in self._keysets if self._keysets.get(name))

    @property
    def current_keyset(self):
        """Stores reference on application's keyset which has been specified for this module run.

        :rtype:  PubNubKeyset
        :return: Reference on application's keyset model or 'None' in case if there is no keysets
                 with specified name.
        """
        keyset = self._keysets.get(self._module.params['keyset'])
        if keyset is None:
            error_fmt = 'There is no \'{0}\' keyset for \'{1}\' application. Make sure what ' + \
                        'correct keyset name has been passed. If keyset doesn\'t exist you can ' + \
                        'create it on admin.pubnub.com.'
            self._module.fail_json(msg=error_fmt.format(keyset, self.name), changed=self.changed)

        return keyset

    @property
    def changed(self):
        """Stores whether application's data has been changed or not.

        :rtype:  bool
        :return: 'True' in case if application or keysets data has been modified.
        """
        changed = False
        for keyset in self.keysets:
            changed = keyset.changed
            if changed:
                break

        return changed

    def save(self):
        """Store any changes to application and/or keyset."""
        for keyset in self.keysets:
            keyset.save()

    def _process_data(self, application, initial=False):
        """Process fetched application data.

        Process received application data to complete model configuration.
        :type application:  dict
        :param application: Reference on dictionary which describe application which is registered
                            for authorized account.
        :type initial:      bool
        :param initial:     Whether application created during account initialization from the
                            scratch (not from cache).
        """
        keysets = application.pop('keys') if application.get('keys') is not None else list()
        self._service_data = copy.deepcopy(application)
        for ks in keysets:
            keyset = PubNubKeyset(self._module, application=self, api_client=self._api, keyset=ks,
                                  initial=initial)
            self._keysets[keyset.name] = keyset


class PubNubKeyset(object):
    """PubNub application's keyset representation model."""

    def __init__(self, module, application, api_client, keyset, initial=False):
        """Construct application's keyset model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial
                            functionality to module.
        :type application:  PubNubApplication
        :param application: Reference on application model to which keyset belong.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client.
        :type keyset:       dict
        :param keyset:      PubNub service response with information about particular application's
                            keyset.
        :type initial:      bool
        :param initial:     Whether keyset created during account initialization from the scratch
                            (not from cache).
        :rtype:  PubNubKeyset
        :return: Initialized keyset model.
        """
        super(PubNubKeyset, self).__init__()
        self._module = module
        self._changed = False
        self._api = api_client
        self._application = application
        self._service_data = None
        """:type : dict"""
        self._blocks = None
        """:type : dict"""
        self._process_data(keyset=keyset, initial=initial)

    def keys(self):
        """Retrieve list of keyset fields.

        This method used to find out list of fields which should be inside of dict after keyset will
        be serialized to it.
        :rtype:  list
        :return: List of keys which represent keyset.
        """
        return list(self._service_data.keys()) + ['pnm_blocks'] if self._service_data else list()

    def __getitem__(self, item):
        """Retrieve value for requested item.

        Provide values which should be placed inside of dictionary which represent keyset. In
        case if blocks list requested it will be additionally pre-processed to serialize blocks
        models.
        :type item:  str
        :param item: Reference on string which represent key under which stored value which should
                     be serialized as part of keyset entry.
        :return: One of fields which is stored for keyset.
        """
        if item != 'pnm_blocks':
            value = self._service_data.get(item)
        else:
            value = list(dict(block) for block in self.blocks)

        return value

    @property
    def uid(self):
        """Stores reference on unique keyset identifier.

        :rtype:  int | None
        :return: Reference on unique keyset identifier or 'None' in case if keyset model
                 configuration not completed.
        """
        uid = _object_value(obj=self._service_data, key='id')
        return int(uid) if uid is not None else uid

    @property
    def name(self):
        """Stores reference on keyset name.

        :rtype:  str
        :return: Reference on keyset name or 'None' in case if keyset model configuration not
                 completed.
        """
        return _object_value(obj=self._service_data, key='properties.name')

    @property
    def blocks(self):
        """Stores reference on list of block models.

        All blocks which is registered for this keyset represented by models and stored in this
         property.
        :rtype:  list[PubNubBlock]
        :return: List of block models.
        """
        # Fetch blocks list if it is required.
        self._fetch_blocks_if_required()

        return list(self._blocks[name] for name in self._blocks if self._blocks.get(name))

    @property
    def current_block(self):
        """Stores reference on block which has been specified for this module run.

        :rtype:  PubNubBlock
        :return: Reference on block model or 'None' in case if there is no block with specified
                 name.
        """
        # Fetch blocks list if it is required.
        self._fetch_blocks_if_required()

        block_name = self._module.params['name']
        block = self._blocks.get(block_name)
        if block is None and self._module.params['state'] in ['start', 'stop']:
            self._module.fail_json(msg="'{0}' block doesn't exists.".format(block_name),
                                   changed=self.changed)

        return block

    @property
    def changed(self):
        """Check whether keyset's data has been changed or not.

        Whether something in keyset has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if keyset or block data has been modified.
        """
        changed = self._changed
        for block in self.blocks:
            changed = changed or block.changed
            if changed:
                break

        return changed

    def add_block(self, new_block):
        """Add new block to keyset.

        Create new block by user request and store it in keyset model.
        :type new_block:  PubNubBlock
        :param new_block: Reference on initialized new block which should be created.
        """
        # Fetch blocks list if it is required.
        self._fetch_blocks_if_required()

        if self._blocks.get(new_block.name) is None:
            new_block.api = self._api
            self._blocks[new_block.name] = new_block

    def replace_block(self, old_name, block, new_name=None):
        """Update block which is stored under specified keys.

        :type old_name:  str
        :param old_name: Reference on name under which 'block' should be stored.
        :type block:     PubNubBlock
        :param block:    Reference on PubNubBlock model instance which should be placed under
                         specified 'old_name' or 'new_name' (if specified).
        :type new_name:  str
        :param new_name: Reference on name under which 'block' should be stored. If specified, block
                         which is stored under 'old_name' will be removed.
        """
        # Fetch blocks list if it is required.
        self._fetch_blocks_if_required()

        if new_name and self._blocks.get(old_name):
            del self._blocks[old_name]
        self._blocks[new_name or old_name] = block

    def remove_block(self, block):
        """Remove block from keyset.

        Stop and remove target block if it exists.
        :type block:  PubNubBlock
        :param block: Reference on PubNubBlock model instance which should be removed.
        """
        # Fetch blocks list if it is required.
        self._fetch_blocks_if_required()

        if self._blocks.get(block.name):
            block.delete()

    def save(self):
        """Store any changes to keyset and/or blocks."""
        blocks_for_removal = list(block.name for block in self.blocks if block.should_delete)
        for block in self.blocks:
            block.save()
        for block_name in blocks_for_removal:
            del self._blocks[block_name]
        if blocks_for_removal:
            self._changed = True

    def _fetch_blocks_if_required(self):
        """Fetch keyset's blocks if required.

        In case if this is first time when keyset is used blocks should be retrieved.
        """
        if self._blocks is None:
            self._process_data(blocks=self._api.fetch_blocks(self.uid))

    def _process_data(self, keyset=None, blocks=None, initial=False):
        """Process fetched keyset data.

        Process received keyset data to complete model configuration.
        :type keyset:   dict
        :param keyset:  Reference on dictionary which contain information about application's
                        keyset.
        :type blocks:   list
        :param blocks:  Reference on list of dictionaries each of which represent block with event
                        handlers.
        :type initial:  bool
        :param initial: Whether keyset created during account initialization from the scratch (not
                        from cache).
        """
        cached_blocks = _object_value(obj=keyset, key='pnm_blocks')
        b_data = keyset.pop('pnm_blocks') if cached_blocks is not None else None
        # Store keyset information.
        if keyset:
            self._service_data = copy.deepcopy(keyset)
        # Process blocks data.
        if blocks is not None:
            if self._blocks is None:
                self._blocks = dict()
            for blk in blocks:
                block = PubNubBlock(self._module, keyset=self, api_client=self._api, block=blk)
                self._blocks[block.name] = block
        if not initial and b_data is not None:
            self._process_data(blocks=b_data, initial=initial)


class PubNubBlock(object):
    """PubNub block representation model."""

    def __init__(self, module, keyset, api_client=None, block=None, name=None, description=None):
        """Construct block model using service response.

        :type module:       AnsibleModule
        :param module:      Reference on initialized AnsibleModule which provide some initial
                            functionality to module.
        :type keyset:       PubNubKeyset
        :param keyset:      Reference on keyset model to which block belong.
        :type api_client:   PubNubAPIClient
        :param: api_client  Reference on API access client. 'None' can be in case if block has been
                            just created.
        :type block:        dict
        :param block:       PubNub service response with information about particular block. 'None'
                            possible in case if there is request to create new block.
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
        self._service_data = None
        """:type : dict"""
        self._block_data = None
        """:type : dict"""
        self._event_handlers = dict()
        self._should_delete = False
        if block:
            self._process_data(block)
        else:
            self.name = name
            self.description = description

    def keys(self):
        """Retrieve list of block fields.

        This method used to find out list of fields which should be inside of dict after block will
        be serialized to it.
        :rtype:  list
        :return: List of keys which represent block.
        """
        # Caching current payload before serialization started.
        block_data = copy.deepcopy(self._service_data or dict())
        block_data.update(self._block_data or dict())
        setattr(self, '_block_serialization_data', block_data)

        return list(block_data.keys()) + ['event_handlers'] if block_data else list()

    def __getitem__(self, item):
        """Retrieve value for requested item.

        Provide values which should be placed inside of dictionary which represent block. In
        case if event handlers list requested it will be additionally pre-processed to serialize
        handler models.
        :type item:  str
        :param item: Reference on string which represent key under which stored value which should
                     be serialized as part of block entry.
        :return: One of fields which is stored for block.
        """
        if item != 'event_handlers':
            value = getattr(self, '_block_serialization_data').get(item)
        else:
            value = list(dict(event_handler) for event_handler in self.event_handlers)

        return value

    @property
    def uid(self):
        """Stores reference on unique block's identifier.

        :rtype:  int | None
        :return: Reference on unique block's identifier or 'None' in case if block model
                 configuration not completed.
        """
        uid = _object_value(obj=self._service_data, key='id')
        return int(uid) if uid is not None else uid

    @property
    def name(self):
        """Stores reference on block's name.

        :rtype:  str | None
        :return: Reference on block's name or 'None' in case if block model configuration not
                 completed.
        """
        return _object_value(obj=(self._service_data or self._block_data), key='name')

    @name.setter
    def name(self, name):
        """Update block's name.

        :type name:  str
        :param name: Reference on new block name.
        """
        self._set_block_data(field='name', value=name)

    @property
    def description(self):
        """Stores reference on block's description.

        :rtype:  str | None
        :return: Reference on block's description or 'None' in case if block model configuration not
                 completed.
        """
        return _object_value(obj=(self._service_data or self._block_data), key='description')

    @description.setter
    def description(self, description):
        """Update block's description.

        :type description:  str
        :param description: Reference on new block's description.
        """
        self._set_block_data(field='description', value=description)

    @property
    def state(self):
        """Stores reference on current block's state.

        :rtype:  str | None
        :return: Reference on block's state or 'None' in case if block model configuration not
                 completed.
        """
        return _object_value(obj=self._service_data, key='state')

    @property
    def target_state(self):
        """Stores reference on target block's state.

        :rtype:  str
        :return: Reference on block's state or 'None' in case if block model configuration not
                 completed.
        """
        return _object_value(obj=self._service_data, key='intended_state')

    @target_state.setter
    def target_state(self, target_state):
        """Update block's target state.

        :type target_state:  str
        :param target_state: Reference on new block's target state.
        """
        self._set_block_data(field='intended_state', value=target_state)

    @property
    def should_delete(self):
        """Stores whether block should be removed during save operation or not.

        Block removal will happen at the same moment when account will be asked to 'save' changes.
        """
        return self._should_delete

    @property
    def event_handlers(self):
        """Stores reference on list of block's event handler models.

        All event handlers which is registered for this block represented by models and stored in
        this property.
        :rtype:  list[PubNubEventHandler]
        :return: List of block models.
        """
        return list(self._event_handlers[name] for name in self._event_handlers
                    if self._event_handlers.get(name))

    @property
    def payload(self):
        """Stores reference on block data structured as it required by PubNub service.

        :rtype:  dict
        :return: Block information in format which is known to PubNub service.
        """
        payload = dict()
        if self._service_data:
            payload.update(key_id=self.keyset.uid, block_id=self.uid, name=self.name,
                           description=self.description)
        if self._block_data:
            default_name = _object_value(obj=payload, key='name')
            default_description = _object_value(obj=payload, key='description')
            payload['name'] = _object_value(obj=self._block_data, key='name', default=default_name)
            payload['description'] = _object_value(obj=self._block_data, key='description',
                                                   default=default_description)
        if not _object_value(obj=payload, key='description'):
            payload['description'] = 'New block'

        return payload

    @property
    def changed(self):
        """Check whether block's data has been changed or not.

        Whether something in block has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if block or event handlers data has been modified.
        """
        changed = self._changed
        for event_handler in self.event_handlers:
            changed = changed or event_handler.changed
            if changed:
                break

        return changed

    @property
    def api(self):
        """Stores reference on API access client.

        :return: PubNubAPIClient
        """
        return self._api

    @api.setter
    def api(self, api_client):
        """Update information about API client which should be used by block.

        :type api_client:  PubNubAPIClient
        :param: api_client Reference on API access client. 'None' can be in case if block has been
                           just created.
        """
        self._api = api_client
        for event_handler in self.event_handlers:
            event_handler.api = api_client

    @property
    def keyset(self):
        """Stores reference on keyset for which block has been created.

        :rtype:  PubNubKeyset
        :return: Reference on keyset model.
        """
        return self._keyset

    @staticmethod
    def name_from_payload(payload):
        """Retrieve block's name from raw payload.

        :rtype:  str
        :return: Reference on block's name or 'None' in case if block model configuration not
                 completed.
        """
        return _object_value(obj=payload, key='name')

    def apply_changes(self):
        """Update block information if required."""
        # Check whether block name should be changed or not.
        changes = self._module.params['changes']
        if _object_value(obj=changes, key='name'):
            self.name = changes['name']
            self._module.params['name'] = changes['name']
            self.keyset.replace_block(old_name=self.name, block=self, new_name=changes['name'])
        if _object_value(obj=self._module.params, key='description') and \
                self._module.params['description'] != self.description:
            self.description = self._module.params['description']

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
        :param event_handlers: Reference on list of dictionaries which represent event handlers
                               changes.
        """
        existing_handlers = list(self._event_handlers.keys())
        for eh in event_handlers:
            eh_name = PubNubEventHandler.name_from_payload(eh)
            if eh_name not in existing_handlers:
                event_handler = PubNubEventHandler(module=self._module, block=self,
                                                   api_client=self.api, event_handler=eh)
                if not event_handler.should_delete:
                    self._event_handlers[eh_name] = event_handler
            else:
                event_handler = self._event_handlers[eh_name]
                """:type : PubNubEventHandler"""
                if event_handler:
                    event_handler.update_with_data(eh)

    def save(self):
        """Save block changes.

        Depending on whether block existed before or not it may be created and updated if required.
        """
        will_change = self._should_create() or self.should_delete or self._should_save()
        should_stop_for_event_handlers = self._event_handlers_change_require_stop()
        block_data = self.payload
        if self._should_create():
            if not self._module.check_mode:
                block_data.update(self._api.create_block(keyset_id=self.keyset.uid,
                                                         block_payload=block_data))
                block_data['block_id'] = block_data['id']
            else:
                block_data['id'] = 1616
        elif self.should_delete:
            self._change_block_state(state='stopped', update_cached_state=False)
            if not self._module.check_mode:
                self._api.delete_block(keyset_id=self.keyset.uid, block_id=self.uid)
        elif self._should_save():
            # Update block own information.
            if not self._module.check_mode and \
                    self._should_save(['key_id', 'state', 'intended_state']):
                self._api.update_block(keyset_id=self.keyset.uid, block_id=self.uid,
                                       block_payload=block_data)
            block_data = self._service_data
            block_data.update(self.payload or dict())
            # Change block operation state as it has been requested during module call.
            if not should_stop_for_event_handlers:
                self._change_block_state(state=_object_value(obj=self._block_data,
                                                             key='intended_state'))
        elif should_stop_for_event_handlers:
            # Stop block in case if event_handlers modification is required.
            self._change_block_state(state='stopped', update_cached_state=False)

        if will_change:
            self._changed = True
            if not self.should_delete:
                if self._should_create():
                    block_data.update(dict(intended_state='stopped', state='stopped'))
                self._process_data(block_data)

        event_handlers_for_removal = list(eh.name for eh in self.event_handlers if eh.should_delete)
        for event_handler in self.event_handlers:
            event_handler.save()
        for event_handler_name in event_handlers_for_removal:
            del self._event_handlers[event_handler_name]
        if event_handlers_for_removal:
            self._changed = True

        if should_stop_for_event_handlers:
            if not self._event_handlers:
                self._set_block_data(field='intended_state', value='stopped')
            self._change_block_state(state=_object_value(obj=self._block_data,
                                                         key='intended_state'))

    def _should_create(self):
        """Check whether block should be created or not.

        :rtype:  bool
        :return: 'True' in case if there is no raw data from PubNub service about this block.
        """
        return self._service_data is None

    def _should_save(self, excluded_fields=None):
        """Check whether there is block changes which should be saved.

        :type excluded_fields:  list
        :param excluded_fields: List of fields which should be removed from comparision.
        :rtype:  bool
        :return: 'True' in case if there is unsaved changes.
        """
        should_save = self._should_create()
        if not should_save and self._service_data and self._block_data:
            service_data_copy = copy.deepcopy(self._service_data)
            block_data_copy = copy.deepcopy(self._block_data)
            for key in (excluded_fields or list()):
                if key in service_data_copy:
                    del service_data_copy[key]
                if key in block_data_copy:
                    del block_data_copy[key]
            should_save = not _is_equal(service_data_copy, block_data_copy)

        return should_save

    def _event_handlers_change_require_stop(self):
        """Check whether any block's event handler will change.

        Check whether any user-provided event handlers' data will cause their modification or not.
        :rtype:  bool
        :return: 'True' in case if any event handler change information which require block stop.
        """
        require_stop = False
        for event_handler in self.event_handlers:
            require_stop = event_handler.change_require_block_stop
            if require_stop:
                break

        return require_stop

    def _change_block_state(self, state, update_cached_state=True):
        """Update actual block state.

        Perform block operation state change request and process service response.
        :type state:  str
        :param state: Reference on expected block operation state (running or stopped).
        :type update_cached_state:  bool
        :param update_cached_state: Whether desired block state should be modified as well (the one
                                    which is asked by user during module configuration).
        """
        if self._event_handlers and \
                (self._service_data['intended_state'] != state or
                 self._service_data['state'] != state):
            current_state = state if self._service_data['intended_state'] == state else None
            if not self._module.check_mode:
                operation = dict(running=self._api.start_block, stopped=self._api.stop_block)
                (timeout, error_reason, stack) = operation[state](keyset_id=self.keyset.uid,
                                                                  block_id=self.uid,
                                                                  current_state=current_state)
                self._handle_block_state_change(state='start' if state == 'running' else 'stop',
                                                timeout=timeout, error_reason=error_reason,
                                                stack=stack)
            self._service_data['intended_state'] = state
            self._service_data['state'] = state
            self._block_data['state'] = state
            if update_cached_state:
                self._block_data['intended_state'] = state

            if not current_state:
                self._changed = True

    def _process_data(self, block):
        """Process fetched block data.

        Process received block data to complete model configuration.
        :type block:  dict
        :param block: Reference on dictionary which contain information about specific block.
        """
        cached_handlers = block.get('event_handlers')
        event_handlers = block.pop('event_handlers') if cached_handlers is not None else list()
        for eh in event_handlers:
            event_handler = PubNubEventHandler(self._module, block=self, api_client=self.api,
                                               event_handler=eh)
            self._event_handlers[event_handler.name] = event_handler
        self._service_data = copy.deepcopy(block)
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
        :param stack:        Reference on string which represent event handler execution stack
                             trace.
        """
        err_msg = None
        if timeout:
            delay = PN_BLOCK_STATE_CHECK_MAX_COUNT * PN_BLOCK_STATE_CHECK_INTERVAL
            err_msg = '\'{0}\' block not {1}\'ed in {2} seconds'.format(self.name, state, delay)
        elif stack:
            err_msg = 'Unable to {0} \'{1}\' block because of error: {2}'.format(state, self.name,
                                                                                 error_reason)
        if err_msg:
            self._module.fail_json(msg=err_msg, changed=self.changed, stack=stack)

    def _set_block_data(self, field, value):
        """Update user-provided block information.

        Method allow to store till saved user-provided changes to block. If this is new block, then
        storage will be created.
        :type field:  str
        :param field: Name of block property for which value has been passed.
        :type value:  any
        :param value: Value which should be assigned to block's property.
        """
        if self._block_data is None:
            self._block_data = dict()
        self._block_data[field] = value


class PubNubEventHandler(object):
    """PubNub event handler representation model."""

    def __init__(self, module, block, api_client, event_handler):
        """Construct block model using service response.

        :type module:         AnsibleModule
        :param module:        Reference on initialized AnsibleModule which provide some initial
                              functionality to module.
        :type block:          PubNubBlock
        :param block:         Reference on block model to which event handler belong.
        :type api_client:     PubNubAPIClient
        :param: api_client    Reference on API access client.
        :type event_handler:  dict
        :param event_handler: PubNub service response with information about particular event
                              handler.
        :rtype:  PubNubEventHandler
        :return: Initialized event handler model.
        """
        super(PubNubEventHandler, self).__init__()
        self._module = module
        self._changed = False
        self._api = api_client
        self._block = block
        self._service_data = None
        """:type : dict"""
        self._event_handler_data = None
        """:type : dict"""
        self._state = 'present'
        self._should_delete = False
        self._process_data(event_handler)

    def keys(self):
        """Retrieve list of event handler fields.

        This method used to find out list of fields which should be inside of dict after event
        handler will be serialized to it.
        :rtype:  list
        :return: List of keys which event handler block.
        """
        # Caching current payload before serialization started.
        event_handler = copy.deepcopy(self._service_data or dict())
        event_handler.update(self._event_handler_data or dict())
        setattr(self, '_event_handler_serialization_data', event_handler)

        return event_handler.keys() or list()

    def __getitem__(self, item):
        """Retrieve value for requested item.

        Provide values which should be placed inside of dictionary which represent event handler.
        :type item:  str
        :param item: Reference on string which represent key under which stored value which should
                     be serialized as part of event handler entry.
        :return: One of fields which is stored for event handler.
        """
        return getattr(self, '_event_handler_serialization_data').get(item)

    @property
    def uid(self):
        """Stores reference on unique block's identifier.

        :rtype:  int | None
        :return: Reference on unique block's identifier or 'None' in case if event handler model
                 configuration not completed.
        """
        uid = _object_value(obj=self._service_data, key='id')
        return int(uid) if uid is not None else uid

    @property
    def name(self):
        """Stores reference on event handler's name.

        :rtype:  str
        :return: Reference on event handler's name or 'None' in case if event handler model
                 configuration not completed.
        """
        return _object_value(obj=(self._service_data or self._event_handler_data), key='name')

    @name.setter
    def name(self, name):
        """Update event handler's name.

        :type name:  str
        :param name: Reference on new event handler name.
        """
        self._set_event_handler_data(field='name', value=name)

    @property
    def code(self):
        """Stores reference on event handler's code.

        :rtype:  str
        :return: Reference on event handler's code or 'None' in case if event handler model
                 configuration not completed.
        """
        return _object_value(obj=(self._service_data or self._event_handler_data), key='code')

    @code.setter
    def code(self, code):
        """Update event handler's code.

        :type code:  str
        :param code: Reference on new event handler code.
        """
        self._set_event_handler_data(field='code', value=code)

    @property
    def channels(self):
        """Stores reference on event handler's trigger channel.

        :rtype:  str
        :return: Reference on event handler's trigger channel or 'None' in case if event handler
                 model configuration not completed.
        """
        return _object_value(obj=(self._service_data or self._event_handler_data), key='channels')

    @channels.setter
    def channels(self, channels):
        """Update event handler's trigger channel.

        :type channels:  str
        :param channels: Reference on new event handler trigger channel.
        """
        self._set_event_handler_data(field='channels', value=channels)

    @property
    def event(self):
        """Stores reference on event handler's trigger event.

        :rtype:  str
        :return: Reference on event handler's trigger event or 'None' in case if event handler model
                 configuration not completed.
        """
        return _object_value(obj=(self._service_data or self._event_handler_data), key='event')

    @event.setter
    def event(self, event):
        """Update event handler's trigger event.

        :type event:  str
        :param event: Reference on new event handler trigger event.
        """
        self._set_event_handler_data(field='event', value=event)

    @property
    def change_require_block_stop(self):
        """Check whether further event handlers require block to be stopped.

        All properties expect handler's name require to stop block before changing anything in
        handler.
        :rtype:  bool
        :return: 'True' in case if base handler data should be changed and block should stop.
        """
        require_block_stop = self._service_data is None or self.should_delete
        if not require_block_stop and not self.should_delete:
            # Retrieve user-provided handler information.
            fields = ['code', 'channels', 'event']
            (cur_code, cur_channels, cur_event) = tuple(_values(dct=self._service_data,
                                                                keys=fields))
            (new_code, new_channels, new_event) = tuple(_values(dct=self._event_handler_data,
                                                                keys=fields))
            require_block_stop = cur_code != new_code or cur_channels != new_channels
            require_block_stop = require_block_stop or cur_event != new_event

        return require_block_stop

    @property
    def should_delete(self):
        """Stores whether event handler should be removed during save operation or not.

        Block removal will happen at the same moment when block will be asked to 'save' changes.
        :rtype:  bool
        :return: Whether event handler should be removed.
        """
        return self._should_delete or self._state == 'absent'

    @property
    def payload(self):
        """Stores reference on event handler data structured as it required by PubNub service.

        :rtype:  dict
        :return: Event handler information in format which is known to PubNub service.
        """
        payload = dict()
        if self._service_data:
            payload.update(key_id=self._block.keyset.uid, block_id=self._block.uid, name=self.name,
                           channels=self.channels, code=self.code, event=self.event,
                           type=self._service_data['type'],
                           output=self._service_data['output'],
                           log_level=self._service_data['log_level'])
        payload.update(self._event_handler_data or dict())

        return payload

    @property
    def changed(self):
        """Check whether event handler's data has been changed or not.

        Whether something in block has been changed lately or not.
        :rtype:  bool
        :return: 'True' in case if event handler data has been modified.
        """
        return self._changed

    @property
    def api(self):
        """Stores reference on API access client.

        :return: PubNubAPIClient
        """
        return self._api

    @api.setter
    def api(self, api_client):
        """Update information about API client which should be used by event handler.

        :type api_client:  PubNubAPIClient
        :param: api_client Reference on API access client.
        """
        self._api = api_client

    @staticmethod
    def name_from_payload(payload):
        """Retrieve event handler's name from raw payload.

        :rtype:  str
        :return: Reference on event handler's name or 'None' in case if block model configuration
                 not completed.
        """
        return _object_value(obj=payload, key='name')

    def will_change_with_data(self, event_handler=None):
        """Check whether receiver handler can be updated with provided data.

        Check whether any portion of event handler can be updated with user-provided information or
        not.
        :type event_handler:  dict
        :param event_handler: Reference on dictionary which represent event handler changes.
        :rtype:  bool
        :return: 'True' in case if any portion of event handler require modification.
        """
        should_update = self._service_data is None and self._event_handler_data or \
            not event_handler and self.should_delete
        if not should_update and event_handler:
            # Retrieve user-provided handler information.
            fields = ['name', 'src', 'channels', 'event']
            (name, src_path, channels, event) = tuple(_values(dct=event_handler, keys=fields))
            if _object_value(obj=event_handler, key='changes.name'):
                name = event_handler['changes']['name']
            should_update = name != self.name or event and event != self.event
            should_update = should_update or channels and channels != self.channels
            if not should_update:
                code = _content_of_file_at_path(src_path)
                should_update = code and code != self.code
            handler_state = _object_value(obj=event_handler, key='state', default='present')
            should_update = should_update or handler_state == 'absent'
        elif not should_update and self._service_data and self._event_handler_data:
            should_update = not _is_equal(self._service_data, self._event_handler_data)

        return should_update

    def update_with_data(self, event_handler):
        """Update handler data.

        :type event_handler:  dict
        :param event_handler: Reference on dictionary which represent event handler changes.
        """
        handler_state = _object_value(obj=event_handler, key='state', default='present')
        if handler_state != 'absent':
            # Retrieve user-provided handler information.
            fields = ['name', 'src', 'channels', 'event']
            (name, src_path, channels, event) = tuple(_values(dct=event_handler, keys=fields))
            if _object_value(obj=event_handler, key='changes.name'):
                name = event_handler['changes']['name']
            self.name = name
            if channels:
                self.channels = channels
            if event:
                self.event = event
            code = _content_of_file_at_path(src_path)
            if code:
                self.code = code
        else:
            self._should_delete = True

    def save(self):
        """Save event handler's changes.

        Depending on whether event handler existed before or not it may be created and updated if
        required.
        """
        will_change = self._should_create() or self.should_delete or self.will_change_with_data()
        handler_data = self.payload
        # Create new event handler if required.
        if self._should_create():
            fields = ['name', 'channels', 'event', 'code']
            handler_data.update(self._default_handler_payload() or dict())
            (name, channels, event, code) = _values(dct=handler_data, keys=fields)
            if name and channels and event and code:
                if not self._module.check_mode:
                    response = self._api.create_event_handler(keyset_id=self._block.keyset.uid,
                                                              payload=handler_data)
                    handler_data.update(response or dict())
                else:
                    handler_data['id'] = 1617
                self._changed = True
            else:
                missed_fields = list()
                missed_fields.append('name') if not name else None
                missed_fields.append('channels') if not channels else None
                missed_fields.append('code') if not code else None
                missed_fields.append('event') if not event else None
                error_message = 'Unable create event handler w/o following fields: ' + \
                                '{0}.'.format(', '.join(missed_fields))
                self._module.fail_json(changed=self.changed, msg=error_message)
        elif self.should_delete:
            if not self._module.check_mode:
                self._api.delete_event_handler(keyset_id=self._block.keyset.uid,
                                               handler_id=self.uid)
            self._changed = True
        elif self.will_change_with_data():
            if not self._module.check_mode:
                self._api.update_event_handler(keyset_id=self._block.keyset.uid,
                                               handler_id=self.uid, payload=handler_data)
            handler_data = self._service_data
            handler_data.update(self.payload or dict())

        if will_change:
            self._changed = True
            if not self.should_delete:
                self._process_data(handler_data)

    def _should_create(self):
        """Check whether event handler should be created or not.

        :rtype:  bool
        :return: 'True' in case if this is new event handler (doesn't have unique identifier
                 assigned by PubNub service).
        """
        return self._service_data is None and self._state == 'present'

    def _process_data(self, event_handler):
        """Process received event handler's information.

        Use provided information to complete event handler initialization.
        :type event_handler:  dict
        :param event_handler: Reference on dictionary with event handler information from PubNub
                              service or cached information from previous module call.
        """
        # Check whether event handler payload belong to new handler or not.
        event_handler_exists = _object_value(obj=event_handler, key='id') is not None
        self._state = _object_value(obj=event_handler, key='state', default='present')
        if not event_handler_exists and self._state == 'present':
            keys = ['name', 'channels', 'event', 'src']
            (name, channels, event, src_path) = _values(dct=event_handler, keys=keys)
            if _object_value(obj=event_handler, key='changes.name'):
                name = event_handler['changes']['name']
            code = _content_of_file_at_path(src_path)
            self._event_handler_data = dict(name=name, channels=channels, event=event, code=code)
        elif event_handler_exists:
            self._should_delete = True if self._state == 'absent' else False
            self._service_data = copy.deepcopy(event_handler)
            self._event_handler_data = copy.deepcopy(event_handler)

    def _default_handler_payload(self):
        """Compose default payload for event handler create / update.

        Payload include application-wide information and doesn't depend from particular event
        handler configuration.
        :rtype:  dict
        :return: Initial payload dictionary which can be used for event handler manipulation
                 requests.
        """
        return dict(key_id=self._block.keyset.uid, block_id=self._block.uid,
                    log_level='debug', output="output-{}".format(random.random()), type='js')

    def _set_event_handler_data(self, field, value):
        """Update user-provided event handler information.

        Method allow to store till saved user-provided changes to event handler. If this is new
        event handler, then storage will be created.
        :type field:  str
        :param field: Name of event handler property for which value has been passed.
        :type value:  any
        :param value: Value which should be assigned to event handler's property.
        """
        if self._event_handler_data is None:
            self._event_handler_data = dict()
        self._event_handler_data[field] = value


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
        :param identifier: Reference on unique identifier of authorized user for which applications
                           should be retrieved.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        return PubNubEndpoint._endpoint_with_query(endpoint='/apps',
                                                   query=dict(owner_id=identifier))

    @staticmethod
    def block(keyset_id, block_id=None):
        """Provide endpoint to get block information.

        Endpoint allow to retrieve information about specific block or all blocks registered for
        keyset (if 'block_id' is 'None').
        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which list of
                          blocks should be retrieved.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block for which information should be
                          retrieved.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        endpoint = '/v1/blocks/key/{}/block'.format(keyset_id)
        if block_id:
            endpoint = '{}/{}'.format(endpoint, block_id)

        return endpoint

    @staticmethod
    def block_state(keyset_id, block_id, state):
        """Provide endpoint which will allow change current block operation mode.

        Endpoint allow to retrieve information about specific block or all blocks registered for
        keyset (if 'block_id'
        is 'None').
        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which block
                          state should be changed.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block for which operation state should
                          be changed.
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
        :param keyset_id:  Reference on unique identifier of application's keyset for which event
                           handler access required.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of block's event handler.
        :rtype:  str
        :return: Target REST API endpoint which is relative to base address.
        """
        endpoint = '/v1/blocks/key/{}/event_handler'.format(keyset_id)
        if handler_id:
            endpoint = '{}/{}'.format(endpoint, handler_id)

        return endpoint

    @staticmethod
    def _endpoint_with_query(endpoint, query):
        """Add if required list of query parameters to API endpoint

        :type endpoint:  str
        :param endpoint: Reference on REST API endpoint to which list of query parameters should be
                         appended.
        :type query:     dict
        :param query:    Reference on dictionary which represent key/value pairs for query string
                         which will be appended to API endpoint string.
        :rtype:  str
        :return: Reference on string which is composed from API endpoint path components and query
                 string.
        """
        return '{}?{}'.format(endpoint, urlencode(query))


class PubNubAPIClient(object):
    """PubNub REST API access client.

    Class provide access to set of API endpoints which allow to manage blocks.
    """

    def __init__(self, module, account):
        """Client provide entry point to interact with PubNub REST API by performing authorized
        requests.

        :type module:   AnsibleModule
        :param module:  Reference on initialized AnsibleModule which provide some initial
                        functionality to module.
        :type account:  PubNubAccount
        :param account: Reference on model which is used along with API client to get access to
                        REST API.
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
                    password=dict(default='', required=False, type='str', no_log=True))

    @property
    def session(self):
        """Stores reference on started session identifier.
        :rtype:  str
        :return: Reference on started session identifier or 'None' if there is no registered
                 session.
        """
        return self._session

    @session.setter
    def session(self, session):
        """Update active session identifier

        :type session:  str
        :param session: Reference on started session identifier.
        """
        self._session = session

    def start_session(self, email, password):
        """Start new PubNub block management API access session using provided account credentials.
        :type email:     str
        :param email:    Email of account for which REST API calls should be authorized.
        :type password:  str
        :param password: Account's password.
        :rtype:  dict
        :return: Reference on dictionary which contain information about authorized account.
        """
        response = self.request(api_endpoint=PubNubEndpoint.account(), http_method='POST',
                                data=dict(email=email, password=password))
        self._session = response['result']['token']

        return response['result']

    def fetch_applications(self, account_id):
        """Fetch information about list of applications / keys which has been created.

        :type account_id:  int
        :param account_id: Reference on uniquie authorized account identifier for which list if
                           registered applications should be received.
        :rtype:  list
        :return: Reference on list of dictionaries which represent list of registered applications
                 for authorized account.
        """
        # Send account information audit request.
        response = self.request(api_endpoint=PubNubEndpoint.applications(account_id),
                                http_method='GET')

        return _object_value(obj=response, key='result', default=list())

    def fetch_blocks(self, keyset_id):
        """Retrieve list of blocks created for keyset.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of application's keyset for which list of
                          blocks should be retrieved.
        :rtype:  list
        :return: Reference on list of dictionaries each represent particular block with event
                 handlers information.
        """
        # Send blocks information audit request.
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id),
                                http_method='GET')

        return response['payload']

    def fetch_block(self, keyset_id, block_id):
        """Retrieve information about specific block.

        Request allow to get smaller amount of information with request performed against concrete
        block using it's ID.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be
                              retrieved.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be retrieved.
        :rtype:  dict
        :return: Reference on dictionary which represent particular block with event handlers
                 information.
        """
        # Send block audit request.
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id,
                                                                  block_id=block_id),
                                http_method='GET')
        block = response['payload']

        return block[0] if block else list()

    def create_block(self, keyset_id, block_payload):
        """Create new block using initial payload.

        New block can be created with minimal block information (name and/ description).
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which new block should be
                              created.
        :type block_payload:  dict
        :param block_payload: Reference on payload which should be pushed to PubNub REST API to
                              create new block.
        :rtype:  dict
        :return: Reference on dictionary which contain block information provided by PubNub service.
        """
        # Prepare new block payload
        payload = dict(key_id=keyset_id)
        payload.update(block_payload or dict())
        # Create new block
        response = self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id),
                                http_method='POST',
                                data=payload)

        return response['payload']

    def update_block(self, keyset_id, block_id, block_payload):
        """Update block information using data from payload.

        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be
                              updated.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block for which changes should be
                              done.
        :type block_payload:  dict
        :param block_payload: Reference on payload which contain changed for block.
        """
        # Prepare new block payload
        payload = dict(key_id=keyset_id, block_id=block_id)
        payload.update(block_payload or dict())
        payload['id'] = block_id
        # Update block information
        self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id),
                     http_method='PUT',
                     data=payload)

    def delete_block(self, keyset_id, block_id):
        """Remove block from keyset.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of keyset from which block should be
                          removed.
        :type block_id:   int
        :param block_id:  Reference on unique identifier of block which should be removed.
        """
        # Remove block from keyset.
        self.request(api_endpoint=PubNubEndpoint.block(keyset_id=keyset_id, block_id=block_id),
                     http_method='DELETE')

    def start_block(self, keyset_id, block_id, current_state=None):
        """Start target block.

        Client will try to start specific block and verify operation success by requesting updated
        block information.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset for which block should be
                              started.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be started.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if
                              it reached, change request won't be sent and only wait for transition
                              to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block starting results.
        """
        return self._set_block_operation_state(keyset_id=keyset_id, block_id=block_id,
                                               state='start', current_state=current_state)

    def stop_block(self, keyset_id, block_id, current_state=None):
        """Start target block.

        Client will try to start specific block and verify operation success by requesting updated
        block information.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset from which block should be
                              stopped.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be stopped.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if
                              it reached, change request won't be sent and only wait for transition
                              to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block stopping results.
        """
        return self._set_block_operation_state(keyset_id=keyset_id, block_id=block_id, state='stop',
                                               current_state=current_state)

    def _set_block_operation_state(self, keyset_id, block_id, state, current_state=None):
        """Update current block's operation state.

        Depending from requested state block can be stopped or started.
        :type keyset_id:      int
        :param keyset_id:     Reference on unique identifier of keyset from which block should be
                              removed.
        :type block_id:       int
        :param block_id:      Reference on unique identifier of block which should be removed.
        :type state:          str
        :param state:         Reference on new block state to which it should be switched.
        :type current_state:  str
        :param current_state: Reference on current block (specified with block_id) state. In case if
                              it reached, change request won't be sent and only wait for transition
                              to new state completion.
        :rtype:  tuple
        :return: Tuple with details of block operation state change.
        """
        timeout = False
        in_transition = current_state is not None and \
            current_state == ('running' if state == 'start' else 'stopped')
        error_reason = None
        stack = None
        if not in_transition:
            response = self.request(api_endpoint=PubNubEndpoint.block_state(keyset_id=keyset_id,
                                                                            block_id=block_id,
                                                                            state=state),
                                    http_method='POST', ignored_status_codes=[409],
                                    data=dict(block_id=block_id))
        else:
            response = None

        if in_transition or response['status'] != 409:
            check_count = 0
            block = self.fetch_block(keyset_id=keyset_id, block_id=block_id)
            # Block require some time to change it's state, so this while loop will check it few
            # times after specified interval. In case if after fixed iterations count state still
            # won't be same as requested it will report error.
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
            if _object_value(obj=response, key='message'):
                service_message = response['message']
                if _object_value(obj=service_message, key='text'):
                    error_reason = service_message['text']
                if _object_value(obj=service_message, key='stack'):
                    stack = service_message['stack']
        return timeout, error_reason, stack

    def create_event_handler(self, keyset_id, payload):
        """Create new event handler for block.

        :type keyset_id:  int
        :param keyset_id: Reference on unique identifier of keyset for which event handler should be
                          created for target block.
        :type payload:    dict
        :param payload:   Reference on new event handler payload.
        """
        # Send event handler creation request
        response = self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id),
                                http_method='POST', data=payload)

        return response['payload']

    def update_event_handler(self, keyset_id, handler_id, payload):
        """Update event handler's event data.

        Use provided information to update event handler behaviour and data processing flow (handler
        code).
        :type keyset_id:   int
        :param keyset_id:  Reference on unique identifier of keyset for which event handler data
                           should be updated.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of event handler which should be updated.
        :type payload:     dict
        :param payload:    Reference on updated event handler payload.
        :rtype:  dict
        :return: Reference on dictionary which contain handler information provided by PubNub
                 service.
        """
        # Append handler identifier to payload.
        payload['id'] = handler_id
        # Update event handler information.
        self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id,
                                                               handler_id=handler_id),
                     http_method='PUT', data=payload)

    def delete_event_handler(self, keyset_id, handler_id):
        """Remove event handler from target block.

        :type keyset_id:   int
        :param keyset_id:  Reference on unique identifier of keyset from which event handler data
                           should be removed.
        :type handler_id:  int
        :param handler_id: Reference on unique identifier of event handler which should be removed.
        """
        self.request(api_endpoint=PubNubEndpoint.event_handler(keyset_id=keyset_id,
                                                               handler_id=handler_id),
                     http_method='DELETE')

    def request(self, api_endpoint, http_method='GET', data=None, ignored_status_codes=list()):
        """Construct request to get access to PubNub's REST API and pre-process service response.

        :type  api_endpoint:         str
        :param api_endpoint:         Represent URI path to REST API endpoint (relative to base API
                                     URL 'PUBNUB_API_URL').
        :type  http_method:          str
        :param http_method:          Represent HTTP request method (GET, POST, PUT, DELETE).
        :type  data:                 dict
        :param data:                 Data which should be sent with in case if 'POST' has been
                                     passed to 'method'.
        :type  ignored_status_codes: list
        :param ignored_status_codes: Status code numbers which shouldn't be handled as error during
                                     initial request processing.
        :rtype:                      dict
        :return:                     PubNub API processing results.
        """
        response = None
        error_message = None
        url = "{0}{1}".format(PUBNUB_API_URL, api_endpoint)
        headers = {'Accept': 'application/json'}
        if ZLIB_AVAILABLE:
            headers.update({'Accept-Encoding': 'gzip,deflate'})
        if data:
            headers.update({'Content-Type': 'application/json'})
            # Prepare POST data if required (if provided).
            try:
                post_json_data = self.module.jsonify(data)
            except ValueError as exc:
                exc_msg = exc.message if hasattr(exc, 'message') else exc.args[0]
                error_message = 'Unable JSON encode POST body: {0}. Body: {1}'.format(exc_msg, data)
        else:
            post_json_data = None

        # Authorize request if required.
        if self.session:
            headers['X-Session-Token'] = self.session

        res_stream, res_inf = fetch_url(self.module, url=url, data=post_json_data, headers=headers,
                                        method=http_method, force=True)
        if res_inf['status'] >= 400 and res_inf['status'] not in ignored_status_codes:
            # Process API call error.
            descr = None
            try:
                if _object_value(obj=res_inf, key='body'):
                    descr = self.module.from_json(to_text(res_inf['body']))
            except ValueError:
                error_message = _object_value(obj=res_inf, key='body')
            if descr:
                error_message = _object_value(obj=descr, key='message')
        elif not res_stream:
            error_message = '{0} ({1})'.format(_object_value(obj=res_inf, key='msg'),
                                               _object_value(obj=res_inf, key='url'))
        else:
            raw_response = _decompress_if_possible(res_stream.read(), res_inf)
            if not raw_response:
                error_message = 'Unexpected response: Empty PubNub service response.'
            else:
                try:
                    response = self.module.from_json(to_text(raw_response))
                except (ValueError, TypeError) as exc:
                    exc_msg = exc.message if hasattr(exc, 'message') else exc.args[0]
                    error_message = "Unexpected response: {0}: {1}".format(exc_msg, raw_response)
        if error_message:
            self.module.fail_json(changed=self.state_changed, msg=error_message,
                                  url=_object_value(obj=res_inf, key='url'), headers=headers,
                                  status=res_inf['status'], post_body=data,
                                  module_cache=dict(self.account), inf=res_inf)

        return response


def _is_equal(value1, value2):
    """Check whether passed values are equal or not.

    :param value1: First value against which check should be done.
    :param value2: Second value against which check should be done.
    :rtype:  bool
    :return: True in case if passed objects are equal.
    """
    is_equal = value1 is not None and value2 is not None
    if PY3:
        value1_collection_type = _collection_type(value1)
        value2_collection_type = _collection_type(value2)
        if is_equal and value1_collection_type is not None and value2_collection_type is not None:
            is_equal = value1_collection_type == value2_collection_type
            if is_equal:
                is_equal = len(value1) == len(value2)
                if is_equal and value1_collection_type == dict:
                    for key in value1:
                        is_equal = _is_equal(value1[key], value2[key])
                        if not is_equal:
                            break
                if is_equal and value1_collection_type in [list, tuple]:
                    for idx, value in value1:
                        is_equal = _is_equal(value, value2[idx])
                        if not is_equal:
                            break
        elif is_equal:
            is_equal = value1 == value2
    elif is_equal:
        is_equal = value1 == value2

    return is_equal


def _collection_type(value):
    """Retrieve which collection type value represent.

    Check whether value is collection and return what type.
    :param value: Reference on value which should be checked.
    :rtype:  class | None
    :return: Collection type.
    """
    collection_type = dict if isinstance(value, dict) else None
    collection_type = collection_type or list if isinstance(value, list) else None

    return collection_type or tuple if isinstance(value, tuple) else None


def _object_value(obj, key=None, default=None, treat_as_key_path=True, lowercase_keys=False):
    """Retrieve value which is stored under specified 'key'.

    Function allow to handle case when 'dct' is None and can't respond to 'get()'.
    :param obj:               Reference on object for which value should be retrieved.
    :param key:               str
    :param key:               Reference on key which should be used to fetch value from dictionary.
                              Key can be specified as key-path by joining path components with '.'.
    :param default:           Reference on value which should be returned in case if no value has
                              been found for 'key'.
    :type treat_as_key_path:  bool
    :param treat_as_key_path: Whether passed key should be treated as key-path and retrieved
                              recursively if required.
    :type lowercase_keys:     bool
    :param lowercase_keys:    Whether object's keys should be converted to lowercase before trying
                              to fetch value from it.
    :return: Reference on value which is stored for 'key' or 'None' in case if dictionary is 'None'
             or no value for 'key'.
    """
    if lowercase_keys:
        lkobj = dict()
        for okey, ovalue in obj.items():
            lkobj[okey.lower()] = ovalue
        obj = lkobj

    value = obj if treat_as_key_path else obj.get(key)
    if value is not None:
        if key:
            for part in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(part) if value.get(part) is not None else default
                elif isinstance(value, tuple) or isinstance(value, list):
                    index = int(part)
                    value = value[index] if index < len(value) else default
                if default is not None and value and value == default:
                    break
        else:
            value = default
    else:
        value = default

    return value


def _values(dct, keys):
    """Extract values for specified list of fields.

    Try get from  passed 'dict' all values which is stored under specified 'keys'.
    :type dct:   dict
    :param dct:  Reference on dictionary from which values should be retrieved.
    :type keys:  list
    :param keys: Reference on list of
    :rtype:  list
    :return: List of values which is stored in 'dct' under specified 'keys'.
    """
    return list(dct.get(key) for key in keys)


def _content_of_file_at_path(path):
    """Read file content.

    Try read content of file at specified path.
    :type path:  str
    :param path: Full path to location of file which should be read'ed.
    :rtype:  content
    :return: File content or 'None'
    """
    content = None
    if path and os.path.exists(path):
        with open(path, mode="rt") as opened_file:
            b_content = opened_file.read()
            try:
                content = to_text(b_content, errors='surrogate_or_strict')
            except UnicodeError:
                pass

    return content


def _decompress_if_possible(data, information):
    """Try decompress provided data.

    Depending from whether 'zlib' module available or not provided data can be decompressed or
    returned as-is.
    :type  data:  str
    :param data: Reference on object which should be decompressed if possible.
    :type information:  dict
    :param information: Reference on dictionary which contain additional information about processed
                        data.
    :rtype:  str
    :return: Decompressed object content or same object if 'zlib' not available.
    """
    encoding = _object_value(obj=information, key='content-encoding', lowercase_keys=True)
    return zlib.decompress(data, 16 + zlib.MAX_WBITS) if encoding in ['gzip', 'deflate'] else data


def main():
    fields = PubNubAPIClient.authorization_fields()
    fields.update(dict(application=dict(required=True, type='str'),
                       keyset=dict(required=True, type='str'),
                       state=dict(default='present', type='str',
                                  choices=['start', 'stop', 'present', 'absent']),
                       name=dict(required=True, type='str'), description=dict(type='str'),
                       event_handlers=dict(default=list(), type='list'),
                       changes=dict(default=dict(), type='dict'),
                       cache=dict(default=dict(), type='dict'),
                       validate_certs=dict(default=True, type='bool')))
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

    module_cache = None
    if _object_value(obj=module.params, key='cache.module_cache'):
        module_cache = copy.deepcopy(module.params['cache']['module_cache'])
    account = PubNubAccount(module, cache=module_cache)
    if not module_cache:
        if module.params['email'] and module.params['password']:
            account.login(email=module.params['email'], password=module.params['password'])
        else:
            module.fail_json(msg='Missing account credentials.',
                             description='It looks like not account credentials has been passed'
                                         'or \'cache\' field doesn\'t have result of previous '
                                         'module call.')
    # Retrieve reference on target application (the one which user decided to manage).
    application = account.current_application
    application.active_keyset = application.current_keyset

    # Retrieve reference on target block (the one which used decided to manager).
    block = application.active_keyset.current_block
    is_new_block = not block and module.params['state'] != 'absent'

    # Create new block if required.
    if is_new_block:
        if _object_value(obj=module.params, key='description'):
            description = module.params['description']
        else:
            description = 'New block'
        block = PubNubBlock(module=module, keyset=application.active_keyset,
                            name=module.params['name'], description=description)
        application.active_keyset.add_block(block)

    # Remove block if required.
    if module.params['state'] == 'absent' and block:
        application.active_keyset.remove_block(block)
        block = None

    if block:
        # Apply block changed if required.
        block.apply_changes()

        # Update event-handlers if required.
        block.update_event_handlers(module.params['event_handlers'])

    # Update block operation state if required.
    if block and not is_new_block:
        if module.params['state'] == 'start':
            block.start()
        elif module.params['state'] == 'stop':
            block.stop()
    account.save()

    module.exit_json(changed=account.changed, module_cache=dict(account))


if __name__ == '__main__':
    main()
