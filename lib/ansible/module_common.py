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
REPLACER_ARGS = "<<INCLUDE_ANSIBLE_MODULE_ARGS>>"

MODULE_COMMON = """

# == BEGIN DYNAMICALLY INSERTED CODE ==

MODULE_ARGS = <<INCLUDE_ANSIBLE_MODULE_ARGS>>

BOOLEANS_TRUE = ['yes', 'on', '1', 'true', 1]
BOOLEANS_FALSE = ['no', 'off', '0', 'false', 0]
BOOLEANS = BOOLEANS_TRUE + BOOLEANS_FALSE

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
import base64
import os
import re
import shlex
import subprocess
import sys
import syslog
import types

try:
    from hashlib import md5 as _md5
except ImportError:
    from md5 import md5 as _md5

class AnsibleModule(object):

    def __init__(self, argument_spec, bypass_checks=False, no_log=False, 
        check_invalid_arguments=True, mutually_exclusive=None, required_together=None,
        required_one_of=None):

        '''
        common code for quickly building an ansible module in Python
        (although you can write modules in anything that can return JSON)
        see library/* for examples
        '''

        self.argument_spec = argument_spec
        (self.params, self.args) = self._load_params()

        self._legal_inputs = []
        self._handle_aliases()

        # this may be disabled where modules are going to daisy chain into others
        if check_invalid_arguments:
            self._check_invalid_arguments()

        self._set_defaults(pre=True)

        if not bypass_checks:
            self._check_required_arguments()
            self._check_argument_types()
            self._check_mutually_exclusive(mutually_exclusive)
            self._check_required_together(required_together)
            self._check_required_one_of(required_one_of)

        self._set_defaults(pre=False)
        if not no_log:
            self._log_invocation()

    def _handle_aliases(self):
        for (k,v) in self.argument_spec.iteritems():
            self._legal_inputs.append(k)
            aliases = v.get('aliases', None)
            default = v.get('default', None)
            required = v.get('required', False)
            if default is not None and required:
                # not alias specific but this is a good place to check this
                self.fail_json(msg="internal error: required and default are mutally exclusive for %s" % k)
            if aliases is None:
                continue
            if type(aliases) != list:
                self.fail_json(msg='internal error: aliases must be a list')
            for alias in aliases:
                self._legal_inputs.append(alias)
                if alias in self.params:
                    self.params[k] = self.params[alias]

    def _check_invalid_arguments(self):
        for (k,v) in self.params.iteritems():
            if k not in self._legal_inputs:
                self.fail_json(msg="unsupported parameter for module: %s" % k)

    def _count_terms(self, check):
        count = 0
        for term in check:
           if term in self.params:
               count += 1
        return count

    def _check_mutually_exclusive(self, spec):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check)
            if count > 1:
                self.fail_json(msg="parameters are mutually exclusive: %s" % check)

    def _check_required_one_of(self, spec):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check)
            if count == 0:
                self.fail_json(msg="one of the following is required: %s" % check)

    def _check_required_together(self, spec):
        if spec is None:
            return
        for check in spec:
            counts = [ self.count_terms([field]) for field in check ]
            non_zero = [ c for c in counts if c > 0 ]
            if len(non_zero) > 0:
                if 0 in counts:
                    self.fail_json(msg="parameters are required together: %s" % check) 

    def _check_required_arguments(self):
        ''' ensure all required arguments are present '''
        missing = []
        for (k,v) in self.argument_spec.iteritems():
            required = v.get('required', False)
            if required and k not in self.params:
                missing.append(k)
        if len(missing) > 0:
            self.fail_json(msg="missing required arguments: %s" % ",".join(missing))

    def _check_argument_types(self):
        ''' ensure all arguments have the requested values, and there are no stray arguments '''
        for (k,v) in self.argument_spec.iteritems():
            choices = v.get('choices',None)
            if choices is None:
                continue
            if type(choices) == list:
                if k in self.params:
                    if self.params[k] not in choices:
                        choices_str=",".join(choices)
                        msg="value of %s must be one of: %s, got: %s" % (k, choices_str, self.params[k])
                        self.fail_json(msg=msg)
            else:
                self.fail_json(msg="internal error: do not know how to interpret argument_spec")

    def _set_defaults(self, pre=True):
         for (k,v) in self.argument_spec.iteritems():
             default = v.get('default', None)
             if pre == True:
                 # this prevents setting defaults on required items
                 if default and k not in self.params:
                     self.params[k] = default
             else:
                 # make sure things without a default still get set None
                 if k not in self.params:
                     self.params[k] = default

    def _load_params(self):
        ''' read the input and return a dictionary and the arguments string '''
        args = MODULE_ARGS
        items   = shlex.split(args)
        params = {}
        for x in items:
            try:
                (k, v) = x.split("=",1)
            except:
                self.fail_json(msg="this module requires key=value arguments")
            params[k] = v
        return (params, args)

    def _log_invocation(self):
        ''' log that ansible ran the module '''
        syslog.openlog('ansible-%s' % os.path.basename(__file__))
        # Sanitize possible password argument when logging
        log_args = re.sub(r'password=.+ (.*)', r"password=NOT_LOGGING_PASSWORD \1", self.args)
        log_args = re.sub(r'login_password=.+ (.*)', r"login_password=NOT_LOGGING_PASSWORD \1", log_args)
        syslog.syslog(syslog.LOG_NOTICE, 'Invoked with %s' % log_args)

    def get_bin_path(self, arg, opt_dirs=[]):
        '''
        find system executable in PATH.
        if found return full path; otherwise return None
        '''
        sbin_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
        paths = []
        for d in opt_dirs:
            if d is not None and os.path.exists(d):
                paths.append(d)
        paths += os.environ.get('PATH').split(':')
        bin_path = None
        # mangle PATH to include /sbin dirs
        for p in sbin_paths:
            if p not in paths and os.path.exists(p):
                paths.append(p)
        for d in paths:
            path = os.path.join(d, arg)
            if os.path.exists(path) and os.access(path, os.X_OK):
                bin_path = path
                break
        return bin_path

    def boolean(self, arg):
        ''' return a bool for the arg '''
        if arg is None or type(arg) == bool:
            return arg
        if type(arg) in types.StringTypes:
            arg = arg.lower()
        if arg in BOOLEANS_TRUE:
            return True
        elif arg in BOOLEANS_FALSE:
            return False
        else:
            self.fail_json(msg='Boolean %s not in either boolean list' % arg)

    def jsonify(self, data):
        return json.dumps(data)

    def exit_json(self, **kwargs):
        ''' return from the module, without error '''
        print self.jsonify(kwargs)
        sys.exit(0)

    def fail_json(self, **kwargs):
        ''' return from the module, with an error message '''
        assert 'msg' in kwargs, "implementation error -- msg to explain the error is required"
        kwargs['failed'] = True
        print self.jsonify(kwargs)
        sys.exit(1)

    def md5(self, filename):
        ''' Return MD5 hex digest of local file, or None if file is not present. '''
        if not os.path.exists(filename):
            return None
        if os.path.isdir(filename):
            self.fail_json(msg="attempted to take md5sum of directory: %s" % filename)
        digest = _md5()
        blocksize = 64 * 1024
        infile = open(filename, 'rb')
        block = infile.read(blocksize)
        while block:
            digest.update(block)
            block = infile.read(blocksize)
        infile.close()
        return digest.hexdigest()


# == END DYNAMICALLY INSERTED CODE ===

"""
