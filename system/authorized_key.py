#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to add authorized_keys for ssh logins.
(c) 2012, Brad Olson <brado@movedbylight.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: authorized_key
short_description: Adds or removes an SSH authorized key
description:
     - Adds or removes an SSH authorized key for a user from a remote host.
version_added: "0.5"
options:
  user:
    description:
      - The username on the remote host whose authorized_keys file will be modified
    required: true
    default: null
    aliases: []
  key:
    description:
      - The SSH public key(s), as a string or (since 1.9) url (https://github.com/username.keys)
    required: true
    default: null
  path:
    description:
      - Alternate path to the authorized_keys file
    required: false
    default: "(homedir)+/.ssh/authorized_keys"
    version_added: "1.2"
  manage_dir:
    description:
      - Whether this module should manage the directory of the authorized key file.  If
        set, the module will create the directory, as well as set the owner and permissions
        of an existing directory. Be sure to
        set C(manage_dir=no) if you are using an alternate directory for
        authorized_keys, as set with C(path), since you could lock yourself out of
        SSH access. See the example below.
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
    version_added: "1.2"
  state:
    description:
      - Whether the given key (with the given key_options) should or should not be in the file
    required: false
    choices: [ "present", "absent" ]
    default: "present"
  key_options:
    description:
      - A string of ssh key options to be prepended to the key in the authorized_keys file
    required: false
    default: null
    version_added: "1.4"
  exclusive:
    description:
      - Whether to remove all other non-specified keys from the
        authorized_keys file. Multiple keys can be specified in a single
        key= string value by separating them by newlines.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "1.9"
description:
    - "Adds or removes authorized keys for particular user accounts"
author: Brad Olson
'''

EXAMPLES = '''
# Example using key data from a local file on the management machine
- authorized_key: user=charlie key="{{ lookup('file', '/home/charlie/.ssh/id_rsa.pub') }}"

# Using github url as key source
- authorized_key: user=charlie key=https://github.com/charlie.keys

# Using alternate directory locations:
- authorized_key: user=charlie
                  key="{{ lookup('file', '/home/charlie/.ssh/id_rsa.pub') }}"
                  path='/etc/ssh/authorized_keys/charlie'
                  manage_dir=no

# Using with_file
- name: Set up authorized_keys for the deploy user
  authorized_key: user=deploy
                  key="{{ item }}"
  with_file:
    - public_keys/doe-jane
    - public_keys/doe-john

# Using key_options:
- authorized_key: user=charlie
                  key="{{ lookup('file', '/home/charlie/.ssh/id_rsa.pub') }}"
                  key_options='no-port-forwarding,host="10.0.1.1"'

# Set up authorized_keys exclusively with one key
- authorized_key: user=root key=public_keys/doe-jane state=present
                   exclusive=yes
'''

# Makes sure the public key line is present or absent in the user's .ssh/authorized_keys.
#
# Arguments
# =========
#    user = username
#    key = line to add to authorized_keys for user
#    path = path to the user's authorized_keys file (default: ~/.ssh/authorized_keys)
#    manage_dir = whether to create, and control ownership of the directory (default: true)
#    state = absent|present (default: present)
#
# see example in examples/playbooks

import sys
import os
import pwd
import os.path
import tempfile
import re
import shlex

class keydict(dict):

    """ a dictionary that maintains the order of keys as they are added """
    
    # http://stackoverflow.com/questions/2328235/pythonextend-the-dict-class

    def __init__(self, *args, **kw):
        super(keydict,self).__init__(*args, **kw)
        self.itemlist = super(keydict,self).keys()
    def __setitem__(self, key, value):
        self.itemlist.append(key)
        super(keydict,self).__setitem__(key, value)        
    def __iter__(self):
        return iter(self.itemlist)
    def keys(self):
        return self.itemlist
    def values(self):
        return [self[key] for key in self]
    def itervalues(self):
        return (self[key] for key in self)    

def keyfile(module, user, write=False, path=None, manage_dir=True):
    """
    Calculate name of authorized keys file, optionally creating the
    directories and file, properly setting permissions.

    :param str user: name of user in passwd file
    :param bool write: if True, write changes to authorized_keys file (creating directories if needed)
    :param str path: if not None, use provided path rather than default of '~user/.ssh/authorized_keys'
    :param bool manage_dir: if True, create and set ownership of the parent dir of the authorized_keys file
    :return: full path string to authorized_keys for user
    """

    try:
        user_entry = pwd.getpwnam(user)
    except KeyError, e:
        module.fail_json(msg="Failed to lookup user %s: %s" % (user, str(e)))
    if path is None:
        homedir    = user_entry.pw_dir
        sshdir     = os.path.join(homedir, ".ssh")
        keysfile   = os.path.join(sshdir, "authorized_keys")
    else:
        sshdir     = os.path.dirname(path)
        keysfile   = path

    if not write:
        return keysfile

    uid = user_entry.pw_uid
    gid = user_entry.pw_gid

    if manage_dir:
        if not os.path.exists(sshdir):
            os.mkdir(sshdir, 0700)
            if module.selinux_enabled():
                module.set_default_selinux_context(sshdir, False)
        os.chown(sshdir, uid, gid)
        os.chmod(sshdir, 0700)

    if not os.path.exists(keysfile):
        basedir = os.path.dirname(keysfile)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        try:
            f = open(keysfile, "w") #touches file so we can set ownership and perms
        finally:
            f.close()
        if module.selinux_enabled():
            module.set_default_selinux_context(keysfile, False)

    try:
        os.chown(keysfile, uid, gid)
        os.chmod(keysfile, 0600)
    except OSError:
        pass

    return keysfile

def parseoptions(module, options):
    ''' 
    reads a string containing ssh-key options 
    and returns a dictionary of those options
    '''
    options_dict = keydict() #ordered dict
    if options:
        try:
            # the following regex will split on commas while
            # ignoring those commas that fall within quotes
            regex = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
            parts = regex.split(options)[1:-1]
            for part in parts:
                if "=" in part:
                    (key, value) = part.split("=", 1)
                    options_dict[key] = value
                elif part != ",":
                    options_dict[part] = None
        except:
            module.fail_json(msg="invalid option string: %s" % options)

    return options_dict

def parsekey(module, raw_key):
    '''
    parses a key, which may or may not contain a list
    of ssh-key options at the beginning
    '''

    VALID_SSH2_KEY_TYPES = [
        'ssh-ed25519',
        'ecdsa-sha2-nistp256',
        'ecdsa-sha2-nistp384',
        'ecdsa-sha2-nistp521', 
        'ssh-dss',
        'ssh-rsa',
    ]

    options    = None   # connection options
    key        = None   # encrypted key string
    key_type   = None   # type of ssh key
    type_index = None   # index of keytype in key string|list

    # remove comment yaml escapes
    raw_key = raw_key.replace('\#', '#')

    # split key safely
    lex = shlex.shlex(raw_key)
    lex.quotes = []
    lex.commenters = '' #keep comment hashes
    lex.whitespace_split = True
    key_parts = list(lex)

    for i in range(0, len(key_parts)):
        if key_parts[i] in VALID_SSH2_KEY_TYPES:
            type_index = i
            key_type = key_parts[i]
            break

    # check for options
    if type_index is None:
        return None
    elif type_index > 0:
        options = " ".join(key_parts[:type_index])

    # parse the options (if any)
    options = parseoptions(module, options)

    # get key after the type index
    key = key_parts[(type_index + 1)]

    # set comment to everything after the key
    if len(key_parts) > (type_index + 1):
        comment = " ".join(key_parts[(type_index + 2):])

    return (key, key_type, options, comment)

def readkeys(module, filename):

    if not os.path.isfile(filename):
        return {}

    keys = {}
    f = open(filename)
    for line in f.readlines():
        key_data = parsekey(module, line)
        if key_data:
            # use key as identifier
            keys[key_data[0]] = key_data
        else:
            # for an invalid line, just append the line
            # to the array so it will be re-output later
            keys[line] = line
    f.close()
    return keys

def writekeys(module, filename, keys):

    fd, tmp_path = tempfile.mkstemp('', 'tmp', os.path.dirname(filename))
    f = open(tmp_path,"w")
    try:
        for index, key in keys.items():
            try:
                (keyhash,type,options,comment) = key
                option_str = ""
                if options:
                    option_strings = []
                    for option_key in options.keys():
                        if options[option_key]:
                            option_strings.append("%s=%s" % (option_key, options[option_key]))
                        else:
                            option_strings.append("%s" % option_key)

                    option_str = ",".join(option_strings)
                    option_str += " "
                key_line = "%s%s %s %s\n" % (option_str, type, keyhash, comment)
            except:
                key_line = key
            f.writelines(key_line)
    except IOError, e:
        module.fail_json(msg="Failed to write to file %s: %s" % (tmp_path, str(e)))
    f.close()
    module.atomic_move(tmp_path, filename)

def enforce_state(module, params):
    """
    Add or remove key.
    """

    user        = params["user"]
    key         = params["key"]
    path        = params.get("path", None)
    manage_dir  = params.get("manage_dir", True)
    state       = params.get("state", "present")
    key_options = params.get("key_options", None)
    exclusive   = params.get("exclusive", False)
    error_msg   = "Error getting key from: %s"

    # if the key is a url, request it and use it as key source
    if key.startswith("http"):
        try:
            resp, info = fetch_url(module, key)
            if info['status'] != 200:
                module.fail_json(msg=error_msg % key)
            else:
                key = resp.read()
        except Exception:
            module.fail_json(msg=error_msg % key)

    # extract individual keys into an array, skipping blank lines and comments
    key = [s for s in key.splitlines() if s and not s.startswith('#')]

    # check current state -- just get the filename, don't create file
    do_write = False
    params["keyfile"] = keyfile(module, user, do_write, path, manage_dir)
    existing_keys = readkeys(module, params["keyfile"])

    # Add a place holder for keys that should exist in the state=present and
    # exclusive=true case
    keys_to_exist = []

    # Check our new keys, if any of them exist we'll continue.
    for new_key in key:
        parsed_new_key = parsekey(module, new_key)

        if not parsed_new_key:
            module.fail_json(msg="invalid key specified: %s" % new_key)

        if key_options is not None:
            parsed_options = parseoptions(module, key_options)
            parsed_new_key = (parsed_new_key[0], parsed_new_key[1], parsed_options, parsed_new_key[3])

        present = False
        matched = False
        non_matching_keys = []

        if parsed_new_key[0] in existing_keys:
            present = True
            # Then we check if everything matches, including
            # the key type and options. If not, we append this
            # existing key to the non-matching list
            # We only want it to match everything when the state
            # is present
            if parsed_new_key != existing_keys[parsed_new_key[0]] and state == "present":
                non_matching_keys.append(existing_keys[parsed_new_key[0]])
            else:
                matched = True


        # handle idempotent state=present
        if state=="present":
            keys_to_exist.append(parsed_new_key[0])
            if len(non_matching_keys) > 0:
                for non_matching_key in non_matching_keys:
                    if non_matching_key[0] in existing_keys:
                        del existing_keys[non_matching_key[0]]
                        do_write = True

            if not matched:
                existing_keys[parsed_new_key[0]] = parsed_new_key
                do_write = True

        elif state=="absent":
            if not matched:
                continue
            del existing_keys[parsed_new_key[0]]
            do_write = True

    # remove all other keys to honor exclusive
    if state == "present" and exclusive:
        to_remove = frozenset(existing_keys).difference(keys_to_exist)
        for key in to_remove:
            del existing_keys[key]
            do_write = True

    if do_write:
        if module.check_mode:
            module.exit_json(changed=True)
        writekeys(module, keyfile(module, user, do_write, path, manage_dir), existing_keys)
        params['changed'] = True
    else:
        if module.check_mode:
            module.exit_json(changed=False)

    return params

def main():

    module = AnsibleModule(
        argument_spec = dict(
           user        = dict(required=True, type='str'),
           key         = dict(required=True, type='str'),
           path        = dict(required=False, type='str'),
           manage_dir  = dict(required=False, type='bool', default=True),
           state       = dict(default='present', choices=['absent','present']),
           key_options = dict(required=False, type='str'),
           unique      = dict(default=False, type='bool'),
           exclusive   = dict(default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    results = enforce_state(module, module.params)
    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
