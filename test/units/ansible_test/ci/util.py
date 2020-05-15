from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json
import re


def common_auth_test(auth):
    private_key_pem = auth.initialize_private_key()
    public_key_pem = auth.public_key_pem

    extract_pem_key(private_key_pem, private=True)
    extract_pem_key(public_key_pem, private=False)

    request = dict(hello='World')
    auth.sign_request(request)

    verify_signature(request, public_key_pem)


def extract_pem_key(value, private):
    assert isinstance(value, type(u''))

    key_type = '(EC )?PRIVATE' if private else 'PUBLIC'
    pattern = r'^-----BEGIN ' + key_type + r' KEY-----\n(?P<key>.*?)\n-----END ' + key_type + r' KEY-----\n$'
    match = re.search(pattern, value, flags=re.DOTALL)

    assert match, 'key "%s" does not match pattern "%s"' % (value, pattern)

    base64.b64decode(match.group('key'))  # make sure the key can be decoded


def verify_signature(request, public_key_pem):
    signature = request.pop('signature')
    payload_bytes = json.dumps(request, sort_keys=True).encode()

    assert isinstance(signature, type(u''))

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    public_key = load_pem_public_key(public_key_pem.encode(), default_backend())

    verifier = public_key.verifier(
        base64.b64decode(signature.encode()),
        ec.ECDSA(hashes.SHA256()),
    )

    verifier.update(payload_bytes)
    verifier.verify()
