# Copyright (c), Edoardo Tenani <e.tenani@arduino.cc>, 2018-2020
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

from ansible.errors import AnsibleError

from subprocess import Popen, PIPE

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
    ''' Extend AnsibleError class with sops specific informations '''

    def __init__(self, filename, exit_code, message,):
        exception_name = sops_error_codes[exit_code]
        message = "error with file %s: %s exited with code %d: %s" % (filename, exception_name, exit_code, message)
        super(SopsError, self).__init__(message=message)


class Sops():
    ''' Utility class to perform sops CLI actions '''

    @staticmethod
    def decrypt(encrypted_file):
        # Run sops directly, python module is deprecated
        command = ["sops", "--decrypt", encrypted_file]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        return output, err, exit_code
