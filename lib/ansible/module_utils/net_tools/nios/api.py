# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2018 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import os
from functools import partial
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_text

try:
    from infoblox_client.connector import Connector
    from infoblox_client.exceptions import InfobloxException
    HAS_INFOBLOX_CLIENT = True
except ImportError:
    HAS_INFOBLOX_CLIENT = False

# defining nios constants
NIOS_DNS_VIEW = 'view'
NIOS_NETWORK_VIEW = 'networkview'
NIOS_HOST_RECORD = 'record:host'
NIOS_IPV4_NETWORK = 'network'
NIOS_IPV6_NETWORK = 'ipv6network'
NIOS_ZONE = 'zone_auth'

NIOS_PROVIDER_SPEC = {
    'host': dict(),
    'username': dict(),
    'password': dict(no_log=True),
    'ssl_verify': dict(type='bool', default=False),
    'silent_ssl_warnings': dict(type='bool', default=True),
    'http_request_timeout': dict(type='int', default=10),
    'http_pool_connections': dict(type='int', default=10),
    'http_pool_maxsize': dict(type='int', default=10),
    'max_retries': dict(type='int', default=3),
    'wapi_version': dict(default='2.1'),
    'max_results': dict(type='int', default=1000)
}


def get_connector(*args, **kwargs):
    ''' Returns an instance of infoblox_client.connector.Connector
    :params args: positional arguments are silently ignored
    :params kwargs: dict that is passed to Connector init
    :returns: Connector
    '''
    if not HAS_INFOBLOX_CLIENT:
        raise Exception('infoblox-client is required but does not appear '
                        'to be installed.  It can be installed using the '
                        'command `pip install infoblox-client`')

    if not set(kwargs.keys()).issubset(NIOS_PROVIDER_SPEC.keys()):
        raise Exception('invalid or unsupported keyword argument for connector')
    for key, value in iteritems(NIOS_PROVIDER_SPEC):
        if key not in kwargs:
            # apply default values from NIOS_PROVIDER_SPEC since we cannot just
            # assume the provider values are coming from AnsibleModule
            if 'default' in value:
                kwargs[key] = value['default']

            # override any values with env variables unless they were
            # explicitly set
            env = ('INFOBLOX_%s' % key).upper()
            if env in os.environ:
                kwargs[key] = os.environ.get(env)

    return Connector(kwargs)


def normalize_extattrs(value):
    ''' Normalize extattrs field to expected format
    The module accepts extattrs as key/value pairs.  This method will
    transform the key/value pairs into a structure suitable for
    sending across WAPI in the format of:
        extattrs: {
            key: {
                value: <value>
            }
        }
    '''
    return dict([(k, {'value': v}) for k, v in iteritems(value)])


def flatten_extattrs(value):
    ''' Flatten the key/value struct for extattrs
    WAPI returns extattrs field as a dict in form of:
        extattrs: {
            key: {
                value: <value>
            }
        }
    This method will flatten the structure to:
        extattrs: {
            key: value
        }
    '''
    return dict([(k, v['value']) for k, v in iteritems(value)])


class WapiBase(object):
    ''' Base class for implementing Infoblox WAPI API '''
    provider_spec = {'provider': dict(type='dict', options=NIOS_PROVIDER_SPEC)}

    def __init__(self, provider):
        self.connector = get_connector(**provider)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if name.startswith('_'):
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, name))
            return partial(self._invoke_method, name)

    def _invoke_method(self, name, *args, **kwargs):
        try:
            method = getattr(self.connector, name)
            return method(*args, **kwargs)
        except InfobloxException as exc:
            if hasattr(self, 'handle_exception'):
                self.handle_exception(name, exc)
            else:
                raise


class WapiLookup(WapiBase):
    ''' Implements WapiBase for lookup plugins '''
    pass


class WapiInventory(WapiBase):
    ''' Implements WapiBase for dynamic inventory script '''
    pass


class WapiModule(WapiBase):
    ''' Implements WapiBase for executing a NIOS module '''
    def __init__(self, module):
        self.module = module
        provider = module.params['provider']
        try:
            super(WapiModule, self).__init__(provider)
        except Exception as exc:
            self.module.fail_json(msg=to_text(exc))

    def handle_exception(self, method_name, exc):
        ''' Handles any exceptions raised
        This method will be called if an InfobloxException is raised for
        any call to the instance of Connector and also, in case of generic
        exception. This method will then gracefully fail the module.
        :args exc: instance of InfobloxException
        '''
        if ('text' in exc.response):
            self.module.fail_json(
                msg=exc.response['text'],
                type=exc.response['Error'].split(':')[0],
                code=exc.response.get('code'),
                operation=method_name
            )
        else:
            self.module.fail_json(msg=to_native(exc))

    def run(self, ib_obj_type, ib_spec):
        ''' Runs the module and performans configuration tasks
        :args ib_obj_type: the WAPI object type to operate against
        :args ib_spec: the specification for the WAPI object as a dict
        :returns: a results dict
        '''

        update = new_name = None
        state = self.module.params['state']
        if state not in ('present', 'absent'):
            self.module.fail_json(msg='state must be one of `present`, `absent`, got `%s`' % state)

        result = {'changed': False}

        obj_filter = dict([(k, self.module.params[k]) for k, v in iteritems(ib_spec) if v.get('ib_req')])

        if('name' in obj_filter):
            ib_obj_ref, update, new_name = self.get_object_ref(ib_obj_type, obj_filter, ib_spec)
        else:
            ib_obj_ref = self.get_object(ib_obj_type, obj_filter.copy(), return_fields=ib_spec.keys())

        if ib_obj_ref:
            current_object = ib_obj_ref[0]
            if 'extattrs' in current_object:
                current_object['extattrs'] = flatten_extattrs(current_object['extattrs'])
            ref = current_object.pop('_ref')
        else:
            current_object = obj_filter
            ref = None

        proposed_object = {}
        for key, value in iteritems(ib_spec):
            if self.module.params[key] is not None:
                if 'transform' in value:
                    proposed_object[key] = value['transform'](self.module)
                else:
                    proposed_object[key] = self.module.params[key]

        # checks if the name's field has been updated
        if update and new_name:
            proposed_object['name'] = new_name

        res = None
        modified = not self.compare_objects(current_object, proposed_object)
        if 'extattrs' in proposed_object:
            proposed_object['extattrs'] = normalize_extattrs(proposed_object['extattrs'])
        if state == 'present':
            if ref is None:
                if not self.module.check_mode:
                    self.create_object(ib_obj_type, proposed_object)
                result['changed'] = True
            elif modified:
                if (ib_obj_type in (NIOS_HOST_RECORD, NIOS_NETWORK_VIEW, NIOS_DNS_VIEW)):
                    proposed_object = self.on_update(proposed_object, ib_spec)
                    res = self.update_object(ref, proposed_object)
                elif 'network_view' in proposed_object:
                    proposed_object.pop('network_view')
                if not self.module.check_mode and res is None:
                    proposed_object = self.on_update(proposed_object, ib_spec)
                    self.update_object(ref, proposed_object)
                result['changed'] = True

        elif state == 'absent':
            if ref is not None:
                if not self.module.check_mode:
                    self.delete_object(ref)
                result['changed'] = True

        return result

    def issubset(self, item, objects):
        ''' Checks if item is a subset of objects
        :args item: the subset item to validate
        :args objects: superset list of objects to validate against
        :returns: True if item is a subset of one entry in objects otherwise
            this method will return None
        '''
        for obj in objects:
            if isinstance(item, dict):
                if all(entry in obj.items() for entry in item.items()):
                    return True
            else:
                if item in obj:
                    return True

    def compare_objects(self, current_object, proposed_object):
        for key, proposed_item in iteritems(proposed_object):
            current_item = current_object.get(key)

            # if proposed has a key that current doesn't then the objects are
            # not equal and False will be immediately returned
            if current_item is None:
                return False

            elif isinstance(proposed_item, list):
                for subitem in proposed_item:
                    if not self.issubset(subitem, current_item):
                        return False

            elif isinstance(proposed_item, dict):
                return self.compare_objects(current_item, proposed_item)

            else:
                if current_item != proposed_item:
                    return False

        return True

    def get_object_ref(self, ib_obj_type, obj_filter, ib_spec):
        ''' this function gets and returns the current object based on name/old_name passed'''
        update = False
        old_name = new_name = None
        try:
            name_obj = self.module._check_type_dict(obj_filter['name'])
            old_name = name_obj['old_name']
            new_name = name_obj['new_name']
        except TypeError:
            name = obj_filter['name']

        if old_name and new_name:
            if (ib_obj_type == NIOS_HOST_RECORD):
                test_obj_filter = dict([('name', old_name), ('view', obj_filter['view'])])
            else:
                test_obj_filter = dict([('name', old_name)])
            # get the object reference
            ib_obj = self.get_object(ib_obj_type, test_obj_filter, return_fields=ib_spec.keys())
            if ib_obj:
                obj_filter['name'] = new_name
            else:
                test_obj_filter['name'] = new_name
                ib_obj = self.get_object(ib_obj_type, test_obj_filter, return_fields=ib_spec.keys())
            update = True
            return ib_obj, update, new_name
        if (ib_obj_type == NIOS_HOST_RECORD):
            test_obj_filter = dict([('name', name), ('view', obj_filter['view'])])
        else:
            test_obj_filter = dict([('name', name)])
        ib_obj = self.get_object(ib_obj_type, test_obj_filter.copy(), return_fields=ib_spec.keys())
        return ib_obj, update, new_name

    def on_update(self, proposed_object, ib_spec):
        ''' Event called before the update is sent to the API endpoing
        This method will allow the final proposed object to be changed
        and/or keys filtered before it is sent to the API endpoint to
        be processed.
        :args proposed_object: A dict item that will be encoded and sent
            the the API endpoint with the updated data structure
        :returns: updated object to be sent to API endpoint
        '''
        keys = set()
        for key, value in iteritems(proposed_object):
            update = ib_spec[key].get('update', True)
            if not update:
                keys.add(key)
        return dict([(k, v) for k, v in iteritems(proposed_object) if k not in keys])
