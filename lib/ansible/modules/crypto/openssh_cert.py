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
module: openssh_cert
author: "David Kainz (@lolcube)"
version_added: "2.8"
short_description: Generate OpenSSH host or user certificates.
description:
    - Generate and regenerate OpenSSH host or user certificates.
requirements:
    - "ssh-keygen"
options:
    state:
        description:
            - Whether the host or user certificate should exist or not, taking action if the state is different from what is stated.
        type: str
        default: "present"
        choices: [ 'present', 'absent' ]
    type:
        description:
            - Whether the module should generate a host or a user certificate.
        type: str
        required: true
        choices: ['host', 'user']
    force:
        description:
            - Should the certificate be regenerated even if it already exists and is valid.
        type: bool
        default: false
    path:
        description:
            - Path of the file containing the certificate.
        type: path
        required: true
    signing_key:
        description:
            - The path to the private openssh key that is used for signing the public key in order to generate the certificate.
        type: path
        required: true
    public_key:
        description:
            - The path to the public key that will be signed with the signing key in order to generate the certificate.
        type: path
        required: true
    valid_from:
        description:
            - "The point in time the certificate is valid from. Time can be specified either as relative time or as absolute timestamp.
               Time will always be interpreted as UTC. Valid formats are: C([+-]timespec | YYYY-MM-DD | YYYY-MM-DDTHH:MM:SS | YYYY-MM-DD HH:MM:SS | always)
               where timespec can be an integer + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
               Note that if using relative time this module is NOT idempotent."
        type: str
        required: true
    valid_to:
        description:
            - "The point in time the certificate is valid to. Time can be specified either as relative time or as absolute timestamp.
               Time will always be interpreted as UTC. Valid formats are: C([+-]timespec | YYYY-MM-DD | YYYY-MM-DDTHH:MM:SS | YYYY-MM-DD HH:MM:SS | forever)
               where timespec can be an integer + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
               Note that if using relative time this module is NOT idempotent."
        type: str
        required: true
    valid_at:
        description:
            - "Check if the certificate is valid at a certain point in time. If it is not the certificate will be regenerated.
               Time will always be interpreted as UTC. Mainly to be used with relative timespec for I(valid_from) and / or I(valid_to).
               Note that if using relative time this module is NOT idempotent."
        type: str
    principals:
        description:
            - "Certificates may be limited to be valid for a set of principal (user/host) names.
              By default, generated certificates are valid for all users or hosts."
        type: list
        elements: str
    options:
        description:
            - "Specify certificate options when signing a key. The option that are valid for user certificates are:"
            - "C(clear): Clear all enabled permissions.  This is useful for clearing the default set of permissions so permissions may be added individually."
            - "C(force-command=command): Forces the execution of command instead of any shell or
               command specified by the user when the certificate is used for authentication."
            - "C(no-agent-forwarding): Disable ssh-agent forwarding (permitted by default)."
            - "C(no-port-forwarding): Disable port forwarding (permitted by default)."
            - "C(no-pty Disable): PTY allocation (permitted by default)."
            - "C(no-user-rc): Disable execution of C(~/.ssh/rc) by sshd (permitted by default)."
            - "C(no-x11-forwarding): Disable X11 forwarding (permitted by default)"
            - "C(permit-agent-forwarding): Allows ssh-agent forwarding."
            - "C(permit-port-forwarding): Allows port forwarding."
            - "C(permit-pty): Allows PTY allocation."
            - "C(permit-user-rc): Allows execution of C(~/.ssh/rc) by sshd."
            - "C(permit-x11-forwarding): Allows X11 forwarding."
            - "C(source-address=address_list): Restrict the source addresses from which the certificate is considered valid.
               The C(address_list) is a comma-separated list of one or more address/netmask pairs in CIDR format."
            - "At present, no options are valid for host keys."
        type: list
        elements: str
    identifier:
        description:
            - Specify the key identity when signing a public key. The identifier that is logged by the server when the certificate is used for authentication.
        type: str
    serial_number:
        description:
            - "Specify the certificate serial number.
               The serial number is logged by the server when the certificate is used for authentication.
               The certificate serial number may be used in a KeyRevocationList.
               The serial number may be omitted for checks, but must be specified again for a new certificate.
               Note: The default value set by ssh-keygen is 0."
        type: int

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
    valid_from: "2001-01-21"
    valid_to: "2019-01-21"

# Generate an OpenSSH user Certificate with clear and force-command option:
- openssh_cert:
    type: user
    signing_key: /path/to/private_key
    public_key: /path/to/public_key.pub
    path: /path/to/certificate
    valid_from: always
    valid_to: forever
    options:
        - "clear"
        - "force-command=/tmp/bla/foo"

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
    sample: /tmp/certificate-cert.pub
info:
    description: Information about the certificate. Output of C(ssh-keygen -L -f).
    returned: change or success
    type: list

'''

import os
import errno
import re
import tempfile

from datetime import datetime
from datetime import MINYEAR, MAXYEAR
from shutil import copy2
from shutil import rmtree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.crypto import convert_relative_to_datetime
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
        self.serial_number = module.params['serial_number']
        self.valid_from = module.params['valid_from']
        self.valid_to = module.params['valid_to']
        self.valid_at = module.params['valid_at']
        self.principals = module.params['principals']
        self.options = module.params['options']
        self.changed = False
        self.check_mode = module.check_mode
        self.cert_info = {}

        if self.state == 'present':

            if self.options and self.type == "host":
                module.fail_json(msg="Options can only be used with user certificates.")

            if self.valid_at:
                self.valid_at = self.valid_at.lstrip()

            self.valid_from = self.valid_from.lstrip()
            self.valid_to = self.valid_to.lstrip()

        self.ssh_keygen = module.get_bin_path('ssh-keygen', True)

    def generate(self, module):

        if not self.is_valid(module, perms_required=False) or self.force:
            args = [
                self.ssh_keygen,
                '-s', self.signing_key
            ]

            validity = ""

            if not (self.valid_from == "always" and self.valid_to == "forever"):

                if not self.valid_from == "always":
                    timeobj = self.convert_to_datetime(module, self.valid_from)
                    validity += (
                        str(timeobj.year).zfill(4) +
                        str(timeobj.month).zfill(2) +
                        str(timeobj.day).zfill(2) +
                        str(timeobj.hour).zfill(2) +
                        str(timeobj.minute).zfill(2) +
                        str(timeobj.second).zfill(2)
                    )
                else:
                    validity += "19700101010101"

                validity += ":"

                if self.valid_to == "forever":
                    # on ssh-keygen versions that have the year 2038 bug this will cause the datetime to be 2038-01-19T04:14:07
                    timeobj = datetime(MAXYEAR, 12, 31)
                else:
                    timeobj = self.convert_to_datetime(module, self.valid_to)

                validity += (
                    str(timeobj.year).zfill(4) +
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

            if self.serial_number is not None:
                args.extend(['-z', str(self.serial_number)])

            if self.principals:
                args.extend(['-n', ','.join(self.principals)])

            if self.options:
                for option in self.options:
                    args.extend(['-O'])
                    args.extend([option])

            args.extend(['-P', ''])

            try:
                temp_directory = tempfile.mkdtemp()
                copy2(self.public_key, temp_directory)
                args.extend([temp_directory + "/" + os.path.basename(self.public_key)])
                module.run_command(args, environ_update=dict(TZ="UTC"), check_rc=True)
                copy2(temp_directory + "/" + os.path.splitext(os.path.basename(self.public_key))[0] + "-cert.pub", self.path)
                rmtree(temp_directory, ignore_errors=True)
                proc = module.run_command([self.ssh_keygen, '-L', '-f', self.path])
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

    def convert_to_datetime(self, module, timestring):

        if self.is_relative(timestring):
            result = convert_relative_to_datetime(timestring)
            if result is None:
                module.fail_json(
                    msg="'%s' is not a valid time format." % timestring)
            else:
                return result
        else:
            formats = ["%Y-%m-%d",
                       "%Y-%m-%d %H:%M:%S",
                       "%Y-%m-%dT%H:%M:%S",
                       ]
            for fmt in formats:
                try:
                    return datetime.strptime(timestring, fmt)
                except ValueError:
                    pass
            module.fail_json(msg="'%s' is not a valid time format" % timestring)

    def is_relative(self, timestr):
        if timestr.startswith("+") or timestr.startswith("-"):
            return True
        return False

    def is_same_datetime(self, datetime_one, datetime_two):

        # This function is for backwards compatibility only because .total_seconds() is new in python2.7
        def timedelta_total_seconds(time_delta):
            return (time_delta.microseconds + 0.0 + (time_delta.seconds + time_delta.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        # try to use .total_ seconds() from python2.7
        try:
            return (datetime_one - datetime_two).total_seconds() == 0.0
        except AttributeError:
            return timedelta_total_seconds(datetime_one - datetime_two) == 0.0

    def is_valid(self, module, perms_required=True):

        def _check_state():
            return os.path.exists(self.path)

        if _check_state():
            proc = module.run_command([self.ssh_keygen, '-L', '-f', self.path], environ_update=dict(TZ="UTC"), check_rc=False)
            if proc[0] != 0:
                return False
            self.cert_info = proc[1].split()
            principals = re.findall("(?<=Principals:)(.*)(?=Critical)", proc[1], re.S)[0].split()
            principals = list(map(str.strip, principals))
            if principals == ["(none)"]:
                principals = None
            cert_type = re.findall("( user | host )", proc[1])[0].strip()
            serial_number = re.search(r"Serial: (\d+)", proc[1]).group(1)
            validity = re.findall("(from (\\d{4}-\\d{2}-\\d{2}T\\d{2}(:\\d{2}){2}) to (\\d{4}-\\d{2}-\\d{2}T\\d{2}(:\\d{2}){2}))", proc[1])
            if validity:
                if validity[0][1]:
                    cert_valid_from = self.convert_to_datetime(module, validity[0][1])
                    if self.is_same_datetime(cert_valid_from, self.convert_to_datetime(module, "1970-01-01 01:01:01")):
                        cert_valid_from = datetime(MINYEAR, 1, 1)
                else:
                    cert_valid_from = datetime(MINYEAR, 1, 1)

                if validity[0][3]:
                    cert_valid_to = self.convert_to_datetime(module, validity[0][3])
                    if self.is_same_datetime(cert_valid_to, self.convert_to_datetime(module, "2038-01-19 03:14:07")):
                        cert_valid_to = datetime(MAXYEAR, 12, 31)
                else:
                    cert_valid_to = datetime(MAXYEAR, 12, 31)
            else:
                cert_valid_from = datetime(MINYEAR, 1, 1)
                cert_valid_to = datetime(MAXYEAR, 12, 31)
        else:
            return False

        def _check_perms(module):
            file_args = module.load_file_common_arguments(module.params)
            return not module.set_fs_attributes_if_different(file_args, False)

        def _check_serial_number():
            if self.serial_number is None:
                return True
            return self.serial_number == int(serial_number)

        def _check_type():
            return self.type == cert_type

        def _check_principals():
            if not principals or not self.principals:
                return self.principals == principals
            return set(self.principals) == set(principals)

        def _check_validity(module):
            if self.valid_from == "always":
                earliest_time = datetime(MINYEAR, 1, 1)
            elif self.is_relative(self.valid_from):
                earliest_time = None
            else:
                earliest_time = self.convert_to_datetime(module, self.valid_from)

            if self.valid_to == "forever":
                last_time = datetime(MAXYEAR, 12, 31)
            elif self.is_relative(self.valid_to):
                last_time = None
            else:
                last_time = self.convert_to_datetime(module, self.valid_to)

            if earliest_time:
                if not self.is_same_datetime(earliest_time, cert_valid_from):
                    return False
            if last_time:
                if not self.is_same_datetime(last_time, cert_valid_to):
                    return False

            if self.valid_at:
                if cert_valid_from <= self.convert_to_datetime(module, self.valid_at) <= cert_valid_to:
                    return True

            if earliest_time and last_time:
                return True

            return False

        if perms_required and not _check_perms(module):
            return False

        return _check_type() and _check_principals() and _check_validity(module) and _check_serial_number()

    def dump(self):

        """Serialize the object into a dictionary."""

        def filter_keywords(arr, keywords):
            concated = []
            string = ""
            for word in arr:
                if word in keywords:
                    concated.append(string)
                    string = word
                else:
                    string += " " + word
            concated.append(string)
            # drop the certificate path
            concated.pop(0)
            return concated

        def format_cert_info():
            return filter_keywords(self.cert_info, [
                "Type:",
                "Public",
                "Signing",
                "Key",
                "Serial:",
                "Valid:",
                "Principals:",
                "Critical",
                "Extensions:"])

        if self.state == 'present':
            result = {
                'changed': self.changed,
                'type': self.type,
                'filename': self.path,
                'info': format_cert_info(),
            }
        else:
            result = {
                'changed': self.changed,
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


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            force=dict(type='bool', default=False),
            type=dict(type='str', choices=['host', 'user']),
            signing_key=dict(type='path'),
            public_key=dict(type='path'),
            path=dict(type='path', required=True),
            identifier=dict(type='str'),
            serial_number=dict(type='int'),
            valid_from=dict(type='str'),
            valid_to=dict(type='str'),
            valid_at=dict(type='str'),
            principals=dict(type='list', elements='str'),
            options=dict(type='list', elements='str'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
        required_if=[('state', 'present', ['type', 'signing_key', 'public_key', 'valid_from', 'valid_to'])],
    )

    def isBaseDir(path):
        base_dir = os.path.dirname(path) or '.'
        if not os.path.isdir(base_dir):
            module.fail_json(
                name=base_dir,
                msg='The directory %s does not exist or the file is not a directory' % base_dir
            )
    if module.params['state'] == "present":
        isBaseDir(module.params['signing_key'])
        isBaseDir(module.params['public_key'])

    isBaseDir(module.params['path'])

    certificate = Certificate(module)

    if certificate.state == 'present':

        if module.check_mode:
            certificate.changed = module.params['force'] or not certificate.is_valid(module)
        else:
            try:
                certificate.generate(module)
            except Exception as exc:
                module.fail_json(msg=to_native(exc))

    else:

        if module.check_mode:
            certificate.changed = os.path.exists(module.params['path'])
            if certificate.changed:
                certificate.cert_info = {}
        else:
            try:
                certificate.remove()
            except Exception as exc:
                module.fail_json(msg=to_native(exc))

    result = certificate.dump()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
