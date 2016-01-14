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
import hmac

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    from hashlib import sha1
except ImportError:
    import sha as sha1

HASHED_KEY_MAGIC = "|1|"

def add_git_host_key(module, url, accept_hostkey=True, create_dir=True):

    """ idempotently add a git url hostkey """

    if is_ssh_url(url):

        fqdn = get_fqdn(url)

        if fqdn:
            known_host = check_hostkey(module, fqdn)
            if not known_host:
                if accept_hostkey:
                    rc, out, err = add_host_key(module, fqdn, create_dir=create_dir)
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

def check_hostkey(module, fqdn):
   return not not_in_host_file(module, fqdn)

# this is a variant of code found in connection_plugins/paramiko.py and we should modify
# the paramiko code to import and use this.

def not_in_host_file(self, host):


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

    hfiles_not_found = 0
    for hf in host_file_list:
        if not os.path.exists(hf):
            hfiles_not_found += 1
            continue

        try:
            host_fh = open(hf)
        except IOError:
            hfiles_not_found += 1
            continue
        else:
            data = host_fh.read()
            host_fh.close()

        for line in data.split("\n"):
            if line is None or " " not in line:
                continue
            tokens = line.split()
            if tokens[0].find(HASHED_KEY_MAGIC) == 0:
                # this is a hashed known host entry
                try:
                    (kn_salt,kn_host) = tokens[0][len(HASHED_KEY_MAGIC):].split("|",2)
                    hash = hmac.new(kn_salt.decode('base64'), digestmod=sha1)
                    hash.update(host)
                    if hash.digest() == kn_host.decode('base64'):
                        return False
                except:
                    # invalid hashed host key, skip it
                    continue
            else:
                # standard host file entry
                if host in tokens[0]:
                    return False

    return True


def add_host_key(module, fqdn, key_type="rsa", create_dir=False):

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

    this_cmd = "%s -t %s %s" % (keyscan_cmd, key_type, fqdn)

    rc, out, err = module.run_command(this_cmd)
    module.append_to_file(user_host_file, out)

    return rc, out, err

