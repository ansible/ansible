#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, David Kainz <dkainz@mgit.at> <dave.jokain@gmx.at>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: opencertt
author: "David Kainz (@lolcube)"
version_added: "2.8"
short_description: Generate OpenSSH host or user certificates.
description:
    - "Generate and regenerate OpensSSH host or user certificates."
requirements:
    - "ssh-keygen"
options:
    state:
        required: false
        default: present
        choices: [ present, absent ]
        description:
            - Whether the host or user certificate should exist or not, taking action if the state is different from what is stated.
    type:
        required: true
        choices: ['host', 'user']
        description:
            - Whether the module should generate a host or a user certificate.
    force:
        required: false
        default: false
        type: bool
        description:
            - Should the certificate be regenerated even if it already exists and is valid.
    path:
        required: true
        description:
            - Path of the file containing the certificate.
    signing_key:
        required: true
        description:
            - The path to the private openssh key that is used for signing the public key in order to generate the certificate.
    public_key:
        required: true
        description:
            - The path to the public key that will be signed with the signing key in order to generate the certificate.
    valid_from:
        required: true
        description:
            - "The point in time the certificate is valid from. Time can be specified either as relative time or as absolute timestamp. Time will always be interpreted as UTC.
              Valid formats are: [+-]timespec | YYYY:MM:DD | YYYY:MM:DD:HH:MM:SS | YYYY:MM:DD HH:MM:SS | \"always\" where timespec can be an integer + [w | d | h | m | s] (e.g. +32w1d2h).
              Note that if using relative time this module is NOT idempotent."
    valid_to:
        required: true
        description:
            - "The point in time the certificate is valid to. Time can be specified either as relative time or as absolute timestamp. Time will always be interpreted as UTC.
              Valid formats are: [+-]timespec | YYYY:MM:DD | YYYY:MM:DD:HH:MM:SS | YYYY:MM:DD HH:MM:SS | \"forever\" where timespec can be an integer + [w | d | h | m | s] (e.g. +32w1d2h).
              Note that if using relative time this module is NOT idempotent."
    valid_at:
        required: false
        description:
            - "Check if the certificate is valid at a certain point in time. If it is not the certificate will be regenerated. Time will always be interpreted as UTC.
               Mainly to be used with relative timespec for valid_from and / or valid_to. Note that if using relative time this module is NOT idempotent."
    principals:
        required: false
        description:
            - Certificates may be limited to be valid for a set of principal (user/host) names.  By default, generated certificates are valid for all users or hosts.
    options:
        required: false
        description:
            - Specify a certificate options when signing a key. The option that are valid for user certificates are:

             clear   Clear all enabled permissions.  This is useful for clearing the default set of permissions so permissions may be added individually.

             force-command=command
                     Forces the execution of command instead of any shell or command specified by the user when the certificate is used for authentication.

             no-agent-forwarding
                     Disable ssh-agent forwarding (permitted by default).

             no-port-forwarding
                     Disable port forwarding (permitted by default).

             no-pty  Disable PTY allocation (permitted by default).

             no-user-rc
                     Disable execution of ~/.ssh/rc by sshd (permitted by default).

             no-x11-forwarding
                     Disable X11 forwarding (permitted by default).

             permit-agent-forwarding
                     Allows ssh-agent forwarding.

             permit-port-forwarding
                     Allows port forwarding.

             permit-pty
                     Allows PTY allocation.

             permit-user-rc
                     Allows execution of ~/.ssh/rc by sshd.

             permit-x11-forwarding
                     Allows X11 forwarding.

             source-address=address_list
                     Restrict the source addresses from which the certificate is considered valid.  The address_list is a comma-separated list of one or more address/netmask pairs in CIDR format.

             At present, no options are valid for host keys.

    identifier:
        required: false
        description:
            - Specify the key identity when signing a public key. The identifier that is logged by the server when the certificate is used for authentication.

extends_documentation_fragment: files
'''

EXAMPLES = '''
# Generate an OpenSSH user certificate that is valid forever and for all users
- openssh_cert:
    type: user
    signing_key: /path/to/private_key
    public_key: /path/to/public_key.pub
    path: /path/to/certificate
    valid_from: always
    valid_to: forever

# Generate an OpenSSH host certificate that is valid for 32 weeks from now and will be regenerated
# if it is valid for less than 2 weeks from the time the module is being run
- openssh_cert:
    type: host
    signing_key: /path/to/private_key
    public_key: /path/to/public_key.pub
    path: /path/to/certificate
    valid_from: +0s
    valid_to: +32w
    valid_at: +2w

# Generate an OpenSSH host certificate that is valid forever and only for example.com and examplehost
- openssh_cert:
    type: host
    signing_key: /path/to/private_key
    public_key: /path/to/public_key.pub
    path: /path/to/certificate
    valid_from: always
    valid_to: forever
    principals:
        - example.com
        - examplehost

# Generate an OpenSSH host Certificate that is valid from 21.1.2001 to 21.1.2019
- openssh_cert:
    type: host
    signing_key: /path/to/private_key
    public_key: /path/to/public_key.pub
    path: /path/to/certificate
    valid_from: 2001:01:21
    valid_to: 2019:01:21

'''

RETURN = '''
type:
    description: type of the certificate (host or user)
    returned: changed or success
    type: str
    sample: host
filename:
    description: path to the certificate
    returned: changed or success
    type: str
    sample: /tmp/certifivate-cert.pub
info:
    description: Information about the certificate. Output of "ssh-keygen -L -f".

'''

import os
import errno
import random
import re
import tempfile

from datetime import datetime
from datetime import MINYEAR, MAXYEAR
from datetime import timedelta
from shutil import copy2
from shutil import rmtree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class CertificateError(Exception):
    pass


class Certificate(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.force = module.params['force']
        self.type = module.params['type']
        self.signing_key = module.params['signing_key']
        self.public_key = module.params['public_key']
        self.path = module.params['path']
        self.identifier = module.params['identifier']
        self.valid_from = module.params['valid_from']
        self.valid_to = module.params['valid_to']
        self.valid_at = module.params['valid_at']
        self.principals = module.params['principals']
        self.options = module.params['options']
        self.changed = False
        self.check_mode = module.check_mode
        self.cert_info = {}

        if self.options and self.type == "host":
            module.fail_json(msg="Options can only be used with user certificates.")

        if self.valid_at:
            self.valid_at = self.valid_at.lstrip()
        
        self.valid_from = self.valid_from.lstrip()
        self.valid_to = self.valid_to.lstrip()

    def generate(self, module):

        if not self.isValid(module, perms_required=False) or self.force:
            args = [
                module.get_bin_path('ssh-keygen', True),
                '-s', self.signing_key
            ]

            validity = ""
            
            if not (self.valid_from == "always" and self.valid_to == "forever"):
               
               if not self.valid_from == "always":
                   timeobj = self.convertToDatetime(module, self.valid_from)
                   validity += ( str(timeobj.year).zfill(4) +
                           str(timeobj.month).zfill(2) +
                           str(timeobj.day).zfill(2) +
                           str(timeobj.hour).zfill(2) +
                           str(timeobj.minute).zfill(2) +
                           str(timeobj.second).zfill(2)
                       )
               else:    
                   validity += "19700101010101" # some versions of ssh-keygen die if you give them something below that date

               validity += ":"
               
               if self.valid_to == "forever":
                  timeobj = datetime(MAXYEAR, 12, 31) # on ssh-keygen versions that have the year 2038 bug this will cause the datetime to be 2038-01-19T04:14:07
               else:
                  timeobj = self.convertToDatetime(module, self.valid_to)
              
               validity += ( str(timeobj.year).zfill(4) +
                        str(timeobj.month).zfill(2) +
                        str(timeobj.day).zfill(2) +
                        str(timeobj.hour).zfill(2) +
                        str(timeobj.minute).zfill(2) +
                        str(timeobj.second).zfill(2)
                       ) 

               args.extend(["-V", validity])

            if self.type == 'host':
                args.extend(['-h'])

            if self.identifier:
                args.extend(['-I', self.identifier])
            else:
                args.extend(['-I', ""])
           
            if self.principals:
                args.extend(['-n', ','.join(self.principals)])
            
            if self.options:
               args.extend(['-O', self.options])
 
            args.extend(['-P', ''])
            
            try:
                temp_directory = tempfile.mkdtemp()
                copy2(self.public_key, temp_directory)
                args.extend([temp_directory + "/" + os.path.basename(self.public_key)])
                module.run_command(args, environ_update=dict(TZ="UTC"))
                copy2(temp_directory + "/" + os.path.splitext(os.path.basename(self.public_key))[0] + "-cert.pub", self.path)
                rmtree(temp_directory, ignore_errors=True)
                proc = module.run_command([module.get_bin_path('ssh-keygen', True), '-L', '-f', self.path])
                self.cert_info = proc[1].split()
                self.changed = True
            except Exception as e:
                try:
                    self.remove()
                    rmtree(temp_directory, ignore_errors=True)
                except OSError as exc:
                    if exc.errno != errno.ENOENT:
                        raise CertificateError(exc)
                    else:
                        pass
                module.fail_json(msg="%s" % to_native(e))

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
             self.changed = True

    def convertToDatetime(self, module, timestring): # use snakecase conv_to_datetime

        if self.isRelative(timestring): 
            dispatched_time = re.findall("^([+\-])((\d+)[w])?((\d+)[d])?((\d+)[h])?((\d+)[m])?((\d+)[s])?$", timestring, re.I)
            if not dispatched_time:
                module.fail_json(msg="'%s' is not valid" % timestring)
            dispatched_time = dispatched_time[0]
            if dispatched_time[0] == "+":
                return datetime.utcnow() + timedelta(
                    weeks=int('0' + dispatched_time[2]), 
                    days=int('0' + dispatched_time[4]), 
                    hours=int('0' + dispatched_time[6]), 
                    minutes=int('0' + dispatched_time[8]),
                    seconds=int('0' + dispatched_time[10]))
            else:
                return datetime.utcnow() - timedelta(
                    weeks=int('0' + dispatched_time[2]), 
                    days=int('0' + dispatched_time[4]), 
                    hours=int('0' + dispatched_time[6]), 
                    minutes=int('0' + dispatched_time[8]),
                    seconds=int('0' + dispatched_time[10]))
        else:
            formats = ["%Y:%m:%d", "%Y:%m:%d %H:%M:%S", "%Y:%m:%d:%H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
            for fmt in formats:
                try:
                    return datetime.strptime(timestring, fmt)
                except:
                    pass
            module.fail_json(msg="'%s' is not a valid time format" % timestring)


    def isRelative(self, timestr):
        if timestr.startswith("+") or timestr.startswith("-"):
            return True
        return False

    def isValid(self, module, perms_required=True):

        def _check_state():
            return os.path.exists(self.path)

        if _check_state():
            proc = module.run_command([module.get_bin_path('ssh-keygen', True), '-L', '-f', self.path], environ_update=dict(TZ="UTC"))
            self.cert_info = proc[1].split()
            principals = re.findall("(?<=Principals:)(.*)(?=Critical)", proc[1], re.S)[0].split()
            principals = list(map(str.strip, principals))
            cert_type = re.findall("( user | host )", proc[1])[0].strip()
            validity = re.findall("(from (\d{4}-\d{2}-\d{2}T\d{2}(:\d{2}){2}) to (\d{4}-\d{2}-\d{2}T\d{2}(:\d{2}){2}))", proc[1])
            if validity:
               cert_valid_from = self.convertToDatetime(module, validity[0][1])
               cert_valid_to = self.convertToDatetime(module, validity[0][3])
            else:
               cert_valid_from = datetime(MINYEAR, 1, 1)
               cert_valid_to = datetime(MAXYEAR, 12, 31)
        else:
            return False

        def _check_perms(module):
            file_args = module.load_file_common_arguments(module.params)
            return not module.set_fs_attributes_if_different(file_args, False)

        def _check_type():
            return self.type == cert_type

        def _check_principals():
            return self.principals == principals

        def _check_validity(module):
            if self.valid_from == "always":
                earliest_time = datetime(MINYEAR, 1, 1)
            elif self.isRelative(self.valid_from):
               earliest_time = None
            else:
               earliest_time = self.convertToDatetime(module, self.valid_from)

            if self.valid_to == "forever":
               last_time = datetime(MAXYEAR, 12, 31)
            elif self.isRelative(self.valid_to):
               last_time = None
            else:
               last_time = self.convertToDatetime(module, self.valid_to)

            if earliest_time:
               if not (earliest_time - cert_valid_from).total_seconds == 0.0:
                  return False
            if last_time:
               if not (last_time - cert_valid_to).total_seconds == 0.0:
                  return False

            if self.valid_at:
               if cert_valid_from <= self.convertToDatetime(module, self.vaid_at) <= cert_valid_to:
                  return True

            if earliest_time and last_time:
               return True

            return False

        if not perms_required:
            return  _check_type() and _check_principals() and _check_validity(module)

        return  _check_perms(module) and _check_type() and _check_principals() and _check_validity(module)

    def dump(self):
    
        """Serialize the object into a dictionary."""
        
        def filterKeywords(arr, keywords):
            concated = []
            string = ""
            for word in arr:
                if word in keywords:
                    concated.extend([string])
                    string = ""
                string += " " + word
            concated.extend([string])
            return concated

        def formatCertInfo():
            return filterKeywords(self.cert_info, [
                "Type:",
                "Public",
                "Signing",
                "Key",
                "Serial:",
                "Valid:",
                "Principals:",
                "Critical",
                "Extensions:"])

        result = {
            'changed': self.changed,
            'type': self.type,
            'filename': self.path,
            'info': formatCertInfo(),
      }

        return result

    def remove(self):
        """Remove the resource from the filesystem."""

        try:
            os.remove(self.path)
            self.changed = True
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise CertificateError(exc)
            else:
                pass
        return


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            force=dict(default=False, type=bool),
            type=dict(required=True, choices=['host', 'user'], type='str'),
            signing_key=dict(required=True, type='path'),
            public_key=dict(required=True, type='path'),
            path=dict(required=True,type='path'),
            identifier=dict(type='str'),
            valid_from=dict(required=True, type='str'),
            valid_to=dict(required=True, type='str'),
            valid_at=dict(type='str'),
            principals=dict(type=list),
            options=dict(type=list),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    def isBaseDir(path):
        base_dir = os.path.dirname(path)
        if not os.path.isdir(base_dir):
            module.fail_json(
                name=base_dir,
                msg='The directory %s does not exist or the file is not a directory' % base_dir
            )

    isBaseDir(module.params['signing_key'])
    isBaseDir(module.params['public_key'])
    isBaseDir(module.params['path'])

    certificate = Certificate(module)

    if certificate.state == 'present':

        if module.check_mode:
            result = certificate.dump()
            result['changed'] = module.params['force'] or not certificate.isValid(module)
            module.exit_json(**result)

        try:
            certificate.generate(module)
        except Exception as exc:
            module.fail_json(msg=to_native(exc))

    else:

        if module.check_mode:
            certificate.changed = os.path.exists(module.params['path'])
            if certificate.changed:
                certificate.cert_info = {}
            result = certificate.dump()
            module.exit_json(**result)

        try:
            certificate.remove()
        except Exception as exc:
            module.fail_json(msg=to_native(exc))

    result = certificate.dump()

    module.exit_json(**result) 
       
if __name__ == '__main__':
    main()
