#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Netservers Ltd. <support@netservers.co.uk>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_console_cert
short_description: Uploads SSL certificates for console proxy on Apache CloudStack.
description:
    - Uploads SSL certificates for console proxy on Apache CloudStack.
    - One root and multiple intermediate certificates are supported.
    - This module cannot remove certificates due to api limitations
    - Verification that the certificate has been successfully deployed
    - is done by direct connection to port 443 on the console proxy.
    - The machine running this module must have access to port 443 on
    - the console proxy, and DNS for the url_domain must be set-up in
    - advance. This module will fail if the console proxy cannot be reached.
    - A gap of several minutes is advised between playbook runs in order
    - to give the console proxy time to boot with the new certificate.
version_added: "2.4"
author: "Netservers Ltd. (@netservers)"
options:
  url_domain:
    description:
      - The domain used to connect to the console proxy.
      - Although not directly related to upload of the certificate
      - we use a mismatched url_domain as a trigger to (re-)upload the cert
    required: true
  force_upload:
    description:
      - Forced the upload of the certificate, even if the url_domain
      - already matches, and the live certificate matches.
      - This module cannot detect changes in the intermediate or root certs
      - which is one reason you might want to force an update.
      - Do not repreatedly force updates, as this will cause your console
      - proxy to reboot each time.
    default: false
    required: false
  domain_suffix:
    description:
      - Domain name suffix of the server certificate.
    required: true
  root_certificate:
    description:
      - Root certificate provided by the Certificate Authority
    required: true
  server_certificate:
    description:
      - The certificate
    required: true
  intermediate_certificates:
    description:
      - One or more intermediate certificates provided by the Certificate Authority.
    required: false
    default: none
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Ensure certificate with root and intermediates are present - read from files
- local_action:
    module: cs_console_cert
    url_domain: console.mycompany.net
    domain_suffix: mycompany.net
    root_certificate: "{{ lookup('file', 'files/console_root.crt') }}"
    server_certificate: "{{ lookup('file', 'files/console.crt') }}"
    private_key: "{{ lookup('file', 'files/console.key') }}"
    intermediate_certificates:
    - "{{ lookup('file', 'files/console_intermediate.crt') }}"

# Ensure certificate with root and intermediates are present
- local_action:
    module: cs_console_cert
    url_domain: console.mycompany.net
    domain_suffix: mycompany.net
    root_certificate: |
        -----BEGIN CERTIFICATE-----
        MIIFdDCCBFygAwIBAgIQJ2buVutJ846r13Ci/ITeIjANBgkqhkiG9w0BAQwFADBv
        MQswCQYDVQQGEwJTRTEUMBIGA1UEChMLQWRkVHJ1c3QgQUIxJjAkBgNVBAsTHUFk
        ZFRydXN0IEV4dGVybmFsIFRUUCBOZXR3b3JrMSIwIAYDVQQDExlBZGRUcnVzdCBF
        Jw5dhHk3QBN39bSsHNA7qxcS1u80GH4r6XnTq1dFDK8o+tDb5VCViLvfhVdpfZLY
        Uspzgb8c8+a4bmYRBbMelC1/kZWSWfFMzqORcUx8Rww7Cxn2obFshj5cqsQugsv5
        B5a6SE2Q8pTIqXOi6wZ7I53eovNNVZ96YUWYGGjHXkBrI/V5eu+MtWuLt29G9Hvx
        PUsE2JOAWVrgQSQdso8VYFhH2+9uRv0V9dlfmrPb2LjkQLPNlzmuhbsdjrzch5vR
        pu/xO28QOG8=
        -----END CERTIFICATE-----
    intermediate_certificates:
    - |
        -----BEGIN CERTIFICATE-----
        MIIFdDCCBFygAwIBAgIQJ2buVutJ846r13Ci/ITeIjANBgkqhkiG9w0BAQwFADBv
        MQswCQYDVQQGEwJTRTEUMBIGA1UEChMLQWRkVHJ1c3QgQUIxJjAkBgNVBAsTHUFk
        ZFRydXN0IEV4dGVybmFsIFRUUCBOZXR3b3JrMSIwIAYDVQQDExlBZGRUcnVzdCBF
        Jw5dhHk3QBN39bSsHNA7qxcS1u80GH4r6XnTq1dFDK8o+tDb5VCViLvfhVdpfZLY
        Uspzgb8c8+a4bmYRBbMelC1/kZWSWfFMzqORcUx8Rww7Cxn2obFshj5cqsQugsv5
        B5a6SE2Q8pTIqXOi6wZ7I53eovNNVZ96YUWYGGjHXkBrI/V5eu+MtWuLt29G9Hvx
        PUsE2JOAWVrgQSQdso8VYFhH2+9uRv0V9dlfmrPb2LjkQLPNlzmuhbsdjrzch5vR
        pu/xO28QOG8=
        -----END CERTIFICATE-----
    private_key: |
        -----BEGIN PRIVATE KEY-----
        MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDn+TxIhHHkOD7p
        ZphWnf2aVMqjCUH8YQJrsGAgjy7IXi8OHRoqSC24iJPCT62TxpjFA4aAXiKjRIlt
        9ZRzwpGLkEGby5QhJZXjd7bxbRhgnsvoc9pfzDs20MtK6aeBAA8nXf4V53bF38vo
        Qch+GOYw9dzHzNAank9foOtBwrhIatNVpbXYpTBkDmFl65ld/piLbs2FrCBh3EGZ
        aEiclIWICUris6/VQHGZ/TS4zkrfq54Od9xIOlJ/SexT9clSaSSk6pdWzvWdjP8S
        nHL2bSZy3i9LoQtfvyUggMTfiWJNho/eRxpAluRbqQKBgBqJjxpMqevF6ALUU6ZD
        IPrXeUmiDmdJHzZcMm4p4ppUotKqGAxEFCBFnGI4qfaK5oWgY6pceem/dmSyxSik
        ZkBT6/QPH0nY7Lbz4NUx+ecXaRU8Q1A706G/6knHitUobqHdx1MI5f4fdqQpJtRi
        JwPaW+Jmy5bAmWXTiTvEP6qc
        -----END PRIVATE KEY-----
    server_certificate: |
        -----BEGIN CERTIFICATE-----
        MIIDXTCCAkWgAwIBAgIJAPmOsHBNbF1oMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
        BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
        aWRnaXRzIFB0eSBMdGQwHhcNMTcwNjExMDk1MzQwWhcNMTgwNjExMDk1MzQwWjBF
        E/Imk2FYdDyxl6rs606G0t5Sh7pm8aEP4hCBSiYuVbGkqwlTdBXHkhnO0a9Uv13d
        0PeFRTGsroOFuHLfBdh1Rb0W+IQl2cmBc/YS0qg1wvHWikS6evC23LExOILuc31+
        SQ==
        -----END CERTIFICATE-----
'''

RETURN = ''' # '''

import ssl
import socket
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    CloudStackException,
    cs_argument_spec,
    cs_required_together,
)


class AnsibleCloudStackConsoleCert(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackConsoleCert, self).__init__(module)
        self.returns = {}
        self.consoleproxy_url = None

    def get_cert_signature(self):
        if self.cert_signature:
            return self.cert_signature

        key = self.module.params.get('private_key')
        cert = self.module.params.get('server_certificate')
        root = self.module.params.get('root_certificate')
        intermediate = self.module.params.get('intermediate_certificates').join("\n")
        self.cert_signature = hashlib.md5(key + cert + root + intermediate).hexdigest()

        return self.cert_signature

    def get_configuration(self, name=None):
        configuration = None
        args = {'name': 'consoleproxy.url.domain'}
        configurations = self.cs.listConfigurations(**args)
        if not configurations:
            self.module.fail_json(msg="Configuration %s not found." % args['name'])
        configuration = configurations['configuration'][0]
        return configuration

    def set_configuration(self, name=None, value=None):
        args = {
            'name': name,
            'value': value,
        }
        res = self.cs.updateConfiguration(**args)
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
        return res['configuration']

    def get_live_consoleproxy_url(self):
        if self.consoleproxy_url is None:
            self.consoleproxy_url = self.get_configuration('consoleproxy.url.domain')['value']

        return self.consoleproxy_url

    def console_proxy_port_open(self, port=443):
        url_domain = self.module.params.get('url_domain')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((url_domain, port))
        if result == 0:
            sock.close()
            return True

        return False

    def update_required(self):
        url_domain = self.module.params.get('url_domain')
        new_cert = self.module.params.get('server_certificate').rstrip()
        if self.module.params.get('force_upload') or \
           (url_domain != self.get_live_consoleproxy_url()):
            return True

        if not self.console_proxy_port_open(443) and not self.console_proxy_port_open(80):
            module.fail_json(msg='Failed: console proxy %s is not online for certificate check.' % url_domain)

        try:
            current_live_cert = ssl.get_server_certificate((url_domain, 443)).rstrip()
        except:
            return True

        if current_live_cert != new_cert:
            return True

        return False

    def upload_cert(self, name=None, id=None, certificate=None, private_key=None):
        args = {
            'name': name,
            'id': id,
            'domainsuffix': self.module.params.get('domain_suffix'),
            'certificate': certificate,
            'privatekey': private_key,
        }
        res = self.cs.uploadCustomCertificate(**args)
        if 'errortext' in res:
            self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

        return self.poll_job(res, 'customcertificate')

    def apply(self):
        if not self.update_required():
            return

        self.result['changed'] = True
        server_certificate = self.module.params.get('server_certificate')
        private_key = self.module.params.get('private_key')
        intermediates = self.module.params.get('intermediate_certificates')

        self.set_configuration('consoleproxy.url.domain', self.module.params.get('url_domain'))

        id = 1
        self.upload_cert(name='root', id=id, certificate=self.module.params.get('root_certificate'))

        for x in range(0, len(intermediates)):
            id = id + 1
            name = "intermediate{}".format(x + 1)
            self.upload_cert(name=name, id=id, certificate=intermediates[x])

        id = id + 1
        return self.upload_cert(id=id, certificate=server_certificate, private_key=private_key)


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        url_domain=dict(required=True),
        force_upload=dict(type='bool', default=False),
        domain_suffix=dict(required=True),
        root_certificate=dict(required=True),
        server_certificate=dict(required=True),
        private_key=dict(required=True),
        intermediate_certificates=dict(type='list', default=None),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    try:
        acs_cert = AnsibleCloudStackConsoleCert(module)
        cert = acs_cert.apply()
        result = acs_cert.get_result(cert)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
