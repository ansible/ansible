#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Jonathan Mainguy <jon@soh.re>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: uncompress
version_added: 2.4
short_description: Uncompresses an file after (optionally) copying it from the local machine.
extends_documentation_fragment: files
description:
     - Uncompresses an file. By default, it will copy the source file from the local system to the target before unpacking.
     - set copy=no to uncompress an file which already exists on the target.
options:
  src:
    description:
      - If copy=yes (default), local path to compressed file to copy to the target server; can be absolute or relative.
      - If copy=no, path on the target server to existing compressed file to unpack.
      - If copy=no and src contains ://, the remote machine will download the file from the url first.
    required: true
    default: null
  dest:
    description:
      - Remote absolute path where the file should be uncompressed.
    required: true
    default: null
  copy:
    description:
      - "If true, the file is copied from local 'master' to the target machine, otherwise, the plugin will look for src file at the target machine."
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
  deep_check:
    description:
      - "If true, and dest already exists, the file performs a longer and more extensive test than just filesize before deciding to overwrite or not"
    required: false
    choices: [ "yes", "no" ]
    default: "no"
author: "Jonathan Mainguy (@Jmainguy)"
notes:
    - requires C(file)/C(xz) commands on target host
    - requires gzip and bzip python modules
    - can handle I(gzip), I(bzip2) and I(xz) compressed files
    - detects type of compressed file automatically
'''


EXAMPLES = '''
- name: Uncompress foo.gz to /tmp/foo
  uncompress: src=foo.gz dest=/tmp/foo

- name: Uncompress a file that is already on the remote machine
  uncompress: src=/tmp/foo.xz dest=/usr/local/bin/foo copy=no

- name: Uncompress a file that needs to be downloaded
  uncompress: src=https://example.com/example.bz2 dest=/usr/local/bin/example copy=no
'''


RETURN = '''
changed:
    description: Whether anything was changed
    returned: always
    type: boolean
    sample: True
'''

import os
import shutil
import gzip
import bz2
import filecmp
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.pycompat24 import get_exception


# When downloading an archive, how much of the archive to download before
# saving to a tempfile (64k)
BUFSIZE = 65536


def ungzip(src, dest):
    """
    Uncompress gzip files.
    """
    try:
        f_out = open(dest, 'wb')
        f_in = gzip.open(src, 'rb')
        try:
            shutil.copyfileobj(f_in, f_out)
        finally:
            f_out.close()
            f_in.close()
        msg = ""
    except Exception:
        e = get_exception()
        f_out.close()
        f_in.close()
        msg = "%s" % e

    return msg


def unbzip(src, dest):
    """
    Uncompress bzip files.
    """
    try:
        f_out = open(dest, 'wb')
        f_in = bz2.BZ2File(src, 'rb')
        try:
            shutil.copyfileobj(f_in, f_out)
        finally:
            f_out.close()
            f_in.close()
        msg = ""
    except Exception:
        e = get_exception()
        f_out.close()
        f_in.close()
        msg = "%s" % e

    return msg


def unxzip(module, src, dest):
    """
    Uncompress xz files. Since we must support python 2.4 (EL 5) we cannot import lzma and use native python.
    We guess the filename of the output. .xz and .lzma get stripped, .txz and .lzma get replaced with .tar
    """
    cmd_path = module.get_bin_path('xz')
    cmd = '%s -k -d %s' % (cmd_path, src)
    # Guess filename of output
    prefix, suffix = os.path.splitext(src)
    if (suffix == '.xz') or (suffix == '.lzma'):
        ufile = prefix
    elif (suffix == '.txz') or (suffix == '.tlz'):
        ufile = prefix + '.tar'
    else:
        module.fail_json(msg="xz does not understand suffix %s" % suffix)
    try:
        module.run_command(cmd)
        if not os.path.isfile(ufile):
            module.fail_json(msg="%s should have uncompressed to %s, but alas it did not" % (src, ufile))
        shutil.move(ufile, dest)
        msg = ""
    except Exception:
        e = get_exception()
        msg = "%s" % e

    return msg


def filetype(module, src):
    """
    Get the filetype from the unix command file, and then pick the correct compression method to use for it
    """
    cmd_path = module.get_bin_path('file')
    cmd = "%s -b -i %s" % (cmd_path, src)
    ftype = module.run_command(cmd)

    return ftype


def copyfile(src, dest, deep_check):
    """
    Copy file from tempsrc to final destination. Unless its already at dest, and the same as tempsrc.
    """
    changed = False
    if os.path.isfile(dest):
        # This takes a long time
        if deep_check:
            nodiff = filecmp.cmp(src, dest, shallow=True)
        # This is much quicker
        else:
            destsize = os.path.getsize(dest)
            srcsize = os.path.getsize(src)
            if destsize != srcsize:
                nodiff = False
            else:
                nodiff = True
        # If there is a difference, then we change the destination
        if nodiff is False:
            shutil.move(src, dest)
            changed = True
    # If the destination file does not exist, then place it.
    else:
        shutil.move(src, dest)
        changed = True

    return changed


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(required=True),
            dest=dict(required=True),
            copy=dict(default=True, type='bool'),
            original_basename=dict(required=False),  # used to handle 'dest is a directory' via template, a slight hack
            deep_check=dict(default=False, type='bool'),  # This check takes a long time if dest already exists.
        ),
        add_file_common_args=True,
    )

    src = os.path.expanduser(module.params['src'])
    dest = os.path.expanduser(module.params['dest'])
    copy = module.params['copy']
    deep_check = module.params['deep_check']
    file_args = module.load_file_common_arguments(module.params)
    tempdir = os.path.dirname(__file__)
    fdir, ffile = os.path.split(dest)

    # did tar file arrive?
    if not os.path.exists(src):
        if copy:
            module.fail_json(msg="Source '%s' failed to transfer" % src)
        # If copy=false, and src= contains ://, try and download the file to a temp directory.
        elif '://' in src:
            package = os.path.join(tempdir, str(src.rsplit('/', 1)[1]))
            try:
                rsp, info = fetch_url(module, src)
                f = open(package, 'w')
                # Read 1kb at a time to save on ram
                while True:
                    data = rsp.read(BUFSIZE)

                    if data == "":
                        break  # End of file, break while loop

                    f.write(data)
                f.close()
                src = package
            except Exception:
                e = get_exception()
                f.close()
                module.fail_json(msg="Failure downloading %s, %s" % (src, e))
        else:
            module.fail_json(msg="Source '%s' does not exist" % src)

    # skip working with 0 size archives
    try:
        if os.path.getsize(src) == 0:
            module.fail_json(msg="Invalid archive '%s', the file is 0 bytes" % src)
    except Exception:
        module.fail_json(msg="Source '%s' not readable" % src)

    # is dest OK to receive tar file?
    if not os.path.isdir(fdir):
        module.fail_json(msg="Destination '%s' is not a directory" % dest)

    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src)

    if os.path.isdir(dest):
        module.fail_json(msg="Destination '%s' is an existing directory, must be a file, consider using unarchive module for archives" % dest)

    # Full path to the uncompressed file in the temp directory.
    tempsrc = os.path.join(tempdir, ffile)

    # Check what kind of compressed file the src is.
    ftype = filetype(module, src)[1]
    if "gzip" in ftype:
        msg = ungzip(src, tempsrc)
    elif "x-bzip2" in ftype:
        msg = unbzip(src, tempsrc)
    elif "x-xz" in ftype:
        msg = unxzip(module, src, tempsrc)
    else:
        module.fail_json(msg="Filetype not supported by uncompress module. %s" % ftype)
    if msg != "":
        module.fail_json(msg=msg)
    # If file already exists at dest, compare uncompressed file and dest, and replace if different.
    changed = copyfile(tempsrc, dest, deep_check)

    # do we need to change perms?
    file_args['path'] = dest
    try:
        changed = module.set_fs_attributes_if_different(file_args, changed)
    except (IOError, OSError):
        e = get_exception()
        module.fail_json(msg="Unexpected error when accessing exploded file: %s" % str(e))

    module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
