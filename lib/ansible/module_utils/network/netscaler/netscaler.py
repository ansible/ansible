# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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

import json
import re
import sys
import codecs
import copy

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

from ansible.module_utils.six.moves.urllib.parse import parse_qs, urlencode, quote


class ConfigProxy(object):

    def __init__(self, actual, client, attribute_values_dict, readwrite_attrs, transforms=None, readonly_attrs=None, immutable_attrs=None, json_encodes=None):
        transforms = {} if transforms is None else transforms
        readonly_attrs = [] if readonly_attrs is None else readonly_attrs
        immutable_attrs = [] if immutable_attrs is None else immutable_attrs
        json_encodes = [] if json_encodes is None else json_encodes

        # Actual config object from nitro sdk
        self.actual = actual

        # nitro client
        self.client = client

        # ansible attribute_values_dict
        self.attribute_values_dict = attribute_values_dict

        self.readwrite_attrs = readwrite_attrs
        self.readonly_attrs = readonly_attrs
        self.immutable_attrs = immutable_attrs
        self.json_encodes = json_encodes
        self.transforms = transforms

        self.attribute_values_processed = {}
        for attribute, value in self.attribute_values_dict.items():
            if value is None:
                continue
            if attribute in transforms:
                for transform in self.transforms[attribute]:
                    if transform == 'bool_yes_no':
                        if value is True:
                            value = 'YES'
                        elif value is False:
                            value = 'NO'
                    elif transform == 'bool_on_off':
                        if value is True:
                            value = 'ON'
                        elif value is False:
                            value = 'OFF'
                    elif callable(transform):
                        value = transform(value)
                    else:
                        raise Exception('Invalid transform %s' % transform)
            self.attribute_values_processed[attribute] = value

        self._copy_attributes_to_actual()

    def _copy_attributes_to_actual(self):
        for attribute in self.readwrite_attrs:
            if attribute in self.attribute_values_processed:
                attribute_value = self.attribute_values_processed[attribute]

                if attribute_value is None:
                    continue

                # Fallthrough
                if attribute in self.json_encodes:
                    attribute_value = json.JSONEncoder().encode(attribute_value).strip('"')
                setattr(self.actual, attribute, attribute_value)

    def __getattr__(self, name):
        if name in self.attribute_values_dict:
            return self.attribute_values_dict[name]
        else:
            raise AttributeError('No attribute %s found' % name)

    def add(self):
        self.actual.__class__.add(self.client, self.actual)

    def update(self):
        return self.actual.__class__.update(self.client, self.actual)

    def delete(self):
        self.actual.__class__.delete(self.client, self.actual)

    def get(self, *args, **kwargs):
        result = self.actual.__class__.get(self.client, *args, **kwargs)

        return result

    def has_equal_attributes(self, other):
        if self.diff_object(other) == {}:
            return True
        else:
            return False

    def diff_object(self, other):
        diff_dict = {}
        for attribute in self.attribute_values_processed:
            # Skip readonly attributes
            if attribute not in self.readwrite_attrs:
                continue

            # Skip attributes not present in module arguments
            if self.attribute_values_processed[attribute] is None:
                continue

            # Check existence
            if hasattr(other, attribute):
                attribute_value = getattr(other, attribute)
            else:
                diff_dict[attribute] = 'missing from other'
                continue

            # Compare values
            param_type = self.attribute_values_processed[attribute].__class__
            if attribute_value is None or param_type(attribute_value) != self.attribute_values_processed[attribute]:
                str_tuple = (
                    type(self.attribute_values_processed[attribute]),
                    self.attribute_values_processed[attribute],
                    type(attribute_value),
                    attribute_value,
                )
                diff_dict[attribute] = 'difference. ours: (%s) %s other: (%s) %s' % str_tuple
        return diff_dict

    def get_actual_rw_attributes(self, filter='name'):
        if self.actual.__class__.count_filtered(self.client, '%s:%s' % (filter, self.attribute_values_dict[filter])) == 0:
            return {}
        server_list = self.actual.__class__.get_filtered(self.client, '%s:%s' % (filter, self.attribute_values_dict[filter]))
        actual_instance = server_list[0]
        ret_val = {}
        for attribute in self.readwrite_attrs:
            if not hasattr(actual_instance, attribute):
                continue
            ret_val[attribute] = getattr(actual_instance, attribute)
        return ret_val

    def get_actual_ro_attributes(self, filter='name'):
        if self.actual.__class__.count_filtered(self.client, '%s:%s' % (filter, self.attribute_values_dict[filter])) == 0:
            return {}
        server_list = self.actual.__class__.get_filtered(self.client, '%s:%s' % (filter, self.attribute_values_dict[filter]))
        actual_instance = server_list[0]
        ret_val = {}
        for attribute in self.readonly_attrs:
            if not hasattr(actual_instance, attribute):
                continue
            ret_val[attribute] = getattr(actual_instance, attribute)
        return ret_val

    def get_missing_rw_attributes(self):
        return list(set(self.readwrite_attrs) - set(self.get_actual_rw_attributes().keys()))

    def get_missing_ro_attributes(self):
        return list(set(self.readonly_attrs) - set(self.get_actual_ro_attributes().keys()))


def get_immutables_intersection(config_proxy, keys):
    immutables_set = set(config_proxy.immutable_attrs)
    keys_set = set(keys)
    # Return list of sets' intersection
    return list(immutables_set & keys_set)


def ensure_feature_is_enabled(client, feature_str):
    enabled_features = client.get_enabled_features()

    if enabled_features is None:
        enabled_features = []

    if feature_str not in enabled_features:
        client.enable_features(feature_str)
        client.save_config()


def get_nitro_client(module):
    from nssrc.com.citrix.netscaler.nitro.service.nitro_service import nitro_service

    if module.params['mas_proxy_call']:

        try:
            from nssrc.com.citrix.netscaler.nitro.service.MasContext import MasContext
        except ImportError as e:
            module.fail_json(msg='The currently installed nitro python SDK does not support MAS proxied calls')

        if module.params['mas_auth_token'] is None:
            module.fail_json(msg='You must provide a mas authentication token to proxy a call trough MAS')
        if module.params['instance_ip'] is None:
            module.fail_json(msg='You must provide  the target NS instance ip to proxy a call trough MAS')

        masCtx = MasContext(
            module.params['mas_ip'],
            module.params['mas_auth_token'],
            module.params['instance_ip'],
        )

        client = nitro_service(masCtx, module.params['nitro_protocol'])
    else:
        if module.params['nitro_user'] is None:
            module.fail_json(msg='You must provide a valid nitro user name')

        if module.params['nitro_pass'] is None:
            module.fail_json(msg='You must provide a valid nitro password')

        client = nitro_service(module.params['nsip'], module.params['nitro_protocol'])
        client.set_credential(module.params['nitro_user'], module.params['nitro_pass'])

    client.timeout = float(module.params['nitro_timeout'])
    client.certvalidation = module.params['validate_certs']

    return client


netscaler_common_arguments = dict(
    nsip=dict(
        required=True,
        aliases=['mas_ip'],
        fallback=(env_fallback, ['NETSCALER_NSIP']),
    ),
    nitro_user=dict(
        required=False,
        aliases=['mas_user'],
        fallback=(env_fallback, ['NETSCALER_NITRO_USER']),
        no_log=True
    ),
    nitro_pass=dict(
        required=False,
        aliases=['mas_pass'],
        fallback=(env_fallback, ['NETSCALER_NITRO_PASS']),
        no_log=True
    ),
    nitro_protocol=dict(
        choices=['http', 'https'],
        fallback=(env_fallback, ['NETSCALER_NITRO_PROTOCOL']),
        default='http'
    ),
    validate_certs=dict(
        default=True,
        type='bool'
    ),
    nitro_timeout=dict(default=310, type='float'),
    state=dict(
        choices=[
            'present',
            'absent',
        ],
        default='present',
    ),
    save_config=dict(
        type='bool',
        default=True,
    ),

    mas_proxy_call=dict(
        default=False,
        type='bool'
    ),
    nitro_auth_token=dict(
        type='str',
        aliases=['mas_auth_token'],
        nolog=True,
    ),
    instance_ip=dict(
        type='str'
    ),
)

loglines = []


def complete_missing_attributes(actual, attrs_list, fill_value=None):
    for attribute in attrs_list:
        if not hasattr(actual, attribute):
            setattr(actual, attribute, fill_value)


def log(msg):
    loglines.append(msg)


def get_ns_version(client):
    from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nsversion import nsversion
    result = nsversion.get(client)
    m = re.match(r'^.*NS(\d+)\.(\d+).*$', result[0].version)
    if m is None:
        return None
    else:
        return int(m.group(1)), int(m.group(2))


def get_ns_hardware(client):
    from nssrc.com.citrix.netscaler.nitro.resource.config.ns.nshardware import nshardware
    result = nshardware.get(client)
    return result


def monkey_patch_nitro_api():

    from nssrc.com.citrix.netscaler.nitro.resource.base.Json import Json

    def new_resource_to_string_convert(self, resrc):
        # Line below is the actual patch
        dict_valid_values = dict((k.replace('_', '', 1), v) for k, v in resrc.__dict__.items() if v)
        return json.dumps(dict_valid_values)
    Json.resource_to_string_convert = new_resource_to_string_convert

    from nssrc.com.citrix.netscaler.nitro.util.nitro_util import nitro_util

    @classmethod
    def object_to_string_new(cls, obj):
        output = []
        flds = obj.__dict__
        for k, v in ((k.replace('_', '', 1), v) for k, v in flds.items() if v):
            if isinstance(v, bool):
                output.append('"%s":%s' % (k, v))
            elif isinstance(v, (binary_type, text_type)):
                v = to_native(v, errors='surrogate_or_strict')
                output.append('"%s":"%s"' % (k, v))
            elif isinstance(v, int):
                output.append('"%s":"%s"' % (k, v))
        return ','.join(output)

    @classmethod
    def object_to_string_withoutquotes_new(cls, obj):
        output = []
        flds = obj.__dict__
        for k, v in ((k.replace('_', '', 1), v) for k, v in flds.items() if v):
            if isinstance(v, (int, bool)):
                output.append('%s:%s' % (k, v))
            elif isinstance(v, (binary_type, text_type)):
                v = to_native(v, errors='surrogate_or_strict')
                output.append('%s:%s' % (k, cls.encode(v)))
        return ','.join(output)

    nitro_util.object_to_string = object_to_string_new
    nitro_util.object_to_string_withoutquotes = object_to_string_withoutquotes_new


class NitroAPIFetcher(object):

    def __init__(self, module, api_path='nitro/v1/config'):

        self._module = module

        self.r = None
        self.info = None
        self.api_path = api_path

        # Prepare the http headers according to module arguments
        self._headers = {}
        self._headers['Content-Type'] = 'application/json'

        # Check for conflicting authentication methods
        have_token = self._module.params['nitro_auth_token'] is not None
        have_userpass = None not in (self._module.params['nitro_user'], self._module.params['nitro_pass'])

        if have_token and have_userpass:
            self.fail_module(msg='Cannot define both authentication token and username/password')

        if have_token:
            self._headers['Cookie'] = "NITRO_AUTH_TOKEN=%s" % self._module.params['nitro_auth_token']

        if have_userpass:
            self._headers['X-NITRO-USER'] = self._module.params['nitro_user']
            self._headers['X-NITRO-PASS'] = self._module.params['nitro_pass']

        # Do header manipulation when doing a MAS proxy call
        if self._module.params['mas_proxy_call']:
            if self._module.params.get('instance_ip') is not None:
                self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_IP'] = self._module.params['instance_ip']
            elif self._module.params.get('instance_name') is not None:
                self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_NAME'] = self._module.params['instance_name']
            elif self._module.params.get('instance_id') is not None:
                self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_ID'] = self._module.params['instance_id']
            else:
                self._module.fail_json(msg='Target netscaler is undefined for MAS proxied NITRO call')

    def edit_response_data(self, r, info, result):
        '''
            Parses the r and info values from ansible fetch
            and manipulates the result accordingly
        '''

        # Save raw values to corresponding member variables
        self.r = r
        self.info = info

        # Search for body in both http body and http data
        if r is not None:
            result['http_response_body'] = codecs.decode(r.read(), 'utf-8')
        elif 'body' in info:
            result['http_response_body'] = codecs.decode(info['body'], 'utf-8')
            del info['body']
        else:
            result['http_response_body'] = ''

        result['http_response_data'] = info

        # Update the nitro_* parameters

        # Nitro return code in http data
        result['nitro_errorcode'] = None
        result['nitro_message'] = None
        result['nitro_severity'] = None

        if result['http_response_body'] != '':
            try:
                data = self._module.from_json(result['http_response_body'])

                # Get rid of the string representation if json parsing succeeds
                del result['http_response_body']
            except ValueError:
                data = {}
            result['data'] = data
            result['nitro_errorcode'] = data.get('errorcode')
            result['nitro_message'] = data.get('message')
            result['nitro_severity'] = data.get('severity')

    def _construct_query_string(self, args={}, attrs=[], filter={}, action=None, count=False):

        query_dict = {}

        # Construct args
        args_val = ','.join(['%s:%s' % (k, quote(args[k], safe='')) for k in args])

        if args_val != '':
            args_val = 'args=%s' % args_val

        # Construct attrs
        attrs_val = ','.join(attrs)
        if attrs_val != '':
            attrs_val = 'attrs=%s' % attrs_val

        # Construct filters
        filter_val = ','.join(['%s:%s' % (k, filter[k]) for k in filter])
        if filter_val != '':
            filter_val = 'filter=%s' % filter_val

        # Construct action
        action_val = ''
        if action is not None:
            action_val = 'action=%s' % action

        # Construct count
        count_val = ''
        if count:
            count_val = 'count=yes'

        # Construct the query string
        # Filter out empty string parameters
        val_list = [args_val, attrs_val, filter_val, action_val, count_val]
        query_params = '&'.join([v for v in val_list if v != ''])

        if query_params != '':
            query_params = '?%s' % query_params

        return query_params

    def put(self, put_data, resource, id):

        url = '%s://%s/%s/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self.api_path,
            resource,
            id,
        )

        data = self._module.jsonify(put_data)

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='PUT',
        )

        result = {}
        self.edit_response_data(r, info, result)

        return result

    def get(self, resource, id=None, args={}, attrs=[], filter={}):

        # Construct basic get url
        url = '%s://%s/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self.api_path,
            resource,
        )

        # Append resource id
        if id is not None:
            url = '%s/%s' % (url, id)

        query_params = self._construct_query_string(args=args, attrs=attrs, filter=filter)

        # Append query params
        url = '%s%s' % (url, query_params)

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )

        result = {}
        self.edit_response_data(r, info, result)

        return result

    def delete(self, resource, id=None, args={}):

        # Deletion by name takes precedence over deletion by attributes

        url = '%s://%s/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self.api_path,
            resource
        )

        # Append resource id
        if id is not None:
            url = '%s/%s' % (url, id)

        # Append query params
        query_params = self._construct_query_string(args=args)
        url = '%s%s' % (url, query_params)

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='DELETE',
        )

        result = {}
        self.edit_response_data(r, info, result)

        return result

    def post(self, post_data, resource, action=None):

        # Construct basic get url
        url = '%s://%s/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self.api_path,
            resource,
        )

        query_params = self._construct_query_string(action=action)

        # Append query params
        url = '%s%s' % (url, query_params)

        data = self._module.jsonify(post_data)

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='POST',
        )

        result = {}
        self.edit_response_data(r, info, result)

        return result


class NitroResourceConfig(object):

    def __init__(self, module, resource, attributes_list, attribute_values_dict={}, transforms={}, actual_dict={}):
        self.resource = resource
        self.module = module
        self.fetcher = NitroAPIFetcher(module)
        self.attributes_list = attributes_list
        self.attribute_values_dict = attribute_values_dict
        self.transforms = transforms
        log('transforms %s' % transforms)
        log('attribute_values_dict %s' % attribute_values_dict)

        self.actual_dict = actual_dict

        self.values_dict = {}

        # Process the value dict so only values of not None are included
        # Also apply any transforms
        # attribute_values_dict takes precedence over actual_dict
        if self.attribute_values_dict != {}:
            for attribute in attributes_list:
                attribute_value = attribute_values_dict.get(attribute)
                if attribute_value is not None:
                    if attribute in self.transforms:
                        actual_value = self.transforms[attribute](attribute_value)
                        log('Transformed value %s to %s' % (attribute_value, actual_value))
                    else:
                        actual_value = attribute_value

                    self.values_dict[attribute] = actual_value
        elif self.actual_dict != {}:
            self.values_dict = copy.deepcopy(self.actual_dict)
        else:
            raise Exception('Cannot instantiate a NITRO config object without any values')

        # Populate the id values dictionary
        self.id_values_dict = {}

    def __eq__(self, other):
        raise NotImplementedError
        log('Running eq')
        if not isinstance(other, NitroResourceConfig):
            return False

        return self.values_dict == other.values_dict

    def __ne__(self, other):
        raise NotImplementedError
        log('Running ne')
        return not self.__eq__(other)

    def __contains__(self, item):
        raise NotImplementedError
        log('Running contains')

    def _get_actual_instance(self, get_id_attributes=[]):
        # Try to get the item using the get_id_attributes
        if get_id_attributes == []:
            raise Exception('Cannot get NITRO object without get_id_attributes')

        # Get the defined id attributes
        defined_ids = []
        for id_attribute in get_id_attributes:
            if self.values_dict.get(id_attribute) is not None:
                defined_ids.append(id_attribute)

        if len(defined_ids) == 0:
            raise Exception('Cannot get resource without some get_id attribute defined')
        else:
            args = {}
            for id in defined_ids:
                args[id] = self.values_dict[id]
            result = self.fetcher.get(self.resource, args=args)

        log('result retrieved %s' % result)

        if result['nitro_errorcode'] == 0:
            # This is the non existent condition for bindings
            # No NITRO error but also no expected data strutcture
            if result['data'].get(self.resource) is None:
                return None

            return result['data'][self.resource]

        else:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )

    @classmethod
    def get_all(cls, module, resource, id=None):

        # Construct get url
        fetcher = NitroAPIFetcher(module)
        result = fetcher.get(resource, id)
        log('get all result is %s' % result)

        if result['nitro_errorcode'] != 0:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )
        elif resource in result['data']:
            return result['data'][resource]
        else:
            return []

    def get_actual(self, get_id_attributes):
        retval = self._get_actual_instance(get_id_attributes)

        if retval is None:
            self.actual_dict = {}
        elif isinstance(retval, list):
            if len(retval) > 1:
                raise Exception('get actual returned multiple values')
            elif len(retval) == 1:
                self.actual_dict = retval[0]
            elif len(retval) == 0:
                self.actual_dict = {}
        elif isinstance(retval, dict):
            self.actual_dict = retval
        else:
            raise Exception('Cannot handle retval from _get_actual_instance')

    def exists(self, get_id_attributes):
        self.get_actual(get_id_attributes)
        return self.actual_dict != {}

    def binding_exists():
        pass

    def diff_list(self):
        log('diff_list')
        diff_list = []
        # We compare only the attributes defined in the values_dict
        for key in self.values_dict.keys():
            actual_value = self.actual_dict.get(key)

            present_value = self.values_dict[key]

            if actual_value is None:
                diff_list.append('"%s" attribute missing from retrieved NITRO object' % key)
            elif actual_value != present_value:
                str_tuple = (
                    key,
                    type(present_value),
                    present_value,
                    type(actual_value),
                    actual_value,
                )
                diff_list.append('Attribute "%s" differs. Playbook parameter: (%s) %s. Retrieved NITRO object: (%s) %s' % str_tuple)
        return diff_list

    def values_identical_to_dict(self, values_dict):
        log('running values_identical_to_dict')
        # We check only the values that appear in our values dict
        log('other values dict %s' % values_dict)

        for key in self.values_dict.keys():
            if key not in values_dict:
                log('key %s not found in target dict' % key)
                return False
            if values_dict[key] != self.values_dict[key]:
                tvals = (key, type(self.values_dict[key]), self.values_dict[key], type(values_dict[key]), values_dict[key])
                log('value differs for key %s. ours (%s, %s) theirs(%s, %s)' % tvals)
                return False

        # Fallthrough to success
        return True

    def values_by_key_identical_to_dict(self, values_dict, key_list):
        id_values_dict = {}
        for key in key_list:
            if key in self.values_dict:
                id_values_dict[key] = self.values_dict[key]

        for key in id_values_dict.keys():
            if key not in values_dict:
                log('key %s not found in target dict' % key)
                return False
            if values_dict[key] != id_values_dict[key]:
                tvals = (key, type(id_values_dict[key]), id_values_dict[key], type(values_dict[key]), values_dict[key])
                log('value differs for key %s. ours (%s, %s) theirs (%s, %s)' % tvals)
                return False

        # Fallthrough to success
        return True

    def values_subgroup_of_actual(self):
        log('values_subgroup_of_actual')
        diff_list = self.diff_list()
        log('diff_list result %s' % diff_list)
        if diff_list == []:
            return True
        else:
            return False

    def values_subgroup_of(self, other):
        for key, value in self.values_dict.items():
            other_value = other.values_dict.get(key)
            if other_value is None:
                return False
            if other_value != value:
                return False

        # Fallthrough to success
        return True

    def import_object(self):
        if self.values_dict == {}:
            raise Exception('Cannot create NITRO object without any attribute values')

        post_data = {
            self.resource: self.values_dict
        }

        import_object_resource = "{}{}".format(self.resource, "?action=Import")
        result = self.fetcher.post(post_data=post_data, resource=import_object_resource)
        log('result of post: %s' % result)
        if result['http_response_data']['status'] == 200:
            if result.get('nitro_errorcode') is not None:
                if result['nitro_errorcode'] != 0:
                    raise NitroException(
                        errorcode=result['nitro_errorcode'],
                        message=result.get('nitro_message'),
                        severity=result.get('nitro_severity'),
                    )
        elif 400 <= result['http_response_data']['status'] <= 599:
            raise NitroException(
                errorcode=result.get('nitro_errorcode'),
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )
        else:
            raise Exception('Did not get nitro errorcode and http status was not 201 or 4xx (%s)' % result['http_response_data']['status'])

    def update_object(self):
        if self.values_dict == {}:
            raise Exception('Cannot create NITRO object without any attribute values')

        update_object_resource_dict = {'name': self.values_dict['name']}
        post_data = {
            self.resource: update_object_resource_dict
        }

        update_object_resource = "{}{}".format(self.resource, "?action=update")
        result = self.fetcher.post(post_data=post_data, resource=update_object_resource)
        log('result of post: %s' % result)
        if result['http_response_data']['status'] == 200:
            if result.get('nitro_errorcode') is not None:
                if result['nitro_errorcode'] != 0:
                    raise NitroException(
                        errorcode=result['nitro_errorcode'],
                        message=result.get('nitro_message'),
                        severity=result.get('nitro_severity'),
                    )
        elif 400 <= result['http_response_data']['status'] <= 599:
            raise NitroException(
                errorcode=result.get('nitro_errorcode'),
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )
        else:
            raise Exception('Did not get nitro errorcode and http status was not 201 or 4xx (%s)' % result['http_response_data']['status'])

    def create(self):
        if self.values_dict == {}:
            raise Exception('Cannot create NITRO object without any attribute values')

        post_data = {
            self.resource: self.values_dict
        }

        result = self.fetcher.post(post_data=post_data, resource=self.resource)
        log('result of post: %s' % result)
        if result['http_response_data']['status'] == 201:
            if result.get('nitro_errorcode') is not None:
                if result['nitro_errorcode'] != 0:
                    raise NitroException(
                        errorcode=result['nitro_errorcode'],
                        message=result.get('nitro_message'),
                        severity=result.get('nitro_severity'),
                    )
        elif 400 <= result['http_response_data']['status'] <= 599:
            raise NitroException(
                errorcode=result.get('nitro_errorcode'),
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )
        else:
            raise Exception('Did not get nitro errorcode and http status was not 201 or 4xx (%s)' % result['http_response_data']['status'])

    def update(self, id_attribute=None):
        if self.values_dict == {}:
            raise Exception('Cannot update NITRO object without any attribute values')

        put_data = {
            self.resource: self.values_dict
        }
        if id_attribute is None:
            id = None
        else:
            id = self.values_dict.get(id_attribute)
            if id is None:
                raise Exception('id attribute does not have a value for update')

        log('request put data: %s' % put_data)
        result = self.fetcher.put(put_data=put_data, resource=self.resource, id=id)

        log('result of put: %s' % result)

        if result['nitro_errorcode'] != 0:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )

    def delete(self, delete_id_attributes):
        id_values_dict = {}
        for id in delete_id_attributes:
            if id in self.values_dict:
                id_values_dict[id] = self.values_dict[id]

        args = id_values_dict
        id = None

        result = self.fetcher.delete(resource=self.resource, id=id, args=args)
        log('delete result %s' % result)

        if result['nitro_errorcode'] != 0:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )


class MASResourceConfig(object):

    def __init__(self, module, resource, attributes_list, attribute_values_dict={}, transforms={}, actual_dict={}, api_path='nitro/v1/config'):
        self.resource = resource
        self.module = module
        self.fetcher = NitroAPIFetcher(module, api_path=api_path)
        self.attributes_list = attributes_list
        self.attribute_values_dict = attribute_values_dict
        self.transforms = transforms
        log('transforms %s' % transforms)
        log('attribute_values_dict %s' % attribute_values_dict)

        self.actual_dict = actual_dict

        self.values_dict = {}

        # Process the value dict so only values of not None are included
        # Also apply any transforms
        # attribute_values_dict takes precedence over actual_dict
        if self.attribute_values_dict != {}:
            for attribute in attributes_list:
                attribute_value = attribute_values_dict.get(attribute)
                if attribute_value is not None:
                    if attribute in self.transforms:
                        actual_value = self.transforms[attribute](attribute_value)
                        log('Transformed value %s to %s' % (attribute_value, actual_value))
                    else:
                        actual_value = attribute_value

                    self.values_dict[attribute] = actual_value
        elif self.actual_dict != {}:
            self.values_dict = copy.deepcopy(self.actual_dict)
        else:
            raise Exception('Cannot instantiate a MAS config object without any values')

    def get_actual_instance(self, get_id_attributes, success_codes, use_filter):
        # Try to get the item using the get_id_attributes
        if get_id_attributes == []:
            raise Exception('Cannot get NITRO object without get_id_attributes')

        # Get the defined id attributes
        defined_ids = []
        for id_attribute in get_id_attributes:
            if self.values_dict.get(id_attribute) is not None:
                defined_ids.append(id_attribute)

        defined_id_attributes_dict = {}
        for id in defined_ids:
            defined_id_attributes_dict[id] = self.values_dict[id]

        if len(defined_ids) == 0:
            raise Exception('Cannot get resource without some get_id attribute defined')
        elif use_filter:
            result = self.fetcher.get(self.resource, filter=defined_id_attributes_dict)
        else:
            args = {}
            for id in defined_ids:
                args[id] = self.values_dict[id]

            result = self.fetcher.get(self.resource, args=defined_id_attributes_dict)

        log('result retrieved %s' % result)

        if result['nitro_errorcode'] in success_codes:
            # This is the non existent condition for bindings
            # No NITRO error but also no expected data strutcture
            data = result['data'].get(self.resource)
            if data is None:
                self.actual_dict = {}
            elif isinstance(data, list):
                if len(data) > 1:
                    raise Exception('get actual returned multiple values')
                elif len(data) == 1:
                    self.actual_dict = data[0]
                elif len(data) == 0:
                    self.actual_dict = {}
            else:
                raise Exception('Unexcpected value from GET operation `%s`' % data)

        else:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )

    def exists(self, get_id_attributes, success_codes=[None, 0], use_filter=True):
        self.get_actual_instance(get_id_attributes, success_codes, use_filter)
        return self.actual_dict != {}

    def values_subset_of_actual(self, skip_attributes=[]):
        log('values_subset_of_actual')
        return self.values_subset_of(self.actual_dict, skip_attributes)

    def values_subset_of(self, other, skip_attributes=[]):
        log('values_subset_of')
        diff_list = self.diff_list(other, skip_attributes)
        return diff_list == []

    def diff_list(self, other, skip_attributes=[]):
        log('diff_list start')
        diff_list = []
        # We compare only the attributes defined in the values_dict
        for key in self.values_dict.keys():

            if key in skip_attributes:
                log('Skipping diff_list attribute `%s`' % key)
                continue

            other_value = other.get(key)

            present_value = self.values_dict[key]

            if other_value is None:
                diff_list.append('"%s" attribute missing from other object' % key)
            elif other_value != present_value:
                str_tuple = (
                    key,
                    type(present_value),
                    present_value,
                    type(other_value),
                    other_value,
                )
                diff_list.append('Attribute "%s" differs. Playbook parameter: (%s) %s. Retrieved NITRO object: (%s) %s' % str_tuple)
        log('diff_list %s' % diff_list)
        return diff_list

    def create(self, success_codes=[None, 0]):
        if self.values_dict == {}:
            raise Exception('Cannot create NITRO object without any attribute values')

        post_data = {
            self.resource: self.values_dict
        }
        result = self.fetcher.post(post_data=post_data, resource=self.resource)
        log('result of post: %s' % result)
        if result['nitro_errorcode'] not in success_codes:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )

    def update(self, success_codes=[None, 0], id_attribute=None):
        if self.values_dict == {}:
            raise Exception('Cannot update NITRO object without any attribute values')

        put_data = {
            self.resource: self.values_dict
        }

        # Explicitly setting the id to None is OK
        if id_attribute is None:
            id = None
        else:
            id = self.actual_dict.get(id_attribute)
            # Not having the declared id attribute in the input variables on the other hand is in fact an error
            if id is None:
                raise Exception('id attribute does not have a value for update')

        log('request put data: %s' % put_data)
        result = self.fetcher.put(put_data=put_data, resource=self.resource, id=id)

        log('result of put: %s' % result)

        if result['nitro_errorcode'] not in success_codes:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )

    def delete(self, delete_id_attributes, success_codes=[None, 0]):
        id_values_dict = {}
        for id in delete_id_attributes:
            if id in self.actual_dict:
                id_values_dict[id] = self.actual_dict[id]

        args = id_values_dict
        id = None

        result = self.fetcher.delete(resource=self.resource, id=id, args=args)
        log('delete result %s' % result)

        if result['nitro_errorcode'] not in success_codes:
            raise NitroException(
                errorcode=result['nitro_errorcode'],
                message=result.get('nitro_message'),
                severity=result.get('nitro_severity'),
            )


class NitroException(Exception):

    def __init__(self, errorcode, message, severity):
        self.errorcode = errorcode
        self.message = message
        self.severity = severity
