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


def cmp(a, b):
    """
    Python 3 does not have a cmp function, this will do the cmp.
    :param a: first object to check
    :param b: second object to check
    :return:
    """
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

    def set_parameters(self, ansible_params):
        self.parameters = dict()
        for param in ansible_params:
            if ansible_params[param] is not None:
                self.parameters[param] = ansible_params[param]
        return self.parameters

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

    @staticmethod
    def check_keys(current, desired):
        ''' TODO: raise an error if keys do not match
            with the exception of:
            new_name, state in desired
        '''
        pass

    def get_modified_attributes(self, current, desired):
        ''' takes two lists of attributes and return a list of attributes that are
            not in the desired state
            It is expected that all attributes of interest are listed in current and
            desired.

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
                    value.sort()
                    desired[key].sort()
                if cmp(value, desired[key]) != 0:
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
