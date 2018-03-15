# (c) 2017, Patrick Deelman <patrick@patrickdeelman.nl>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
    lookup: passwordstore
    version_added: "2.3"
    author:
      - Patrick Deelman <patrick@patrickdeelman.nl>
    short_description: manage passwords with passwordstore.org's pass utility
    description:
      - Enables Ansible to retrieve, create or update passwords from the passwordstore.org pass utility.
        It also retrieves YAML style keys stored as multilines in the passwordfile.
    options:
      _terms:
        description: query key
        required: True
      passwordstore:
        description: location of the password store
        default: '~/.password-store'
      directory:
        description: directory of the password store
        env:
          - name: PASSWORD_STORE_DIR
      create:
        description: flag to create the password
        type: bool
        default: 'no'
      overwrite:
        description: flag to overwrite the password
        type: bool
        default: 'no'
      returnall:
        description: flag to return all the contents of the password store
        type: bool
        default: 'no'
      subkey:
        description: subkey to return
        default: password
      userpass:
        description: user password
      length:
        description: password length
        type: integer
        default: 16
"""
EXAMPLES = """
# Debug is used for examples, BAD IDEA to show passwords on screen
- name: Basic lookup. Fails if example/test doesn't exist
  debug: msg="{{ lookup('passwordstore', 'example/test')}}"

- name: Create pass with random 16 character password. If password exists just give the password
  debug: var=mypassword
  vars:
    mypassword: "{{ lookup('passwordstore', 'example/test create=true')}}"

- name: Different size password
  debug: msg="{{ lookup('passwordstore', 'example/test create=true length=42')}}"

- name: Create password and overwrite the password if it exists. As a bonus, this module includes the old password inside the pass file
  debug: msg="{{ lookup('passwordstore', 'example/test create=true overwrite=true')}}"

- name: Return the value for user in the KV pair user, username
  debug: msg="{{ lookup('passwordstore', 'example/test subkey=user')}}"

- name: Return the entire password file content
  set_fact: passfilecontent="{{ lookup('passwordstore', 'example/test returnall=true')}}"
"""

RETURN = """
_raw:
  description:
    - a password
"""

import os
import subprocess
import time

from distutils import util
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.encrypt import random_password
from ansible.plugins.lookup import LookupBase


# backhacked check_output with input for python 2.7
# http://stackoverflow.com/questions/10103551/passing-data-to-subprocess-check-output
def check_output2(*popenargs, **kwargs):
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    if 'stderr' in kwargs:
        raise ValueError('stderr argument not allowed, it will be overridden.')
    if 'input' in kwargs:
        if 'stdin' in kwargs:
            raise ValueError('stdin and input arguments may not both be used.')
        b_inputdata = to_bytes(kwargs['input'], errors='surrogate_or_strict')
        del kwargs['input']
        kwargs['stdin'] = subprocess.PIPE
    else:
        b_inputdata = None
    process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    try:
        b_out, b_err = process.communicate(b_inputdata)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if retcode != 0 or \
            b'encryption failed: Unusable public key' in b_out or \
            b'encryption failed: Unusable public key' in b_err:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(
            retcode,
            cmd,
            to_native(b_out + b_err, errors='surrogate_or_strict')
        )
    return b_out


class LookupModule(LookupBase):
    def parse_params(self, term):
        # I went with the "traditional" param followed with space separated KV pairs.
        # Waiting for final implementation of lookup parameter parsing.
        # See: https://github.com/ansible/ansible/issues/12255
        params = term.split()
        if len(params) > 0:
            # the first param is the pass-name
            self.passname = params[0]
            # next parse the optional parameters in keyvalue pairs
            try:
                for param in params[1:]:
                    name, value = param.split('=')
                    if name not in self.paramvals:
                        raise AnsibleAssertionError('%s not in paramvals' % name)
                    self.paramvals[name] = value
            except (ValueError, AssertionError) as e:
                raise AnsibleError(e)
            # check and convert values
            try:
                for key in ['create', 'returnall', 'overwrite']:
                    if not isinstance(self.paramvals[key], bool):
                        self.paramvals[key] = util.strtobool(self.paramvals[key])
            except (ValueError, AssertionError) as e:
                raise AnsibleError(e)
            if not isinstance(self.paramvals['length'], int):
                if self.paramvals['length'].isdigit():
                    self.paramvals['length'] = int(self.paramvals['length'])
                else:
                    raise AnsibleError("{0} is not a correct value for length".format(self.paramvals['length']))

            # Set PASSWORD_STORE_DIR if directory is set
            if self.paramvals['directory']:
                if os.path.isdir(self.paramvals['directory']):
                    os.environ['PASSWORD_STORE_DIR'] = self.paramvals['directory']
                else:
                    raise AnsibleError('Passwordstore directory \'{0}\' does not exist'.format(self.paramvals['directory']))

    def check_pass(self):
        try:
            self.passoutput = to_text(
                check_output2(["pass", self.passname]),
                errors='surrogate_or_strict'
            ).splitlines()
            self.password = self.passoutput[0]
            self.passdict = {}
            for line in self.passoutput[1:]:
                if ':' in line:
                    name, value = line.split(':', 1)
                    self.passdict[name.strip()] = value.strip()
        except (subprocess.CalledProcessError) as e:
            if e.returncode == 1 and 'not in the password store' in e.output:
                # if pass returns 1 and return string contains 'is not in the password store.'
                # We need to determine if this is valid or Error.
                if not self.paramvals['create']:
                    raise AnsibleError('passname: {0} not found, use create=True'.format(self.passname))
                else:
                    return False
            else:
                raise AnsibleError(e)
        return True

    def get_newpass(self):
        if self.paramvals['userpass']:
            newpass = self.paramvals['userpass']
        else:
            newpass = random_password(length=self.paramvals['length'])
        return newpass

    def update_password(self):
        # generate new password, insert old lines from current result and return new password
        newpass = self.get_newpass()
        datetime = time.strftime("%d/%m/%Y %H:%M:%S")
        msg = newpass + '\n' + '\n'.join(self.passoutput[1:])
        msg += "\nlookup_pass: old password was {0} (Updated on {1})\n".format(self.password, datetime)
        try:
            check_output2(['pass', 'insert', '-f', '-m', self.passname], input=msg)
        except (subprocess.CalledProcessError) as e:
            raise AnsibleError(e)
        return newpass

    def generate_password(self):
        # generate new file and insert lookup_pass: Generated by Ansible on {date}
        # use pwgen to generate the password and insert values with pass -m
        newpass = self.get_newpass()
        datetime = time.strftime("%d/%m/%Y %H:%M:%S")
        msg = newpass + '\n' + "lookup_pass: First generated by ansible on {0}\n".format(datetime)
        try:
            check_output2(['pass', 'insert', '-f', '-m', self.passname], input=msg)
        except (subprocess.CalledProcessError) as e:
            raise AnsibleError(e)
        return newpass

    def get_passresult(self):
        if self.paramvals['returnall']:
            return os.linesep.join(self.passoutput)
        if self.paramvals['subkey'] == 'password':
            return self.password
        else:
            if self.paramvals['subkey'] in self.passdict:
                return self.passdict[self.paramvals['subkey']]
            else:
                return None

    def run(self, terms, variables, **kwargs):
        result = []
        self.paramvals = {
            'subkey': 'password',
            'directory': variables.get('passwordstore'),
            'create': False,
            'returnall': False,
            'overwrite': False,
            'userpass': '',
            'length': 16,
        }

        for term in terms:
            self.parse_params(term)   # parse the input into paramvals
            if self.check_pass():     # password exists
                if self.paramvals['overwrite'] and self.paramvals['subkey'] == 'password':
                    result.append(self.update_password())
                else:
                    result.append(self.get_passresult())
            else:                     # password does not exist
                if self.paramvals['create']:
                    result.append(self.generate_password())
        return result
