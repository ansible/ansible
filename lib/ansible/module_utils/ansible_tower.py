# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Wayne Witzel III <wayne@riotousliving.com>
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

try:
    import tower_cli.utils.exceptions as exc
    from tower_cli.utils import parser
    from tower_cli.api import client

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def tower_auth_config(module):
    '''tower_auth_config attempts to load the tower-cli.cfg file
    specified from the `tower_config_file` parameter. If found,
    if returns the contents of the file as a dictionary, else
    it will attempt to fetch values from the module pararms and
    only pass those values that have been set.
    '''
    config_file = module.params.pop('tower_config_file', None)
    if config_file:
        config_file = os.path.expanduser(config_file)
        if not os.path.exists(config_file):
            module.fail_json(msg='file not found: %s' % config_file)
        if os.path.isdir(config_file):
            module.fail_json(msg='directory can not be used as config file: %s' % config_file)

        with open(config_file, 'rb') as f:
            return parser.string_to_dict(f.read())
    else:
        auth_config = {}
        host = module.params.pop('tower_host', None)
        if host:
            auth_config['host'] = host
        username = module.params.pop('tower_username', None)
        if username:
            auth_config['username'] = username
        password = module.params.pop('tower_password', None)
        if password:
            auth_config['password'] = password
        verify_ssl = module.params.pop('tower_verify_ssl', None)
        if verify_ssl is not None:
            auth_config['verify_ssl'] = verify_ssl
        return auth_config


def tower_check_mode(module):
    '''Execute check mode logic for Ansible Tower modules'''
    if module.check_mode:
        try:
            result = client.get('/ping').json()
            module.exit_json(changed=True, tower_version='{0}'.format(result['version']))
        except (exc.ServerError, exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(changed=False, msg='Failed check mode: {0}'.format(excinfo))


def tower_argument_spec():
    return dict(
        tower_host=dict(),
        tower_username=dict(),
        tower_password=dict(no_log=True),
        tower_verify_ssl=dict(type='bool', default=True),
        tower_config_file=dict(type='path'),
    )
