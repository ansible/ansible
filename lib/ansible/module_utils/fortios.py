#
# (c) 2017 Benjamin Jolivot, <bjolivot@gmail.com>
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
#

import os
import time


fortios_argument_spec = dict(
    host            = dict(required=True ),
    username        = dict(required=True ),
    password        = dict(required=True, type='str', no_log=True ),
    timeout         = dict(type='int', default=60),
    vdom            = dict(type='str', default=None ),
    backup          = dict(type='bool', default=False),
    backup_path     = dict(type='path'),
    backup_filename = dict(type='str'),
)

fortios_required_if = [
    ['backup',   True   , ['backup_path']   ],
]

def backup(module,running_config):
    backup_path = module.params['backup_path']
    if not os.path.exists(backup_path):
        try:
            os.mkdir(backup_path)
        except:
            module.fail_json(msg="Can't create directory {0} Permission denied ?".format(backup_path))
    tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
    filename = '%s/%s_config.%s' % (backup_path, module.params['host'], tstamp)
    try:
        open(filename, 'w').write(running_config)
    except:
        module.fail_json(msg="Can't create backup file {0} Permission denied ?".format(filename))
