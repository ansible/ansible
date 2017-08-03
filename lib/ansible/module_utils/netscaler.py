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

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils._text import to_native


class ConfigProxy(object):

    def __init__(self, actual, client, attribute_values_dict, readwrite_attrs, transforms={}, readonly_attrs=[], immutable_attrs=[], json_encodes=[]):

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

    client = nitro_service(module.params['nsip'], module.params['nitro_protocol'])
    client.set_credential(module.params['nitro_user'], module.params['nitro_pass'])
    client.timeout = float(module.params['nitro_timeout'])
    client.certvalidation = module.params['validate_certs']
    return client


netscaler_common_arguments = dict(
    nsip=dict(
        required=True,
        fallback=(env_fallback, ['NETSCALER_NSIP']),
    ),
    nitro_user=dict(
        required=True,
        fallback=(env_fallback, ['NETSCALER_NITRO_USER']),
        no_log=True
    ),
    nitro_pass=dict(
        required=True,
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
