#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Nimbis Services, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: htpasswd
version_added: "1.3"
short_description: manage user files for basic authentication
description:
  - Add and remove username/password entries in a password file using htpasswd.
  - This is used by web servers such as Apache and Nginx for basic authentication.
options:
  path:
    required: true
    aliases: [ dest, destfile ]
    description:
      - Path to the file that contains the usernames and passwords
  name:
    required: true
    aliases: [ username ]
    description:
      - User name to add or remove
  password:
    required: false
    description:
      - Password associated with user.
      - Must be specified if user does not exist yet.
  crypt_scheme:
    required: false
    choices: ["apr_md5_crypt", "des_crypt", "ldap_sha1", "plaintext"]
    default: "apr_md5_crypt"
    description:
      - Encryption scheme to be used.  As well as the four choices listed
        here, you can also use any other hash supported by passlib, such as
        md5_crypt and sha256_crypt, which are linux passwd hashes.  If you
        do so the password file will not be compatible with Apache or Nginx
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the user entry should be present or not
  create:
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
    description:
      - Used with C(state=present). If specified, the file will be created
        if it does not already exist. If set to "no", will fail if the
        file does not exist
notes:
  - "This module depends on the I(passlib) Python library, which needs to be installed on all target systems."
  - "On Debian, Ubuntu, or Fedora: install I(python-passlib)."
  - "On RHEL or CentOS: Enable EPEL, then install I(python-passlib)."
requirements: [ passlib>=1.6 ]
author: "Ansible Core Team"
"""

EXAMPLES = """
# Add a user to a password file and ensure permissions are set
- htpasswd:
    path: /etc/nginx/passwdfile
    name: janedoe
    password: '9s36?;fyNp'
    owner: root
    group: www-data
    mode: 0640

# Remove a user from a password file
- htpasswd:
    path: /etc/apache2/passwdfile
    name: foobar
    state: absent

# Add a user to a password file suitable for use by libpam-pwdfile
- htpasswd:
    path: /etc/mail/passwords
    name: alex
    password: oedu2eGh
    crypt_scheme: md5_crypt
"""


import os
import tempfile
from distutils.version import LooseVersion

try:
    from passlib.apache import HtpasswdFile, htpasswd_context
    from passlib.context import CryptContext
    import passlib
except ImportError:
    passlib_installed = False
else:
    passlib_installed = True

apache_hashes = ["apr_md5_crypt", "des_crypt", "ldap_sha1", "plaintext"]


def create_missing_directories(dest):
    destpath = os.path.dirname(dest)
    if not os.path.exists(destpath):
        os.makedirs(destpath)


def present(dest, username, password, crypt_scheme, create, check_mode):
    """ Ensures user is present

    Returns (msg, changed) """
    if crypt_scheme in apache_hashes:
        context = htpasswd_context
    else:
        context = CryptContext(schemes=[crypt_scheme] + apache_hashes)
    if not os.path.exists(dest):
        if not create:
            raise ValueError('Destination %s does not exist' % dest)
        if check_mode:
            return ("Create %s" % dest, True)
        create_missing_directories(dest)
        if LooseVersion(passlib.__version__) >= LooseVersion('1.6'):
            ht = HtpasswdFile(dest, new=True, default_scheme=crypt_scheme, context=context)
        else:
            ht = HtpasswdFile(dest, autoload=False, default=crypt_scheme, context=context)
        if getattr(ht, 'set_password', None):
            ht.set_password(username, password)
        else:
            ht.update(username, password)
        ht.save()
        return ("Created %s and added %s" % (dest, username), True)
    else:
        if LooseVersion(passlib.__version__) >= LooseVersion('1.6'):
            ht = HtpasswdFile(dest, new=False, default_scheme=crypt_scheme, context=context)
        else:
            ht = HtpasswdFile(dest, default=crypt_scheme, context=context)

        found = None
        if getattr(ht, 'check_password', None):
            found = ht.check_password(username, password)
        else:
            found = ht.verify(username, password)

        if found:
            return ("%s already present" % username, False)
        else:
            if not check_mode:
                if getattr(ht, 'set_password', None):
                    ht.set_password(username, password)
                else:
                    ht.update(username, password)
                ht.save()
            return ("Add/update %s" % username, True)


def absent(dest, username, check_mode):
    """ Ensures user is absent

    Returns (msg, changed) """
    if LooseVersion(passlib.__version__) >= LooseVersion('1.6'):
        ht = HtpasswdFile(dest, new=False)
    else:
        ht = HtpasswdFile(dest)

    if username not in ht.users():
        return ("%s not present" % username, False)
    else:
        if not check_mode:
            ht.delete(username)
            ht.save()
        return ("Remove %s" % username, True)


def check_file_attrs(module, changed, message):

    file_args = module.load_file_common_arguments(module.params)
    if module.set_fs_attributes_if_different(file_args, False):

        if changed:
            message += " and "
        changed = True
        message += "ownership, perms or SE linux context changed"

    return message, changed


def main():
    arg_spec = dict(
        path=dict(required=True, aliases=["dest", "destfile"]),
        name=dict(required=True, aliases=["username"]),
        password=dict(required=False, default=None, no_log=True),
        crypt_scheme=dict(required=False, default="apr_md5_crypt"),
        state=dict(required=False, default="present"),
        create=dict(type='bool', default='yes'),

    )
    module = AnsibleModule(argument_spec=arg_spec,
                           add_file_common_args=True,
                           supports_check_mode=True)

    path = module.params['path']
    username = module.params['name']
    password = module.params['password']
    crypt_scheme = module.params['crypt_scheme']
    state = module.params['state']
    create = module.params['create']
    check_mode = module.check_mode

    if not passlib_installed:
        module.fail_json(msg="This module requires the passlib Python library")

    # Check file for blank lines in effort to avoid "need more than 1 value to unpack" error.
    try:
        f = open(path, "r")
    except IOError:
        # No preexisting file to remove blank lines from
        f = None
    else:
        try:
            lines = f.readlines()
        finally:
            f.close()

        # If the file gets edited, it returns true, so only edit the file if it has blank lines
        strip = False
        for line in lines:
            if not line.strip():
                strip = True
                break

        if strip:
            # If check mode, create a temporary file
            if check_mode:
                temp = tempfile.NamedTemporaryFile()
                path = temp.name
            f = open(path, "w")
            try:
                [f.write(line) for line in lines if line.strip()]
            finally:
                f.close()

    try:
        if state == 'present':
            (msg, changed) = present(path, username, password, crypt_scheme, create, check_mode)
        elif state == 'absent':
            if not os.path.exists(path):
                module.exit_json(msg="%s not present" % username,
                                 warnings="%s does not exist" % path, changed=False)
            (msg, changed) = absent(path, username, check_mode)
        else:
            module.fail_json(msg="Invalid state: %s" % state)

        check_file_attrs(module, changed, msg)
        module.exit_json(msg=msg, changed=changed)
    except Exception:
        e = get_exception()
        module.fail_json(msg=str(e))


# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

if __name__ == '__main__':
    main()
