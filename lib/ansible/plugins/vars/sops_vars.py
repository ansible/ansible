# Copyright 2019 Arduino, srl
#
#############################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    vars: sops_vars
    author: Edoardo Tenani <e.tenani@arduino.cc>
    version_added: "2.8"
    short_description: Loading sops-encrypted vars files
    description:
        - Load encrypted YAML files into correspondind groups/hosts in group_vars/ and host_vars/ directories.
        - Files are encrypted prior to reading, making this plugin an effective companion to host_group_vars plugin.
        - Files are restricted to .sops.yaml, .sops.yml, .sops.json extensions.
        - Hidden files are ignored.
    options:
      _valid_extensions:
        default: [".sops.yml", ".sops.yaml", ".sops.json"]
        description:
          - "Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these."
          - 'This affects vars_files, include_vars, inventory and vars plugins among others.'
        type: list
'''

import os
from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars
from ansible.errors import AnsibleError
from subprocess import Popen, PIPE
from ansible.utils.display import Display
display = Display()

FOUND = {}
DEFAULT_VALID_EXTENSIONS = [".sops.yaml", ".sops.yml", ".sops.json"]

# From https://github.com/mozilla/sops/blob/master/cmd/sops/codes/codes.go
# Should be manually updated
sops_error_codes = {
    1: "SopsErrorGeneric",
    2: "SopsCouldNotReadInputFile",
    3: "SopsCouldNotWriteOutputFile",
    4: "SopsErrorDumpingTree",
    5: "SopsErrorReadingConfig",
    6: "SopsErrorInvalidKMSEncryptionContextFormat",
    7: "SopsErrorInvalidSetFormat",
    8: "SopsErrorConflictingParameters",
    21: "SopsErrorEncryptingMac",
    23: "SopsErrorEncryptingTree",
    24: "SopsErrorDecryptingMac",
    25: "SopsErrorDecryptingTree",
    49: "SopsCannotChangeKeysFromNonExistentFile",
    51: "SopsMacMismatch",
    52: "SopsMacNotFound",
    61: "SopsConfigFileNotFound",
    85: "SopsKeyboardInterrupt",
    91: "SopsInvalidTreePathFormat",
    100: "SopsNoFileSpecified",
    128: "SopsCouldNotRetrieveKey",
    111: "SopsNoEncryptionKeyFound",
    200: "SopsFileHasNotBeenModified",
    201: "SopsNoEditorFound",
    202: "SopsFailedToCompareVersions",
    203: "SopsFileAlreadyEncrypted"
}


class SopsError(AnsibleError):
    ''' extend AnsibleError class with sops specific informations '''

    def __init__(self, filename, exit_code, message="Unknown error",):
        message = "error with file %s: sops exited with code %d: %s" % (filename, exit_code, message)
        super(SopsError, self).__init__(message=message)


class SopsErrorGeneric(SopsError):
    pass


class SopsCouldNotReadInputFile(SopsError):
    pass


class SopsCouldNotWriteOutputFile(SopsError):
    pass


class SopsErrorDumpingTree(SopsError):
    pass


class SopsErrorReadingConfig(SopsError):
    pass


class SopsErrorInvalidKMSEncryptionContextFormat(SopsError):
    pass


class SopsErrorInvalidSetFormat(SopsError):
    pass


class SopsErrorConflictingParameters(SopsError):
    pass


class SopsErrorEncryptingMac(SopsError):
    pass


class SopsErrorEncryptingTree(SopsError):
    pass


class SopsErrorDecryptingMac(SopsError):
    pass


class SopsErrorDecryptingTree(SopsError):
    pass


class SopsCannotChangeKeysFromNonExistentFile(SopsError):
    pass


class SopsMacMismatch(SopsError):
    pass


class SopsMacNotFound(SopsError):
    pass


class SopsConfigFileNotFound(SopsError):
    pass


class SopsKeyboardInterrupt(SopsError):
    pass


class SopsInvalidTreePathFormat(SopsError):
    pass


class SopsNoFileSpecified(SopsError):
    pass


class SopsCouldNotRetrieveKey(SopsError):
    pass


class SopsNoEncryptionKeyFound(SopsError):
    pass


class SopsFileHasNotBeenModified(SopsError):
    pass


class SopsNoEditorFound(SopsError):
    pass


class SopsFailedToCompareVersions(SopsError):
    pass


class SopsFileAlreadyEncrypted(SopsError):
    pass


def decrypt_with_sops(filename):
    display.vvvv(u"sops --decrypt %s" % filename)

    # Run sops directly as python module is deprecated
    process = Popen(["sops", "--decrypt", filename], stdout=PIPE, stderr=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()

    # DO NOT display output
    # is the decrypted secret and would easily end in logs :)
    # if output:
    #     display.vvvv(output)

    # sops logs always to stderr ( stdout is used for file content )
    if err:
        display.vvvv(err)

    if exit_code > 0:
        if exit_code in sops_error_codes.keys():
            exception_name = sops_error_codes[exit_code]
            raise globals()[exception_name](filename, exit_code, err)
        else:
            raise AnsibleError(message=err)

    return output


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):
        ''' parses the inventory file '''

        if not isinstance(entities, list):
            entities = [entities]

        super(VarsModule, self).get_vars(loader, path, entities)

        data = {}
        for entity in entities:
            if isinstance(entity, Host):
                subdir = 'host_vars'
            elif isinstance(entity, Group):
                subdir = 'group_vars'
            else:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            # avoid 'chroot' type inventory hostnames /path/to/chroot
            if not entity.name.startswith(os.path.sep):
                try:
                    found_files = []
                    # load vars
                    b_opath = os.path.realpath(to_bytes(os.path.join(self._basedir, subdir)))
                    opath = to_text(b_opath)
                    key = '%s.%s' % (entity.name, opath)
                    self._display.vvvv("key: %s" % (key))
                    if cache and key in FOUND:
                        found_files = FOUND[key]
                    else:
                        # no need to do much if path does not exist for basedir
                        if os.path.exists(b_opath):
                            if os.path.isdir(b_opath):
                                self._display.debug("\tprocessing dir %s" % opath)
                                found_files = loader.find_vars_files(opath, entity.name, DEFAULT_VALID_EXTENSIONS)
                                FOUND[key] = found_files
                            else:
                                self._display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))

                    for found in found_files:
                        file_content = decrypt_with_sops(found)
                        new_data = loader.load(file_content)
                        if new_data:  # ignore empty files
                            data = combine_vars(data, new_data)

                except Exception as e:
                    raise AnsibleParserError(to_native(e))

        return data
