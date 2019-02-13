# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # inventory cache
    DOCUMENTATION = r'''
options:
  cache:
    description:
      - Toggle to enable/disable the caching of the inventory's source data, requires a cache plugin setup to work.
    type: bool
    default: no
    env:
      - name: ANSIBLE_INVENTORY_CACHE
    ini:
      - section: inventory
        key: cache
  cache_plugin:
    description:
      - Cache plugin to use for the inventory's source data.
    type: str
    env:
      - name: ANSIBLE_INVENTORY_CACHE_PLUGIN
    ini:
      - section: inventory
        key: cache_plugin
  cache_timeout:
    description:
      - Cache duration in seconds
    default: 3600
    type: int
    env:
      - name: ANSIBLE_INVENTORY_CACHE_TIMEOUT
    ini:
      - section: inventory
        key: cache_timeout
  cache_connection:
    description:
      - Cache connection data or path, read cache plugin documentation for specifics.
    type: str
    env:
      - name: ANSIBLE_INVENTORY_CACHE_CONNECTION
    ini:
      - section: inventory
        key: cache_connection
'''
