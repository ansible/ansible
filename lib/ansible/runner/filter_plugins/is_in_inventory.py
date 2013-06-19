# (c) 2013, Trbs <trbs@trbs.net>
# License: GPLv3
DOCUMENTATION = """
---
plugin: filter
short_description: Boolean match to see if value matches the current inventory
description:
    - "This filter will operate on a hostname, groupname of list of them."
    - "It will return True or False based on weather or not the input matches with the current inventory."
"""
EXAMPLES = """
- vars:
    my_groups:
      - name: group1
        gid: 2001
        servers:
          - server1
          - server2
          - eastcoast
      - name: group2
        gid: 2002
        servers:
          - eastcoast

- name: Ensure some groups exist
  action: group name={{ item.name }} gid={{ item.gid }} state=present
  with_items: $my_groups
  when: item.servers|is_in_inventory()

# group1 will be created on 'server1', 'server2' and group 'eastcoast'
# group2 will be created on all servers in group 'eastcoast' only
"""


from jinja2 import contextfilter, Undefined
from ansible import errors

@contextfilter
def is_in_inventory(ctx, list_or_host):
    """ is_in_inventory matched a hostname, groupname or list of them to the current inventory. """
    if list_or_host is None or isinstance(list_or_host, Undefined):
        return False
    if isinstance(list_or_host, basestring):
        list_or_host = [list_or_host]
    if not isinstance(list_or_host, (tuple, list)):
        raise errors.AnsibleError("|failed expects list or string, should be a hostname or groupname or list them")

    inventory_hostname = ctx['inventory_hostname']
    for item in list_or_host:
        if item == inventory_hostname:
            return True

    group_names = ctx['group_names']
    if not 'all' in group_names:
        group_names.append('all')
    for item in list_or_host:
        if item in group_names:
            return True

    return False

class FilterModule(object):
    """ Ansible is_in_inventory filter module """
    def filters(self):
        return {
            'is_in_inventory': is_in_inventory,
        }

