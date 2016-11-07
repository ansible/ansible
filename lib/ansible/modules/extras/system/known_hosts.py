#!/usr/bin/python

"""
Ansible module to manage the ssh known_hosts file.
Copyright(c) 2014, Matthew Vernon <mcv21@cam.ac.uk>

This module is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This module is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this module.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''
---
module: known_hosts
short_description: Add or remove a host from the C(known_hosts) file
description:
   - The M(known_hosts) module lets you add or remove a host keys from the C(known_hosts) file.
   - Starting at Ansible 2.2, multiple entries per host are allowed, but only one for each key type supported by ssh.
     This is useful if you're going to want to use the M(git) module over ssh, for example.
   - If you have a very large number of host keys to manage, you will find the M(template) module more useful.
version_added: "1.9"
options:
  name:
    aliases: [ 'host' ]
    description:
      - The host to add or remove (must match a host specified in key)
    required: true
    default: null
  key:
    description:
      - The SSH public host key, as a string (required if state=present, optional when state=absent, in which case all keys for the host are removed). The key must be in the right format for ssh (see sshd(1), section "SSH_KNOWN_HOSTS FILE FORMAT")
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
# Example using with_file to set the system known_hosts file
- name: tell the host about our servers it might want to ssh to
  known_hosts: path='/etc/ssh/ssh_known_hosts'
               name='foo.com.invalid'
               key="{{ lookup('file', 'pubkeys/foo.com.invalid') }}"
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
from ansible.module_utils.basic import *

def enforce_state(module, params):
    """
    Add or remove key.
    """

    host = params["name"]
    key = params.get("key",None)
    port = params.get("port",None)
    path = params.get("path")
    hash_host = params.get("hash_host")
    state = params.get("state")
    #Find the ssh-keygen binary
    sshkeygen = module.get_bin_path("ssh-keygen",True)

    # Trailing newline in files gets lost, so re-add if necessary
    if key and key[-1] != '\n':
        key+='\n'

    if key is None and state != "absent":
        module.fail_json(msg="No key specified when adding a host")

    sanity_check(module,host,key,sshkeygen)

    found,replace_or_add,found_line,key=search_for_host_key(module,host,key,hash_host,path,sshkeygen)

    #We will change state if found==True & state!="present"
    #or found==False & state=="present"
    #i.e found XOR (state=="present")
    #Alternatively, if replace is true (i.e. key present, and we must change it)
    if module.check_mode:
        module.exit_json(changed = replace_or_add or (state=="present") != found)

    #Now do the work.

    #Only remove whole host if found and no key provided
    if found and key is None and state=="absent":
        module.run_command([sshkeygen,'-R',host,'-f',path], check_rc=True)
        params['changed'] = True

    #Next, add a new (or replacing) entry
    if replace_or_add or found != (state=="present"):
        try:
            inf=open(path,"r")
        except IOError:
            e = get_exception()
            if e.errno == errno.ENOENT:
                inf=None
            else:
                module.fail_json(msg="Failed to read %s: %s" % \
                                     (path,str(e)))
        try:
            outf=tempfile.NamedTemporaryFile(dir=os.path.dirname(path))
            if inf is not None:
                for line_number, line in enumerate(inf, start=1):
                    if found_line==line_number and (replace_or_add or state=='absent'):
                        continue # skip this line to replace its key
                    outf.write(line)
                inf.close()
            if state == 'present':
                outf.write(key)
            outf.flush()
            module.atomic_move(outf.name,path)
        except (IOError,OSError):
            e = get_exception()
            module.fail_json(msg="Failed to write to file %s: %s" % \
                                 (path,str(e)))

        try:
            outf.close()
        except:
            pass

        params['changed'] = True

    return params

def sanity_check(module,host,key,sshkeygen):
    '''Check supplied key is sensible

    host and key are parameters provided by the user; If the host
    provided is inconsistent with the key supplied, then this function
    quits, providing an error to the user.
    sshkeygen is the path to ssh-keygen, found earlier with get_bin_path
    '''
    #If no key supplied, we're doing a removal, and have nothing to check here.
    if key is None:
        return
    #Rather than parsing the key ourselves, get ssh-keygen to do it
    #(this is essential for hashed keys, but otherwise useful, as the
    #key question is whether ssh-keygen thinks the key matches the host).

    #The approach is to write the key to a temporary file,
    #and then attempt to look up the specified host in that file.
    try:
        outf=tempfile.NamedTemporaryFile()
        outf.write(key)
        outf.flush()
    except IOError:
        e = get_exception()
        module.fail_json(msg="Failed to write to temporary file %s: %s" % \
                             (outf.name,str(e)))
    rc,stdout,stderr=module.run_command([sshkeygen,'-F',host,
                                         '-f',outf.name],
                                        check_rc=True)
    try:
        outf.close()
    except:
        pass

    if stdout=='': #host not found
        module.fail_json(msg="Host parameter does not match hashed host field in supplied key")

def search_for_host_key(module,host,key,hash_host,path,sshkeygen):
    '''search_for_host_key(module,host,key,path,sshkeygen) -> (found,replace_or_add,found_line)

    Looks up host and keytype in the known_hosts file path; if it's there, looks to see
    if one of those entries matches key. Returns:
    found (Boolean): is host found in path?
    replace_or_add (Boolean): is the key in path different to that supplied by user?
    found_line (int or None): the line where a key of the same type was found
    if found=False, then replace is always False.
    sshkeygen is the path to ssh-keygen, found earlier with get_bin_path
    '''
    if os.path.exists(path)==False:
        return False, False, None, key

    sshkeygen_command=[sshkeygen,'-F',host,'-f',path]

    #openssh >=6.4 has changed ssh-keygen behaviour such that it returns
    #1 if no host is found, whereas previously it returned 0
    rc,stdout,stderr=module.run_command(sshkeygen_command,
                                 check_rc=False)
    if stdout=='' and stderr=='' and (rc==0 or rc==1):
        return False, False, None, key #host not found, no other errors
    if rc!=0: #something went wrong
        module.fail_json(msg="ssh-keygen failed (rc=%d,stdout='%s',stderr='%s')" % (rc,stdout,stderr))

    #If user supplied no key, we don't want to try and replace anything with it
    if key is None:
        return True, False, None, key

    lines=stdout.split('\n')
    new_key = normalize_known_hosts_key(key)

    sshkeygen_command.insert(1,'-H')
    rc,stdout,stderr=module.run_command(sshkeygen_command,check_rc=False)
    if rc!=0: #something went wrong
        module.fail_json(msg="ssh-keygen failed to hash host (rc=%d,stdout='%s',stderr='%s')" % (rc,stdout,stderr))
    hashed_lines=stdout.split('\n')

    for lnum,l in enumerate(lines):
        if l=='':
            continue
        elif l[0]=='#': # info output from ssh-keygen; contains the line number where key was found
            try:
                # This output format has been hardcoded in ssh-keygen since at least OpenSSH 4.0
                # It always outputs the non-localized comment before the found key
                found_line = int(re.search(r'found: line (\d+)', l).group(1))
            except IndexError:
                e = get_exception()
                module.fail_json(msg="failed to parse output of ssh-keygen for line number: '%s'" % l)
        else:
            found_key = normalize_known_hosts_key(l)
            if hash_host==True:
                if found_key['host'][:3]=='|1|':
                    new_key['host']=found_key['host']
                else:
                    hashed_host=normalize_known_hosts_key(hashed_lines[lnum])
                    found_key['host']=hashed_host['host']
                key=key.replace(host,found_key['host'])
            if new_key==found_key: #found a match
                return True, False, found_line, key #found exactly the same key, don't replace
            elif new_key['type'] == found_key['type']: # found a different key for the same key type
                return True, True, found_line, key
    #No match found, return found and replace, but no line
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
    k=key.strip() #trim trailing newline
    k=key.split()
    d = dict()
    #The optional "marker" field, used for @cert-authority or @revoked
    if k[0][0] == '@':
        d['options'] = k[0]
        d['host']=k[1]
        d['type']=k[2]
        d['key']=k[3]
    else:
        d['host']=k[0]
        d['type']=k[1]
        d['key']=k[2]
    return d

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name      = dict(required=True,  type='str', aliases=['host']),
            key       = dict(required=False,  type='str'),
            path      = dict(default="~/.ssh/known_hosts", type='path'),
            hash_host = dict(required=False, type='bool' ,default=False),
            state     = dict(default='present', choices=['absent','present']),
            ),
        supports_check_mode = True
        )

    results = enforce_state(module,module.params)
    module.exit_json(**results)

main()
