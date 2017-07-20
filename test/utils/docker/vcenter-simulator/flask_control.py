#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2017 James Tanner (@jctanner) <tanner.jc@gmail.com>
#          Abhijeet Kasurde (@akasurde) <akasurde@redhat.com>
#
# Written by James Tanner <tanner.jc@gmail.com>
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

import os
import psutil
import socket
import subprocess

from flask import Flask
from flask import jsonify
from flask import request


app = Flask(__name__)
GOPATH = os.path.expanduser('/opt/gocode')
VCSIMPATH = os.path.join(GOPATH, 'bin', 'vcsim')
GOVCPATH = os.path.join(GOPATH, 'bin', 'govc')
GOVCURL = None


@app.route('/')
def m_index():
    return 'vcsim controller'


@app.route('/kill/<int:number>')
def kill_one(number):
    """Kill any arbitrary process id"""

    success = False
    e = None

    try:
        p = psutil.Process(number)
        p.terminate()
        success = True
    except Exception as e:
        pass

    return jsonify({'success': success, 'e': str(e)})


@app.route('/killall')
def kill_all():
    """Kill ALL of the running vcsim pids"""

    results = []

    for x in psutil.pids():
        p = psutil.Process(x)
        if VCSIMPATH in p.cmdline():
            success = False
            e = None
            try:
                p.terminate()
                success = True
            except Exception as e:
                pass
            results.append(
                {'pid': x, 'cmdline': p.cmdline(),
                 'success': success, 'e': str(e)}
            )

    return jsonify(results)


@app.route('/spawn')
def spawn_vcsim():
    """Launch vcsim in a background process and return the pid+govcm_url"""

    global GOVCURL

    username = request.args.get('username') or 'user'
    password = request.args.get('password') or 'pass'
    hostname = request.args.get('hostname') or \
        socket.gethostbyname(socket.gethostname())
    port = request.args.get('port') or '443'
    port = int(port)

    # FIXME - enable tracing
    if request.args.get('trace'):
        trace = True
    else:
        trace = False

    # vcsim cli options and their default values
    cli_opts = [
        ['app', 0],
        ['cluster', 0],
        ['dc', 1],
        ['ds', 1],
        ['folder', 1],
        ['host', 3],
        ['pg', 1],
        ['pod', 1],
        ['pool', 1],
        ['vm', 2]
    ]

    # useful for client govc commands
    govc_url = 'https://%s:%s@%s:%s' % (username, password, hostname, port)
    GOVCURL = govc_url

    # need these to run the service
    env = {
        'GOPATH': GOPATH,
        'GOVC_URL': govc_url,
        'GOVC_INSECURE': '1'
    }

    # build the command
    cmd = [
        VCSIMPATH,
        '-httptest.serve',
        '%s:%s' % (hostname, port),
    ]
    for x in cli_opts:
        name = x[0]
        default = x[1]
        if request.args.get(name):
            default = request.args.get(name)
        cmd.append('-%s=%s' % (name, default))
    cmd = ' '.join(cmd)
    cmd += ' 2>&1 > vcsim.log'

    # run it with environment settings
    p = subprocess.Popen(
        cmd,
        env=env,
        shell=True
    )

    # return the relevant data
    pid = p.pid
    rdata = {
        'cmd': cmd,
        'pid': pid,
        'host': hostname,
        'port': port,
        'username': username,
        'password': password,
        'GOVC_URL': govc_url
    }

    return jsonify(rdata)


@app.route('/govc_find')
def govc_find():
    """Run govc find and optionally filter results"""
    ofilter = request.args.get('filter') or None
    stdout_lines = _get_all_objs(ofilter=ofilter)
    return jsonify(stdout_lines)


@app.route('/govc_vm_info')
def get_govc_vm_info():
    """Run govc vm info """
    vm_name = request.args.get('vm_name') or None
    vm_output = {}
    if vm_name:
        all_vms = [vm_name]
    else:
        # Get all VMs
        all_vms = _get_all_objs(ofilter='VM')

    for vm_name in all_vms:
        vm_info = _get_vm_info(vm_name=vm_name)
        name = vm_info.get('Name', vm_name)
        vm_output[name] = vm_info

    return jsonify(vm_output)


@app.route('/govc_host_info')
def get_govc_host_info():
    """ Run govc host.info """
    host_name = request.args.get("host_name") or None
    host_output = {}
    if host_name:
        all_hosts = [host_name]
    else:
        all_hosts = _get_all_objs(ofilter='H')
    for host_system in all_hosts:
        host_info = _get_host_info(host_name=host_system)
        name = host_info.get('Name', host_system)
        host_output[name] = host_info

    return jsonify(host_output)


def _get_host_info(host_name=None):
    """
    Get all information of host from vcsim
    :param vm_name: Name of host
    :return: Dictionary containing information about VM,
             where KEY represent attributes and VALUE represent attribute's value
    """
    cmd = '%s host.info -host=%s 2>&1' % (GOVCPATH, host_name)

    host_info = {}
    if host_name is None:
        return host_info
    host_info = parse_govc_info(cmd)

    return host_info


def _get_vm_info(vm_name=None):
    """
    Get all information of VM from vcsim
    :param vm_name: Name of VM
    :return: Dictionary containing information about VM,
             where KEY represent attributes and VALUE represent attribute's value
    """
    cmd = '%s vm.info %s 2>&1' % (GOVCPATH, vm_name)

    vm_info = {}
    if vm_name is None:
        return vm_info
    vm_info = parse_govc_info(cmd)

    return vm_info


def parse_govc_info(cmd):
    """
    Helper function to parse output of govc info commands
    :param cmd: command variable to run and parse output for
    :return: Dictionary containing information about object
    """
    so, se = run_cmd(cmd)
    stdout_lines = so.splitlines()
    info = {}
    for line in stdout_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.lstrip()
            info[key] = value.strip()

    return info


def _get_all_objs(ofilter=None):
    """
    Get all VM Objects from vcsim
    :param ofilter: Specify which object to get
    :return: list of Object specified by ofilter
    """
    cmd = '%s find ' % GOVCPATH
    filter_mapping = dict(VA='a', CCR='c', DC='d', F='f', DVP='g', H='h',
                          VM='m', N='n', ON='o', RP='p', CR='r', D='s', DVS='w')
    if ofilter:
        type_filter = filter_mapping.get(ofilter, '')
        if type_filter != '':
            cmd += '-type %s ' % type_filter

    cmd += "2>&1"
    so, se = run_cmd(cmd)
    stdout_lines = so.splitlines()
    return stdout_lines


def run_cmd(cmd):
    """
    Helper Function to run commands
    :param cmd: Command string to execute
    :return: StdOut and StdErr in string format
    """
    global GOVCURL

    env = {
        'GOPATH': GOPATH,
        'GOVC_URL': GOVCURL,
        'GOVC_INSECURE': '1'
    }

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=True
    )

    (so, se) = p.communicate()
    return so, se


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
