# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import bigsuds
    bigsuds_found = True
except ImportError:
    bigsuds_found = False


from ansible.module_utils.basic import env_fallback


def f5_argument_spec():
    return dict(
        server=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ['F5_SERVER'])
        ),
        user=dict(
            type='str',
            required=True,
            fallback=(env_fallback, ['F5_USER'])
        ),
        password=dict(
            type='str',
            aliases=['pass', 'pwd'],
            required=True,
            no_log=True,
            fallback=(env_fallback, ['F5_PASSWORD'])
        ),
        validate_certs=dict(
            default='yes',
            type='bool',
            fallback=(env_fallback, ['F5_VALIDATE_CERTS'])
        ),
        server_port=dict(
            type='int',
            default=443,
            fallback=(env_fallback, ['F5_SERVER_PORT'])
        ),
        state=dict(
            type='str',
            default='present',
            choices=['present', 'absent']
        ),
        partition=dict(
            type='str',
            default='Common',
            fallback=(env_fallback, ['F5_PARTITION'])
        )
    )


def f5_parse_arguments(module):
    if not bigsuds_found:
        module.fail_json(msg="the python bigsuds module is required")

    if module.params['validate_certs']:
        import ssl
        if not hasattr(ssl, 'SSLContext'):
            module.fail_json(
                msg="bigsuds does not support verifying certificates with python < 2.7.9."
                    "Either update python or set validate_certs=False on the task'")

    return (
        module.params['server'],
        module.params['user'],
        module.params['password'],
        module.params['state'],
        module.params['partition'],
        module.params['validate_certs'],
        module.params['server_port']
    )


def bigip_api(bigip, user, password, validate_certs, port=443):
    try:
        if bigsuds.__version__ >= '1.0.4':
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password, verify=validate_certs, port=port)
        elif bigsuds.__version__ == '1.0.3':
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password, verify=validate_certs)
        else:
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
    except TypeError:
        # bigsuds < 1.0.3, no verify param
        if validate_certs:
            # Note: verified we have SSLContext when we parsed params
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)
        else:
            import ssl
            if hasattr(ssl, 'SSLContext'):
                # Really, you should never do this.  It disables certificate
                # verification *globally*.  But since older bigip libraries
                # don't give us a way to toggle verification we need to
                # disable it at the global level.
                # From https://www.python.org/dev/peps/pep-0476/#id29
                ssl._create_default_https_context = ssl._create_unverified_context
            api = bigsuds.BIGIP(hostname=bigip, username=user, password=password)

    return api


# Fully Qualified name (with the partition)
def fq_name(partition, name):
    if name is not None and not name.startswith('/'):
        return '/%s/%s' % (partition, name)
    return name


# Fully Qualified name (with partition) for a list
def fq_list_names(partition, list_names):
    if list_names is None:
        return None
    return map(lambda x: fq_name(partition, x), list_names)
