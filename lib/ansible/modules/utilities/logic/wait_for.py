#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: wait_for
short_description: Waits for a condition before continuing
description:
     - You can wait for a set amount of time C(timeout), this is the default if nothing is specified or just C(timeout) is specified.
       This does not produce an error.
     - Waiting for a port to become available is useful for when services are not immediately available after their init scripts return
       which is true of certain Java application servers.
     - It is also useful when starting guests with the M(virt) module and needing to pause until they are ready.
     - This module can also be used to wait for a regex match a string to be present in a file.
     - In Ansible 1.6 and later, this module can also be used to wait for a file to be available or
       absent on the filesystem.
     - In Ansible 1.8 and later, this module can also be used to wait for active connections to be closed before continuing, useful if a node
       is being rotated out of a load balancer pool.
     - For Windows targets, use the M(win_wait_for) module instead.
version_added: "0.7"
options:
  host:
    description:
      - A resolvable hostname or IP address to wait for.
    type: str
    default: 127.0.0.1
  timeout:
    description:
      - Maximum number of seconds to wait for, when used with another condition it will force an error.
      - When used without other conditions it is equivalent of just sleeping.
    type: int
    default: 300
  connect_timeout:
    description:
      - Maximum number of seconds to wait for a connection to happen before closing and retrying.
    type: int
    default: 5
  delay:
    description:
      - Number of seconds to wait before starting to poll.
    type: int
    default: 0
  port:
    description:
      - Port number to poll.
      - C(path) and C(port) are mutually exclusive parameters.
    type: int
  active_connection_states:
    description:
      - The list of TCP connection states which are counted as active connections.
    type: list
    default: [ ESTABLISHED, FIN_WAIT1, FIN_WAIT2, SYN_RECV, SYN_SENT, TIME_WAIT ]
    version_added: "2.3"
  state:
    description:
      - Either C(present), C(started), or C(stopped), C(absent), or C(drained).
      - When checking a port C(started) will ensure the port is open, C(stopped) will check that it is closed, C(drained) will check for active connections.
      - When checking for a file or a search string C(present) or C(started) will ensure that the file or string is present before continuing,
        C(absent) will check that file is absent or removed.
    type: str
    choices: [ absent, drained, present, started, stopped ]
    default: started
  path:
    description:
      - Path to a file on the filesystem that must exist before continuing.
      - C(path) and C(port) are mutually exclusive parameters.
    type: path
    version_added: "1.4"
  search_regex:
    description:
      - Can be used to match a string in either a file or a socket connection.
      - Defaults to a multiline regex.
    type: str
    version_added: "1.4"
  exclude_hosts:
    description:
      - List of hosts or IPs to ignore when looking for active TCP connections for C(drained) state.
    type: list
    version_added: "1.8"
  sleep:
    description:
      - Number of seconds to sleep between checks.
      - Before Ansible 2.3 this was hardcoded to 1 second.
    type: int
    default: 1
    version_added: "2.3"
  msg:
    description:
      - This overrides the normal error message from a failure to meet the required conditions.
    type: str
    version_added: "2.4"
notes:
  - The ability to use search_regex with a port connection was added in Ansible 1.7.
  - Prior to Ansible 2.4, testing for the absence of a directory or UNIX socket did not work correctly.
  - Prior to Ansible 2.4, testing for the presence of a file did not work correctly if the remote user did not have read access to that file.
  - Under some circumstances when using mandatory access control, a path may always be treated as being absent even if it exists, but
    can't be modified or created by the remote user either.
  - When waiting for a path, symbolic links will be followed.  Many other modules that manipulate files do not follow symbolic links,
    so operations on the path using other modules may not work exactly as expected.
seealso:
- module: wait_for_connection
- module: win_wait_for
- module: win_wait_for_process
author:
    - Jeroen Hoekx (@jhoekx)
    - John Jarvis (@jarv)
    - Andrii Radyk (@AnderEnder)
'''

EXAMPLES = r'''
- name: sleep for 300 seconds and continue with play
  wait_for:
    timeout: 300
  delegate_to: localhost

- name: Wait for port 8000 to become open on the host, don't start checking for 10 seconds
  wait_for:
    port: 8000
    delay: 10

- name: Waits for port 8000 of any IP to close active connections, don't start checking for 10 seconds
  wait_for:
    host: 0.0.0.0
    port: 8000
    delay: 10
    state: drained

- name: Wait for port 8000 of any IP to close active connections, ignoring connections for specified hosts
  wait_for:
    host: 0.0.0.0
    port: 8000
    state: drained
    exclude_hosts: 10.2.1.2,10.2.1.3

- name: Wait until the file /tmp/foo is present before continuing
  wait_for:
    path: /tmp/foo

- name: Wait until the string "completed" is in the file /tmp/foo before continuing
  wait_for:
    path: /tmp/foo
    search_regex: completed

- name: Wait until regex pattern matches in the file /tmp/foo and print the matched group
  wait_for:
    path: /tmp/foo
    search_regex: completed (?P<task>\w+)
  register: waitfor
- debug:
    msg: Completed {{ waitfor['groupdict']['task'] }}

- name: Wait until the lock file is removed
  wait_for:
    path: /var/lock/file.lock
    state: absent

- name: Wait until the process is finished and pid was destroyed
  wait_for:
    path: /proc/3466/status
    state: absent

- name: Output customized message when failed
  wait_for:
    path: /tmp/foo
    state: present
    msg: Timeout to find file /tmp/foo

# Do not assume the inventory_hostname is resolvable and delay 10 seconds at start
- name: Wait 300 seconds for port 22 to become open and contain "OpenSSH"
  wait_for:
    port: 22
    host: '{{ (ansible_ssh_host|default(ansible_host))|default(inventory_hostname) }}'
    search_regex: OpenSSH
    delay: 10
  connection: local

# Same as above but you normally have ansible_connection set in inventory, which overrides 'connection'
- name: Wait 300 seconds for port 22 to become open and contain "OpenSSH"
  wait_for:
    port: 22
    host: '{{ (ansible_ssh_host|default(ansible_host))|default(inventory_hostname) }}'
    search_regex: OpenSSH
    delay: 10
  vars:
    ansible_connection: local
'''

RETURN = r'''
elapsed:
  description: The number of seconds that elapsed while waiting
  returned: always
  type: int
  sample: 23
match_groups:
  description: Tuple containing all the subgroups of the match as returned by U(https://docs.python.org/2/library/re.html#re.MatchObject.groups)
  returned: always
  type: list
  sample: ['match 1', 'match 2']
match_groupdict:
  description: Dictionary containing all the named subgroups of the match, keyed by the subgroup name,
    as returned by U(https://docs.python.org/2/library/re.html#re.MatchObject.groupdict)
  returned: always
  type: dict
  sample:
    {
      'group': 'match'
    }
'''

import binascii
import datetime
import errno
import math
import os
import re
import select
import socket
import sys
import time
import traceback

from ansible.module_utils.basic import AnsibleModule, load_platform_subclass, missing_required_lib
from ansible.module_utils._text import to_native


HAS_PSUTIL = False
PSUTIL_IMP_ERR = None
try:
    import psutil
    HAS_PSUTIL = True
    # just because we can import it on Linux doesn't mean we will use it
except ImportError:
    PSUTIL_IMP_ERR = traceback.format_exc()


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
    ipv4_mapped_ipv6_address = {
        'prefix': '::ffff',
        'match_all': '::ffff:0.0.0.0'
    }

    def __new__(cls, *args, **kwargs):
        return load_platform_subclass(TCPConnectionInfo, args, kwargs)

    def __init__(self, module):
        self.module = module
        self.ips = _convert_host_to_ip(module.params['host'])
        self.port = int(self.module.params['port'])
        self.exclude_ips = self._get_exclude_ips()
        if not HAS_PSUTIL:
            module.fail_json(msg=missing_required_lib('psutil'), exception=PSUTIL_IMP_ERR)

    def _get_exclude_ips(self):
        exclude_hosts = self.module.params['exclude_hosts']
        exclude_ips = []
        if exclude_hosts is not None:
            for host in exclude_hosts:
                exclude_ips.extend(_convert_host_to_ip(host))
        return exclude_ips

    def get_active_connections_count(self):
        active_connections = 0
        for p in psutil.process_iter():
            if hasattr(p, 'get_connections'):
                connections = p.get_connections(kind='inet')
            else:
                connections = p.connections(kind='inet')
            for conn in connections:
                if conn.status not in self.module.params['active_connection_states']:
                    continue
                if hasattr(conn, 'local_address'):
                    (local_ip, local_port) = conn.local_address
                else:
                    (local_ip, local_port) = conn.laddr
                if self.port != local_port:
                    continue
                if hasattr(conn, 'remote_address'):
                    (remote_ip, remote_port) = conn.remote_address
                else:
                    (remote_ip, remote_port) = conn.raddr
                if (conn.family, remote_ip) in self.exclude_ips:
                    continue
                if any((
                    (conn.family, local_ip) in self.ips,
                    (conn.family, self.match_all_ips[conn.family]) in self.ips,
                    local_ip.startswith(self.ipv4_mapped_ipv6_address['prefix']) and
                        (conn.family, self.ipv4_mapped_ipv6_address['match_all']) in self.ips,
                )):
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
    ipv4_mapped_ipv6_address = {
        'prefix': '0000000000000000FFFF0000',
        'match_all': '0000000000000000FFFF000000000000'
    }
    local_address_field = 1
    remote_address_field = 2
    connection_state_field = 3

    def __init__(self, module):
        self.module = module
        self.ips = _convert_host_to_hex(module.params['host'])
        self.port = "%0.4X" % int(module.params['port'])
        self.exclude_ips = self._get_exclude_ips()

    def _get_exclude_ips(self):
        exclude_hosts = self.module.params['exclude_hosts']
        exclude_ips = []
        if exclude_hosts is not None:
            for host in exclude_hosts:
                exclude_ips.extend(_convert_host_to_hex(host))
        return exclude_ips

    def get_active_connections_count(self):
        active_connections = 0
        for family in self.source_file.keys():
            if not os.path.isfile(self.source_file[family]):
                continue
            f = open(self.source_file[family])
            for tcp_connection in f.readlines():
                tcp_connection = tcp_connection.strip().split()
                if tcp_connection[self.local_address_field] == 'local_address':
                    continue
                if (tcp_connection[self.connection_state_field] not in
                        [get_connection_state_id(_connection_state) for _connection_state in self.module.params['active_connection_states']]):
                    continue
                (local_ip, local_port) = tcp_connection[self.local_address_field].split(':')
                if self.port != local_port:
                    continue
                (remote_ip, remote_port) = tcp_connection[self.remote_address_field].split(':')
                if (family, remote_ip) in self.exclude_ips:
                    continue
                if any((
                    (family, local_ip) in self.ips,
                    (family, self.match_all_ips[family]) in self.ips,
                    local_ip.startswith(self.ipv4_mapped_ipv6_address['prefix']) and
                        (family, self.ipv4_mapped_ipv6_address['match_all']) in self.ips,
                )):
                    active_connections += 1
            f.close()
        return active_connections


def _convert_host_to_ip(host):
    """
    Perform forward DNS resolution on host, IP will give the same IP

    Args:
        host: String with either hostname, IPv4, or IPv6 address

    Returns:
        List of tuples containing address family and IP
    """
    addrinfo = socket.getaddrinfo(host, 80, 0, 0, socket.SOL_TCP)
    ips = []
    for family, socktype, proto, canonname, sockaddr in addrinfo:
        ip = sockaddr[0]
        ips.append((family, ip))
        if family == socket.AF_INET:
            ips.append((socket.AF_INET6, "::ffff:" + ip))
    return ips


def _convert_host_to_hex(host):
    """
    Convert the provided host to the format in /proc/net/tcp*

    /proc/net/tcp uses little-endian four byte hex for ipv4
    /proc/net/tcp6 uses little-endian per 4B word for ipv6

    Args:
        host: String with either hostname, IPv4, or IPv6 address

    Returns:
        List of tuples containing address family and the
        little-endian converted host
    """
    ips = []
    if host is not None:
        for family, ip in _convert_host_to_ip(host):
            hexip_nf = binascii.b2a_hex(socket.inet_pton(family, ip))
            hexip_hf = ""
            for i in range(0, len(hexip_nf), 8):
                ipgroup_nf = hexip_nf[i:i + 8]
                ipgroup_hf = socket.ntohl(int(ipgroup_nf, base=16))
                hexip_hf = "%s%08X" % (hexip_hf, ipgroup_hf)
            ips.append((family, hexip_hf))
    return ips


def _create_connection(host, port, connect_timeout):
    """
    Connect to a 2-tuple (host, port) and return
    the socket object.

    Args:
        2-tuple (host, port) and connection timeout
    Returns:
        Socket object
    """
    if sys.version_info < (2, 6):
        (family, _) = (_convert_host_to_ip(host))[0]
        connect_socket = socket.socket(family, socket.SOCK_STREAM)
        connect_socket.settimeout(connect_timeout)
        connect_socket.connect((host, port))
    else:
        connect_socket = socket.create_connection((host, port), connect_timeout)
    return connect_socket


def _timedelta_total_seconds(timedelta):
    return (
        timedelta.microseconds + 0.0 +
        (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


def get_connection_state_id(state):
    connection_state_id = {
        'ESTABLISHED': '01',
        'SYN_SENT': '02',
        'SYN_RECV': '03',
        'FIN_WAIT1': '04',
        'FIN_WAIT2': '05',
        'TIME_WAIT': '06',
    }
    return connection_state_id[state]


def main():

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', default='127.0.0.1'),
            timeout=dict(type='int', default=300),
            connect_timeout=dict(type='int', default=5),
            delay=dict(type='int', default=0),
            port=dict(type='int'),
            active_connection_states=dict(type='list', default=['ESTABLISHED', 'FIN_WAIT1', 'FIN_WAIT2', 'SYN_RECV', 'SYN_SENT', 'TIME_WAIT']),
            path=dict(type='path'),
            search_regex=dict(type='str'),
            state=dict(type='str', default='started', choices=['absent', 'drained', 'present', 'started', 'stopped']),
            exclude_hosts=dict(type='list'),
            sleep=dict(type='int', default=1),
            msg=dict(type='str'),
        ),
    )

    host = module.params['host']
    timeout = module.params['timeout']
    connect_timeout = module.params['connect_timeout']
    delay = module.params['delay']
    port = module.params['port']
    state = module.params['state']
    path = module.params['path']
    search_regex = module.params['search_regex']
    msg = module.params['msg']

    if search_regex is not None:
        compiled_search_re = re.compile(search_regex, re.MULTILINE)
    else:
        compiled_search_re = None

    match_groupdict = {}
    match_groups = ()

    if port and path:
        module.fail_json(msg="port and path parameter can not both be passed to wait_for", elapsed=0)
    if path and state == 'stopped':
        module.fail_json(msg="state=stopped should only be used for checking a port in the wait_for module", elapsed=0)
    if path and state == 'drained':
        module.fail_json(msg="state=drained should only be used for checking a port in the wait_for module", elapsed=0)
    if module.params['exclude_hosts'] is not None and state != 'drained':
        module.fail_json(msg="exclude_hosts should only be with state=drained", elapsed=0)
    for _connection_state in module.params['active_connection_states']:
        try:
            get_connection_state_id(_connection_state)
        except Exception:
            module.fail_json(msg="unknown active_connection_state (%s) defined" % _connection_state, elapsed=0)

    start = datetime.datetime.utcnow()

    if delay:
        time.sleep(delay)

    if not port and not path and state != 'drained':
        time.sleep(timeout)
    elif state in ['absent', 'stopped']:
        # first wait for the stop condition
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.utcnow() < end:
            if path:
                try:
                    if not os.access(path, os.F_OK):
                        break
                except IOError:
                    break
            elif port:
                try:
                    s = _create_connection(host, port, connect_timeout)
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except Exception:
                    break
            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])
        else:
            elapsed = datetime.datetime.utcnow() - start
            if port:
                module.fail_json(msg=msg or "Timeout when waiting for %s:%s to stop." % (host, port), elapsed=elapsed.seconds)
            elif path:
                module.fail_json(msg=msg or "Timeout when waiting for %s to be absent." % (path), elapsed=elapsed.seconds)

    elif state in ['started', 'present']:
        # wait for start condition
        end = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.utcnow() < end:
            if path:
                try:
                    os.stat(path)
                except OSError as e:
                    # If anything except file not present, throw an error
                    if e.errno != 2:
                        elapsed = datetime.datetime.utcnow() - start
                        module.fail_json(msg=msg or "Failed to stat %s, %s" % (path, e.strerror), elapsed=elapsed.seconds)
                    # file doesn't exist yet, so continue
                else:
                    # File exists.  Are there additional things to check?
                    if not compiled_search_re:
                        # nope, succeed!
                        break
                    try:
                        f = open(path)
                        try:
                            search = re.search(compiled_search_re, f.read())
                            if search:
                                if search.groupdict():
                                    match_groupdict = search.groupdict()
                                if search.groups():
                                    match_groups = search.groups()

                                break
                        finally:
                            f.close()
                    except IOError:
                        pass
            elif port:
                alt_connect_timeout = math.ceil(_timedelta_total_seconds(end - datetime.datetime.utcnow()))
                try:
                    s = _create_connection(host, port, min(connect_timeout, alt_connect_timeout))
                except Exception:
                    # Failed to connect by connect_timeout. wait and try again
                    pass
                else:
                    # Connected -- are there additional conditions?
                    if compiled_search_re:
                        data = ''
                        matched = False
                        while datetime.datetime.utcnow() < end:
                            max_timeout = math.ceil(_timedelta_total_seconds(end - datetime.datetime.utcnow()))
                            (readable, w, e) = select.select([s], [], [], max_timeout)
                            if not readable:
                                # No new data.  Probably means our timeout
                                # expired
                                continue
                            response = s.recv(1024)
                            if not response:
                                # Server shutdown
                                break
                            data += to_native(response, errors='surrogate_or_strict')
                            if re.search(compiled_search_re, data):
                                matched = True
                                break

                        # Shutdown the client socket
                        try:
                            s.shutdown(socket.SHUT_RDWR)
                        except socket.error as e:
                            if e.errno != errno.ENOTCONN:
                                raise
                        # else, the server broke the connection on its end, assume it's not ready
                        else:
                            s.close()
                        if matched:
                            # Found our string, success!
                            break
                    else:
                        # Connection established, success!
                        try:
                            s.shutdown(socket.SHUT_RDWR)
                        except socket.error as e:
                            if e.errno != errno.ENOTCONN:
                                raise
                        # else, the server broke the connection on its end, assume it's not ready
                        else:
                            s.close()
                        break

            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])

        else:   # while-else
            # Timeout expired
            elapsed = datetime.datetime.utcnow() - start
            if port:
                if search_regex:
                    module.fail_json(msg=msg or "Timeout when waiting for search string %s in %s:%s" % (search_regex, host, port), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg=msg or "Timeout when waiting for %s:%s" % (host, port), elapsed=elapsed.seconds)
            elif path:
                if search_regex:
                    module.fail_json(msg=msg or "Timeout when waiting for search string %s in %s" % (search_regex, path), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg=msg or "Timeout when waiting for file %s" % (path), elapsed=elapsed.seconds)

    elif state == 'drained':
        # wait until all active connections are gone
        end = start + datetime.timedelta(seconds=timeout)
        tcpconns = TCPConnectionInfo(module)
        while datetime.datetime.utcnow() < end:
            try:
                if tcpconns.get_active_connections_count() == 0:
                    break
            except IOError:
                pass
            # Conditions not yet met, wait and try again
            time.sleep(module.params['sleep'])
        else:
            elapsed = datetime.datetime.utcnow() - start
            module.fail_json(msg=msg or "Timeout when waiting for %s:%s to drain" % (host, port), elapsed=elapsed.seconds)

    elapsed = datetime.datetime.utcnow() - start
    module.exit_json(state=state, port=port, search_regex=search_regex, match_groups=match_groups, match_groupdict=match_groupdict, path=path,
                     elapsed=elapsed.seconds)


if __name__ == '__main__':
    main()
