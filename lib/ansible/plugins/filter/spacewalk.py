# (c) 2017, Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import errors
from ansible.module_utils.six.moves import xmlrpc_client

DOCUMENTATION = """
    filter: spacewalk
    author: Tim Rightnour <thegarbledone@gmail.com>
    version_added: "2.5"
    short_description: Translate hostnames from spacewalk/Satellite 5
    description:
        - Searches for a hostname, or partial hostname in spacewalk.
        - Can return the spacewalk hostname, ip, system ID, or full record.
    options:
      _terms:
        description: hostnames to lookup
        required: true
      saturl:
        description: The URL of the spacwalk server API
        required: true
      user:
        description: user to connect to spacewalk as
        required: true
      password:
        description: password for spacewalk user
        required: true
    notes:
      - If there are multiple matches for the hostname, this filter will
        return "ENOTUNIQ".
"""

EXAMPLES = """
"{{ansible_hostname | spacewalk_hostname(saturl=http://sat/rpc/api, user=satuser, password=password) }}"
"{{ansible_hostname | spacewalk_sysid(saturl=http://sat/rpc/api, user=satuser, password=password) }}"
"{{ansible_hostname | spacewalk_ip(saturl=http://sat/rpc/api, user=satuser, password=password) }}"
"{{ansible_hostname | spacewalk_record(saturl=http://sat/rpc/api, user=satuser, password=password) }}"
"""

RETURN = """
  _raw:
    description: Translated data
"""


def spacewalk_connect(kwargs):
    saturl = kwargs.get('saturl')
    password = kwargs.get('password')
    user = kwargs.get('user')

    sw_conn = dict()
    if password is None or saturl is None or user is None:
        raise errors.AnsibleFilterError('password, saturl and user are required values')
    try:
        sw_conn['client'] = xmlrpc_client.Server(saturl)
        sw_conn['session'] = sw_conn['client'].auth.login(user, password)
    except Exception as e:
        raise errors.AnsibleFilterError('Unable to login to spacwalk/satellite server: {}'.format(str(e)))

    return sw_conn


def spacewalk_hostname(term, **kwargs):
    sw = spacewalk_connect(kwargs)
    systems = sw['client'].system.search.hostname(sw['session'], term)

    if len(systems) > 1:
        return "ENOTUNIQ"

    # return the first (and only) match
    for system in systems:
        hostname = system.get('name')
        sw['client'].auth.logout(sw['session'])
        return hostname


def spacewalk_sysid(term, **kwargs):
    sw = spacewalk_connect(kwargs)
    systems = sw['client'].system.search.hostname(sw['session'], term)

    if len(systems) > 1:
        return "ENOTUNIQ"

    # return the first (and only) match
    for system in systems:
        id = system.get('id')
        sw['client'].auth.logout(sw['session'])
        return id


def spacewalk_ip(term, **kwargs):
    sw = spacewalk_connect(kwargs)
    systems = sw['client'].system.search.hostname(sw['session'], term)

    if len(systems) > 1:
        return "ENOTUNIQ"

    # return the first (and only) match
    for system in systems:
        ip = system.get('ip')
        sw['client'].auth.logout(sw['session'])
        return ip


def spacewalk_record(term, **kwargs):
    sw = spacewalk_connect(kwargs)
    systems = sw['client'].system.search.hostname(sw['session'], term)

    if len(systems) > 1:
        return "ENOTUNIQ"

    # return the first (and only) match
    for system in systems:
        sw['client'].auth.logout(sw['session'])
        return system


# Declare the available filters to Ansible:
class FilterModule(object):
    def filters(self):
        return {
            'spacewalk_hostname': spacewalk_hostname,
            'spacewalk_sysid': spacewalk_sysid,
            'spacewalk_id': spacewalk_sysid,
            'spacewalk_ip': spacewalk_ip,
            'spacewalk_record': spacewalk_record,
        }
