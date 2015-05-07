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
   - The M(known_hosts) module lets you add or remove a host from the C(known_hosts) file. 
     This is useful if you're going to want to use the M(git) module over ssh, for example. 
     If you have a very large number of host keys to manage, you will find the M(template) module more useful.
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
      - The SSH public host key, as a string (required if state=present, optional when state=absent, in which case all keys for the host are removed)
    required: false
    default: null
  path:
    description:
      - The known_hosts file to edit
    required: no
    default: "(homedir)+/.ssh/known_hosts"
  state:
    description:
      - I(present) to add the host, I(absent) to remove it.
    choices: [ "present", "absent" ]
    required: no
    default: present
requirements: [ ]
author: Matthew Vernon
'''

EXAMPLES = '''
# Example using with_file to set the system known_hosts file
- name: tell the host about our servers it might want to ssh to
  known_hosts: path='/etc/ssh/ssh_known_hosts'
               host='foo.com.invalid'
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
#    state = absent|present (default: present)

import os
import os.path
import tempfile
import errno

def enforce_state(module, params):
    """
    Add or remove key.
    """

    host = params["name"]
    key = params.get("key",None)
    port = params.get("port",None)
    #expand the path parameter; otherwise module.add_path_info
    #(called by exit_json) unhelpfully says the unexpanded path is absent.
    path = os.path.expanduser(params.get("path"))
    state = params.get("state")
    #Find the ssh-keygen binary
    sshkeygen = module.get_bin_path("ssh-keygen",True)

    #trailing newline in files gets lost, so re-add if necessary
    if key is not None and key[-1]!='\n':
        key+='\n'

    if key is None and state != "absent":
        module.fail_json(msg="No key specified when adding a host")

    sanity_check(module,host,key,sshkeygen)

    current,replace=search_for_host_key(module,host,key,path,sshkeygen)

    #We will change state if current==True & state!="present"
    #or current==False & state=="present"
    #i.e (current) XOR (state=="present")
    #Alternatively, if replace is true (i.e. key present, and we must change it)
    if module.check_mode:
        module.exit_json(changed = replace or ((state=="present") != current))

    #Now do the work.

    #First, remove an extant entry if required
    if replace==True or (current==True and state=="absent"):
        module.run_command([sshkeygen,'-R',host,'-f',path],
                           check_rc=True)
        params['changed'] = True
    #Next, add a new (or replacing) entry
    if replace==True or (current==False and state=="present"):
        try:
            inf=open(path,"r")
        except IOError, e:
            if e.errno == errno.ENOENT:
                inf=None
            else:
                module.fail_json(msg="Failed to read %s: %s" % \
                                     (path,str(e)))
        try:
            outf=tempfile.NamedTemporaryFile(dir=os.path.dirname(path))
            if inf is not None:
                for line in inf:
                    outf.write(line)
                inf.close()
            outf.write(key)
            outf.flush()
            module.atomic_move(outf.name,path)
        except (IOError,OSError),e:
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
    except IOError,e:
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

def search_for_host_key(module,host,key,path,sshkeygen):
    '''search_for_host_key(module,host,key,path,sshkeygen) -> (current,replace)

    Looks up host in the known_hosts file path; if it's there, looks to see
    if one of those entries matches key. Returns:
    current (Boolean): is host found in path?
    replace (Boolean): is the key in path different to that supplied by user?
    if current=False, then replace is always False.
    sshkeygen is the path to ssh-keygen, found earlier with get_bin_path
    '''
    replace=False
    if os.path.exists(path)==False:
        return False, False
    #openssh >=6.4 has changed ssh-keygen behaviour such that it returns
    #1 if no host is found, whereas previously it returned 0
    rc,stdout,stderr=module.run_command([sshkeygen,'-F',host,'-f',path],
                                 check_rc=False)
    if stdout=='' and stderr=='' and (rc==0 or rc==1):
        return False, False #host not found, no other errors
    if rc!=0: #something went wrong
        module.fail_json(msg="ssh-keygen failed (rc=%d,stdout='%s',stderr='%s')" % (rc,stdout,stderr))

#If user supplied no key, we don't want to try and replace anything with it
    if key is None:
        return True, False

    lines=stdout.split('\n')
    k=key.strip() #trim trailing newline
    #ssh-keygen returns only the host we ask about in the host field,
    #even if the key entry has multiple hosts. Emulate this behaviour here,
    #otherwise we get false negatives.
    #Only necessary for unhashed entries.
    if k[0] !='|':
        k=k.split()
        #The optional "marker" field, used for @cert-authority or @revoked
        if k[0][0] == '@':
            k[1]=host
        else:
            k[0]=host
        k=' '.join(k)
    for l in lines:
        if l=='': 
            continue
        if l[0]=='#': #comment
            continue
        if k==l: #found a match
            return True, False #current, not-replace
    #No match found, return current and replace
    return True, True

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name      = dict(required=True,  type='str', aliases=['host']),
            key       = dict(required=False,  type='str'),
            path      = dict(default="~/.ssh/known_hosts", type='str'),
            state     = dict(default='present', choices=['absent','present']),
            ),
        supports_check_mode = True
        )

    results = enforce_state(module,module.params)
    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
main()
