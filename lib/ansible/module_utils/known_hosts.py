# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import re

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

def add_git_host_key(module, url, accept_hostkey=True, create_dir=True):

    """ idempotently add a git url hostkey """

    if is_ssh_url(url):

        fqdn = get_fqdn(url)
        ssh_port = get_ssh_port(url)

        if fqdn:
            known_host = check_hostkey(module, fqdn, ssh_port)

            if not known_host:

                if accept_hostkey:
                    rc, out, err = add_host_key(module, fqdn, ssh_port, create_dir=create_dir)
                    if rc != 0:
                        module.fail_json(msg="failed to add %s hostkey: %s" % (fqdn, out + err))
                else:
                    module.fail_json(msg="%s has an unknown hostkey. Set accept_hostkey to True or manually add the hostkey prior to running the git module" % fqdn)

def is_ssh_url(url):

    """ check if url is ssh """

    if "@" in url and "://" not in url:
        return True
    for scheme in "ssh://", "git+ssh://", "ssh+git://":
        if url.startswith(scheme):
            return True
    return False

def get_fqdn(repo_url):

    """ chop the hostname out of a url """

    result = None
    if "@" in repo_url and "://" not in repo_url:
        # most likely an user@host:path or user@host/path type URL
        repo_url = repo_url.split("@", 1)[1]
        if repo_url.startswith('['):
            result = repo_url.split(']', 1)[0] + ']'
        elif ":" in repo_url:
            result = repo_url.split(":")[0]
        elif "/" in repo_url:
            result = repo_url.split("/")[0]
    elif "://" in repo_url:
        # this should be something we can parse with urlparse
        parts = urlparse.urlparse(repo_url)
        # parts[1] will be empty on python2.4 on ssh:// or git:// urls, so
        # ensure we actually have a parts[1] before continuing.
        if parts[1] != '':
            result = parts[1]
            if "@" in result:
                result = result.split("@", 1)[1]

            if result[0].startswith('['):
                result = result.split(']', 1)[0] + ']'
            elif ":" in result:
                result = result.split(":")[0]
    return result

def get_ssh_port(url):

    """ get possible custom ssh port in urls like ssh://[user@]domain.com:[port]/<project_name> """

    port = 22
    if url.startswith('ssh://'):
        result = url.split(":")[2]
        custom_port = re.match("(^\d+)\/", result)
        if custom_port:
            port = custom_port.group(1)

    return port

def check_hostkey(module, fqdn, ssh_port):

    """ check if we have ssh host key """

    if 'USER' in os.environ:
        user_host_file = os.path.expandvars("~${USER}/.ssh/known_hosts")
    else:
        user_host_file = "~/.ssh/known_hosts"
    user_host_file = os.path.expanduser(user_host_file)

    host_file_list = []
    host_file_list.append(user_host_file)
    host_file_list.append("/etc/ssh/ssh_known_hosts")
    host_file_list.append("/etc/ssh/ssh_known_hosts2")
    host_file_list.append("/etc/openssh/ssh_known_hosts")

    for hf in host_file_list:
        if not os.path.exists(hf):
            continue
        #Find the ssh-keygen binary
        sshkeygen = module.get_bin_path("ssh-keygen", True)

        #openssh >=6.4 has changed ssh-keygen behaviour such that it returns
        #1 if no host is found, whereas previously it returned 0
        # Host key present if returned code = 0, present output on stdout and absent output on stderr
        rc, stdout, stderr = module.run_command([sshkeygen, '-F', fqdn, '-f', hf], check_rc = False)

        if stdout != '' and stderr == '' and rc == 0:
            return True # host key present
        if rc != 0 and rc != 1: #something went wrong
            module.fail_json(msg = "ssh-keygen failed (rc = %d, stdout = '%s', stderr = '%s')" % (rc, stdout, stderr))

    return False

def add_host_key(module, fqdn, ssh_port, create_dir=False):

    """ use ssh-keyscan to add the hostkey """

    keyscan_cmd = module.get_bin_path('ssh-keyscan', True)

    if 'USER' in os.environ:
        user_ssh_dir = os.path.expandvars("~${USER}/.ssh/")
        user_host_file = os.path.expandvars("~${USER}/.ssh/known_hosts")
    else:
        user_ssh_dir = "~/.ssh/"
        user_host_file = "~/.ssh/known_hosts"
    user_ssh_dir = os.path.expanduser(user_ssh_dir)

    if not os.path.exists(user_ssh_dir):
        if create_dir:
            try:
                os.makedirs(user_ssh_dir, int('700', 8))
            except:
                module.fail_json(msg="failed to create host key directory: %s" % user_ssh_dir)
        else:
            module.fail_json(msg="%s does not exist" % user_ssh_dir)
    elif not os.path.isdir(user_ssh_dir):
        module.fail_json(msg="%s is not a directory" % user_ssh_dir)

    # I don't use -H for hash because with this option I've got strange results
    this_cmd = "%s -p %s -t rsa,ecdsa %s" % (keyscan_cmd, ssh_port, fqdn)
    rc, out, err = module.run_command(this_cmd)
    # ssh-keyscan gives a 0 exit code and prints nothins on timeout
    if rc != 0 or not out:
        module.fail_json(msg='failed to get the hostkey for %s' % fqdn)
    module.append_to_file(user_host_file, out)

    return rc, out, err
