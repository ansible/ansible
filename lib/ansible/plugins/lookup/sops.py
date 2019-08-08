# -*- coding: utf-8 -*-
#
#  Copyright 2018 Edoardo Tenani <e.tenani@arduino.cc> [@endorama]
#
# This file is part of Ansible.
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
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleParserError, AnsibleLookupError
from ansible.plugins.lookup import LookupBase

from ansible.utils.display import Display
display = Display()

from subprocess import Popen, PIPE

DOCUMENTATION = """
    lookup: sops
    author: Edoardo Tenani <e.tenani@arduino.cc>
    version_added: "2.8"
    short_description: Read sops encrypted file contents
    description:
        - This lookup returns the contents from a file on the Ansible controller's file system.
        - This lookup requires the sops executable to be available in the controller PATH.
    options:
        _terms:
            description: path(s) of files to read
            required: True
        binary:
            description: determine if sops output should be decoded as text or considered binary
            type: bool
            required: False
            default: False
    notes:
        - this lookup does not understand 'globing' - use the fileglob lookup instead.
"""

EXAMPLES = """
tasks:
  - name : output secrets to screen (BAD IDEA)
    debug:
        msg: "Content: {{lookup('sops', item)}}"
    with_file:
    - sops-encrypted-file.enc.yaml

  - name: add ssh private key
    copy:
        content: "{{lookup('sops', user + '-id_rsa')}}"
        dest: /home/{{user}}/.ssh/id_rsa
        owner: "{{user}}"
        group: "{{user}}"
        mode: 0600
"""

RETURN = """
    _raw:
        description: decrypted file content
"""

# From https://github.com/mozilla/sops/blob/master/cmd/sops/codes/codes.go
# Should be manually updated
sops_error_codes = {
    1: "ErrorGeneric",
    2: "CouldNotReadInputFile",
    3: "CouldNotWriteOutputFile",
    4: "ErrorDumpingTree",
    5: "ErrorReadingConfig",
    6: "ErrorInvalidKMSEncryptionContextFormat",
    7: "ErrorInvalidSetFormat",
    8: "ErrorConflictingParameters",
    21: "ErrorEncryptingMac",
    23: "ErrorEncryptingTree",
    24: "ErrorDecryptingMac",
    25: "ErrorDecryptingTree",
    49: "CannotChangeKeysFromNonExistentFile",
    51: "MacMismatch",
    52: "MacNotFound",
    61: "ConfigFileNotFound",
    85: "KeyboardInterrupt",
    91: "InvalidTreePathFormat",
    100: "NoFileSpecified",
    128: "CouldNotRetrieveKey",
    111: "NoEncryptionKeyFound",
    200: "FileHasNotBeenModified",
    201: "NoEditorFound",
    202: "FailedToCompareVersions",
    203: "FileAlreadyEncrypted"
}


class Sops():
    @staticmethod
    def decrypt(encrypted_file):
        # Run sops directly, python module is deprecated
        command = ["sops", "--decrypt", encrypted_file]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        return output, err, exit_code


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        ret = []

        sops_text_output = True
        if 'binary' in kwargs:
            sops_text_output = not kwargs['binary']

        for term in terms:
            display.debug("Sops lookup term: %s" % term)
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"Sops lookup using %s as file" % lookupfile)

            try:
                if lookupfile:
                    # Run sops directly, python module is deprecated
                    command = ["sops", "--decrypt", lookupfile]
                    process = Popen(command, stdout=PIPE, stderr=PIPE)
                    (output, err) = process.communicate()
                    exit_code = process.wait()

                    if sops_text_output:
                        # output is binary, we want UTF-8 string
                        output = output.decode('UTF-8')

                    # the process output is the decrypted secret; displaying it
                    # here would easily end in logs, be cautious
                    # if output:
                    #     display.vvvv(output)

                    # sops logs always to stderr, as stdout is used for
                    # file content
                    if err:
                        display.vvvv(err)

                    if exit_code > 0:
                        if exit_code in sops_error_codes.keys():
                            raise AnsibleLookupError("could not decrypt file %s; Sops error: %s" % (term, sops_error_codes[exit_code]))
                        else:
                            raise AnsibleLookupError("could not decrypt file %s; Unknown sops error code: %s" % (term, exit_code))

                    ret.append(output.rstrip())
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("could not locate file in lookup: %s" % term)

        return ret
