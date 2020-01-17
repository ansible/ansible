# -*- coding: utf-8 -*-
# Copyright (c) 2020 Christian Felder <webmaster@bsm-felder.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
    name: freeipa_ldap3_orm
    plugin_type: inventory
    author:
      - Christian Felder <webmaster@bsm-felder.de>
    short_description: Ansible dynamic inventory plugin for ipaHostGroups.
    description:
      - Creates inventory from ipaHostGroup entries.
      - Uses ldap3_orm configuration files.
    requirements:
    - "ldap3_orm >= 2.6.0"
"""

EXAMPLES = """
# Reuses existing ldap3_orm configuration files
# see: :py:class:`~ldap3_orm.config.config` for more details
# example configuration file (needs keyring module), e.g.
# ~/.config/ldap3-orm/default

url = "ldaps://ldap.example.com"
base_dn = "cn=accounts,dc=example,dc=com"

connconfig = dict(
    user = "uid=guest,cn=users,cn=accounts,dc=example,dc=com",
    password = keyring,
)
"""


from ldap3_orm import ObjectDef, Reader
from ldap3_orm._config import read_config, config

from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):

    NAME = "freeipa_ldap3_orm"

    def verify_file(self, path):
        # the following commands may raise an exception otherwise return True
        cfg = read_config(path)
        config.apply(cfg)
        return True

    def parse(self, inventory, loader, path, cache=True):
        BaseInventoryPlugin.parse(self, inventory, loader, path, cache)
        # late import to create connection in respect to loaded config
        from ldap3_orm.connection import conn

        r = Reader(conn, ObjectDef("ipaHostGroup", conn),
                   config.userconfig.get("hostgroup_base_dn",
                                         "cn=hostgroups," + config.base_dn))
        for hg in r.search():
            group = self.inventory.add_group(hg.cn.value)
            for dn in hg.member:
                host = dn.split(',')[0].replace("fqdn=", '')
                self.inventory.add_host(host, group)
