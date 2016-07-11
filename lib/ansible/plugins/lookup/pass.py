#!/usr/bin/python
# (c) 2016, Patrick Deelman <morphje@morphje.nl>
# (c) 2016, Mark Janssen <mark@sig-io.nl>
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


'''

#ansible_pass_lookup
====================
An Ansible lookup for [password store](https://www.passwordstore.org/) passwords 

This lookup enables the ansible admin to retrieve, create or update passwords from
his pass store. It also retrieves YAML style keys stored as multilines in the passwordfile

Examples
--------
(for detailed information see [ansible website](http://docs.ansible.com/ansible/playbooks_lookups.html))

Basic lookup. Fails if example/test doesn't exist
`password="{{ lookup('pass', 'example/test')}}`

Create pass with random 16 char password. If password exists just give the password
`password="{{ lookup('pass', 'example/test create=true')}}`

Different size password
`password="{{ lookup('pass', 'example/test create=true length=42')}}`

Create pass and overwrite the password if it exists
As a bonus, this module includes the old password inside the pass file
`password="{{ lookup('pass', 'example/test create=true overwrite=true')}}`

Return the value for user in the KV pair user: username
`password="{{ lookup('pass', 'example/test subkey=user')}}`

Return the entire pass file content
`password="{{ lookup('pass', 'example/test returnall=true')}}`

The location of the password-store directory can be specified in the following ways:
  - Default is ~/.password-store
  - Can be overruled by PASSWORD_STORE_DIR environment variable
  - Can be overruled by 'passwordstore: path/to/.password-store' ansible setting
  - Can be overrules by 'directory=path' argument in the lookup call

'''



from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import subprocess
import time
from distutils import util
from ansible.errors import AnsibleError
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
        inputdata = kwargs['input']
        del kwargs['input']
        kwargs['stdin'] = subprocess.PIPE
    else:
        inputdata = None
    process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    try:
        out,err = process.communicate(inputdata)
    except:
        process.kill()
        process.wait()
        raise
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, out+err)
    return out

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
                    assert(name in self.paramvals)
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
                    raise AnsibleError("{} is not a correct value for length".format(self.paramvals['length']))

            # Set PASSWORD_STORE_DIR if directory is set
            if self.paramvals['directory']:
                if os.path.isdir(self.paramvals['directory']):
                    os.environ['PASSWORD_STORE_DIR'] = self.paramvals['directory']
                else:
                    raise AnsibleError('Passwordstore directory \'{}\' does not exist'.format(self.paramvals['directory']))

    def check_pass(self):
        try:
            self.passoutput = check_output2(["pass", self.passname]).splitlines()
            self.password = self.passoutput[0]
            self.passdict = {}
            for line in self.passoutput[1:]:
                if ":" in line:
                    name, value = line.split(':', 1)
                    self.passdict[name.strip()] = value.strip()
        except (subprocess.CalledProcessError) as e:
            if e.returncode == 1 and 'not in the password store' in e.output:
                # if pass returns 1 and return string contains 'is not in the password store.'
                # We need to determine if this is valid or Error.
                if not self.paramvals['create']:
                    raise AnsibleError('passname: {} not found, use create=True'.format(self.passname))
                else:
                    return False
            else:
                raise AnsibleError(e)
        return True

    def update_password(self):
        # generate new password, insert old lines from current result and return new password
        try:
            newpass = check_output2(['pwgen','-cns',str(self.paramvals['length']), '1']).rstrip()
            datetime= time.strftime("%d/%m/%Y %H:%M:%S")
            msg = newpass +'\n' + '\n'.join(self.passoutput[1:]) + "\nlookup_pass: old password was {} (Updated on {})\n".format(self.password, datetime)
            generate = check_output2(['pass','insert','-f','-m',self.passname], input=msg)
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

    def generate_password(self):
        # generate new file and insert lookup_pass: Generated by Ansible on {date}
        # use pwgen to generate the password and insert values with pass -m
        try:
            newpass = check_output2(['pwgen','-cns',str(self.paramvals['length']), '1']).rstrip()
            datetime = time.strftime("%d/%m/%Y %H:%M:%S")
            msg = newpass + '\n' + "lookup_pass: First generated by ansible on {}\n".format(datetime)
            generate = check_output2(['pass','insert','-f','-m',self.passname], input=msg)
        except (subprocess.CalledProcessError) as e:
            raise AnsibleError(e)
        return newpass

    def run(self, terms, variables, **kwargs):
        result = []
        self.paramvals = {
            'subkey':'password',
            'directory':variables.get('passwordstore'),
            'create':False,
            'returnall': False,
            'overwrite':False,
            'length': 16}

        for term in terms:
            self.parse_params(term)
            if self.check_pass(): #password exists
                if self.paramvals['create'] and self.paramvals['overwrite'] and self.paramvals['subkey'] == 'password':
                    result.append(self.update_password())
                else:
                    result.append(self.get_passresult())
            else: # initial call to pass already generated an Error, so just call generate_password
                result.append(self.generate_password())
        return result

