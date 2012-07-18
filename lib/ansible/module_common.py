# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

REPLACER = "#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"

MODULE_COMMON = """

# == BEGIN DYNAMICALLY INSERTED CODE ==

# ansible modules can be written in any language.  To simplify
# development of Python modules, the functions available here
# can be inserted in any module source automatically by including
# #<<INCLUDE_ANSIBLE_MODULE_COMMON>> on a blank line by itself inside
# of an ansible module. The source of this common code lives
# in lib/ansible/module_common.py

try:
    import json
except ImportError:
    import simplejson as json
import os
import shlex
import subprocess
import sys
import syslog

class AnsibleModule(object):

    def __init__(self, argument_spec, bypass_checks=False, no_log=False):
        ''' 
        @argument_spec: a hash of argument names, where the values are none if
        the types are NOT checked, or a list of valid types where the argument
        must be one of those values.  All possible arguments must be listed.

        @required_arguments: a list of arguments that must be sent to the module
        '''

        self.argument_spec = argument_spec
        (self.params, self.args) = self._load_params()
        if not bypass_checks:
            self._check_required_arguments()
            self._check_argument_types()
        if not no_log:
            self._log_invocation()

    def _check_required_arguments(self):
        ''' ensure all required arguments are present '''
        missing = []
        for (k,v) in self.argument_spec.iteritems():
            (type_spec, required) = v
            if required and k not in self.params:
                missing.append(k)
        if len(missing) > 0:
            self.fail_json(msg="missing required arguments: %s" % ",".join(missing))

    def _check_argument_types(self):
        ''' ensure all arguments have the requested values, and there are no stray arguments '''
        for (k,v) in self.argument_spec.iteritems():
            (type_spec, required) = v
            if type_spec is not None:
                if type(spec) == list:
                    if v not in spec:
                        self.fail_json(msg="value of %s must be one of: %s, recieved: %s" % (k, ",".join(spec), v))
                else:
                    self.fail_json(msg="internal error: do not know how to interpret argument_spec")

    def _load_params(self):
        ''' read the input and return a dictionary and the arguments string '''
        if len(sys.argv) == 2 and os.path.exists(sys.argv[1]):
            argfile = sys.argv[1]
            args    = open(argfile, 'r').read()
        else:
            args = ' '.join(sys.argv[1:])
        items   = shlex.split(args)
        params = {}
        for x in items:
            (k, v) = x.split("=")
            params[k] = v
        return (params, args)        

    def _log_invocation(self):
        ''' log that ansible ran the module '''
        syslog.openlog('ansible-%s' % os.path.basename(__file__))
        syslog.syslog(syslog.LOG_NOTICE, 'Invoked with %s' % self.args)

    def exit_json(self, rc=0, **kwargs):
        ''' return from the module, without error '''
        kwargs['rc'] = rc
        print json.dumps(kwargs)
        sys.exit(rc)

    def fail_json(self, **kwargs):
        ''' return from the module, with an error message '''
        assert 'msg' in kwargs, "implementation error -- msg to explain the error is required"
        kwargs['failed'] = True
        self.exit_json(rc=1, **kwargs)

# == END DYNAMICALLY INSERTED CODE ===

"""
