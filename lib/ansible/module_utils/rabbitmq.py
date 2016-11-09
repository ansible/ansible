# -*- coding: utf-8 -*-

# (c) 2016, Jorge Rodriguez <jorge.rodriguez@tiriel.eu>
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
