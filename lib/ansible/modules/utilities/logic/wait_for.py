#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
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

import socket
import datetime
import time
import sys
import re
import binascii

HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
    # just because we can import it on Linux doesn't mean we will use it
except ImportError:
    pass

DOCUMENTATION = '''
---
module: wait_for
short_description: Waits for a condition before continuing.
description:
     - Waiting for a port to become available is useful for when services 
       are not immediately available after their init scripts return - 
       which is true of certain Java application servers. It is also 
       useful when starting guests with the M(virt) module and
       needing to pause until they are ready. 
     - This module can also be used to wait for a regex match a string to be present in a file.
     - In 1.6 and later, this module can 
       also be used to wait for a file to be available or absent on the 
       filesystem.
     - In 1.8 and later, this module can also be used to wait for active
       connections to be closed before continuing, useful if a node
       is being rotated out of a load balancer pool.
version_added: "0.7"
options:
  host:
    description:
      - hostname or IP address to wait for
    required: false
    default: "127.0.0.1"
    aliases: []
  timeout:
    description:
      - maximum number of seconds to wait for
    required: false
    default: 300
  delay:
    description:
      - number of seconds to wait before starting to poll
    required: false
    default: 0
  port:
    description:
      - port number to poll
    required: false
  state:
    description:
      - either C(present), C(started), or C(stopped), C(absent), or C(drained)
      - When checking a port C(started) will ensure the port is open, C(stopped) will check that it is closed, C(drained) will check for active connections
      - When checking for a file or a search string C(present) or C(started) will ensure that the file or string is present before continuing, C(absent) will check that file is absent or removed
    choices: [ "present", "started", "stopped", "absent", "drained" ]
    default: "started"
  path:
    version_added: "1.4"
    required: false
    description:
      - path to a file on the filesytem that must exist before continuing
  search_regex:
    version_added: "1.4"
    required: false
    description:
      - Can be used to match a string in either a file or a socket connection. Defaults to a multiline regex.
  exclude_hosts:
    version_added: "1.8"
    required: false
    description:
      - list of hosts or IPs to ignore when looking for active TCP connections for C(drained) state
notes:
  - The ability to use search_regex with a port connection was added in 1.7.
requirements: []
author: Jeroen Hoekx, John Jarvis, Andrii Radyk
'''

EXAMPLES = '''

# wait 300 seconds for port 8000 to become open on the host, don't start checking for 10 seconds
- wait_for: port=8000 delay=10

# wait 300 seconds for port 8000 of any IP to close active connections, don't start checking for 10 seconds
- wait_for: host=0.0.0.0 port=8000 delay=10 state=drained

# wait 300 seconds for port 8000 of any IP to close active connections, ignoring connections for specified hosts
- wait_for: host=0.0.0.0 port=8000 state=drained exclude_hosts=10.2.1.2,10.2.1.3

# wait until the file /tmp/foo is present before continuing
- wait_for: path=/tmp/foo

# wait until the string "completed" is in the file /tmp/foo before continuing
- wait_for: path=/tmp/foo search_regex=completed

# wait until the lock file is removed
- wait_for: path=/var/lock/file.lock state=absent 

# wait until the process is finished and pid was destroyed
- wait_for: path=/proc/3466/status state=absent

# Wait 300 seconds for port 22 to become open and contain "OpenSSH", don't start checking for 10 seconds
- local_action: wait_for port=22 host="{{ inventory_hostname }}" search_regex=OpenSSH delay=10

'''

class TCPConnectionInfo(object):
    """
    This is a generic TCP Connection Info strategy class that relies
    on the psutil module, which is not ideal for targets, but necessary
    for cross platform support.

    A subclass may wish to override some or all of these methods.
      - _get_exclude_ips()
      - get_active_connections()

    All subclasses MUST define platform and distribution (which may be None).
    """
    platform = 'Generic'
    distribution = None

    match_all_ips = {
        socket.AF_INET: '0.0.0.0',
        socket.AF_INET6: '::',
    }
    connection_states = {
        '01': 'ESTABLISHED',
        '02': 'SYN_SENT',
        '03': 'SYN_RECV',
        '04': 'FIN_WAIT1',
        '05': 'FIN_WAIT2',
        '06': 'TIME_WAIT',
    }

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(TCPConnectionInfo, args, kwargs)

    def __init__(self, module):
        self.module = module
        (self.family, self.ip) = _convert_host_to_ip(self.module.params['host'])
        self.port = int(self.module.params['port'])
        self.exclude_ips = self._get_exclude_ips()
        if not HAS_PSUTIL:
            module.fail_json(msg="psutil module required for wait_for")

    def _get_exclude_ips(self):
        if self.module.params['exclude_hosts'] is None:
            return []
        exclude_hosts = self.module.params['exclude_hosts']
        return [ _convert_host_to_hex(h)[1] for h in exclude_hosts ]

    def get_active_connections_count(self):
        active_connections = 0
        for p in psutil.process_iter():
            connections = p.get_connections(kind='inet')
            for conn in connections:
                if conn.status not in self.connection_states.values():
                    continue
                (local_ip, local_port) = conn.local_address
                if self.port == local_port and self.ip in [self.match_all_ips[self.family], local_ip]:
                     (remote_ip, remote_port) = conn.remote_address
                     if remote_ip not in self.exclude_ips:
                         active_connections += 1
        return active_connections


# ===========================================
# Subclass: Linux

class LinuxTCPConnectionInfo(TCPConnectionInfo):
    """
    This is a TCP Connection Info evaluation strategy class
    that utilizes information from Linux's procfs. While less universal,
    does allow Linux targets to not require an additional library.
    """
    platform = 'Linux'
    distribution = None

    source_file = {
        socket.AF_INET: '/proc/net/tcp',
        socket.AF_INET6: '/proc/net/tcp6'
    }
    match_all_ips = {
        socket.AF_INET: '00000000',
        socket.AF_INET6: '00000000000000000000000000000000',
    }
    local_address_field = 1
    remote_address_field = 2
    connection_state_field = 3

    def __init__(self, module):
        self.module = module
        (self.family, self.ip) = _convert_host_to_hex(module.params['host'])
        self.port = "%0.4X" % int(module.params['port'])
        self.exclude_ips = self._get_exclude_ips()

    def _get_exclude_ips(self):
        if self.module.params['exclude_hosts'] is None:
            return []
        exclude_hosts = self.module.params['exclude_hosts']
        return [ _convert_host_to_hex(h) for h in exclude_hosts ]

    def get_active_connections_count(self):
        active_connections = 0
        f = open(self.source_file[self.family])
        for tcp_connection in f.readlines():
            tcp_connection = tcp_connection.strip().split()
            if tcp_connection[self.local_address_field] == 'local_address':
                continue
            if tcp_connection[self.connection_state_field] not in self.connection_states:
                continue
            (local_ip, local_port) = tcp_connection[self.local_address_field].split(':')
            if self.port == local_port and self.ip in [self.match_all_ips[self.family], local_ip]:
                 (remote_ip, remote_port) = tcp_connection[self.remote_address_field].split(':')
                 if remote_ip not in self.exclude_ips:
                     active_connections += 1
        f.close()
        return active_connections


def _convert_host_to_ip(host):
    """
    Perform forward DNS resolution on host, IP will give the same IP

    Args:
        host: String with either hostname, IPv4, or IPv6 address

    Returns:
        Tuple containing address family and IP
    """
    addrinfo = socket.getaddrinfo(host, 80, 0, 0, socket.SOL_TCP)[0]
    return (addrinfo[0], addrinfo[4][0])

def _convert_host_to_hex(host):
    """
    Convert the provided host to the format in /proc/net/tcp*

    /proc/net/tcp uses little-endian four byte hex for ipv4
    /proc/net/tcp6 uses little-endian per 4B word for ipv6

    Args:
        host: String with either hostname, IPv4, or IPv6 address

    Returns:
        Tuple containing address family and the little-endian converted host
    """
    (family, ip) = _convert_host_to_ip(host)
    hexed = binascii.hexlify(socket.inet_pton(family, ip)).upper()
    if family == socket.AF_INET:
        hexed = _little_endian_convert_32bit(hexed)
    elif family == socket.AF_INET6:
        # xrange loops through each 8 character (4B) set in the 128bit total
        hexed = "".join([ _little_endian_convert_32bit(hexed[x:x+8]) for x in xrange(0, 32, 8) ])
    return (family, hexed)

def _little_endian_convert_32bit(block):
    """
    Convert to little-endian, effectively transposing
    the order of the four byte word
    12345678 -> 78563412

    Args:
        block: String containing a 4 byte hex representation

    Returns:
        String containing the little-endian converted block
    """
    # xrange starts at 6, and increments by -2 until it reaches -2
    # which lets us start at the end of the string block and work to the begining
    return "".join([ block[x:x+2] for x in xrange(6, -2, -2) ])

def main():

    module = AnsibleModule(
        argument_spec = dict(
            host=dict(default='127.0.0.1'),
            timeout=dict(default=300),
            connect_timeout=dict(default=5),
            delay=dict(default=0),
            port=dict(default=None),
            path=dict(default=None),
            search_regex=dict(default=None),
            state=dict(default='started', choices=['started', 'stopped', 'present', 'absent', 'drained']),
            exclude_hosts=dict(default=None, type='list')
        ),
    )

    params = module.params

    host = params['host']
    timeout = int(params['timeout'])
    connect_timeout = int(params['connect_timeout'])
    delay = int(params['delay'])
    if params['port']:
        port = int(params['port'])
    else:
        port = None
    state = params['state']
    path = params['path']
    search_regex = params['search_regex']

    if port and path:
        module.fail_json(msg="port and path parameter can not both be passed to wait_for")
    if path and state == 'stopped':
        module.fail_json(msg="state=stopped should only be used for checking a port in the wait_for module")
    if path and state == 'drained':
        module.fail_json(msg="state=drained should only be used for checking a port in the wait_for module")
    if params['exclude_hosts'] is not None and state != 'drained':
        module.fail_json(msg="exclude_hosts should only be with state=drained")

    start = datetime.datetime.now()

    if delay:
        time.sleep(delay)

    if state in [ 'stopped', 'absent' ]:
        ### first wait for the stop condition
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.now() < end:
            if path:
                try:
                    f = open(path)
                    f.close()
                    time.sleep(1)
                    pass
                except IOError:
                    break
            elif port:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(connect_timeout)
                try:
                    s.connect( (host, port) )
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                    time.sleep(1)
                except:
                    break
        else:
            elapsed = datetime.datetime.now() - start
            if port:
                module.fail_json(msg="Timeout when waiting for %s:%s to stop." % (host, port), elapsed=elapsed.seconds)
            elif path:
                module.fail_json(msg="Timeout when waiting for %s to be absent." % (path), elapsed=elapsed.seconds)

    elif state in ['started', 'present']:
        ### wait for start condition
        end = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() < end:
            if path:
                try:
                    os.stat(path)
                    if search_regex:
                        try:
                            f = open(path)
                            try:
                                if re.search(search_regex, f.read(), re.MULTILINE):
                                    break
                                else:
                                    time.sleep(1)
                            finally:
                                f.close()
                        except IOError:
                            time.sleep(1)
                            pass
                    else:
                        break
                except OSError, e:
                    # File not present
                    if e.errno == 2:
                        time.sleep(1)
                    else:
                        elapsed = datetime.datetime.now() - start
                        module.fail_json(msg="Failed to stat %s, %s" % (path, e.strerror), elapsed=elapsed.seconds)
            elif port:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(connect_timeout)
                try:
                    s.connect( (host, port) )
                    if search_regex:
                        data = ''
                        matched = False
                        while 1:
                            data += s.recv(1024)
                            if not data:
                                break
                            elif re.search(search_regex, data, re.MULTILINE):
                                matched = True
                                break
                        if matched:
                            s.shutdown(socket.SHUT_RDWR)
                            s.close()
                            break
                    else:
                        s.shutdown(socket.SHUT_RDWR)
                        s.close()
                        break
                except:
                    time.sleep(1)
                    pass
        else:
            elapsed = datetime.datetime.now() - start
            if port:
                if search_regex:
                    module.fail_json(msg="Timeout when waiting for search string %s in %s:%s" % (search_regex, host, port), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg="Timeout when waiting for %s:%s" % (host, port), elapsed=elapsed.seconds)
            elif path:
                if search_regex:
                    module.fail_json(msg="Timeout when waiting for search string %s in %s" % (search_regex, path), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg="Timeout when waiting for file %s" % (path), elapsed=elapsed.seconds)

    elif state == 'drained':
        ### wait until all active connections are gone
        end = start + datetime.timedelta(seconds=timeout)
        tcpconns = TCPConnectionInfo(module)
        while datetime.datetime.now() < end:
            try:
                if tcpconns.get_active_connections_count() == 0:
                    break
            except IOError:
                pass
            time.sleep(1)
        else:
            elapsed = datetime.datetime.now() - start
            module.fail_json(msg="Timeout when waiting for %s:%s to drain" % (host, port), elapsed=elapsed.seconds)

    elapsed = datetime.datetime.now() - start
    module.exit_json(state=state, port=port, search_regex=search_regex, path=path, elapsed=elapsed.seconds)

# import module snippets
from ansible.module_utils.basic import *
main()
