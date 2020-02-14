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
from ansible.module_utils._text import to_text, to_native

from ansible.utils.display import Display
display = Display()

from subprocess import Popen, PIPE

DOCUMENTATION = """
    lookup: sops
    author: Edoardo Tenani <e.tenani@arduino.cc>
    version_added: "2.10"
    short_description: Read sops encrypted file contents
    description:
        - This lookup returns the contents from a file on the Ansible controller's file system.
        - This lookup requires the C(sops) executable to be available in the controller PATH.
    options:
        _terms:
            description: path(s) of files to read
            required: True
        print:
            description: print the decrypted content
            type: bool
            required: False
            default: False
    notes:
        - This lookup does not understand 'globbing' - use the fileglob lookup instead.
"""

EXAMPLES = """
tasks:
  - name : output secrets to screen (BAD IDEA)
    debug:
        msg: "Content: {{lookup('sops', item)}}"
    with_items:
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


class SopsError(AnsibleError):
    ''' extend AnsibleError class with sops specific informations '''

    def __init__(self, filename, exit_code, message,):
        exception_name = sops_error_codes[exit_code]
        message = "error with file %s: %s exited with code %d: %s" % (filename, exception_name, exit_code, message)
        super(SopsError, self).__init__(message=message)


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

        print_decrypted = False
        if 'print' in kwargs:
            print_decrypted = kwargs['print']

        for term in terms:
            display.debug("Sops lookup term: %s" % term)
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"Sops lookup using %s as file" % lookupfile)

            try:
                if lookupfile:
                    (output, err, exit_code) = Sops.decrypt(lookupfile)

                    # output is binary, we want UTF-8 string
                    output = to_text(output, errors='surrogate_or_strict')

                    # the process output is the decrypted secret; displaying it
                    # here would easily end in logs, be cautious
                    if print_decrypted and output:
                        display.display(u"Sops decrypted output:")
                        display.display(str(output).rstrip())

                    # sops logs always to stderr, as stdout is used for
                    # file content
                    if err:
                        display.vvvv(err)

                    if exit_code > 0:
                        if exit_code in sops_error_codes.keys():
                            raise SopsError(lookupfile, exit_code, err)
                        else:
                            raise AnsibleLookupError("could not decrypt file %s; Unknown sops error code: %s" % (to_native(term), to_native(exit_code)))

                    ret.append(output.rstrip())
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("could not locate file in lookup: %s" % to_native(term))

        return ret
