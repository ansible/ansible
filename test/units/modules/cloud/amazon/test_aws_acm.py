# (c) 2017 Red Hat Inc.
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

# (c) 2017 Red Hat Inc.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.modules.cloud.amazon.aws_acm import cert_compare
from ansible.module_utils.crypto import get_fingerprint_from_pem_cert as get_fingerprint
from ansible.module_utils._text import to_bytes, to_text

# You can manually check the fingerprints with
# openssl x509 -in a.pem -noout -sha256 -fingerprint
test_certs = [
    { # docs.ansible.com 28/8/19
        'expected_fingerprint':'3D:F4:22:86:43:80:51:0F:0D:F9:E0:60:79:33:18:D4:F5:8E:6D:5F:94:0A:08:D8:56:DF:2F:22:B6:D4:74:06',
        'path': 'test/units/modules/cloud/amazon/fixtures/certs/a.pem'        
    },
    { # cryptography.io 28/8/19
        'expected_fingerprint':'E0:BA:7D:45:F1:95:67:2C:DE:6D:EC:4E:18:9B:5C:94:C4:5D:F4:16:CA:16:0C:06:C5:0B:8A:8A:6C:5E:6D:DE',
        'path': 'test/units/modules/cloud/amazon/fixtures/certs/b.pem'        
    }
]

def test_fingerprinting():
    for cert in test_certs:
        with open(cert['path'],'r') as f:
            cert['pem_bytes'] = to_bytes(f.read())
        cert['pem_text'] = to_text(cert['pem_bytes'])
        cert['fingerprint_bytes'] = get_fingerprint(cert['pem_bytes'])
        
        # convert to the format of test_cert['expected_fingerprint']
        # Which is what you can copy and paste from a browser
        cert['fingerprint_text'] = cert['fingerprint_bytes'].hex().upper()
        cert['expected_fingerprint'] = cert['expected_fingerprint'].replace(':','')
        if cert['fingerprint_text'] != cert['expected_fingerprint']:
            print("Expected fingerprint: %s" % cert['expected_fingerprint'])
            print("Actual fingerprint:   %s" % cert['fingerprint_text'])
        assert(cert['fingerprint_text'] == cert['expected_fingerprint'])
        
    # Both bytes
    assert(cert_compare(test_certs[0]['pem_bytes'], test_certs[0]['pem_bytes']))
    assert(cert_compare(test_certs[1]['pem_bytes'], test_certs[1]['pem_bytes']))
    assert(not cert_compare(test_certs[0]['pem_bytes'], test_certs[1]['pem_bytes']))
        
    # both text
    assert(cert_compare(test_certs[0]['pem_text'], test_certs[0]['pem_text']))
    assert(cert_compare(test_certs[1]['pem_text'], test_certs[1]['pem_text']))
    assert(not cert_compare(test_certs[0]['pem_text'], test_certs[1]['pem_text']))
    
    # mixed
    assert(cert_compare(test_certs[0]['pem_bytes'], test_certs[0]['pem_text']))
    assert(cert_compare(test_certs[1]['pem_bytes'], test_certs[1]['pem_text']))
    assert(not cert_compare(test_certs[0]['pem_bytes'], test_certs[1]['pem_text']))
    assert(not cert_compare(test_certs[0]['pem_text'], test_certs[1]['pem_bytes']))
        
    
