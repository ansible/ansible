#!/usr/bin/python

# Copyright(c) 2014, Matthew Vernon <mcv21@cam.ac.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: known_hosts
short_description: Add or remove a host from the C(known_hosts) file
description:
   - The C(known_hosts) module lets you add or remove a host keys from the C(known_hosts) file.
   - Starting at Ansible 2.2, multiple entries per host are allowed, but only one for each key type supported by ssh.
     This is useful if you're going to want to use the M(git) module over ssh, for example.
   - If you have a very large number of host keys to manage, you will find the M(template) module more useful.
version_added: "1.9"
options:
  name:
    aliases: [ 'host' ]
    description:
      - The host to add or remove (must match a host specified in key). It will be converted to lowercase so that ssh-keygen can find it.
    required: true
    default: null
  key:
    description:
      - The SSH public host key, as a string (required if state=present, optional when state=absent, in which case all keys for the host are removed).
        The key must be in the right format for ssh (see sshd(1), section "SSH_KNOWN_HOSTS FILE FORMAT")
    required: false
    default: null
  path:
    description:
      - The known_hosts file to edit
    required: no
    default: "(homedir)+/.ssh/known_hosts"
  hash_host:
    description:
      - Hash the hostname in the known_hosts file
    required: no
    default: no
    version_added: "2.3"
  state:
    description:
      - I(present) to add the host key, I(absent) to remove it.
    choices: [ "present", "absent" ]
    required: no
    default: present
requirements: [ ]
author: "Matthew Vernon (@mcv21)"
'''

EXAMPLES = '''
- name: tell the host about our servers it might want to ssh to
  known_hosts:
    path: /etc/ssh/ssh_known_hosts
    name: foo.com.invalid
    key: "{{ lookup('file', 'pubkeys/foo.com.invalid') }}"
'''

# Makes sure public host keys are present or absent in the given known_hosts
# file.
#
# Arguments
# =========
#    name = hostname whose key should be added (alias: host)
#    key = line(s) to add to known_hosts file
#    path = the known_hosts file to edit (default: ~/.ssh/known_hosts)
#    hash_host = yes|no (default: no) hash the hostname in the known_hosts file
#    state = absent|present (default: present)

import os
import os.path
import tempfile
import errno
import re

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.basic import AnsibleModule


def enforce_state(module, params):
    """
    Add or remove key.
    """

    host = params["name"].lower()
    key = params.get("key", None)
    port = params.get("port", None)
    path = params.get("path")
    hash_host = params.get("hash_host")
    state = params.get("state")
    # Find the ssh-keygen binary
    sshkeygen = module.get_bin_path("ssh-keygen", True)

    # Trailing newline in files gets lost, so re-add if necessary
    if key and key[-1] != '\n':
        key += '\n'

    if key is None and state != "absent":
        module.fail_json(msg="No key specified when adding a host")

    sanity_check(module, host, key, sshkeygen)

    found, replace_or_add, found_line, key = search_for_host_key(module, host, key, hash_host, path, sshkeygen)

    params['diff'] = compute_diff(path, found_line, replace_or_add, state, key)

    # We will change state if found==True & state!="present"
    # or found==False & state=="present"
    # i.e found XOR (state=="present")
    # Alternatively, if replace is true (i.e. key present, and we must change
    # it)
    if module.check_mode:
        module.exit_json(changed=replace_or_add or (state == "present") != found,
                         diff=params['diff'])

    # Now do the work.

    # Only remove whole host if found and no key provided
    if found and key is None and state == "absent":
        module.run_command([sshkeygen, '-R', host, '-f', path], check_rc=True)
        params['changed'] = True

    # Next, add a new (or replacing) entry
    if replace_or_add or found != (state == "present"):
        try:
            inf = open(path, "r")
        except IOError:
            e = get_exception()
            if e.errno == errno.ENOENT:
                inf = None
            else:
                module.fail_json(msg="Failed to read %s: %s" % (path, str(e)))
        try:
            outf = tempfile.NamedTemporaryFile(mode='w+', dir=os.path.dirname(path))
            if inf is not None:
                for line_number, line in enumerate(inf):
                    if found_line == (line_number + 1) and (replace_or_add or state == 'absent'):
                        continue  # skip this line to replace its key
                    outf.write(line)
                inf.close()
            if state == 'present':
                outf.write(key)
            outf.flush()
            module.atomic_move(outf.name, path)
        except (IOError, OSError):
            e = get_exception()
            module.fail_json(msg="Failed to write to file %s: %s" % (path, str(e)))

        try:
            outf.close()
        except:
            pass

        params['changed'] = True

    return params


def sanity_check(module, host, key, sshkeygen):
    '''Check supplied key is sensible

    host and key are parameters provided by the user; If the host
    provided is inconsistent with the key supplied, then this function
    quits, providing an error to the user.
    sshkeygen is the path to ssh-keygen, found earlier with get_bin_path
    '''
    # If no key supplied, we're doing a removal, and have nothing to check here.
    if key is None:
        return
    # Rather than parsing the key ourselves, get ssh-keygen to do it
    # (this is essential for hashed keys, but otherwise useful, as the
    # key question is whether ssh-keygen thinks the key matches the host).

    # The approach is to write the key to a temporary file,
    # and then attempt to look up the specified host in that file.
    try:
        outf = tempfile.NamedTemporaryFile(mode='w+')
        outf.write(key)
        outf.flush()
    except IOError:
        e = get_exception()
        module.fail_json(msg="Failed to write to temporary file %s: %s" %
                             (outf.name, str(e)))

    sshkeygen_command = [sshkeygen, '-F', host, '-f', outf.name]
    rc, stdout, stderr = module.run_command(sshkeygen_command, check_rc=True)
    try:
        outf.close()
    except:
        pass

    if stdout == '':  # host not found
        module.fail_json(msg="Host parameter does not match hashed host field in supplied key")


def search_for_host_key(module, host, key, hash_host, path, sshkeygen):
    '''search_for_host_key(module,host,key,path,sshkeygen) -> (found,replace_or_add,found_line)

    Looks up host and keytype in the known_hosts file path; if it's there, looks to see
    if one of those entries matches key. Returns:
    found (Boolean): is host found in path?
    replace_or_add (Boolean): is the key in path different to that supplied by user?
    found_line (int or None): the line where a key of the same type was found
    if found=False, then replace is always False.
    sshkeygen is the path to ssh-keygen, found earlier with get_bin_path
    '''
    if os.path.exists(path) is False:
        return False, False, None, key

    sshkeygen_command = [sshkeygen, '-F', host, '-f', path]

    # openssh >=6.4 has changed ssh-keygen behaviour such that it returns
    # 1 if no host is found, whereas previously it returned 0
    rc, stdout, stderr = module.run_command(sshkeygen_command, check_rc=False)
    if stdout == '' and stderr == '' and (rc == 0 or rc == 1):
        return False, False, None, key  # host not found, no other errors
    if rc != 0:  # something went wrong
        module.fail_json(msg="ssh-keygen failed (rc=%d, stdout='%s',stderr='%s')" % (rc, stdout, stderr))

    # If user supplied no key, we don't want to try and replace anything with it
    if key is None:
        return True, False, None, key

    lines = stdout.split('\n')
    new_key = normalize_known_hosts_key(key)

    sshkeygen_command.insert(1, '-H')
    rc, stdout, stderr = module.run_command(sshkeygen_command, check_rc=False)
    if rc not in (0, 1) or stderr != '':  # something went wrong
        module.fail_json(msg="ssh-keygen failed to hash host (rc=%d, stdout='%s',stderr='%s')" % (rc, stdout, stderr))
    hashed_lines = stdout.split('\n')

    for lnum, l in enumerate(lines):
        if l == '':
            continue
        elif l[0] == '#':  # info output from ssh-keygen; contains the line number where key was found
            try:
                # This output format has been hardcoded in ssh-keygen since at least OpenSSH 4.0
                # It always outputs the non-localized comment before the found key
                found_line = int(re.search(r'found: line (\d+)', l).group(1))
            except IndexError:
                module.fail_json(msg="failed to parse output of ssh-keygen for line number: '%s'" % l)
        else:
            found_key = normalize_known_hosts_key(l)
            if hash_host is True:
                if found_key['host'][:3] == '|1|':
                    new_key['host'] = found_key['host']
                else:
                    hashed_host = normalize_known_hosts_key(hashed_lines[lnum])
                    found_key['host'] = hashed_host['host']
                key = key.replace(host, found_key['host'])
            if new_key == found_key:  # found a match
                return True, False, found_line, key  # found exactly the same key, don't replace
            elif new_key['type'] == found_key['type']:  # found a different key for the same key type
                return True, True, found_line, key
    # No match found, return found and replace, but no line
    return True, True, None, key


def normalize_known_hosts_key(key):
    '''
    Transform a key, either taken from a known_host file or provided by the
    user, into a normalized form.
    The host part (which might include multiple hostnames or be hashed) gets
    replaced by the provided host. Also, any spurious information gets removed
    from the end (like the username@host tag usually present in hostkeys, but
    absent in known_hosts files)
    '''
    k = key.strip()  # trim trailing newline
    k = key.split()
    d = dict()
    # The optional "marker" field, used for @cert-authority or @revoked
    if k[0][0] == '@':
        d['options'] = k[0]
        d['host'] = k[1]
        d['type'] = k[2]
        d['key'] = k[3]
    else:
        d['host'] = k[0]
        d['type'] = k[1]
        d['key'] = k[2]
    return d


def compute_diff(path, found_line, replace_or_add, state, key):
    diff = {
        'before_header': path,
        'after_header': path,
        'before': '',
        'after': '',
    }
    try:
        inf = open(path, "r")
    except IOError:
        e = get_exception()
        if e.errno == errno.ENOENT:
            diff['before_header'] = '/dev/null'
    else:
        diff['before'] = inf.read()
        inf.close()
    lines = diff['before'].splitlines(1)
    if (replace_or_add or state == 'absent') and found_line is not None and 1 <= found_line <= len(lines):
        del lines[found_line - 1]
    if state == 'present' and (replace_or_add or found_line is None):
        lines.append(key)
    diff['after'] = ''.join(lines)
    return diff


def main():

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', aliases=['host']),
            key=dict(required=False, type='str'),
            path=dict(default="~/.ssh/known_hosts", type='path'),
            hash_host=dict(required=False, type='bool', default=False),
            state=dict(default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True
    )

    results = enforce_state(module, module.params)
    module.exit_json(**results)

if __name__ == '__main__':
    main()
