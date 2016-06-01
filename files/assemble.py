#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Stephen Fromm <sfromm@gmail.com>
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

import os
import os.path
import tempfile
import re

DOCUMENTATION = '''
---
module: assemble
short_description: Assembles a configuration file from fragments
description:
     - Assembles a configuration file from fragments. Often a particular
       program will take a single configuration file and does not support a
       C(conf.d) style structure where it is easy to build up the configuration
       from multiple sources. M(assemble) will take a directory of files that can be
       local or have already been transferred to the system, and concatenate them
       together to produce a destination file. Files are assembled in string sorting order.
       Puppet calls this idea I(fragments).
version_added: "0.5"
options:
  src:
    description:
      - An already existing directory full of source files.
    required: true
    default: null
    aliases: []
  dest:
    description:
      - A file to create using the concatenation of all of the source files.
    required: true
    default: null
  backup:
    description:
      - Create a backup file (if C(yes)), including the timestamp information so
        you can get the original file back if you somehow clobbered it
        incorrectly.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  delimiter:
    description:
      - A delimiter to separate the file contents.
    version_added: "1.4"
    required: false
    default: null
  remote_src:
    description:
      - If False, it will search for src at originating/master machine, if True it will
        go to the remote/target machine for the src. Default is True.
    choices: [ "True", "False" ]
    required: false
    default: "True"
    version_added: "1.4"
  regexp:
    description:
      - Assemble files only if C(regex) matches the filename. If not set,
        all files are assembled. All "\\" (backslash) must be escaped as
        "\\\\" to comply yaml syntax. Uses Python regular expressions; see
        U(http://docs.python.org/2/library/re.html).
    required: false
    default: null
  ignore_hidden:
    description:
      - A boolean that controls if files that start with a '.' will be included or not.
    required: false
    default: false
    version_added: "2.0"
  validate:
    description:
      - The validation command to run before copying into place.  The path to the file to
        validate is passed in via '%s' which must be present as in the sshd example below.
        The command is passed securely so shell features like expansion and pipes won't work.
    required: false
    default: null
    version_added: "2.0"
author: "Stephen Fromm (@sfromm)"
extends_documentation_fragment:
    - files
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- assemble: src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf

# When a delimiter is specified, it will be inserted in between each fragment
- assemble: src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf delimiter='### START FRAGMENT ###'

# Copy a new "sshd_config" file into place, after passing validation with sshd
- assemble: src=/etc/ssh/conf.d/ dest=/etc/ssh/sshd_config validate='/usr/sbin/sshd -t -f %s'
'''

# ===========================================
# Support method

def assemble_from_fragments(src_path, delimiter=None, compiled_regexp=None, ignore_hidden=False):
    ''' assemble a file from a directory of fragments '''
    tmpfd, temp_path = tempfile.mkstemp()
    tmp = os.fdopen(tmpfd,'w')
    delimit_me = False
    add_newline = False

    for f in sorted(os.listdir(src_path)):
        if compiled_regexp and not compiled_regexp.search(f):
            continue
        fragment = "%s/%s" % (src_path, f)
        if not os.path.isfile(fragment) or (ignore_hidden and os.path.basename(fragment).startswith('.')):
            continue
        fragment_content = file(fragment).read()

        # always put a newline between fragments if the previous fragment didn't end with a newline.
        if add_newline:
            tmp.write('\n')

        # delimiters should only appear between fragments
        if delimit_me:
            if delimiter:
                # un-escape anything like newlines
                delimiter = delimiter.decode('unicode-escape')
                tmp.write(delimiter)
                # always make sure there's a newline after the
                # delimiter, so lines don't run together
                if delimiter[-1] != '\n':
                    tmp.write('\n')

        tmp.write(fragment_content)
        delimit_me = True
        if fragment_content.endswith('\n'):
            add_newline = False
        else:
            add_newline = True

    tmp.close()
    return temp_path

def cleanup(path, result=None):
    # cleanup just in case
    if os.path.exists(path):
        try:
            os.remove(path)
        except (IOError, OSError):
            e = get_exception()
            # don't error on possible race conditions, but keep warning
            if result is not None:
                result['warnings'] = ['Unable to remove temp file (%s): %s' % (path, str(e))]

# ==============================================================
# main

def main():

    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            src = dict(required=True),
            delimiter = dict(required=False),
            dest = dict(required=True),
            backup=dict(default=False, type='bool'),
            remote_src=dict(default=False, type='bool'),
            regexp = dict(required=False),
            ignore_hidden = dict(default=False, type='bool'),
            validate = dict(required=False, type='str'),
        ),
        add_file_common_args=True
    )

    changed   = False
    path_hash   = None
    dest_hash   = None
    src       = os.path.expanduser(module.params['src'])
    dest      = os.path.expanduser(module.params['dest'])
    backup    = module.params['backup']
    delimiter = module.params['delimiter']
    regexp    = module.params['regexp']
    compiled_regexp = None
    ignore_hidden = module.params['ignore_hidden']
    validate = module.params.get('validate', None)

    result = dict(src=src, dest=dest)
    if not os.path.exists(src):
        module.fail_json(msg="Source (%s) does not exist" % src)

    if not os.path.isdir(src):
        module.fail_json(msg="Source (%s) is not a directory" % src)

    if regexp != None:
        try:
            compiled_regexp = re.compile(regexp)
        except re.error:
            e = get_exception()
            module.fail_json(msg="Invalid Regexp (%s) in \"%s\"" % (e, regexp))

    if validate and "%s" not in validate:
        module.fail_json(msg="validate must contain %%s: %s" % validate)

    path = assemble_from_fragments(src, delimiter, compiled_regexp, ignore_hidden)
    path_hash = module.sha1(path)
    result['checksum'] = path_hash

    # Backwards compat.  This won't return data if FIPS mode is active
    try:
        pathmd5 = module.md5(path)
    except ValueError:
        pathmd5 = None
    result['md5sum'] = pathmd5

    if os.path.exists(dest):
        dest_hash = module.sha1(dest)

    if path_hash != dest_hash:
        if validate:
            (rc, out, err) = module.run_command(validate % path)
            result['validation'] = dict(rc=rc, stdout=out, stderr=err)
            if rc != 0:
                cleanup(path)
                module.fail_json(msg="failed to validate: rc:%s error:%s" % (rc, err))
        if backup and dest_hash is not None:
            result['backup_file'] = module.backup_local(dest)

        module.atomic_move(path, dest)
        changed = True

    cleanup(path, result)

    # handle file permissions
    file_args = module.load_file_common_arguments(module.params)
    result['changed'] = module.set_fs_attributes_if_different(file_args, changed)

    # Mission complete
    result['msg'] = "OK"
    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

main()

