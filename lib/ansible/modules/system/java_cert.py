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
      - When state is present, the certificate will always idempotently be inserted
      - into the keystore, even if there already exists a cert alias that is different.
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
import tempfile
import random
import string

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.crypto import load_certificate
try:
    from urlparse import urlparse
    from urllib import getproxies
except ModuleNotFoundError:
    from urllib.parse import urlparse
    from urllib.request import getproxies


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


def get_digest_from_x509_in_jks_store(module, executable, keystore_path,
                                      keystore_pass, cert_alias, keystore_type, digest):
    """ Exports an X509 cert from a JKS store, and returns the digest of that cert """
    cert_pem = _export_cert(module, executable, keystore_path,
                            keystore_pass, cert_alias, keystore_type)
    cert_digest = _convert_pem_string_to_x509_object(cert_pem).digest(digest)
    return cert_digest


def _export_cert(module, executable, keystore_path, keystore_pass, alias, keystore_type):
    """ Uses keytool to export the certificate with the specified alias in PEM.
          The certificate is returned as a PEM formatted string """
    export_cmd = ("%s -noprompt -rfc -export -keystore '%s' -storepass '%s' "
                  "-alias '%s' %s") % (executable, keystore_path, keystore_pass, alias, get_keystore_type(keystore_type))
    (_, stdout, _) = module.run_command(export_cmd)
    return stdout


def _convert_pem_string_to_x509_object(pem_string):
    """ Takes a string containing a PEM formatted certificate and
          returns an OpenSSL.crypto.x509 object """
    try:
        (_, tmp) = tempfile.mkstemp()
        with open(tmp, 'w') as f:
            f.write(pem_string)
        cert = load_certificate(tmp)
    finally:
        os.remove(tmp)
    return cert


def get_digest_from_pkcs12_in_jks_store(module, executable, keystore_path, keystore_pass, alias, digest_function):
    """ Large wrapper function that creates a PKCS12 archive from an entry in a JKS store.
          The X509 public cert is then extracted from the PKCS12 archive. The digest is taken
         from this cert, and returned.  """
    random_name = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
    tmp_pkcs12_store = os.path.join(tempfile.gettempdir(), random_name)

    try:
        _convert_jks_to_pkcs12(module, executable, keystore_path, keystore_pass, alias, tmp_pkcs12_store)
        digest = get_digest_from_pkcs12(module, tmp_pkcs12_store, alias, keystore_pass, digest_function)
    finally:
        os.remove(tmp_pkcs12_store)

    return digest


def _convert_jks_to_pkcs12(module, executable, keystore_path, keystore_pass, alias, pkcs12_dest):
    """ Creates a PKCS12 archive from an existing keystore """
    convert_cmd = ("'%s' -importkeystore -srckeystore '%s' -srcstorepass '%s' "
                   "-srcalias '%s'  -deststoretype PKCS12 "
                   "-destalias '%s' -destkeystore '%s' -deststorepass '%s' -noprompt") % (executable, keystore_path, keystore_pass, alias,
                                                                                          alias, pkcs12_dest, keystore_pass)
    module.run_command(convert_cmd)


def get_digest_from_pkcs12(module, pkcs12_path, cert_alias, password, digest_function):
    """ Exports the X509 cert from a PKCS12 store to a temporary file, and then
          returns the digest of that cert """
    (_, tmp_pem_cert) = tempfile.mkstemp()
    try:
        _export_public_cert_from_pkcs12(module, pkcs12_path, cert_alias,
                                        password, tmp_pem_cert)
        new_cert_digest = load_certificate(tmp_pem_cert).digest(digest_function)
    finally:
        os.remove(tmp_pem_cert)
    return new_cert_digest


def _export_public_cert_from_pkcs12(module, pkcs_file, alias, password, dest):
    """ Runs Openssl to extract the public cert from a PKCS12 archive and write it to a file. """
    export_cmd = ("openssl pkcs12 -in '%s' -nokeys -password pass:'%s' "
                  " -name '%s' -out '%s'") % (pkcs_file, password, alias, dest)
    module.run_command(export_cmd)


def get_proxy_settings(scheme='https'):
    """ Returns a tuple containing (proxy_host, proxy_port). (False, False) if no proxy is found """
    proxy_url = getproxies().get(scheme, '')
    if not proxy_url:
        return (False, False)
    else:
        parsed_url = urlparse(proxy_url)
        if parsed_url.scheme:
            (proxy_host, proxy_port) = parsed_url.netloc.split(':')
        else:
            (proxy_host, proxy_port) = parsed_url.path.split(':')
        return (proxy_host, proxy_port)


def build_proxy_options():
    """ Returns string of valid proxy options for keytool """
    (proxy_host, proxy_port) = get_proxy_settings()
    no_proxy = os.getenv("no_proxy")

    proxy_opts = ''
    if proxy_host:
        proxy_opts = "-J-Dhttps.proxyHost=%s -J-Dhttps.proxyPort=%s" % (proxy_host, proxy_port)

        if no_proxy is not None:
            # For Java's nonProxyHosts property, items are separated by '|',
            # and patterns have to start with "*".
            non_proxy_hosts = no_proxy.replace(',', '|')
            non_proxy_hosts = re.sub(r'(^|\|)\.', r'\1*.', non_proxy_hosts)

            # The property name is http.nonProxyHosts, there is no
            # separate setting for HTTPS.
            proxy_opts += " -J-Dhttp.nonProxyHosts='%s'" % non_proxy_hosts
    return proxy_opts


def download_cert_url(module, executable, url, port):
    """ Fetches the certificate from the remote URL using `keytool -printcert...`
          The PEM formatted string is returned """
    proxy_opts = build_proxy_options()
    fetch_cmd = "%s -printcert -rfc -sslserver %s %s:%d" % (executable, proxy_opts, url, port)

    # Fetch SSL certificate from remote host.
    (_, fetch_out, _) = module.run_command(fetch_cmd, check_rc=True)

    return fetch_out


def import_cert_url(module, executable, keystore_path, keystore_pass, alias, keystore_type, cert_data):
    """Takes cert_data as a PEM string and imports the certificate into the keystore """
    import_cmd = ("%s -importcert -noprompt -keystore '%s' "
                  "-storepass '%s' -alias '%s' %s") % (executable, keystore_path,
                                                       keystore_pass, alias,
                                                       get_keystore_type(keystore_type))

    # Use remote certificate from remote host and import it to a java keystore
    (import_rc, import_out, import_err) = module.run_command(import_cmd,
                                                             data=cert_data,
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


def delete_cert(module, executable, keystore_path, keystore_pass, alias, keystore_type, exit_after=True):
    ''' Delete certificate identified with alias from keystore on keystore_path '''
    del_cmd = ("%s -delete -keystore '%s' -storepass '%s' "
               "-alias '%s' %s") % (executable, keystore_path, keystore_pass, alias, get_keystore_type(keystore_type))

    # Delete SSL certificate from keystore
    (del_rc, del_out, del_err) = module.run_command(del_cmd, check_rc=True)

    if exit_after:
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
        required_if=[['state', 'present', ('cert_path', 'cert_url', 'pkcs12_path'), True]],
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

    digest = 'sha1'
    alias_exists = check_cert_present(module, executable, keystore_path,
                                      keystore_pass, cert_alias, keystore_type)

    if alias_exists and state == 'present':
        # The alias exists in the keystore so we must now compare the SHA1 hash of the
        # public certificate already in the keystore, and the certificate we  are wanting to add
        if pkcs12_path:
            # To get the digest of the PKCS12 file we need to convert the JKS
            # format to PKCS12. Then we can run OpenSSL to print out only the
            # public cert. We can then load the public cert and get the digest
            keystore_cert_digest = get_digest_from_pkcs12_in_jks_store(module, executable,
                                                                       keystore_path, keystore_pass, cert_alias, digest)

            new_cert_digest = get_digest_from_pkcs12(module, pkcs12_path,
                                                     cert_alias, keystore_pass, digest)
        elif path:
            # Extracting the X509 digest is a bit easier. Keytool will print the PEM
            # certificate to stdout so we don't need to do any transformations.
            keystore_cert_digest = get_digest_from_x509_in_jks_store(module, executable,
                                                                     keystore_path, keystore_pass, cert_alias, keystore_type, digest)
            new_cert_digest = load_certificate(path).digest(digest)

        elif url:
            # Getting the X509 digest from a URL is the same as from a path, we just have
            # to download the cert first
            keystore_cert_digest = get_digest_from_x509_in_jks_store(module, executable,
                                                                     keystore_path, keystore_pass, cert_alias, keystore_type, digest)
            remote_cert_pem = download_cert_url(module, executable, url, port)
            new_cert_digest = _convert_pem_string_to_x509_object(remote_cert_pem).digest(digest)
        certificates_are_not_equal = keystore_cert_digest != new_cert_digest
    else:
        certificates_are_not_equal = True

    if state == 'absent' and alias_exists:
        if module.check_mode:
            module.exit_json(changed=True)

        delete_cert(module, executable, keystore_path, keystore_pass, cert_alias, keystore_type)

    elif state == 'present' and certificates_are_not_equal:
        if module.check_mode:
            module.exit_json(changed=True)

        # The certificate in the keystore does not match with the one we want to be present
        # The existing certificate must first be deleted before we insert the correct one
        if alias_exists:
            delete_cert(module, executable, keystore_path, keystore_pass, cert_alias, keystore_type, False)

        if pkcs12_path:
            import_pkcs12_path(module, executable, pkcs12_path, keystore_path,
                               keystore_pass, pkcs12_pass, pkcs12_alias, cert_alias, keystore_type)

        if path:
            import_cert_path(module, executable, path, keystore_path,
                             keystore_pass, cert_alias, keystore_type)

        if url:
            import_cert_url(module, executable, keystore_path,
                            keystore_pass, cert_alias, keystore_type, remote_cert_pem)

    module.exit_json(changed=False)


if __name__ == "__main__":
    main()
