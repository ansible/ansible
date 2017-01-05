# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
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
from ansible.module_utils.six import iteritems

class ComplexDict:

    def __init__(self, attrs):
        self._attributes = attrs
        self.attr_names = frozenset(self._attributes.keys())
        for name, attr in iteritems(self._attributes):
            if attr.get('key'):
                attr['required'] = True

    def __call__(self, value):
        if isinstance(value, dict):
            unknown = set(value.keys()).difference(self.attr_names)
            if unknown:
                raise ValueError('invalid keys: %s' % ','.join(unknown))
            for name, attr in iteritems(self._attributes):
                if attr.get('required') and name not in value:
                    raise ValueError('missing required attribute %s' % name)
                if not value.get(name):
                    value[name] = attr.get('default')
            return value
        else:
            obj = {}
            for name, attr in iteritems(self._attributes):
                if attr.get('key'):
                    obj[name] = value
                else:
                    obj[name] = attr.get('default')
            return obj


class ComplexList:

    def __init__(self, attrs):
        self._attributes = attrs
        self.attr_names = frozenset(self._attributes.keys())
        for name, attr in iteritems(self._attributes):
            if attr.get('key'):
                attr['required'] = True


    def __call__(self, values):
        objects = list()
        for value in values:
            if isinstance(value, dict):
                for name, attr in iteritems(self._attributes):
                    if attr.get('required') and name not in value:
                        raise ValueError('missing required attr %s' % name)
                    if not value.get(name):
                        value[name] = attr.get('default')
                objects.append(value)
            else:
                obj = {}
                for name, attr in iteritems(self._attributes):
                    if attr.get('key'):
                        obj[name] = value
                    else:
                        obj[name] = attr.get('default')
                objects.append(obj)
        return objects

