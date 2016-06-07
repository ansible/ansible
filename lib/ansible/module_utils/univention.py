#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
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


"""univention corporate server access module"""

try:
    import univention.uldap
    import univention.config_registry
    import univention.admin.uldap
    import univention.admin.objects
    import univention.admin.config
    import re
    import thread
    import ldap as orig_ldap
    has_lib_univention = True
except ImportError:
    has_lib_univention = False

__all__ = [
    'ldap_search',
    'config_registry',
    'base_dn',
    'ldap',
    'config',
    'position_base_dn',
    'get_umc_admin_objects',
]

config_registry = univention.config_registry.ConfigRegistry()
config_registry.load()
base_dn         = config_registry["ldap/base"]

try:
    secret_file = open('/etc/ldap.secret', 'r')
    bind_dn     = 'cn=admin,{}'.format(base_dn)
except IOError:  # pragma: no cover
    secret_file = open('/etc/machine.secret', 'r')
    bind_dn     = config_registry["ldap/hostdn"]
pwd_line        = secret_file.readline()
pwd             = re.sub('\n', '', pwd_line)

ldap = univention.admin.uldap.access(
    host      = config_registry['ldap/master'],
    base      = base_dn,
    binddn    = bind_dn,
    bindpw    = pwd,
    start_tls = 1
)
config = univention.admin.config.config()
univention.admin.modules.update()
position_base_dn = univention.admin.uldap.position(base_dn)
modules_by_name = {}


def ldap_dn_tree_parent(dn, count=1):
    dn_array = dn.split(',')
    dn_array[0:count] = []
    return ','.join(dn_array)


def ldap_search(filter, base=base_dn, attr=None):
    """Replaces uldaps search and uses a generator.
   !! Arguments are not the same."""
    msgid = ldap.lo.lo.search(
        base,
        orig_ldap.SCOPE_SUBTREE,
        filterstr=filter,
        attrlist=attr
    )
    # I used to have a try: finally: here but there seems to be a bug in python
    # which swallows the KeyboardInterrupt
    # The abandon now doesn't make too much sense
    while True:
        result_type, result_data = ldap.lo.lo.result(msgid, all=0)
        if not result_data:
            break
        if result_type is orig_ldap.RES_SEARCH_RESULT:  # pragma: no cover
            break
        else:
            if result_type is orig_ldap.RES_SEARCH_ENTRY:
                for res in result_data:
                    yield res
    ldap.lo.lo.abandon(msgid)


def module_name(module_name_):
    """Returns an initialized UMC module, identified by the given name.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   If the module does not exist, a KeyError is raised.

   The modules are cached, so they won't be re-initialized
   in subsequent calls.
   """

    if module_name_ not in modules_by_name:
        module = univention.admin.modules.get(module_name_)
        univention.admin.modules.init(ldap, position_base_dn, module)

        modules_by_name[module_name_] = module

    return modules_by_name[module_name_]


def get_umc_admin_objects():
    """Convenience accessor for getting univention.admin.objects.

   This implements delayed importing, so the univention.* modules
   are not loaded until this function is called.
   """
    return univention.admin.objects


def umc_module_for_add(module, container_dn, superordinate=None):
    """Returns an UMC module object prepared for creating a new entry.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   The container_dn MUST be the dn of the container (not of the object to
   be created itself!).
   """
    mod = module_name(module)

    position = position_base_dn
    position.setDn(container_dn)

    # config, ldap objects from common module
    obj = mod.object(config, ldap, position, superordinate=superordinate)
    obj.open()

    return obj


def umc_module_for_edit(module, object_dn, superordinate=None):
    """Returns an UMC module object prepared for editing an existing entry.

   The module is a module specification according to the udm commandline.
   Example values are:
       * users/user
       * shares/share
       * groups/group

   The object_dn MUST be the dn of the object itself, not the container!
   """
    mod = module_name(module)

    objects = get_umc_admin_objects()

    position = position_base_dn
    position.setDn(ldap_dn_tree_parent(object_dn))

    obj = objects.get(
        mod,
        config,
        ldap,
        position=position,
        superordinate=superordinate,
        dn=object_dn
    )
    obj.open()

    return obj


def create_containers_and_parents(container_dn):
    """Create a container and if needed the parents containers"""
    import univention.admin.uexceptions as uexcp
    assert container_dn.startswith("cn=")
    try:
        parent = ldap_dn_tree_parent(container_dn)
        obj = umc_module_for_add(
            'container/cn',
            parent
        )
        obj['name'] = container_dn.split(',')[0].split('=')[1]
        obj['description'] = "container created by import"
    except uexcp.ldapError:
        create_containers_and_parents(parent)
        obj = umc_module_for_add(
            'container/cn',
            parent
        )
        obj['name'] = container_dn.split(',')[0].split('=')[1]
        obj['description'] = "container created by import"

