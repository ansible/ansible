#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, RSD Services S.A
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: java_cert
version_added: '2.3'
short_description: Uses keytool to import/remove key from java keystore (cacerts)
description:
  - This is a wrapper module around keytool, which can be used to import/remove
    certificates from a given java keystore.
options:
  cert_url:
    description:
      - Basic URL to fetch SSL certificate from.
      - One of C(cert_url) or C(cert_path) is required to load certificate.
    type: str
  cert_port:
    description:
      - Port to connect to URL.
      - This will be used to create server URL:PORT.
    type: int
    default: 443
  cert_path:
    description:
      - Local path to load certificate from.
      - One of C(cert_url) or C(cert_path) is required to load certificate.
    type: path
  cert_alias:
    description:
      - Imported certificate alias.
      - The alias is used when checking for the presence of a certificate in the keystore.
    type: str
  pkcs12_path:
    description:
      - Local path to load PKCS12 keystore from.
    type: path
    version_added: "2.4"
  pkcs12_password:
    description:
      - Password for importing from PKCS12 keystore.
    type: str
    default: ''
    version_added: "2.4"
  pkcs12_alias:
    description:
      - Alias in the PKCS12 keystore.
    type: str
    version_added: "2.4"
  keystore_path:
    description:
      - Path to keystore.
    type: path
  keystore_pass:
    description:
      - Keystore password.
    type: str
    required: true
  keystore_create:
    description:
      - Create keystore if it does not exist.
    type: bool
  keystore_type:
    description:
      - Keystore type (JCEKS, JKS).
    type: str
    version_added: "2.8"
  executable:
    description:
      - Path to keytool binary if not used we search in PATH for it.
    type: str
    default: keytool
  state:
    description:
      - Defines action which can be either certificate import or removal.
    type: str
    choices: [ absent, present ]
    default: present
author:
- Adam Hamsik (@haad)
'''

EXAMPLES = r'''
- name: Import SSL certificate from google.com to a given cacerts keystore
  java_cert:
    cert_url: google.com
    cert_port: 443
    keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
    keystore_pass: changeit
    state: present

- name: Remove certificate with given alias from a keystore
  java_cert:
    cert_url: google.com
    keystore_path: /usr/lib/jvm/jre7/lib/security/cacerts
    keystore_pass: changeit
    executable: /usr/lib/jvm/jre7/bin/keytool
    state: absent

- name: Import SSL certificate from google.com to a keystore, create it if it doesn't exist
  java_cert:
    cert_url: google.com
    keystore_path: /tmp/cacerts
    keystore_pass: changeit
    keystore_create: yes
    state: present

- name: Import a pkcs12 keystore with a specified alias, create it if it doesn't exist
  java_cert:
    pkcs12_path: "/tmp/importkeystore.p12"
    cert_alias: default
    keystore_path: /opt/wildfly/standalone/configuration/defaultkeystore.jks
    keystore_pass: changeit
    keystore_create: yes
    state: present

- name: Import SSL certificate to JCEKS keystore
  java_cert:
    pkcs12_path: "/tmp/importkeystore.p12"
    pkcs12_alias: default
    pkcs12_password: somepass
    cert_alias: default
    keystore_path: /opt/someapp/security/keystore.jceks
    keystore_type: "JCEKS"
    keystore_pass: changeit
    keystore_create: yes
    state: present
'''

RETURN = r'''
msg:
  description: Output from stdout of keytool command after execution of given command.
  returned: success
  type: str
  sample: "Module require existing keystore at keystore_path '/tmp/test/cacerts'"

rc:
  description: Keytool command execution return value.
  returned: success
  type: int
  sample: "0"

cmd:
  description: Executed command to get action done.
  returned: success
  type: str
  sample: "keytool -importcert -noprompt -keystore"
'''

import os
import re

# import module snippets
from ansible.module_utils.basic import AnsibleModule


def get_keystore_type(keystore_type):
    ''' Check that custom keystore is presented in parameters '''
    if keystore_type:
        return " -storetype '%s'" % keystore_type
    return ''


def check_cert_present(module, executable, keystore_path, keystore_pass, alias, keystore_type):
    ''' Check if certificate with alias is present in keystore
        located at keystore_path '''
    test_cmd = ("%s -noprompt -list -keystore '%s' -storepass '%s' "
                "-alias '%s' %s") % (executable, keystore_path, keystore_pass, alias, get_keystore_type(keystore_type))

    (check_rc, _, _) = module.run_command(test_cmd)
    if check_rc == 0:
        return True
    return False


def import_cert_url(module, executable, url, port, keystore_path, keystore_pass, alias, keystore_type):
    ''' Import certificate from URL into keystore located at keystore_path '''

    https_proxy = os.getenv("https_proxy")
    no_proxy = os.getenv("no_proxy")

    proxy_opts = ''
    if https_proxy is not None:
        (proxy_host, proxy_port) = https_proxy.split(':')
        proxy_opts = "-J-Dhttps.proxyHost=%s -J-Dhttps.proxyPort=%s" % (proxy_host, proxy_port)

        if no_proxy is not None:
            # For Java's nonProxyHosts property, items are separated by '|',
            # and patterns have to start with "*".
            non_proxy_hosts = no_proxy.replace(',', '|')
            non_proxy_hosts = re.sub(r'(^|\|)\.', r'\1*.', non_proxy_hosts)

            # The property name is http.nonProxyHosts, there is no
            # separate setting for HTTPS.
            proxy_opts += " -J-Dhttp.nonProxyHosts='%s'" % non_proxy_hosts

    fetch_cmd = "%s -printcert -rfc -sslserver %s %s:%d" % (executable, proxy_opts, url, port)
    import_cmd = ("%s -importcert -noprompt -keystore '%s' "
                  "-storepass '%s' -alias '%s' %s") % (executable, keystore_path,
                                                       keystore_pass, alias,
                                                       get_keystore_type(keystore_type))

    # Fetch SSL certificate from remote host.
    (_, fetch_out, _) = module.run_command(fetch_cmd, check_rc=True)

    # Use remote certificate from remote host and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             data=fetch_out,
                                                             check_rc=False)
    diff = {'before': '\n', 'after': '%s\n' % alias}
    if import_rc == 0:
        module.exit_json(changed=True, msg=import_out,
                         rc=import_rc, cmd=import_cmd, stdout=import_out,
                         diff=diff)
    else:
        module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd,
                         error=import_err)


def import_cert_path(module, executable, path, keystore_path, keystore_pass, alias, keystore_type):
    ''' Import certificate from path into keystore located on
        keystore_path as alias '''
    import_cmd = ("%s -importcert -noprompt -keystore '%s' "
                  "-storepass '%s' -file '%s' -alias '%s' %s") % (executable, keystore_path,
                                                                  keystore_pass, path, alias,
                                                                  get_keystore_type(keystore_type))

    # Use local certificate from local path and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             check_rc=False)

    diff = {'before': '\n', 'after': '%s\n' % alias}
    if import_rc == 0:
        module.exit_json(changed=True, msg=import_out,
                         rc=import_rc, cmd=import_cmd, stdout=import_out,
                         error=import_err, diff=diff)
    else:
        module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd)


def import_pkcs12_path(module, executable, path, keystore_path, keystore_pass, pkcs12_pass, pkcs12_alias, alias, keystore_type):
    ''' Import pkcs12 from path into keystore located on
        keystore_path as alias '''
    import_cmd = ("%s -importkeystore -noprompt -destkeystore '%s' -srcstoretype PKCS12 "
                  "-deststorepass '%s' -destkeypass '%s' -srckeystore '%s' -srcstorepass '%s' "
                  "-srcalias '%s' -destalias '%s' %s") % (executable, keystore_path, keystore_pass,
                                                          keystore_pass, path, pkcs12_pass, pkcs12_alias,
                                                          alias, get_keystore_type(keystore_type))

    # Use local certificate from local path and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             check_rc=False)

    diff = {'before': '\n', 'after': '%s\n' % alias}
    if import_rc == 0:
        module.exit_json(changed=True, msg=import_out,
                         rc=import_rc, cmd=import_cmd, stdout=import_out,
                         error=import_err, diff=diff)
    else:
        module.fail_json(msg=import_out, rc=import_rc, cmd=import_cmd)


def delete_cert(module, executable, keystore_path, keystore_pass, alias, keystore_type):
    ''' Delete certificate identified with alias from keystore on keystore_path '''
    del_cmd = ("%s -delete -keystore '%s' -storepass '%s' "
               "-alias '%s' %s") % (executable, keystore_path, keystore_pass, alias, get_keystore_type(keystore_type))

    # Delete SSL certificate from keystore
    (del_rc, del_out, del_err) = module.run_command(del_cmd, check_rc=True)

    diff = {'before': '%s\n' % alias, 'after': None}

    module.exit_json(changed=True, msg=del_out,
                     rc=del_rc, cmd=del_cmd, stdout=del_out,
                     error=del_err, diff=diff)


def test_keytool(module, executable):
    ''' Test if keytool is actually executable or not '''
    module.run_command("%s" % executable, check_rc=True)


def test_keystore(module, keystore_path):
    ''' Check if we can access keystore as file or not '''
    if keystore_path is None:
        keystore_path = ''

    if not os.path.exists(keystore_path) and not os.path.isfile(keystore_path):
        # Keystore doesn't exist we want to create it
        module.fail_json(changed=False, msg="Module require existing keystore at keystore_path '%s'" % keystore_path)


def main():
    argument_spec = dict(
        cert_url=dict(type='str'),
        cert_path=dict(type='path'),
        pkcs12_path=dict(type='path'),
        pkcs12_password=dict(type='str', no_log=True),
        pkcs12_alias=dict(type='str'),
        cert_alias=dict(type='str'),
        cert_port=dict(type='int', default=443),
        keystore_path=dict(type='path'),
        keystore_pass=dict(type='str', required=True, no_log=True),
        keystore_create=dict(type='bool', default=False),
        keystore_type=dict(type='str'),
        executable=dict(type='str', default='keytool'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[['cert_path', 'cert_url', 'pkcs12_path']],
        required_together=[['keystore_path', 'keystore_pass']],
        mutually_exclusive=[
            ['cert_url', 'cert_path', 'pkcs12_path']
        ],
        supports_check_mode=True,
    )

    url = module.params.get('cert_url')
    path = module.params.get('cert_path')
    port = module.params.get('cert_port')

    pkcs12_path = module.params.get('pkcs12_path')
    pkcs12_pass = module.params.get('pkcs12_password', '')
    pkcs12_alias = module.params.get('pkcs12_alias', '1')

    cert_alias = module.params.get('cert_alias') or url

    keystore_path = module.params.get('keystore_path')
    keystore_pass = module.params.get('keystore_pass')
    keystore_create = module.params.get('keystore_create')
    keystore_type = module.params.get('keystore_type')
    executable = module.params.get('executable')
    state = module.params.get('state')

    if path and not cert_alias:
        module.fail_json(changed=False,
                         msg="Using local path import from %s requires alias argument."
                             % keystore_path)

    test_keytool(module, executable)

    if not keystore_create:
        test_keystore(module, keystore_path)

    cert_present = check_cert_present(module, executable, keystore_path,
                                      keystore_pass, cert_alias, keystore_type)

    if state == 'absent' and cert_present:
        if module.check_mode:
            module.exit_json(changed=True)

        delete_cert(module, executable, keystore_path, keystore_pass, cert_alias, keystore_type)

    elif state == 'present' and not cert_present:
        if module.check_mode:
            module.exit_json(changed=True)

        if pkcs12_path:
            import_pkcs12_path(module, executable, pkcs12_path, keystore_path,
                               keystore_pass, pkcs12_pass, pkcs12_alias, cert_alias, keystore_type)

        if path:
            import_cert_path(module, executable, path, keystore_path,
                             keystore_pass, cert_alias, keystore_type)

        if url:
            import_cert_url(module, executable, url, port, keystore_path,
                            keystore_pass, cert_alias, keystore_type)

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
