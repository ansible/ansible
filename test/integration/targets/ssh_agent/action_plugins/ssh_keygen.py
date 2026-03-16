from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible._internal._ssh._ssh_agent import PublicKeyMsg
from ansible.module_utils.common.text.converters import to_bytes, to_text


from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key as rsa_generate_private_key
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.dsa import generate_private_key as dsa_generate_private_key
from cryptography.hazmat.primitives.asymmetric.ec import SECP384R1, generate_private_key as ecdsa_generate_private_key


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect
        match self._task.args.get('type'):
            case 'ed25519':
                private_key = Ed25519PrivateKey.generate()
            case 'rsa':
                private_key = rsa_generate_private_key(65537, 4096)
            case 'dsa':
                private_key = dsa_generate_private_key(1024)
            case 'ecdsa':
                private_key = ecdsa_generate_private_key(SECP384R1())
            case _:
                return {'failed': True, 'msg': 'not implemented'}

        public_key = private_key.public_key()
        public_key_msg = PublicKeyMsg.from_public_key(public_key)

        if not (passphrase := self._task.args.get('passphrase')):
            encryption_algorithm = serialization.NoEncryption()
        else:
            encryption_algorithm = serialization.BestAvailableEncryption(
                to_bytes(passphrase)
            )

        return {
            'changed': True,
            'private_key': to_text(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=encryption_algorithm,
            )),
            'public_key': to_text(public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH,
            )),
            'fingerprint': f'SHA256:{public_key_msg.fingerprint}',
        }
