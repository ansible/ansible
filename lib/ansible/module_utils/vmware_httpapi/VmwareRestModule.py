# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Paul Knight <paul.knight@delaware.gov>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import sys

from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_native

# VMware ReST APIs
#
# Describes each supported VMware ReST APIs and lists its base URL. All
# vSphere ReST APIs begin with '/rest'.
API = dict(
    appliance=dict(base='/rest/appliance'),
    cis=dict(base='/rest/com/vmware/cis'),
    content=dict(base='/rest/com/vmware/content'),
    vapi=dict(base='/rest'),
    vcenter=dict(base='/rest/vcenter'),
    vrops=dict(base='/suiteapi')
)

# Query Filters
#
# This dictionary identifies every valid filter that can be applied to a
# vSphere ReST API query. Each filter has a name, which may be the same
# depending on the type object; an id of the value specified; a type,
# which is typically either a string or a list.  If it is a string, the
# format of the expected values is provided as a regex.
FILTER = dict(
    clusters=dict(
        name='clusters',
        id='id',
        type='str',
        format=r'domain\-[0-9a-fA-F]+',
    ),
    connection_states=dict(
        name='connection_states',
        id='connection state',
        type='list',
        choices=[
            'CONNECTED',
            'DISCONNECTED',
            'NOT_RESPONDING',
        ],
    ),
    datacenters=dict(
        name='datacenters',
        id='id',
        type='str',
        format=r'datacenter\-[0-9a-fA-F]+',
    ),
    datastore_types=dict(
        name='types',
        id='type',
        type='list',
        choices=[
            '',
            'CIFS',
            'NFS',
            'NFS41',
            'VFFS',
            'VMFS',
            'VSAN',
            'VVOL',
        ]
    ),
    datastores=dict(
        name='datastores',
        id='id',
        type='str',
        format=r'datastore\-[0-9a-fA-F]+',
    ),
    folder_types=dict(
        name='type',
        id='type',
        type='list',
        choices=[
            '',
            'DATACENTER',
            'DATASTORE',
            'HOST',
            'NETWORK',
            'VIRTUAL_MACHINE',
        ]
    ),
    folders=dict(
        name='folders',
        id='id',
        type='str',
        format=r'group\-[hnv][0-9a-fA-F]+',
    ),
    hosts=dict(
        name='hosts',
        id='id',
        type='str',
        format=r'host\-[0-9a-fA-F]+',
    ),
    names=dict(
        name='names',
        id='name',
        type='str',
        format=r'.+',
    ),
    network_types=dict(
        name='types',
        id='type',
        type='list',
        choices=[
            'DISTRIBUTED_PORTGROUP',
            'OPAQUE_NETWORK',
            'STANDARD_PORTGROUP',
        ],
    ),
    networks=dict(
        name='networks',
        id='id',
        type='str',
        format=r'[dvportgroup|network]\-[0-9a-fA-F]+',
    ),
    parent_folders=dict(
        name='parent_folders',
        id='id',
        type='str',
        format=r'group\-[hnv][0-9a-fA-F]+',
    ),
    parent_resource_pools=dict(
        name='parent_resource_pools',
        id='id',
        type='str',
        format=r'resgroup\-[0-9a-fA-F]+',
    ),
    policies=dict(
        name='policies',
        id='GUID',
        type='str',
        format=(r'[0-9a-fA-F]{8}'
                r'\-[0-9a-fA-F]{4}'
                r'\-[0-9a-fA-F]{4}'
                r'\-[0-9a-fA-F]{4}'
                r'\-[0-9a-fA-F]{12}'),
    ),
    power_states=dict(
        name='power_states',
        id='power state',
        type='list',
        choices=[
            '',
            'POWERED_OFF',
            'POWERED_ON',
            'SUSPENDED',
        ],
    ),
    resource_pools=dict(
        name='resource_pools',
        id='id',
        type='str',
        format=r'resgroup\-[0-9a-fA-F]+',
    ),
    status=dict(
        name='status',
        id='status',
        type='list',
        choices=[
            'COMPLIANT',
            'NON_COMPLIANT',
            'NOT_APPLICABLE',
            'UNKNOWN',
            'UNKNOWN_COMPLIANCE',
            'OUT_OF_DATE',
        ],
    ),
    vms=dict(
        name='vms',
        id='id',
        type='str',
        format=r'vm\-[0-9a-fA-F]+',
    ),
)

# vSphere Inventory Objects
#
# This dictionary lists the queryable vSphere inventory objects.  Each
# object identifies the API it is managed through, its URL off of the
# API's base, and a list of filters that are valid for this particular
# object.
#
# NOTE:  This will be replaced with a class factory pattern as get_id()
# and the get_url() family are tied to this structure.
INVENTORY = dict(
    category=dict(
        api='cis',
        url='/tagging/category',
        filters=[],
    ),
    cluster=dict(
        api='vcenter',
        url='/cluster',
        filters=[
            'clusters',
            'datacenters',
            'folders',
            'names',
        ],
    ),
    content_library=dict(
        api='content',
        url='/library',
        filters=[],
    ),
    content_type=dict(
        api='content',
        url='/type',
        filters=[],
    ),
    datacenter=dict(
        api='vcenter',
        url='/datacenter',
        filters=[
            'datacenters',
            'folders',
            'names',
        ],
    ),
    datastore=dict(
        api='vcenter',
        url='/datastore',
        filters=[
            'datacenters',
            'datastore_types',
            'datastores',
            'folders',
            'names',
        ],
    ),
    folder=dict(
        api='vcenter',
        url='/folder',
        filters=[
            'datacenters',
            'folder_types',
            'folders',
            'names',
            'parent_folders',
        ],
    ),
    host=dict(
        api='vcenter',
        url='/host',
        filters=[
            'clusters',
            'connection_states',
            'datacenters',
            'folders',
            'hosts',
            'names',
        ],
    ),
    local_library=dict(
        api='content',
        url='/local-library',
        filters=[],
    ),
    network=dict(
        api='vcenter',
        url='/network',
        filters=[
            'datacenters',
            'folders',
            'names',
            'network_types',
            'networks',
        ],
    ),
    resource_pool=dict(
        api='vcenter',
        url='/resource-pool',
        filters=[
            'clusters',
            'datacenters',
            'hosts',
            'names',
            'parent_resource_pools',
            'resource_pools',
        ]
    ),
    storage_policy=dict(
        api='vcenter',
        url='/storage/policies',
        filters=[
            'policies',
            'status',
            'vms',
        ],
    ),
    subscribed_library=dict(
        api='content',
        url='/subscribed-library',
        filters=[],
    ),
    tag=dict(
        api='cis',
        url='/tagging/tag',
        filters=[],
    ),
    session=dict(
        api='cis',
        url='/session',
        filters=[],
    ),
    vm=dict(
        api='vcenter',
        url='/vm',
        filters=[
            'clusters',
            'datacenters',
            'folders',
            'hosts',
            'names',
            'power_states',
            'resource_pools',
            'vms',
        ],
    ),
)


class VmwareRestModule(AnsibleModule):

    def __init__(self, is_multipart=False, use_object_handler=False, *args, **kwargs):
        '''Constructor - This module mediates interactions with the
        VMware httpapi connector plugin, implementing VMware's ReST API.

        :module: VmwareRestModule extended from AnsibleModule.
        :kw is_multipart: Indicates whether module makes multiple API calls.
            Default False
        :kw use_object_handler: Indicates whether module supports
            multiple object types.  Default False
        '''
        # Initialize instance arguments
        self.is_multipart = is_multipart
        self.use_object_handler = use_object_handler

        # Output of module
        self.result = {}

        # Current key of output
        self.key = None

        # Current information going to httpapi
        self.request = dict(
            url=None,
            filter=None,
            data={},
            method=None,
        )

        # Last response from httpapi
        self.response = dict(
            status=None,
            data={},
        )

        # Initialize AnsibleModule superclass before params
        super(VmwareRestModule, self).__init__(*args, **kwargs)

        # Turn on debug if not specified, but ANSIBLE_DEBUG is set
        self.module_debug = {}
        if self._debug:
            self.warn('Enable debug output because ANSIBLE_DEBUG was set.')
            self.params['log_level'] = 'debug'
        self.log_level = self.params['log_level']

        # Params
        #
        # REQUIRED: Their absence will chuck a rod
        self.allow_multiples = self.params['allow_multiples']
        self.status_code = self.params['status_code']
        # OPTIONAL: Use params.get() to gracefully fail
        self.filters = self.params.get('filters')
        self.state = self.params.get('state')

        # Initialize connection via httpapi connector. See "REST API Calls"
        try:
            self._connection = Connection(self._socket_path)
        except Exception as e:
            self.fail(msg=to_native(e))

        # Register default status handlers. See "Dynamic Status Handlers"
        self._status_handlers = {
            'success': self.handle_default_success,
            '401': self.handle_default_401,
            '404': self.handle_default_404,
            'default': self.handle_default_generic,
        }
        if self.use_object_handler:
            self._status_handlers['default'] = self.handle_default_object

    # Debugging
    #
    # Tools to handle debugging output from the APIs.
    def _mod_debug(self, key, **kwargs):
        self.module_debug[key] = kwargs
        if 'module_debug' not in self.module_debug:
            self.module_debug = dict(key=kwargs)
        else:
            self.module_debug.update(key=kwargs)

    def _api_debug(self):
        '''Route debugging output to the module output.

        NOTE: Adding self.path to result['path'] causes an absent in
        output.  Adding response['data'] causes infinite loop.
        '''
        return dict(
            url=self.request['url'],
            filter=self.request['filter'],
            data=self.request['data'],
            method=self.request['method'],
            status=self.response['status'],
            state=self.state,
        )

    # Dynamic Status Handlers
    #
    # A handler is registered by adding its key, either a module-
    # generated value, or the string representation of the status code;
    # and the name of the handler function.  The provided handlers are
    #   success     defined, by default, as a status code of 200, but
    #               can be redefined, per module, using the status_code
    #               parameter in that module's argument_spec.
    #   401         Unauthorized access to the API.
    #   404         Requested object or API was not found.
    #   default     Any status code not otherwise identified.
    # The default handlers are named 'handle_default_[status_code]'.
    # User defined handlers should use 'handle_[status_code]' as a
    # convention.  Note that if the module expects to handle more than
    # one type of object, a default object handler replaces the default
    # generic handler.
    #
    # Handlers do not take any arguments, instead using the instance's
    # variables to determine the status code and any additional data,
    # like object_type.  To create or replace a handler, extend this
    # class, define the new handler and use the provided 'set_handler'
    # method.  User handlers can also chain to the default handlers if
    # desired.
    def set_handler(self, status_key, handler):
        '''Registers the handler to the status_key'''
        self._status_handlers[status_key] = handler

    def _use_handler(self):
        '''Invokes the appropriate handler based on status_code'''
        if self.response['status'] in self.status_code:
            status_key = 'success'
        else:
            status_key = str(self.response['status'])
        if status_key in self._status_handlers.keys():
            self._status_handlers[status_key]()
        else:
            self._status_handlers['default']()

    def handle_default_success(self):
        '''Default handler for all successful status codes'''
        self.result[self.key] = self.response['data']
        if self.log_level == 'debug':
            self.result[self.key].update(
                debug=self._api_debug()
            )
        if not self.is_multipart:
            self.exit()

    def handle_default_401(self):
        '''Default handler for Unauthorized (401) errors'''
        self.fail(msg="Unable to authenticate. Provided credentials are not valid.")

    def handle_default_404(self):
        '''Default handler for Not-Found (404) errors'''
        self.fail(msg="Requested object was not found.")

    def handle_default_generic(self):
        '''Catch-all handler for all other status codes'''
        msg = self.response['data']['value']['messages'][0]['default_message']
        self.fail(msg=msg)

    def handle_default_object(self):
        '''Catch-all handler capable of distinguishing multiple objects'''
        try:
            msg = self.response['data']['value']['messages'][0]['default_message']
        except (KeyError, TypeError):
            msg = 'Unable to find the %s object specified due to %s' % (self.key, self.response)
        self.fail(msg=msg)

    def handle_object_key_error(self):
        '''Lazy exception handler'''
        msg = ('Please specify correct object type to get information, '
               'choices are [%s].' % ", ".join(list(INVENTORY.keys())))
        self.fail(msg=msg)

    # REST API Calls
    #
    # VMware's REST API uses GET, POST, PUT, PATCH and DELETE http
    # calls to read, create, update and delete objects and their
    # attributes.  These calls are implemented as functions here.
    def get(self, url='/rest', key='result'):
        '''Sends a GET request to the httpapi plugin connection to the
        specified URL. If successful, the returned data will be placed
        in the output under the specified key.
        '''
        self.request.update(
            url=url,
            data={},
            method='GET',
        )
        self.key = key
        self.response['status'], self.response['data'] = self._connection.send_request(url, {}, method='GET')
        self._use_handler()

    def post(self, url='/rest', data=None, key='result'):
        '''Sends a POST request to the httpapi plugin connection to the
        specified URL, with the supplied data.  If successful, any
        returned data will be placed in the output under the specified
        key.
        '''
        self.request.update(
            url=url,
            data=data,
            method='POST',
        )
        self.key = key
        try:
            self.response['status'], self.response['data'] = self._connection.send_request(url, data, method='POST')
        except Exception as e:
            self.fail(msg=to_native(e))
        self._use_handler()

    def put(self, url='/rest', data=None, key='result'):
        '''Sends a PUT request to the httpapi plugin connection to the
        specified URL, with the supplied data.  If successful, any
        returned data will be placed in the output under the specified
        key.
        '''
        self.request.update(
            url=url,
            data=data,
            method='PUT',
        )
        self.key = key
        self.response['status'], self.response['data'] = self._connection.send_request(url, data, method='PUT')
        self._use_handler()

    def delete(self, url='/rest', data='result', key='result'):
        '''Sends a DELETE request to the httpapi plugin connection to
        the specified URL, with the supplied data.  If successful, any
        returned data will be placed in the output under the specified
        key.
        '''
        self.request.update(
            url=url,
            data=data,
            method='DELETE',
        )
        self.key = key
        self.response['status'], self.response['data'] = self._connection.send_request(url, data, method='DELETE')
        self._use_handler()

    def get_id(self, object_type, name):
        '''Find id(s) of object(s) with given name.  allow_multiples
        determines whether multiple IDs are returned or not.

        :kw object_type: The inventory object type whose id is desired.
        :kw name: The name of the object(s) to be retrieved.
        :returns: a list of strings representing the IDs of the objects.
        '''

        try:
            url = (API[INVENTORY[object_type]['api']]['base']
                   + INVENTORY[object_type]['url'])
            if '/' in name:
                name.replace('/', '%2F')
            url += '&filter.names=' + name
        except KeyError:
            self.fail(msg='object_type must be one of [%s].'
                      % ", ".join(list(INVENTORY.keys())))

        status, data = self._connection.send_request(url, {}, method='GET')
        if status != 200:
            self.request.update(url=url, data={}, method='GET')
            self.response.update(status=status, data=data)
            self.handle_default_generic()

        num_items = len(data['value'])
        if not self.allow_multiples and num_items > 1:
            msg = ('Found %d objects of type %s with name %s. '
                   'Set allow_multiples to True if this is expected.'
                   % (num_items, object_type, name))
            self.fail(msg=msg)

        ids = []
        for i in range(num_items):
            ids += data[i][object_type]
        return ids

    def _build_filter(self, object_type):
        '''Builds a filter from the optionally supplied params'''
        if self.filters:
            try:
                first = True
                for filter in self.filters:
                    for key in list(filter.keys()):
                        filter_key = key.lower()
                        # Check if filter is valid for current object type or not
                        if filter_key not in INVENTORY[object_type]['filters']:
                            msg = ('%s is not a valid %s filter, choices are [%s].'
                                   % (key, object_type, ", ".join(INVENTORY[object_type]['filters'])))
                            self.fail(msg=msg)
                        # Check if value is valid for the current filter
                        if ((FILTER[filter_key]['type'] == 'str' and not re.match(FILTER[filter_key]['format'], filter[key])) or
                                (FILTER[filter_key]['type'] == 'list' and filter[key] not in FILTER[filter_key]['choices'])):
                            msg = ('%s is not a valid %s %s' % (filter[key], object_type, FILTER[filter_key]['name']))
                            self.fail(msg=msg)
                        if first:
                            self.request['filter'] = '?'
                            first = False
                        else:
                            self.request['filter'] += '&'
                        # Escape characters
                        if '/' in filter[key]:
                            filter[key].replace('/', '%2F')
                        self.request['filter'] += ('filter.%s=%s'
                                                   % (FILTER[filter_key]['name'], filter[key]))
            except KeyError:
                self.handle_object_key_error()
        else:
            self.request['filter'] = None
        return self.request['filter']

    def get_url(self, object_type, with_filter=False):
        '''Retrieves the URL of a particular inventory object with or without filter'''
        try:
            self.url = (API[INVENTORY[object_type]['api']]['base']
                        + INVENTORY[object_type]['url'])
            if with_filter:
                self.url += self._build_filter(object_type)
        except KeyError:
            self.handle_object_key_error()
        return self.url

    def get_url_with_filter(self, object_type):
        '''Same as get_url, only with_filter is explicitly set'''
        return self.get_url(object_type, with_filter=True)

    def reset(self):
        '''Clears the decks for next request'''
        self.request.update(
            url=None,
            data={},
            method=None,
        )
        self.response.update(
            status=None,
            data={},
        )

    def fail(self, msg):
        if self.log_level == 'debug':
            if self.request['url'] is not None:
                self.result['debug'] = self._api_debug()
        AnsibleModule.fail_json(self, msg=msg, **self.result)

    def exit(self):
        '''Called to end client interaction'''
        if 'invocation' not in self.result:
            self.result['invocation'] = {
                'module_args': self.params,
                'module_kwargs': {
                    'is_multipart': self.is_multipart,
                    'use_object_handler': self.use_object_handler,
                }
            }
        if self.log_level == 'debug':
            if not self.is_multipart:
                self.result['invocation'].update(debug=self._api_debug())
            if self.module_debug:
                self.result['invocation'].update(module_debug=self.module_debug)

        AnsibleModule.exit_json(self, **self.result)

    def _merge_dictionaries(self, a, b):
        new = a.copy()
        new.update(b)
        return new

    @staticmethod
    def create_argument_spec(use_filters=False, use_state=False):
        '''Provide a default argument spec for this module.  Filters and
        state are optional parameters dependinf on the module's needs.
        Additional parameters can be added.  The supplied parameters can
        have defaults changed or choices pared down, but should not be
        removed.
        '''

        argument_spec = dict(
            allow_multiples=dict(type='bool', default=False),
            log_level=dict(type='str',
                           choices=['debug', 'info', 'normal'],
                           default='normal'),
            status_code=dict(type='list', default=[200]),
        )
        if use_filters:
            argument_spec.update(filters=dict(type='list', default=[]))
        if use_state:
            argument_spec.update(state=dict(type='list',
                                            choices=['absent', 'present', 'query'],
                                            default='query'))
        return argument_spec
