# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2018, Laurent Nicolas <laurentn@netapp.com>
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

''' Support class for NetApp ansible modules '''

import ansible.module_utils.netapp as netapp_utils


def cmp(a, b):
    """
    Python 3 does not have a cmp function, this will do the cmp.
    :param a: first object to check
    :param b: second object to check
    :return:
    """
    # convert to lower case for string comparison.
    if a is None:
        return -1
    if type(a) is str and type(b) is str:
        a = a.lower()
        b = b.lower()
    # if list has string element, convert string to lower case.
    if type(a) is list and type(b) is list:
        a = [x.lower() if type(x) is str else x for x in a]
        b = [x.lower() if type(x) is str else x for x in b]
        a.sort()
        b.sort()
    return (a > b) - (a < b)


class NetAppModule(object):
    '''
    Common class for NetApp modules
    set of support functions to derive actions based
    on the current state of the system, and a desired state
    '''

    def __init__(self):
        self.log = list()
        self.changed = False
        self.parameters = {'name': 'not intialized'}
        self.zapi_string_keys = dict()
        self.zapi_bool_keys = dict()
        self.zapi_list_keys = dict()
        self.zapi_int_keys = dict()
        self.zapi_required = dict()

    def set_parameters(self, ansible_params):
        self.parameters = dict()
        for param in ansible_params:
            if ansible_params[param] is not None:
                self.parameters[param] = ansible_params[param]
        return self.parameters

    def get_value_for_bool(self, from_zapi, value):
        """
        Convert boolean values to string or vice-versa
        If from_zapi = True, value is converted from string (as it appears in ZAPI) to boolean
        If from_zapi = False, value is converted from boolean to string
        For get() method, from_zapi = True
        For modify(), create(), from_zapi = False
        :param from_zapi: convert the value from ZAPI or to ZAPI acceptable type
        :param value: value of the boolean attribute
        :return: string or boolean
        """
        if value is None:
            return None
        if from_zapi:
            return True if value == 'true' else False
        else:
            return 'true' if value else 'false'

    def get_value_for_int(self, from_zapi, value):
        """
        Convert integer values to string or vice-versa
        If from_zapi = True, value is converted from string (as it appears in ZAPI) to integer
        If from_zapi = False, value is converted from integer to string
        For get() method, from_zapi = True
        For modify(), create(), from_zapi = False
        :param from_zapi: convert the value from ZAPI or to ZAPI acceptable type
        :param value: value of the integer attribute
        :return: string or integer
        """
        if value is None:
            return None
        if from_zapi:
            return int(value)
        else:
            return str(value)

    def get_value_for_list(self, from_zapi, zapi_parent, zapi_child=None, data=None):
        """
        Convert a python list() to NaElement or vice-versa
        If from_zapi = True, value is converted from NaElement (parent-children structure) to list()
        If from_zapi = False, value is converted from list() to NaElement
        :param zapi_parent: ZAPI parent key or the ZAPI parent NaElement
        :param zapi_child: ZAPI child key
        :param data: list() to be converted to NaElement parent-children object
        :param from_zapi: convert the value from ZAPI or to ZAPI acceptable type
        :return: list() or NaElement
        """
        if from_zapi:
            if zapi_parent is None:
                return []
            else:
                return [zapi_child.get_content() for zapi_child in zapi_parent.get_children()]
        else:
            zapi_parent = netapp_utils.zapi.NaElement(zapi_parent)
            for item in data:
                zapi_parent.add_new_child(zapi_child, item)
            return zapi_parent

    def get_cd_action(self, current, desired):
        ''' takes a desired state and a current state, and return an action:
            create, delete, None
            eg:
            is_present = 'absent'
            some_object = self.get_object(source)
            if some_object is not None:
                is_present = 'present'
            action = cd_action(current=is_present, desired = self.desired.state())
        '''
        if 'state' in desired:
            desired_state = desired['state']
        else:
            desired_state = 'present'

        if current is None and desired_state == 'absent':
            return None
        if current is not None and desired_state == 'present':
            return None
        # change in state
        self.changed = True
        if current is not None:
            return 'delete'
        return 'create'

    def compare_and_update_values(self, current, desired, keys_to_compare):
        updated_values = dict()
        is_changed = False
        for key in keys_to_compare:
            if key in current:
                if key in desired and desired[key] is not None:
                    if current[key] != desired[key]:
                        updated_values[key] = desired[key]
                        is_changed = True
                    else:
                        updated_values[key] = current[key]
                else:
                    updated_values[key] = current[key]

        return updated_values, is_changed

    @staticmethod
    def check_keys(current, desired):
        ''' TODO: raise an error if keys do not match
            with the exception of:
            new_name, state in desired
        '''
        pass

    @staticmethod
    def compare_lists(current, desired, get_list_diff):
        ''' compares two lists and return a list of elements that are either the desired elements or elements that are
            modified from the current state depending on the get_list_diff flag
            :param: current: current item attribute in ONTAP
            :param: desired: attributes from playbook
            :param: get_list_diff: specifies whether to have a diff of desired list w.r.t current list for an attribute
            :return: list of attributes to be modified
            :rtype: list
        '''
        desired_diff_list = [item for item in desired if item not in current]  # get what in desired and not in current
        current_diff_list = [item for item in current if item not in desired]  # get what in current but not in desired

        if desired_diff_list or current_diff_list:
            # there are changes
            if get_list_diff:
                return desired_diff_list
            else:
                return desired
        else:
            return []

    def get_modified_attributes(self, current, desired, get_list_diff=False):
        ''' takes two dicts of attributes and return a dict of attributes that are
            not in the current state
            It is expected that all attributes of interest are listed in current and
            desired.
            :param: current: current attributes in ONTAP
            :param: desired: attributes from playbook
            :param: get_list_diff: specifies whether to have a diff of desired list w.r.t current list for an attribute
            :return: dict of attributes to be modified
            :rtype: dict

            NOTE: depending on the attribute, the caller may need to do a modify or a
            different operation (eg move volume if the modified attribute is an
            aggregate name)
        '''
        # if the object does not exist,  we can't modify it
        modified = dict()
        if current is None:
            return modified

        # error out if keys do not match
        self.check_keys(current, desired)

        # collect changed attributes
        for key, value in current.items():
            if key in desired and desired[key] is not None:
                if type(value) is list:
                    modified_list = self.compare_lists(value, desired[key], get_list_diff)  # get modified list from current and desired
                    if modified_list:
                        modified[key] = modified_list
                elif cmp(value, desired[key]) != 0:
                    modified[key] = desired[key]
        if modified:
            self.changed = True
        return modified

    def is_rename_action(self, source, target):
        ''' takes a source and target object, and returns True
            if a rename is required
            eg:
            source = self.get_object(source_name)
            target = self.get_object(target_name)
            action = is_rename_action(source, target)
            :return: None for error, True for rename action, False otherwise
        '''
        if source is None and target is None:
            # error, do nothing
            # cannot rename an non existent resource
            # alternatively we could create B
            return None
        if source is not None and target is not None:
            # error, do nothing
            # idempotency (or) new_name_is_already_in_use
            # alternatively we could delete B and rename A to B
            return False
        if source is None and target is not None:
            # do nothing, maybe the rename was already done
            return False
        # source is not None and target is None:
        # rename is in order
        self.changed = True
        return True
