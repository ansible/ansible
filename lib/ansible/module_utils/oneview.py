# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (2016-2017) Hewlett Packard Enterprise Development LP
# All rights reserved.
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

from __future__ import (absolute_import, division, print_function)

import abc
import collections
import json
import os
import traceback

try:
    from hpOneView.oneview_client import OneViewClient
    HAS_HPE_ONEVIEW = True
except ImportError:
    HAS_HPE_ONEVIEW = False

from ansible.module_utils import six
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def transform_list_to_dict(list_):
    """
    Transforms a list into a dictionary, putting values as keys.

    :arg list list_: List of values
    :return: dict: dictionary built
    """

    ret = {}

    if not list_:
        return ret

    for value in list_:
        if isinstance(value, collections.Mapping):
            ret.update(value)
        else:
            ret[to_native(value, errors='surrogate_or_strict')] = True

    return ret


def merge_list_by_key(original_list, updated_list, key, ignore_when_null=None):
    """
    Merge two lists by the key. It basically:

    1. Adds the items that are present on updated_list and are absent on original_list.

    2. Removes items that are absent on updated_list and are present on original_list.

    3. For all items that are in both lists, overwrites the values from the original item by the updated item.

    :arg list original_list: original list.
    :arg list updated_list: list with changes.
    :arg str key: unique identifier.
    :arg list ignore_when_null: list with the keys from the updated items that should be ignored in the merge,
        if its values are null.
    :return: list: Lists merged.
    """
    ignore_when_null = [] if ignore_when_null is None else ignore_when_null

    if not original_list:
        return updated_list

    items_map = collections.OrderedDict([(i[key], i.copy()) for i in original_list])

    merged_items = collections.OrderedDict()

    for item in updated_list:
        item_key = item[key]
        if item_key in items_map:
            for ignored_key in ignore_when_null:
                if ignored_key in item and item[ignored_key] is None:
                    item.pop(ignored_key)
            merged_items[item_key] = items_map[item_key]
            merged_items[item_key].update(item)
        else:
            merged_items[item_key] = item

    return list(merged_items.values())


def _str_sorted(obj):
    if isinstance(obj, collections.Mapping):
        return json.dumps(obj, sort_keys=True)
    else:
        return str(obj)


def _standardize_value(value):
    """
    Convert value to string to enhance the comparison.

    :arg value: Any object type.

    :return: str: Converted value.
    """
    if isinstance(value, float) and value.is_integer():
        # Workaround to avoid erroneous comparison between int and float
        # Removes zero from integer floats
        value = int(value)

    return str(value)


class OneViewModuleException(Exception):
    """
    OneView base Exception.

    Attributes:
       msg (str): Exception message.
       oneview_response (dict): OneView rest response.
   """

    def __init__(self, data):
        self.msg = None
        self.oneview_response = None

        if isinstance(data, six.string_types):
            self.msg = data
        else:
            self.oneview_response = data

            if data and isinstance(data, dict):
                self.msg = data.get('message')

        if self.oneview_response:
            Exception.__init__(self, self.msg, self.oneview_response)
        else:
            Exception.__init__(self, self.msg)


class OneViewModuleTaskError(OneViewModuleException):
    """
    OneView Task Error Exception.

    Attributes:
       msg (str): Exception message.
       error_code (str): A code which uniquely identifies the specific error.
    """

    def __init__(self, msg, error_code=None):
        super(OneViewModuleTaskError, self).__init__(msg)
        self.error_code = error_code


class OneViewModuleValueError(OneViewModuleException):
    """
    OneView Value Error.
    The exception is raised when the data contains an inappropriate value.

    Attributes:
       msg (str): Exception message.
    """
    pass


class OneViewModuleResourceNotFound(OneViewModuleException):
    """
    OneView Resource Not Found Exception.
    The exception is raised when an associated resource was not found.

    Attributes:
       msg (str): Exception message.
    """
    pass


@six.add_metaclass(abc.ABCMeta)
class OneViewModuleBase(object):
    MSG_CREATED = 'Resource created successfully.'
    MSG_UPDATED = 'Resource updated successfully.'
    MSG_DELETED = 'Resource deleted successfully.'
    MSG_ALREADY_PRESENT = 'Resource is already present.'
    MSG_ALREADY_ABSENT = 'Resource is already absent.'
    MSG_DIFF_AT_KEY = 'Difference found at key \'{0}\'. '
    HPE_ONEVIEW_SDK_REQUIRED = 'HPE OneView Python SDK is required for this module.'

    ONEVIEW_COMMON_ARGS = dict(
        config=dict(type='path'),
        hostname=dict(type='str'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        api_version=dict(type='int'),
        image_streamer_hostname=dict(type='str')
    )

    ONEVIEW_VALIDATE_ETAG_ARGS = dict(validate_etag=dict(type='bool', default=True))

    resource_client = None

    def __init__(self, additional_arg_spec=None, validate_etag_support=False):
        """
        OneViewModuleBase constructor.

        :arg dict additional_arg_spec: Additional argument spec definition.
        :arg bool validate_etag_support: Enables support to eTag validation.
        """
        argument_spec = self._build_argument_spec(additional_arg_spec, validate_etag_support)

        self.module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

        self._check_hpe_oneview_sdk()
        self._create_oneview_client()

        self.state = self.module.params.get('state')
        self.data = self.module.params.get('data')

        # Preload params for get_all - used by facts
        self.facts_params = self.module.params.get('params') or {}

        # Preload options as dict - used by facts
        self.options = transform_list_to_dict(self.module.params.get('options'))

        self.validate_etag_support = validate_etag_support

    def _build_argument_spec(self, additional_arg_spec, validate_etag_support):

        merged_arg_spec = dict()
        merged_arg_spec.update(self.ONEVIEW_COMMON_ARGS)

        if validate_etag_support:
            merged_arg_spec.update(self.ONEVIEW_VALIDATE_ETAG_ARGS)

        if additional_arg_spec:
            merged_arg_spec.update(additional_arg_spec)

        return merged_arg_spec

    def _check_hpe_oneview_sdk(self):
        if not HAS_HPE_ONEVIEW:
            self.module.fail_json(msg=self.HPE_ONEVIEW_SDK_REQUIRED)

    def _create_oneview_client(self):
        if self.module.params.get('hostname'):
            config = dict(ip=self.module.params['hostname'],
                          credentials=dict(userName=self.module.params['username'], password=self.module.params['password']),
                          api_version=self.module.params['api_version'],
                          image_streamer_ip=self.module.params['image_streamer_hostname'])
            self.oneview_client = OneViewClient(config)
        elif not self.module.params['config']:
            self.oneview_client = OneViewClient.from_environment_variables()
        else:
            self.oneview_client = OneViewClient.from_json_file(self.module.params['config'])

    @abc.abstractmethod
    def execute_module(self):
        """
        Abstract method, must be implemented by the inheritor.

        This method is called from the run method. It should contains the module logic

        :return: dict: It must return a dictionary with the attributes for the module result,
            such as ansible_facts, msg and changed.
        """
        pass

    def run(self):
        """
        Common implementation of the OneView run modules.

        It calls the inheritor 'execute_module' function and sends the return to the Ansible.

        It handles any OneViewModuleException in order to signal a failure to Ansible, with a descriptive error message.

        """
        try:
            if self.validate_etag_support:
                if not self.module.params.get('validate_etag'):
                    self.oneview_client.connection.disable_etag_validation()

            result = self.execute_module()

            if "changed" not in result:
                result['changed'] = False

            self.module.exit_json(**result)

        except OneViewModuleException as exception:
            error_msg = '; '.join(to_native(e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

    def resource_absent(self, resource, method='delete'):
        """
        Generic implementation of the absent state for the OneView resources.

        It checks if the resource needs to be removed.

        :arg dict resource: Resource to delete.
        :arg str method: Function of the OneView client that will be called for resource deletion.
            Usually delete or remove.
        :return: A dictionary with the expected arguments for the AnsibleModule.exit_json
        """
        if resource:
            getattr(self.resource_client, method)(resource)

            return {"changed": True, "msg": self.MSG_DELETED}
        else:
            return {"changed": False, "msg": self.MSG_ALREADY_ABSENT}

    def get_by_name(self, name):
        """
        Generic get by name implementation.

        :arg str name: Resource name to search for.

        :return: The resource found or None.
        """
        result = self.resource_client.get_by('name', name)
        return result[0] if result else None

    def resource_present(self, resource, fact_name, create_method='create'):
        """
        Generic implementation of the present state for the OneView resources.

        It checks if the resource needs to be created or updated.

        :arg dict resource: Resource to create or update.
        :arg str fact_name: Name of the fact returned to the Ansible.
        :arg str create_method: Function of the OneView client that will be called for resource creation.
            Usually create or add.
        :return: A dictionary with the expected arguments for the AnsibleModule.exit_json
        """

        changed = False
        if "newName" in self.data:
            self.data["name"] = self.data.pop("newName")

        if not resource:
            resource = getattr(self.resource_client, create_method)(self.data)
            msg = self.MSG_CREATED
            changed = True

        else:
            merged_data = resource.copy()
            merged_data.update(self.data)

            if self.compare(resource, merged_data):
                msg = self.MSG_ALREADY_PRESENT
            else:
                resource = self.resource_client.update(merged_data)
                changed = True
                msg = self.MSG_UPDATED

        return dict(
            msg=msg,
            changed=changed,
            ansible_facts={fact_name: resource}
        )

    def resource_scopes_set(self, state, fact_name, scope_uris):
        """
        Generic implementation of the scopes update PATCH for the OneView resources.
        It checks if the resource needs to be updated with the current scopes.
        This method is meant to be run after ensuring the present state.
        :arg dict state: Dict containing the data from the last state results in the resource.
            It needs to have the 'msg', 'changed', and 'ansible_facts' entries.
        :arg str fact_name: Name of the fact returned to the Ansible.
        :arg list scope_uris: List with all the scope URIs to be added to the resource.
        :return: A dictionary with the expected arguments for the AnsibleModule.exit_json
        """
        if scope_uris is None:
            scope_uris = []
        resource = state['ansible_facts'][fact_name]
        operation_data = dict(operation='replace', path='/scopeUris', value=scope_uris)

        if resource['scopeUris'] is None or set(resource['scopeUris']) != set(scope_uris):
            state['ansible_facts'][fact_name] = self.resource_client.patch(resource['uri'], **operation_data)
            state['changed'] = True
            state['msg'] = self.MSG_UPDATED

        return state

    def compare(self, first_resource, second_resource):
        """
        Recursively compares dictionary contents equivalence, ignoring types and elements order.
        Particularities of the comparison:
            - Inexistent key = None
            - These values are considered equal: None, empty, False
            - Lists are compared value by value after a sort, if they have same size.
            - Each element is converted to str before the comparison.
        :arg dict first_resource: first dictionary
        :arg dict second_resource: second dictionary
        :return: bool: True when equal, False when different.
        """
        resource1 = first_resource
        resource2 = second_resource

        debug_resources = "resource1 = {0}, resource2 = {1}".format(resource1, resource2)

        # The first resource is True / Not Null and the second resource is False / Null
        if resource1 and not resource2:
            self.module.log("resource1 and not resource2. " + debug_resources)
            return False

        # Checks all keys in first dict against the second dict
        for key in resource1:
            if key not in resource2:
                if resource1[key] is not None:
                    # Inexistent key is equivalent to exist with value None
                    self.module.log(self.MSG_DIFF_AT_KEY.format(key) + debug_resources)
                    return False
            # If both values are null, empty or False it will be considered equal.
            elif not resource1[key] and not resource2[key]:
                continue
            elif isinstance(resource1[key], collections.Mapping):
                # recursive call
                if not self.compare(resource1[key], resource2[key]):
                    self.module.log(self.MSG_DIFF_AT_KEY.format(key) + debug_resources)
                    return False
            elif isinstance(resource1[key], list):
                # change comparison function to compare_list
                if not self.compare_list(resource1[key], resource2[key]):
                    self.module.log(self.MSG_DIFF_AT_KEY.format(key) + debug_resources)
                    return False
            elif _standardize_value(resource1[key]) != _standardize_value(resource2[key]):
                self.module.log(self.MSG_DIFF_AT_KEY.format(key) + debug_resources)
                return False

        # Checks all keys in the second dict, looking for missing elements
        for key in resource2.keys():
            if key not in resource1:
                if resource2[key] is not None:
                    # Inexistent key is equivalent to exist with value None
                    self.module.log(self.MSG_DIFF_AT_KEY.format(key) + debug_resources)
                    return False

        return True

    def compare_list(self, first_resource, second_resource):
        """
        Recursively compares lists contents equivalence, ignoring types and element orders.
        Lists with same size are compared value by value after a sort,
        each element is converted to str before the comparison.
        :arg list first_resource: first list
        :arg list second_resource: second list
        :return: True when equal; False when different.
        """

        resource1 = first_resource
        resource2 = second_resource

        debug_resources = "resource1 = {0}, resource2 = {1}".format(resource1, resource2)

        # The second list is null / empty  / False
        if not resource2:
            self.module.log("resource 2 is null. " + debug_resources)
            return False

        if len(resource1) != len(resource2):
            self.module.log("resources have different length. " + debug_resources)
            return False

        resource1 = sorted(resource1, key=_str_sorted)
        resource2 = sorted(resource2, key=_str_sorted)

        for i, val in enumerate(resource1):
            if isinstance(val, collections.Mapping):
                # change comparison function to compare dictionaries
                if not self.compare(val, resource2[i]):
                    self.module.log("resources are different. " + debug_resources)
                    return False
            elif isinstance(val, list):
                # recursive call
                if not self.compare_list(val, resource2[i]):
                    self.module.log("lists are different. " + debug_resources)
                    return False
            elif _standardize_value(val) != _standardize_value(resource2[i]):
                self.module.log("values are different. " + debug_resources)
                return False

        # no differences found
        return True
