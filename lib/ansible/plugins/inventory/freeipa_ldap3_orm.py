# -*- coding: utf-8 -*-

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
