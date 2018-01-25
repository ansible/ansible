#!/usr/bin/env python
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

import argparse
import sys

# TODO: could read these from the files I suppose...
secrets = {'vault-password': 'test-vault-password',
           'vault-password-wrong': 'hunter42',
           'vault-password-ansible': 'ansible',
           'password': 'password',
           'vault-client-password-1': 'password-1',
           'vault-client-password-2': 'password-2'}


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Get a vault password from user keyring')

    parser.add_argument('--vault-id', action='store', default=None,
                        dest='vault_id',
                        help='name of the vault secret to get from keyring')
    parser.add_argument('--username', action='store', default=None,
                        help='the username whose keyring is queried')
    parser.add_argument('--set', action='store_true', default=False,
                        dest='set_password',
                        help='set the password instead of getting it')
    return parser


def get_secret(keyname):
    return secrets.get(keyname, None)


def main():
    rc = 0

    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()
    # print('args: %s' % args)

    keyname = args.vault_id or 'ansible'

    if args.set_password:
        print('--set is not supported yet')
        sys.exit(1)

    secret = get_secret(keyname)
    if secret is None:
        sys.stderr.write('test-vault-client could not find key for vault-id="%s"\n' % keyname)
        # key not found rc=2
        return 2

    sys.stdout.write('%s\n' % secret)

    return rc


if __name__ == '__main__':
    sys.exit(main())
