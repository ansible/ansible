#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ce_ftp
version_added: "2.9"
short_description: Use FTP protocol to transfer file on HUAWEI CloudEngine devices.
description:
    - Use FTP protocol to transfer file on HUAWEI CloudEngine devices.
author: weixiaoxu0512(@weixiaoxu0512)
options:
    ftp_port:
        description:
            - Specifies the port for ftp connection, default 21.
        default: 21
    ftp_server:
        description:
            - Specifies the ftp server ip address.
              if it is none, use C(host) as ftp server when C is not none.
              Otherwise ftp transfer failed.
    ftp_user:
        description:
            - Specifies the ftp user name to login ftp server.
              The value is none,use C(username) as ftp user,if C is not none.
              Otherwise ftp login failed.
    ftp_password:
        description:
            - Specifies the ftp user password to login ftp server.
              The value is none,use C(password) as ftp user,if C is not none.
              Otherwise ftp login failed.
    remote_file:
        description:
            - Remote file name to put/get on ftp server.
              By default, it is same as local file.
              Absolute path is required, if file is not in root directory.
    local_file:
        description:
            - Local file name to put/get to/from ftp server.
              By default, it is same as remote file.
              Absolute path is required, if file is not in work directory.
    mode:
        description:
            - Determines whether the file should be put or got.
        choices: ['put', 'get']
extends_documentation_fragment: ce
"""

EXAMPLES = '''
    - name: "ftp get file"
      ce_ftp:
        ftp_server: 10.78.106.33
        ftp_user: huawei
        ftp_password: huaweiDC
        remote_file: /mpu/profile_666_04211257.dat
        local_file: /usr/xuyuandong/1.txt
        mode: get
'''

RETURN = '''
changed:
  returned: always
  type: bool
  sample: true
local_file:
  date: local file create time
  name: local file name
  size: local file size
  returned: always
  type: dict
mode:
  description: put or get
  type: str
remote_file:
  date: remote file create time
  name: remote file name
  size: remote file size
  returned: always
  type: dict
'''


import sys
import os
import re
import time
from ftplib import FTP
from functools import partial
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec
from ansible.module_utils.six import PY3


if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


def progress(total, current):
    """
    report file transfer progress
    """

    bar_length = 20
    if current >= total:
        percent = 100
        flag = bar_length * '#'
    else:
        percent = current * 100.0 / total
        flag = (int(percent) * bar_length / 100) * '#' + (int(100 - percent) * bar_length / 100) * ' '
    f = open(os.ctermid(), 'w')
    f.write("\rFile transfer progress: [%s] %d%%\r" % (flag, percent))
    f.flush()
    f.close()


def get_file_info(ftp, filename):
    """
    get file information from ftp server
    """

    fps = filename.split('/')
    if len(fps) == 1:
        fname = filename
    else:
        fname = fps[-1]
    output = StringIO()
    try:
        ftp.dir(filename, output.write)
    except Exception:
        return {}
    res = output.getvalue()
    sear = re.compile(r'\S{10}\s+\S+\s+\S+\s+\S+\s+(?P<size>\d+)\s+(?P<date>\S+\s+\S+\s+\S+)\s+(?P<name>\S+)')
    lines = res.split('\n')
    for line in lines:
        m = sear.search(line)
        if m and str(m.group('name')) == fname:
            return dict(size=int(m.group('size')),
                        date=str(m.group('date')),
                        name=filename)
    return {}


def size_format(size):
    """
    format the size to string
    """

    svaule = ' ' * 3 + str(size)
    y = len(svaule)
    values = []
    for i in range(y, 0, -3):
        values = [svaule[i:i + 3]] + values
    return ','.join(values).strip().strip(',') + ' (Byte)'


def local_file_info(filename):
    """
    get local file information
    """

    if not os.path.isfile(filename):
        return {}
    fps = filename.split('\n')
    return {'size': os.stat(filename).st_size,
            'date': time.strftime("%b %d %H:%M:%S %Y", time.localtime(os.stat(filename).st_ctime)),
            'name': fps[-1]}


def ftplib_transfer(kwargs):
    """
    use python ftp lib , and put or get file from or to ftp server.
    """

    result = {}
    server = kwargs.get('server')
    user = kwargs.get('user')
    password = kwargs.get('password')
    port = kwargs.get('port')
    mode = kwargs.get('mode')
    timeout = kwargs.get('timeout') or 60
    local_file = kwargs.get('local_file')
    remote_file = kwargs.get('remote_file')
    result['local_file'] = local_file
    result['remote_file'] = remote_file
    result['mode'] = mode
    result['changed'] = False
    try:
        ftp = FTP()
        ftp.connect(server, port, timeout=timeout)
        ftp.login(user, password)
        remote_info = get_file_info(ftp, remote_file)
        local_info = local_file_info(local_file)
        if remote_info == local_info and not local_info:
            return {'error': 'File transfer failed.Make sure that remote file or local file path or name is correct.'}
        else:
            rs = remote_info.get('size') or 0
            ls = local_info.get('size') or -1
            if mode == 'get' and ls == rs:
                return {'changed': False,
                        'msg': 'local file {0!r} is existed.'.format(local_file),
                        'remote_file': remote_info,
                        'local_file': local_info}
            elif mode == 'put' and ls == rs:
                remote_info['size'] = size_format(remote_info['size'])
                local_info['size'] = size_format(local_info['size'])
                return {'changed': False,
                        'msg': 'remote file {0!r} is existed.'.format(remote_file),
                        'remote_file': remote_info,
                        'local_file': local_info}
        if mode == 'get':
            file = open(local_file, 'wb')
            size = remote_info['size']
            c_size = [0]
            # callback, to write file data

            def save(obj):
                c_size[0] += len(obj)
                progress(size, c_size[0])
                return file.write(obj)
            ftp.retrbinary('RETR %s' % remote_file, save, 1024)
        elif mode == 'put':
            file = open(local_file, 'rb')
            size = os.stat(local_file).st_size
            send_size = [0]
            # callback, to report file transfer progress

            def report_progress(obj):
                send_size[0] += len(obj)
                progress(size, send_size[0])
            ftp.storbinary('STOR %s' % remote_file, file, 1024, report_progress)
            remote_info = get_file_info(ftp, remote_file)
    except Exception as e:
        result['error'] = str(e)
    else:
        result['changed'] = True
        file.close()
        ftp.close()
        local_info = local_file_info(local_file)
        remote_info['size'] = size_format(remote_info['size'])
        local_info['size'] = size_format(local_info['size'])
        result['local_file'] = local_info
        result['remote_file'] = remote_info
    return result


def check_parames(module):
    """
    check params
    may ftp server is same as the host, or not
    """

    kwargs = dict()
    kwargs['server'] = module.params['ftp_server'] or module.params['host']
    kwargs['user'] = module.params['ftp_user'] or module.params['username']
    kwargs['password'] = module.params['ftp_password'] or module.params['password']
    kwargs['port'] = module.params['ftp_port']
    kwargs['mode'] = module.params['mode']
    kwargs['timeout'] = module.params['timeout'] or 60
    kwargs['local_file'] = module.params['local_file']
    kwargs['remote_file'] = module.params['remote_file']
    if kwargs['server'] is None:
        module.fail_json(msg='Error: ftp server is not specified.')
    if not any([kwargs['local_file'], kwargs['remote_file']]):
        module.fail_json(msg='Error: local file or remote file is required.')
    elif kwargs['local_file'] and kwargs['remote_file'] is None:
        fname = kwargs['local_file'].split('/')
        kwargs['remote_file'] = fname[-1]
    elif kwargs['remote_file'] and kwargs['local_file'] is None:
        fname = kwargs['local_file'].split('/')
        kwargs['local_file'] = fname[-1]
    file_name = kwargs['local_file']

    return kwargs


def main():
    """Module main"""

    argument_spec = dict(
        ftp_server=dict(required=False, type='str'),
        ftp_user=dict(required=False, type='str'),
        ftp_port=dict(required=False, type='int', default=21),
        ftp_password=dict(required=False, no_log=True),
        local_file=dict(required=False, type='str'),
        remote_file=dict(required=True, type='str'),
        mode=dict(required=True, choices=['put', 'get'])
    )

    argument_spec.update(ce_argument_spec)
    module = AnsibleModule(argument_spec)
    kwargs = check_parames(module)
    result = ftplib_transfer(kwargs)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
