# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


def rabbitmq_argument_spec():
    return dict(
        login_user=dict(default='guest', type='str'),
        login_password=dict(default='guest', type='str', no_log=True),
        login_host=dict(default='localhost', type='str'),
        login_port=dict(default='15672', type='str'),
        login_protocol=dict(default='http', choices=['http', 'https'], type='str'),
        cacert=dict(required=False, type='path', default=None),
        cert=dict(required=False, type='path', default=None),
        key=dict(required=False, type='path', default=None),
        vhost=dict(default='/', type='str'),
    )
