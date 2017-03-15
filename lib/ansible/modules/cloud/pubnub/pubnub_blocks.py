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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}



DOCUMENTATION = '''
---
module: pubnub_blocks
version_added: '2.2'
short_description: PubNub blocks management module.
description:
  - "This module allows Ansible to interface with the PubNub BLOCKS
  infrastructure by providing the following operations: create / remove,
  start / stop and rename for blocks and create / modify / remove for event
  handlers"
author:
  - PubNub <support@pubnub.com> (@pubnub)
  - Sergey Mamontov <sergey@pubnub.com> (@parfeon)
requirements:
  - "python >= 2.7"
  - "pubnub_blocks_client >= 1.0"
options:
  email:
    description:
      - Email from account for which new session should be started.
      - "Not required if C(cache) contains result of previous module call (in
      same play)."
    required: false
  password:
    description:
      - Password which match to account to which specified C(email) belong.
      - "Not required if C(cache) contains result of previous module call (in
      same play)."
    required: false
  cache:
    description: >
       In case if single play use blocks management module few times it is
       preferred to enabled 'caching' by making previous module to share
       gathered artifacts and pass them to this parameter.
    required: false
    default: {}
  application:
    description:
      - "Name of target PubNub application for which blocks configuration on
      specific C(keyset) will be done."
    required: true
  keyset:
    description:
      - Name of application's keys set which is bound to managed blocks.
    required: true
  state:
    description:
      - "Intended block state after event handlers creation / update process
      will be completed."
    required: false
    default: 'started'
    choices: ['started', 'stopped', 'present', 'absent']
  name:
    description:
      - Name of managed block which will be later visible on admin.pubnub.com.
    required: true
  description:
    description:
        - "Short block description which will be later visible on
        admin.pubnub.com. Used only if block doesn\'t exists and won\'t change
        description for existing block."
    required: false
    default: 'New block'
  event_handlers:
    description:
      - "List of event handlers which should be updated for specified block
      C(name)."
      - "Each entry for new event handler should contain: C(name), C(src),
      C(channels), C(event). C(name) used as event handler name which can be
      used later to make changes to it."
      - C(src) is full path to file with event handler code.
      - "C(channels) is name of channel from which event handler is waiting
      for events."
      - "C(event) is type of event which is able to trigger event handler:
      I(js-before-publish), I(js-after-publish), I(js-after-presence)."
      - "Each entry for existing handlers should contain C(name) (so target
      handler can be identified). Rest parameters (C(src), C(channels) and
      C(event)) can be added if changes required for them."
      - "It is possible to rename event handler by adding C(changes) key to
      event handler payload and pass dictionary, which will contain single key
      C(name), where new name should be passed."
      - "To remove particular event handler it is possible to set C(state) for
      it to C(absent) and it will be removed."
    required: false
    default: []
  changes:
    description:
      - "List of fields which should be changed by block itself (doesn't
      affect any event handlers)."
      - "Possible options for change is: C(name)."
    required: false
    default: {}
  validate_certs:
    description:
      - "This key allow to try skip certificates check when performing REST API
      calls. Sometimes host may have issues with certificates on it and this
      will cause problems to call PubNub REST API."
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
- name: Add '{{ event_handler_1_name }}' handler to '{{ block_name }}'
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
- name: Add '{{ event_handler_2_name }}' handler to '{{ block_name }}'
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
    state: started
'''

RETURN = '''
module_cache:
  description: "Cached account information. In case if with single play module
  used few times it is better to pass cached data to next module calls to speed
  up process."
  type: dict
'''
import copy
import os

# Import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import *

try:
    # Import PubNub BLOCKS client.
    from pubnub_blocks_client import Account, Application, Keyset, Block
    from pubnub_blocks_client import EventHandler
    import pubnub_blocks_client.exceptions as exceptions
    HAS_PUBNUB_BLOCKS_CLIENT = True
except ImportError:
    HAS_PUBNUB_BLOCKS_CLIENT = False


def pubnub_account(module):
    """Create and configure account if it is possible.

    :type module:  AnsibleModule
    :param module: Reference on module which contain module launch
                   information and status report methods.

    :rtype:  Account
    :return: Reference on initialized and ready to use account or 'None' in
             case if not all required information has been passed to block.
    """
    account = None
    params = module.params
    if params.get('cache') and params['cache'].get('module_cache'):
        account = Account()
        account.restore(cache=copy.deepcopy(params['cache']['module_cache']))
    elif params.get('email') and params.get('password'):
        account = Account(email=params.get('email'),
                          password=params.get('password'))
    else:
        err_msg = 'It looks like not account credentials has been passed or ' \
                  '\'cache\' field doesn\'t have result of previous module ' \
                  'call.'
        module.fail_json(msg='Missing account credentials.',
                         description=err_msg, changed=False)

    return account


def pubnub_application(module, account):
    """Retrieve reference on target application from account model.

    NOTE: In case if account authorization will fail or there is no
    application with specified name, module will exit with error.
    :type module:   AnsibleModule
    :param module:  Reference on module which contain module launch
                    information and status report methods.
    :type account:  Account
    :param account: Reference on PubNub account model from which reference
                    on application should be fetched.

    :rtype:  Application
    :return: Reference on initialized and ready to use application model.
    """
    application = None
    params = module.params
    try:
        application = account.application(params['application'])
    except (exceptions.AccountError, exceptions.GeneralPubNubError) as exc:
        exc_msg = _failure_title_from_exception(exc)
        exc_descr = exc.message if hasattr(exc, 'message') else exc.args[0]
        module.fail_json(msg=exc_msg, description=exc_descr,
                         changed=account.changed,
                         module_cache=dict(account))

    if application is None:
        err_fmt = 'There is no \'{0}\' application for {1}. Make sure what ' \
                  'correct application name has been passed. If application ' \
                  'doesn\'t exist you can create it on admin.pubnub.com.'
        email = account.owner.email
        module.fail_json(msg=err_fmt.format(params['application'], email),
                         changed=account.changed, module_cache=dict(account))

    return application


def pubnub_keyset(module, account, application):
    """Retrieve reference on target keyset from application model.

    NOTE: In case if there is no keyset with specified name, module will
    exit with error.
    :type module:       AnsibleModule
    :param module:      Reference on module which contain module launch
                        information and status report methods.
    :type account:      Account
    :param account:     Reference on PubNub account model which will be
                        used in case of error to export cached data.
    :type application:  Application
    :param application: Reference on PubNub application model from which
                        reference on keyset should be fetched.

    :rtype:  Keyset
    :return: Reference on initialized and ready to use keyset model.
    """
    params = module.params
    keyset = application.keyset(params['keyset'])
    if keyset is None:
        err_fmt = 'There is no \'{0}\' keyset for \'{1}\' application. Make ' \
                  'sure what correct keyset name has been passed. If keyset ' \
                  'doesn\'t exist you can create it on admin.pubnub.com.'
        module.fail_json(msg=err_fmt.format(params['keyset'],
                                            application.name),
                         changed=account.changed, module_cache=dict(account))

    return keyset


def pubnub_block(module, account, keyset):
    """Retrieve reference on target keyset from application model.

    NOTE: In case if there is no block with specified name and module
    configured to start/stop it, module will exit with error.
    :type module:   AnsibleModule
    :param module:  Reference on module which contain module launch
                    information and status report methods.
    :type account:  Account
    :param account: Reference on PubNub account model which will be used in
                    case of error to export cached data.
    :type keyset:   Keyset
    :param keyset:  Reference on keyset model from which reference on block
                    should be fetched.

    :rtype:  Block
    :return: Reference on initialized and ready to use keyset model.
    """
    block = None
    params = module.params
    try:
        block = keyset.block(params['name'])
    except (exceptions.KeysetError, exceptions.GeneralPubNubError) as exc:
        exc_msg = _failure_title_from_exception(exc)
        exc_descr = exc.message if hasattr(exc, 'message') else exc.args[0]
        module.fail_json(msg=exc_msg, description=exc_descr,
                         changed=account.changed, module_cache=dict(account))

    # Report error because block doesn't exists and at the same time
    # requested to start/stop.
    if block is None and params['state'] in ['started', 'stopped']:
        block_name = params.get('name')
        module.fail_json(msg="'{0}' block doesn't exists.".format(block_name),
                         changed=account.changed, module_cache=dict(account))

    if block is None and params['state'] == 'present':
        block = Block(name=params.get('name'),
                      description=params.get('description'))
        keyset.add_block(block)

    if block:
        # Update block information if required.
        if params.get('changes') and params['changes'].get('name'):
            block.name = params['changes']['name']
        if params.get('description'):
            block.description = params.get('description')

    return block


def pubnub_event_handler(block, data):
    """Retrieve reference on target event handler from application model.

    :type block:  Block
    :param block: Reference on block model from which reference on event
                  handlers should be fetched.
    :type data:   dict
    :param data:  Reference on dictionary which contain information about
                  event handler and whether it should be created or not.

    :rtype:  EventHandler
    :return: Reference on initialized and ready to use event handler model.
             'None' will be returned in case if there is no handler with
             specified name and no request to create it.
    """
    event_handler = block.event_handler(data['name'])

    # Prepare payload for event handler update.
    changed_name = (data.pop('changes').get('name')
                    if 'changes' in data else None)
    name = data.get('name') or changed_name
    channels = data.get('channels')
    event = data.get('event')
    code = _content_of_file_at_path(data.get('src'))
    state = data.get('state') or 'present'

    # Create event handler if required.
    if event_handler is None and state == 'present':
        event_handler = EventHandler(name=name, channels=channels, event=event,
                                     code=code)
        block.add_event_handler(event_handler)

    # Update event handler if required.
    if event_handler is not None and state == 'present':
        if name is not None:
            event_handler.name = name
        if channels is not None:
            event_handler.channels = channels
        if event is not None:
            event_handler.event = event
        if code is not None:
            event_handler.code = code

    return event_handler


def _failure_title_from_exception(exception):
    """Compose human-readable title for module error title.

    Title will be based on status codes if they has been provided.
    :type exception:  exceptions.GeneralPubNubError
    :param exception: Reference on exception for which title should be
                      composed.

    :rtype:  str
    :return: Reference on error tile which should be shown on module
             failure.
    """
    title = 'General REST API access error.'
    if exception.code == exceptions.PN_AUTHORIZATION_WRONG_CREDENTIALS:
        title = 'Authorization error (wrong credentials).'
    elif exception.code == exceptions.PN_KEYSET_BLOCKS_FETCH_DID_FAIL:
        title = 'Unable fetch list of blocks for keyset.'
    elif exception.code == exceptions.PN_BLOCK_CREATE_DID_FAIL:
        title = 'Block creation did fail.'
    elif exception.code == exceptions.PN_BLOCK_UPDATE_DID_FAIL:
        title = 'Block update did fail.'
    elif exception.code == exceptions.PN_BLOCK_REMOVE_DID_FAIL:
        title = 'Block removal did fail.'
    elif exception.code == exceptions.PN_BLOCK_START_STOP_DID_FAIL:
        title = 'Block start/stop did fail.'
    elif exception.code == exceptions.PN_EVENT_HANDLER_MISSING_FIELDS:
        title = 'Event handler creation did fail: missing fields.'
    elif exception.code == exceptions.PN_EVENT_HANDLER_CREATE_DID_FAIL:
        title = 'Event handler creation did fail.'
    elif exception.code == exceptions.PN_EVENT_HANDLER_UPDATE_DID_FAIL:
        title = 'Event handler update did fail.'
    elif exception.code == exceptions.PN_EVENT_HANDLER_REMOVE_DID_FAIL:
        title = 'Event handler removal did fail.'

    return title


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


def main():
    fields = dict(
        email=dict(default='', required=False, type='str'),
        password=dict(default='', required=False, type='str', no_log=True),
        application=dict(required=True, type='str'),
        keyset=dict(required=True, type='str'),
        state=dict(default='present', type='str',
                   choices=['started', 'stopped', 'present', 'absent']),
        name=dict(required=True, type='str'), description=dict(type='str'),
        event_handlers=dict(default=list(), type='list'),
        changes=dict(default=dict(), type='dict'),
        cache=dict(default=dict(), type='dict'),
        validate_certs=dict(default=True, type='bool'))
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)

    if not HAS_PUBNUB_BLOCKS_CLIENT:
        module.fail_json(msg='pubnub_blocks_client required for this module.')

    params = module.params

    # Initialize PubNub account instance.
    account = pubnub_account(module)
    # Try fetch application with which module should work.
    application = pubnub_application(module, account=account)
    # Try fetch keyset with which module should work.
    keyset = pubnub_keyset(module, account=account, application=application)
    # Try fetch block with which module should work.
    block = pubnub_block(module, account=account, keyset=keyset)
    is_new_block = block is not None and block.uid == -1

    # Check whether block should be removed or not.
    if block is not None and params['state'] == 'absent':
        keyset.remove_block(block)
        block = None

    if block is not None:
        # Update block information if required.
        if params.get('changes') and params['changes'].get('name'):
            block.name = params['changes']['name']

        # Process event changes to event handlers.
        for event_handler_data in params.get('event_handlers') or list():
            state = event_handler_data.get('state') or 'present'
            event_handler = pubnub_event_handler(data=event_handler_data,
                                                 block=block)
            if state == 'absent' and event_handler:
                block.delete_event_handler(event_handler)

    # Update block operation state if required.
    if block and not is_new_block:
        if params['state'] == 'started':
            block.start()
        elif params['state'] == 'stopped':
            block.stop()

    # Save current account state.
    if not module.check_mode:
        try:
            account.save()
        except (exceptions.AccountError, exceptions.KeysetError,
                exceptions.BlockError, exceptions.EventHandlerError,
                exceptions.GeneralPubNubError) as exc:
            exc_msg = _failure_title_from_exception(exc)
            exc_descr = exc.message if hasattr(exc, 'message') else exc.args[0]
            module.fail_json(msg=exc_msg, description=exc_descr,
                             changed=account.changed,
                             module_cache=dict(account))

    # Report module execution results.
    changed_will_change = account.changed or account.will_change
    module.exit_json(changed=changed_will_change, module_cache=dict(account))


if __name__ == '__main__':
    main()
