# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contributer: Brandon Schlueter <b@schlueter.blue> [:schlueter]
# Contributor: Julien Vehent <jvehent@mozilla.com> [:ulfr]
# Contributor: Daniel Thornton <daniel@relud.com>
# Contributor: Alexis Metaireau <alexis@mozilla.com> [:alexis]
# Contributor: Rémy Hubscher <natim@mozilla.com> [:natim]

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    vars: sops
    version_added: "2.6"
    short_description: Loads vars encrypted with Mozilla's sops.
    description:
      - Reads sops configuration from config file in playbook dir or above it.
      - For any file in a group or host vars directory matching a creation
        rule, it is loaded using sops (potentially using a sops configuration
        file closer to it).
      - Files are decrypted by default. This can be disabled by setting the
        ANSIBLE_SOPS_IGNORE environment variable to yes, on, or true. If decryption
        failure should fail the playbook run, ANSIBLE_SOPS_REQUIRE may be set.
'''

import hashlib
import os
import re
import subprocess
import sys
from base64 import b64decode
from socket import gethostname

try:
    import boto3
except ImportError:
    raise AnsibleError("The vars plugin sops requires boto3.")
    
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, modes, algorithms

import yaml
from ansible.errors import AnsibleParserError
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.vars import BaseVarsPlugin
from ansible.utils.vars import combine_vars

UNENCRYPTED_SUFFIX = '_unencrypted'
CONFIG_FILE_SEARCH_DEPTH = 100
DEFAULT_CONFIG_FILE = '.sops.yaml'


class VarsModule(BaseVarsPlugin):
    """ A Vars Module to load vars from files encrypted with Mozilla's Sops

    Parts of this class are taken from Mozilla's original Sops python version at
    https://github.com/mozilla/sops/tree/python-sops.
    """

    def get_vars(self, loader, path, entities, cache=True):
        ''' parses the inventory file '''

        if not isinstance(entities, list):
            entities = [entities]

        super(VarsModule, self).get_vars(loader, path, entities)

        if os.environ.get('ANSIBLE_SOPS_IGNORE', '').lower() in ['yes', 'on', 'true']:
            return {}

        if os.environ.get('ANSIBLE_SOPS_REQUIRE', '').lower() in ['yes', 'on', 'true']:
            self.sops_required = True
        else:
            self.sops_required = False

        found = {}
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
                    opath = os.path.realpath(os.path.join(self._basedir, subdir))
                    key = '%s.%s' % (entity.name, opath)
                    if cache and key in found:
                        found_files = found[key]
                    else:
                        b_opath = to_bytes(opath)
                        # no need to do much if path does not exist for basedir
                        if os.path.exists(b_opath):
                            if os.path.isdir(b_opath):
                                self._display.debug("\tprocessing dir %s" % opath)
                                found_files = self._find_vars_files(opath, entity.name)
                                found[key] = found_files
                            else:
                                self._display.warning("Found %s that is not a "
                                                      "directory, skipping: %s" % (subdir, opath))

                    for found in found_files:
                        # add vars from files to data
                        new_data = self._get_sops_vars(found)
                        if new_data:  # ignore empty files
                            data = combine_vars(data, new_data)

                except Exception as e:
                    raise AnsibleParserError(to_native(e))
        return data

    def _get_sops_vars(self, path):
        tree = self._load_file_into_tree(path)
        sops_key, tree = self._get_key(tree)
        if sops_key is None:
            return {}
        tree = self._walk_and_decrypt(tree, sops_key)
        del tree['sops']
        return dict(tree)

    def _load_file_into_tree(self, path):
        """Load the tree.

        Read data from `path` using format defined by `filetype`.
        Return a dictionary with the data.

        """
        with open(path, "rb") as fd:
            tree = yaml.load(fd)
        if tree is None:
            self._display.vvv("failed to load file into tree, got an empty tree")
        return tree

    def _get_key(self, tree):
        """Obtain a 256 bits symetric key.

        If the document contain an encrypted key, try to decrypt it using
        KMS or PGP. Otherwise, generate a new random key.

        """
        key = self._get_key_from_kms(tree)
        if not (key is None):
            return key, tree
        key = self._get_key_from_pgp(tree)
        if not (key is None):
            return key, tree
        self._sops_failure("Could not retrieve a key to decrypt sops files")
        return None, tree

    def _get_key_from_pgp(self, tree):
        """Retrieve the key from the PGP tree leave."""
        try:
            pgp_tree = tree['sops']['pgp']
        except KeyError:
            return None
        i = -1
        for entry in pgp_tree:
            if not entry:
                continue
            i += 1
            try:
                enc = entry['enc']
            except KeyError:
                continue
            try:
                # check if the user has specified a custom GPG program.
                gpg_exec = os.environ.get('SOPS_GPG_EXEC', 'gpg')

                p = subprocess.Popen([gpg_exec, '--use-agent', '-d'],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE)
                key = p.communicate(input=enc.encode('utf-8'))[0]
            except Exception as e:
                self._display.warning("PGP decryption failed in entry %s with error: %s" % (i, e))
                continue
            if len(key) == 32:
                return key
        return None

    def _get_key_from_kms(self, tree):
        """Get the key form the KMS tree leave."""
        try:
            kms_tree = tree['sops']['kms']
        except KeyError:
            return None
        i = -1
        errors = []
        for entry in kms_tree:
            if not entry:
                continue
            i += 1
            try:
                enc = entry['enc']
            except KeyError:
                continue
            if 'arn' not in entry or entry['arn'] == "":
                self._display.vvv("WARN: KMS ARN not found, skipping entry %s" % i)
                continue
            kms, err = self._get_aws_session_for_entry(entry)
            if err != "":
                errors.append("failed to obtain kms %s, error was: %s" %
                              (entry['arn'], err))
                continue
            if kms is None:
                errors.append("no kms client could be obtained for entry %s" %
                              entry['arn'])
                continue
            context = entry['context'] if 'context' in entry else {}
            try:
                kms_response = kms.decrypt(CiphertextBlob=b64decode(enc),
                                           EncryptionContext=context)
            except Exception as e:
                errors.append("kms %s failed with error: %s " % (entry['arn'], e))
                continue
            return kms_response['Plaintext']
        self._display.debug("WARN: no KMS client could be accessed:")
        for err in errors:
            self._display.debug("* %s" % err)
        return None

    def _get_aws_session_for_entry(self, entry):
        """Return a boto3 session using a role if one exists in the entry"""
        # extract the region from the ARN
        # arn:aws:kms:{REGION}:...
        res = re.match('^arn:aws:kms:(.+):([0-9]+):key/(.+)$', entry['arn'])
        if res is None:
            return (None, "Invalid ARN '%s' in entry" % entry['arn'])
        try:
            region = res.group(1)
        except Exception as e:
            return (None, "Unable to find region from ARN '%s' in entry" %
                          entry['arn'])
        # if there are no role to assume, return the client directly
        if not ('role' in entry):
            try:
                cli = boto3.client('kms', region_name=region)
            except Exception as e:
                return (None, "Unable to get boto3 client in %s" % region)
            return (cli, "")
        # otherwise, create a client using temporary tokens that assume the role
        try:
            client = boto3.client('sts')
            role = client.assume_role(RoleArn=entry['role'],
                                      RoleSessionName='sops@' + gethostname())
        except Exception as e:
            return (None, "Unable to switch roles: %s" % e)
        try:
            self._display.vvv("INFO: assuming AWS role '%s'" % role['AssumedRoleUser']['Arn'])
            keyid = role['Credentials']['AccessKeyId']
            secretkey = role['Credentials']['SecretAccessKey']
            token = role['Credentials']['SessionToken']
            return (boto3.client('kms', region_name=region,
                                 aws_access_key_id=keyid,
                                 aws_secret_access_key=secretkey,
                                 aws_session_token=token),
                    "")
        except KeyError:
            return (None, "failed to initialize KMS client")

    def _walk_and_decrypt(self, branch, key, aad=r'', stash=None, digest=None,
                          isRoot=True, unencrypted=False):
        """Walk the branch recursively and decrypt leaves."""
        if isRoot:
            digest = hashlib.sha512()
        for k, v in branch.items():
            if k == 'sops' and isRoot:
                continue    # everything under the `sops` key stays in clear
            unencrypted_branch = unencrypted or k.endswith(UNENCRYPTED_SUFFIX)
            nstash = dict()
            caad = aad
            caad = aad + k.encode('utf-8') + r':'
            if stash:
                stash[k] = {'has_stash': True}
                nstash = stash[k]
            if isinstance(v, dict):
                branch[k] = self._walk_and_decrypt(v, key, aad=caad, stash=nstash,
                                                   digest=digest, isRoot=False,
                                                   unencrypted=unencrypted_branch)
            elif isinstance(v, list):
                branch[k] = self._walk_list_and_decrypt(v, key, aad=caad, stash=nstash,
                                                        digest=digest,
                                                        unencrypted=unencrypted_branch)
            else:
                branch[k] = self._decrypt(v, key, aad=caad, stash=nstash, digest=digest,
                                          unencrypted=unencrypted_branch)

        if isRoot:
            # compute the hash computed on values with the one stored
            # in the file. If they match, all is well.
            if not ('mac' in branch['sops']):
                self._display.vvv("'mac' not found, unable to verify file integrity")
            h = digest.hexdigest().upper()
            # We know the original hash is trustworthy because it is encrypted
            # with the data key and authenticated using the lastmodified timestamp
            orig_h = self._decrypt(branch['sops']['mac'],
                                   key,
                                   aad=branch['sops']['lastmodified'].encode('utf-8'))
            if h != orig_h:
                self._display.vvv("Checksum verification failed!\nexpected %s\nbut got  %s" % (orig_h, h))

        return branch

    def _walk_list_and_decrypt(self, branch, key, aad=r'', stash=None, digest=None, unencrypted=False):
        """Walk a list contained in a branch and decrypts its values."""
        nstash = dict()
        kl = []
        for i, v in enumerate(list(branch)):
            if stash:
                stash[i] = {'has_stash': True}
                nstash = stash[i]
            if isinstance(v, dict):
                kl.append(self._walk_and_decrypt(v, key, aad=aad, stash=nstash,
                                                 digest=digest, isRoot=False,
                                                 unencrypted=unencrypted))
            elif isinstance(v, list):
                kl.append(self._walk_list_and_decrypt(v, key, aad=aad, stash=nstash,
                                                      digest=digest,
                                                      unencrypted=unencrypted))
            else:
                kl.append(self._decrypt(v, key, aad=aad, stash=nstash, digest=digest,
                                        unencrypted=unencrypted))
        return kl

    def _decrypt(self, value, key, aad=r'', stash=None, digest=None, unencrypted=False):
        """Return a decrypted value."""
        if unencrypted:
            if digest:
                bvalue = to_bytes(value)
                digest.update(bvalue)
            return value

        valre = r'^ENC\[AES256_GCM,data:(.+),iv:(.+),tag:(.+)'
        # extract fields using a regex
        valre += r',type:(.+)'
        valre += r'\]'
        res = re.match(valre, value.encode('utf-8'))
        # if the value isn't in encrypted form, return it as is
        if res is None:
            return value
        enc_value = b64decode(res.group(1))
        iv = b64decode(res.group(2))
        tag = b64decode(res.group(3))
        valtype = 'str'
        valtype = res.group(4)
        decryptor = Cipher(algorithms.AES(key),
                           modes.GCM(iv, tag),
                           default_backend()
                           ).decryptor()
        decryptor.authenticate_additional_data(aad)
        cleartext = decryptor.update(enc_value) + decryptor.finalize()

        if stash:
            # save the values for later if we need to reencrypt
            stash['iv'] = iv
            stash['aad'] = aad
            stash['cleartext'] = cleartext

        if digest:
            digest.update(cleartext)

        if valtype == r'bytes':
            return cleartext
        if valtype == r'str':
            # Welcome to python compatibility hell... :(
            # Python 2 treats everything as str, but python 3 treats bytes and str
            # as different types. So if a file was encrypted by sops with py2, and
            # contains bytes data, it will have type 'str' and py3 will decode
            # it as utf-8. This will result in a UnicodeDecodeError exception
            # because random bytes are not unicode. So the little try block below
            # catches it and returns the raw bytes if the value isn't unicode.
            cv = cleartext
            try:
                cv = cleartext.decode('utf-8')
            except UnicodeDecodeError:
                return cleartext
            return cv
        if valtype == r'int':
            return int(cleartext.decode('utf-8'))
        if valtype == r'float':
            return float(cleartext.decode('utf-8'))
        if valtype == r'bool':
            if cleartext.lower() == r'true':
                return True
            return False
        self._display.vvv("unknown type " + valtype)

    def _find_vars_files(self, path, name):
        """ Find {group,host}_vars files """
        b_path = to_bytes(os.path.join(path, name))
        found = []

        file_regexes = self._get_sops_file_regexes()

        # first look for w/o extensions
        if os.path.exists(b_path):
            if os.path.isdir(b_path):
                found.extend(self._get_dir_files(to_text(b_path), file_regexes))

        return found

    def _get_sops_file_regexes(self):
        config_file_path = self._find_sops_config_file()
        creation_rules_regexes = []
        try:
            config_file = open(config_file_path)
            config_text = config_file.read()
            sops_config = yaml.load(config_text)
            if 'creation_rules' not in sops_config:
                self._display.warning('No creation_rules in sops config')
                return []
            for rule in sops_config["creation_rules"]:
                if "path_regex" not in rule:
                    continue
                creation_rules_regexes.append(rule['path_regex'])
        except Exception as e:
            raise AnsibleParserError(to_native(e))
        self.sops_files_regexes = creation_rules_regexes
        return self.sops_files_regexes

    def _find_sops_config_file(self):
        for i in range(CONFIG_FILE_SEARCH_DEPTH):
            try:
                os.stat((i * "../") + DEFAULT_CONFIG_FILE)
            except Exception:
                continue
            # when we find a file, exit the loop
            return (i * "../") + DEFAULT_CONFIG_FILE
        return None

    def _get_dir_files(self, path, file_regexes):
        found = []
        for spath in sorted(os.listdir(path)):
            if not spath.startswith(u'.') and not spath.endswith(u'~'):  # skip hidden and backups

                full_spath = os.path.join(path, spath)

                if os.path.isdir(full_spath):  # recursive search if dir
                    found.extend(self._get_dir_files(full_spath))
                else:
                    for pattern in file_regexes:
                        if re.search(pattern, full_spath):
                            found.append(full_spath)

        return found

    def _sops_failure(self, msg):
        if self.sops_required:
            raise self.SOPSRequiredException(msg)
        else:
            self._display.warning(msg)

    class SOPSRequiredException(Exception):
        pass
