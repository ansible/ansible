# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    name: active_directory
    plugin_type: inventory
    short_description: Active Directory inventory source
    requirements:
        - ldap3
    extends_documentation_fragment:
        - inventory_cache
    description:
        - Get inventory hosts from Active Directory
        - Uses a YAML configuration file that ends with C(active_directory.(yml|yaml)).
    author:
        - Syed Junaid Ali (@junaidali)
    options:
        username:
          description: The active directory user name used for querying computer objects
          type: string
          required: True
        password:
          description: 
            - The active directory user's password used for querying computer objects
            - It is recommended to use ansible vault to keep the password secret since ansible-inventory command supports ansible vault
          type: string
          required: True
        use_ssl: 
          description: The LDAP connection to active directory domain controllers uses SSL by default. If you have a need to disable SSL for troubleshooting purposes you can disable it by setting this parameter to no. It is highly recommended to use SSL to protect your credential over the wire.
          type: boolean
          default: yes
        domain_controllers:
          description: The list of domain controllers used for querying computer information
          type: list
          default: []
          required: True
        organizational_units:
          description: The list of organizational units (OU's) to be searched for computer objects within the active directory domain
          type: list
          default: []
          required: True
        last_activity:
          description:
            - This setting determines the number of days that are tolerated for a given computer to be considered active
            - It uses the lastLogonTimeStamp active directory attribute to determine if the computer was active within this timeframe
          type: number
          default: 90
        import_disabled:
          description: Forces importing disabled computer objects
          type: boolean
          default: no
        import_computer_groups:
          description: Imports computer groups as ansible inventory host groups
          type: boolean
          default: no
        import_organizational_units_as_inventory_groups:
          description: 
            - Imports organizational units as inventory groups
            - based on the organizational_units list specified, it creates the top level OU as the top level inventory group
            - e.g. if the organizational_units list contains "OU=Devices,DC=ansible,DC=local" there would be an inventory group "Devices" containing all the computer objects.
            - Nested OU's are supported and will be created as nested inventory groups
          type: boolean
          default: yes
"""

EXAMPLES = """
# Fetch all hosts in the active directory domain
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
username: DOMAIN\\username
password: sup3rs3cr3t
organizational_units:
  - dc=ansible,dc=local


# Fetch all hosts in the active directory domain use two domain controllers
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
  - dc2.ansible.local
username: DOMAIN\\username
password: sup3rs3cr3t
organizational_units:
  - dc=ansible,dc=local

# Fetch all hosts within specific organizational unit
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
organizational_units:
  - ou=servers,dc=ansible,dc=local
  - ou=desktops,dc=ansible,dc=local
username: DOMAIN\\username
password: sup3rs3cr3t

# Fetch all hosts within specific organizational unit and last login activity within 60 days
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
organizational_units:
  - ou=servers,dc=ansible,dc=local
  - ou=desktops,dc=ansible,dc=local
last_activity: 60
username: DOMAIN\\username
password: sup3rs3cr3t

# Fetch all hosts within specific organizational unit, even disabled accounts
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
organizational_units:
  - ou=servers,dc=ansible,dc=local
  - ou=desktops,dc=ansible,dc=local
import_disabled: true
username: DOMAIN\\username
password: sup3rs3cr3t

# Fetch all hosts within specific organizational unit along with computer groups
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
organizational_units:
  - ou=servers,dc=ansible,dc=local
  - ou=desktops,dc=ansible,dc=local
username: DOMAIN\\username
password: sup3rs3cr3t
import_computer_groups: yes

# Fetch all hosts within specific organizational unit but do not create inventory host groups using organizational unit heirarchy
plugin: active_directory
domain_controllers:
  - dc1.ansible.local
organizational_units:
  - ou=servers,dc=ansible,dc=local
  - ou=desktops,dc=ansible,dc=local
username: DOMAIN\\username
password: sup3rs3cr3t
import_organizational_units_as_inventory_groups: no
"""

from re import sub, match
from datetime import datetime, timezone

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.utils.display import Display

display = Display()

try:
    from ldap3 import Server, ServerPool, Connection, ALL, SUBTREE, BASE, ALL_ATTRIBUTES
    from ldap3.core.exceptions import LDAPException
except ImportError:
    raise AnsibleError("the active_directory dynamic inventory plugin requires ldap3")


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """ Host inventory parser for ansible using active directory as source. """

    NAME = "active_directory"

    def __init__(self):
        super(InventoryModule, self).__init__()

        # set default values for parameters
        display.verbose("initializing active_directory inventory plugin")
        self.user_name = None
        self.user_password = None
        self.domain_controllers = []
        self.use_ssl = True
        self.import_organizational_units_as_inventory_groups = True
        self.last_activity = 90
        self.import_disabled = False
        self.import_computer_groups = False
        self.query_page_size = 1000

    def _init_data(self):
        """
        :param config_data: contents of the inventory config file
        """
        try:
            self.user_name = self.get_option("username")
        except:
            raise AnsibleError("insufficient credentials found")

        try:
            self.user_password = self.get_option("password")
        except:
            raise AnsibleError("insufficient credentials found")

        try:
            self.domain_controllers = self.get_option("domain_controllers")
        except:
            raise AnsibleError("domain controllers list is empty")

        try:
            self.use_ssl = self.get_option("use_ssl")
        except:
            pass

        try:
            self.import_organizational_units_as_inventory_groups = self.get_option(
                "import_organizational_units_as_inventory_groups"
            )
        except:
            pass

        try:
            self.last_activity = self.get_option("last_activity")
        except:
            pass

        try:
            self.import_disabled = self.get_option("import_disabled")
        except:
            pass

        try:
            self.import_computer_groups = self.get_option("import_computer_groups")
        except:
            pass

        display.verbose("credentials: username - " + self.user_name)

    def _ldap3_conn(self):
        """
        establishes an ldap connection and returns the connection object
        """
        display.verbose("initializing ldap connection")
        if self.user_name == None or self.user_password == None:
            raise AnsibleError("insufficient credentials found")

        if len(self.domain_controllers) > 1:
            display.verbose(
                "creating server connection pool to %s" % self.domain_controllers
            )
            server = ServerPool()
            for dc in self.domain_controllers:
                server.add(Server(host=dc, use_ssl=self.use_ssl))
        elif len(self.domain_controllers) == 1:
            display.verbose(
                "creating single server connection to %s" % self.domain_controllers[0]
            )
            try:
                server = Server(host=self.domain_controllers[0], use_ssl=self.use_ssl)
            except:
                raise AnsibleError(
                    "could not establish connection to domain controller"
                )
        else:
            raise AnsibleError("no domain controller specified")
        display.verbose("initializing connection using server url %s" % server)
        try:
            connection = Connection(
                server=server,
                user=self.user_name,
                password=self.user_password,
                auto_bind=True,
            )
        except LDAPException as err:
            raise AnsibleError("could not connect to domain controller")
        return connection

    def _query(self, connection, path, no_subtree=False):
        """
        queries active directory and returns records using a generator
        :param connection: the ldap3 connection object
        :param path: the ldap path to query
        :param no_subtree: limit search to path only, do not include subtree
        """

        display.verbose("running search query to find computers at path " + path)
        search_scope = BASE if no_subtree else SUBTREE
        try:
            entry_generator = connection.extend.standard.paged_search(
                search_base=path,
                search_filter="(objectclass=computer)",
                attributes=ALL_ATTRIBUTES,
                search_scope=search_scope,
                paged_size=self.query_page_size,
            )
        except LDAPException as err:
            raise AnsibleError("could not retrieve computer objects %s", err)

        for entry in entry_generator:
            display.debug("processing entry for yield " + str(entry))
            if entry["type"] == "searchResEntry":
                if (
                    "msDS-GroupManagedServiceAccount"
                    not in entry["attributes"]["objectClass"]
                ):
                    yield entry
                else:
                    display.warning(
                        "skipping managed service account " + str(entry["dn"])
                    )
            else:
                display.warning("could not yield " + str(entry))

    def _get_hostname(self, entry, hostnames=None):
        """
        :param entry: a ldap3 entry object returned by ldap3 search
        :param hostnames: a list of hostname destination variables in order of preference
        :return the preferred identifer for the host
        """
        if not hostnames:
            hostnames = ["dNSHostName", "name"]

        hostname = ""
        for preference in hostnames:
            try:
                hostname = entry["attributes"][preference]
                break
            except:
                pass

        return to_text(hostname.lower())

    def _get_safe_group_name(self, group_name):
        """
        :param group_name: the name of ansible inventory group you need to sanitize
        :returns the sanitized ansible inventory group name
        """
        sanitized_name = sub("-", "_", group_name)
        sanitized_name = sub("\\s", "_", sanitized_name)
        return sanitized_name.lower()

    def _get_inventory_group_names_from_computer_security_groups(self, security_groups):
        """
        converts active directory group names to ansible inventory group names
        :param security_groups: list of active directory security group names
        """
        result = []
        for group in security_groups:
            display.debug("processing security group %s" % group)
            result.append(to_text(group.split(",")[0].split("=")[1]))
        return result

    def _get_inventory_group_names_from_computer_distinguished_name(
        self, entry_dn, search_ou
    ):
        """
        converts an active directory computer objects distinguished name to ansible inventory group names.
        :param entry_dn: computer object ldap entry distinguished name
        :param search_ou: the base search organization unit that was used to retrieve the entry. all inventory groups are based off of this OU
        """
        result = []
        sub_ous = []
        if search_ou in entry_dn:
            display.debug("parsing %s" % entry_dn)
            if not match("^DC=", search_ou):
                parent_group = search_ou.split(",")[0].split("=")[1]
                result.append(to_text(parent_group))
            dn_without_search_ou = entry_dn.split(search_ou)[0].strip(",")
            display.debug("processing dn_without_search_ou %s" % dn_without_search_ou)
            for count, node in enumerate(dn_without_search_ou.split(",")):
                display.debug("processing node %s" % node)
                if count == 0:
                    display.debug("ignoring object %s in group name calculation" % node)
                else:
                    if "=" in node:
                        sub_ous.append(to_text(node.split("=")[1]))
                    else:
                        display.warning(
                            "node %s cannot be split to get inventory group name" % node
                        )
                count += 1
        else:
            raise AnsibleError("%s does not exists in %s" % (search_ou, entry_dn))

        sub_ous.reverse()
        result = result + sub_ous
        display.debug("returning result %s" % result)
        return result

    def _get_primary_group_name_from_id(self, group_id):
        """
        returns the group name for a given primary group id
        :param group_id: numeric id of the active directory group
        """
        known_groups_dict = {
            512: "Domain Admins",
            513: "Domain Users",
            514: "Domain Guests",
            515: "Domain Computers",
            516: "Domain Controllers",
            498: "Enterprise Read-only Domain Controllers",
            521: "Read-only Domain Controllers",
            517: "Cert Publishers",
            518: "Schema Admins",
            519: "Enterprise Admins",
            520: "Group Policy Creator Owners",
        }
        result = "unknown-primary-group"

        if group_id in known_groups_dict:
            result = known_groups_dict[group_id]
        else:
            display.warning(
                "could not find " + str(group_id) + " in well known primary groups list"
            )

        return result

    def _populate(self, entry, organizational_unit):
        """
        populates ansible inventory with active directory entries
        :param entries: ldap entries list
        """
        return_state = ""
        display.debug(
            "processing entry (_populate)"
            + str(entry)
            + " with ou "
            + organizational_unit
        )
        hostname = self._get_hostname(entry)
        # use userAccountControl flag to check if the computer is enabled or not.
        # As per https://support.microsoft.com/en-us/help/305144/how-to-use-useraccountcontrol-to-manipulate-user-account-properties
        # Typical user : 0x200 (512)
        # Domain controller : 0x82000 (532480)
        # Workstation/server: 0x1000 (4096)
        # ACCOUNTDISABLE: 0x0002 (2)
        if (
            "userAccountControl" in entry["attributes"]
            and entry["attributes"]["userAccountControl"] in [4098, 532482]
            and self.import_disabled == False
        ):
            display.vvvv("Ignoring %s as it is currently disabled" % (hostname))
            return_state = "ignore_disabled"
        elif (
            "lastLogonTimestamp" in entry["attributes"]
            and abs(
                (
                    datetime.now(timezone.utc)
                    - entry["attributes"]["lastLogonTimestamp"]
                ).days
            )
            > self.last_activity
        ):
            display.vvvv(
                "Ignoring %s as its lastLogonTimestamp of %s is past the %d day(s) threshold"
                % (
                    hostname,
                    entry["attributes"]["lastLogonTimestamp"],
                    self.last_activity,
                )
            )
            return_state = "ignore_stale"
        else:
            organizational_unit_groups = self._get_inventory_group_names_from_computer_distinguished_name(
                entry["dn"], organizational_unit
            )
            for count, group in enumerate(organizational_unit_groups, start=0):
                display.debug("%d. processing group %s" % (count, group))
                new_group_name = ""
                if count == 0:
                    parent_group_name = self._get_safe_group_name(
                        organizational_unit_groups[0]
                    )
                    display.debug("adding group %s under all" % (parent_group_name))
                    self.inventory.add_group(parent_group_name)
                    self.inventory.add_child("all", parent_group_name)
                    new_group_name = parent_group_name
                    if (
                        self.import_organizational_units_as_inventory_groups == False
                        or len(organizational_unit_groups) == 1
                    ):
                        self.inventory.add_host(hostname, group=new_group_name)
                        display.vvvv(
                            "%s added to inventory group %s"
                            % (hostname, new_group_name)
                        )
                        return_state = "added"
                else:
                    if self.import_organizational_units_as_inventory_groups == True:
                        parent_group_name = self._get_safe_group_name(
                            "-".join(organizational_unit_groups[0:count])
                        )
                        display.debug("creating parent group %s" % parent_group_name)
                        new_group_name = self._get_safe_group_name(
                            parent_group_name + "_" + group
                        )
                        display.debug(
                            "adding %s to %s" % (new_group_name, parent_group_name)
                        )
                        self.inventory.add_group(new_group_name)
                        self.inventory.add_child(parent_group_name, new_group_name)

                        # add host to leaf ou
                        if count == len(organizational_unit_groups) - 1:
                            self.inventory.add_host(hostname, group=new_group_name)
                            display.vvvv(
                                "%s added to inventory group %s"
                                % (hostname, new_group_name)
                            )
                            return_state = "added"

            if (
                "primaryGroupID" in entry["attributes"]
                and self.import_computer_groups == True
            ):
                primary_group = self._get_primary_group_name_from_id(
                    entry["attributes"]["primaryGroupID"]
                )
                group_name = self._get_safe_group_name(primary_group)
                group_added_name = self.inventory.add_group(group_name)
                self.inventory.add_child(group=group_added_name, child=hostname)
                display.vvvv(
                    "%s added to security group based inventory group %s"
                    % (hostname, group_name)
                )

            if (
                "memberOf" in entry["attributes"]
                and self.import_computer_groups == True
            ):
                display.debug(
                    "processing computer groups %s" % entry["attributes"]["memberOf"]
                )
                computer_security_groups = self._get_inventory_group_names_from_computer_security_groups(
                    entry["attributes"]["memberOf"]
                )
                for computer_security_group in computer_security_groups:
                    group_name = self._get_safe_group_name(computer_security_group)
                    group_added_name = self.inventory.add_group(group_name)
                    self.inventory.add_child(group=group_added_name, child=hostname)
                    display.vvvv(
                        "%s added to security group based inventory group %s"
                        % (hostname, group_name)
                    )

        return return_state

    def verify_file(self, path):
        """
        :param loader: an ansible.parsing.dataloader.DataLoader object
        :param path: the path to the inventory config file
        :return the contents of the config file
        """
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(("active_directory.yml", "active_directory.yaml")):
                return True
        display.verbose(
            "active_directory inventory filename must end with 'active_directory.yml' or 'active_directory.yaml'"
        )
        return False

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        self._read_config_data(path)

        self._init_data()

        stats = {}

        organizational_units_to_search = self.get_option("organizational_units")

        connection = self._ldap3_conn()

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option("cache")

        # Generate inventory
        cache_needs_update = False
        if cache:
            try:
                results = self._cache[cache_key]
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True

        if not cache or cache_needs_update:
            if isinstance(organizational_units_to_search, list):
                display.debug("creating all inventory group")
                self.inventory.add_group("all")
                for organizational_unit in organizational_units_to_search:
                    ou_stats = {
                        "added": 0,
                        "ignore_disabled": 0,
                        "ignore_stale": 0,
                        "unknown": 0,
                    }
                    count = 0
                    for entry in self._query(connection, organizational_unit):
                        return_state = self._populate(entry, organizational_unit)
                        if return_state == "added":
                            ou_stats["added"] = ou_stats["added"] + 1
                        elif return_state == "ignore_disabled":
                            ou_stats["ignore_disabled"] = (
                                ou_stats["ignore_disabled"] + 1
                            )
                        elif return_state == "ignore_stale":
                            ou_stats["ignore_stale"] = ou_stats["ignore_stale"] + 1
                        else:
                            ou_stats["unknown"] = ou_stats["unknown"] + 1
                    stats[organizational_unit] = ou_stats

                display.vvvv("inventory host change statistics:")
                for organizational_unit in organizational_units_to_search:
                    display.vvvv(
                        "OU: "
                        + organizational_unit
                        + " add: "
                        + str(stats[organizational_unit]["added"])
                        + " ignore-disabled: "
                        + str(stats[organizational_unit]["ignore_disabled"])
                        + " ignore-stale: "
                        + str(stats[organizational_unit]["ignore_stale"])
                    )
        # If the cache has expired/doesn't exist or if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option("cache")):
            self._cache[cache_key] = results
