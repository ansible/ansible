#!/usr/bin/env python

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

    global GOVCURL

    ofilter = request.args.get('filter') or None

    env = {
        'GOPATH': GOPATH,
        'GOVC_URL': GOVCURL,
        'GOVC_INSECURE': '1'
    }

    cmd = '%s find 2>&1' % GOVCPATH

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=True
    )

    (so, se) = p.communicate()
    stdout_lines = so.split('\n')

    if ofilter:
        stdout_lines = [x for x in stdout_lines if ofilter in x]

    return jsonify(stdout_lines)


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
