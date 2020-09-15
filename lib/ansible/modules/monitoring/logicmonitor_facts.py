#!/usr/bin/python

# Copyright (C) 2015  LogicMonitor
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: logicmonitor_facts
short_description: Collect facts about LogicMonitor objects
description:
    - LogicMonitor is a hosted, full-stack, infrastructure monitoring platform.
    - This module collects facts about hosts and host groups within your LogicMonitor account.
version_added: "2.2"
author: [Ethan Culler-Mayeno (@ethanculler), Jeff Wozniak (@woz5999)]
notes:
  - You must have an existing LogicMonitor account for this module to function.
requirements: ["An existing LogicMonitor account", "Linux"]
options:
    target:
        description:
            - The LogicMonitor object you wish to manage.
        required: true
        choices: ['host', 'hostgroup']
    company:
        description:
            - The LogicMonitor account company name. If you would log in to your account at "superheroes.logicmonitor.com" you would use "superheroes".
        required: true
    user:
        description:
            - A LogicMonitor user name. The module will authenticate and perform actions on behalf of this user.
        required: true
    password:
        description:
            - The password for the chosen LogicMonitor User.
            - If an md5 hash is used, the digest flag must be set to true.
        required: true
    collector:
        description:
            - The fully qualified domain name of a collector in your LogicMonitor account.
            - This is optional for querying a LogicMonitor host when a displayname is specified.
            - This is required for querying a LogicMonitor host when a displayname is not specified.
    hostname:
        description:
            - The hostname of a host in your LogicMonitor account, or the desired hostname of a device to add into monitoring.
            - Required for managing hosts (target=host).
        default: 'hostname -f'
    displayname:
        description:
            - The display name of a host in your LogicMonitor account or the desired display name of a device to add into monitoring.
        default: 'hostname -f'
    fullpath:
        description:
            - The fullpath of the hostgroup object you would like to manage.
            - Recommend running on a single ansible host.
            - Required for management of LogicMonitor host groups (target=hostgroup).
...
'''

EXAMPLES = '''
# Always run those modules on localhost using delegate_to:localhost, or localaction

- name: query a list of hosts
  logicmonitor_facts:
    target: host
    company: yourcompany
    user: Luigi
    password: ImaLuigi,number1!
  delegate_to: localhost

- name: query a host group
  logicmonitor_facts:
    target: hostgroup
    fullpath: /servers/production
    company: yourcompany
    user: mario
    password: itsame.Mario!
  delegate_to: localhost
'''


RETURN = '''
---
    ansible_facts:
        description: LogicMonitor properties set for the specified object
        returned: success
        type: list
        example: >
            {
                "name": "dc",
                "value": "1"
            },
            {
                "name": "type",
                "value": "prod"
            },
            {
                "name": "system.categories",
                "value": ""
            },
            {
                "name": "snmp.community",
                "value": "********"
            }
...
'''

import json
import socket
import types

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url


class LogicMonitor(object):

    def __init__(self, module, **params):
        self.__version__ = "1.0-python"
        self.module = module
        self.module.debug("Instantiating LogicMonitor object")

        self.check_mode = False
        self.company = params["company"]
        self.user = params["user"]
        self.password = params["password"]
        self.fqdn = socket.getfqdn()
        self.lm_url = "logicmonitor.com/santaba"
        self.__version__ = self.__version__ + "-ansible-module"

    def rpc(self, action, params):
        """Make a call to the LogicMonitor RPC library
        and return the response"""
        self.module.debug("Running LogicMonitor.rpc")

        param_str = urlencode(params)
        creds = urlencode(
            {"c": self.company,
                "u": self.user,
                "p": self.password})

        if param_str:
            param_str = param_str + "&"

        param_str = param_str + creds

        try:
            url = ("https://" + self.company + "." + self.lm_url +
                   "/rpc/" + action + "?" + param_str)

            # Set custom LogicMonitor header with version
            headers = {"X-LM-User-Agent": self.__version__}

            # Set headers
            f = open_url(url, headers=headers)

            raw = f.read()
            resp = json.loads(raw)
            if resp["status"] == 403:
                self.module.debug("Authentication failed.")
                self.fail(msg="Error: " + resp["errmsg"])
            else:
                return raw
        except IOError as ioe:
            self.fail(msg="Error: Exception making RPC call to " +
                          "https://" + self.company + "." + self.lm_url +
                          "/rpc/" + action + "\nException" + to_native(ioe))

    def get_collectors(self):
        """Returns a JSON object containing a list of
        LogicMonitor collectors"""
        self.module.debug("Running LogicMonitor.get_collectors...")

        self.module.debug("Making RPC call to 'getAgents'")
        resp = self.rpc("getAgents", {})
        resp_json = json.loads(resp)

        if resp_json["status"] == 200:
            self.module.debug("RPC call succeeded")
            return resp_json["data"]
        else:
            self.fail(msg=resp)

    def get_host_by_hostname(self, hostname, collector):
        """Returns a host object for the host matching the
        specified hostname"""
        self.module.debug("Running LogicMonitor.get_host_by_hostname...")

        self.module.debug("Looking for hostname " + hostname)
        self.module.debug("Making RPC call to 'getHosts'")
        hostlist_json = json.loads(self.rpc("getHosts", {"hostGroupId": 1}))

        if collector:
            if hostlist_json["status"] == 200:
                self.module.debug("RPC call succeeded")

                hosts = hostlist_json["data"]["hosts"]

                self.module.debug(
                    "Looking for host matching: hostname " + hostname +
                    " and collector " + str(collector["id"]))

                for host in hosts:
                    if (host["hostName"] == hostname and
                            host["agentId"] == collector["id"]):

                        self.module.debug("Host match found")
                        return host
                self.module.debug("No host match found")
                return None
            else:
                self.module.debug("RPC call failed")
                self.module.debug(hostlist_json)
        else:
            self.module.debug("No collector specified")
            return None

    def get_host_by_displayname(self, displayname):
        """Returns a host object for the host matching the
        specified display name"""
        self.module.debug("Running LogicMonitor.get_host_by_displayname...")

        self.module.debug("Looking for displayname " + displayname)
        self.module.debug("Making RPC call to 'getHost'")
        host_json = (json.loads(self.rpc("getHost",
                                         {"displayName": displayname})))

        if host_json["status"] == 200:
            self.module.debug("RPC call succeeded")
            return host_json["data"]
        else:
            self.module.debug("RPC call failed")
            self.module.debug(host_json)
            return None

    def get_collector_by_description(self, description):
        """Returns a JSON collector object for the collector
        matching the specified FQDN (description)"""
        self.module.debug(
            "Running LogicMonitor.get_collector_by_description..."
        )

        collector_list = self.get_collectors()
        if collector_list is not None:
            self.module.debug("Looking for collector with description " +
                              description)
            for collector in collector_list:
                if collector["description"] == description:
                    self.module.debug("Collector match found")
                    return collector
        self.module.debug("No collector match found")
        return None

    def get_group(self, fullpath):
        """Returns a JSON group object for the group matching the
        specified path"""
        self.module.debug("Running LogicMonitor.get_group...")

        self.module.debug("Making RPC call to getHostGroups")
        resp = json.loads(self.rpc("getHostGroups", {}))

        if resp["status"] == 200:
            self.module.debug("RPC called succeeded")
            groups = resp["data"]

            self.module.debug("Looking for group matching " + fullpath)
            for group in groups:
                if group["fullPath"] == fullpath.lstrip('/'):
                    self.module.debug("Group match found")
                    return group

            self.module.debug("No group match found")
            return None
        else:
            self.module.debug("RPC call failed")
            self.module.debug(resp)

        return None

    def create_group(self, fullpath):
        """Recursively create a path of host groups.
        Returns the id of the newly created hostgroup"""
        self.module.debug("Running LogicMonitor.create_group...")

        res = self.get_group(fullpath)
        if res:
            self.module.debug("Group " + fullpath + " exists.")
            return res["id"]

        if fullpath == "/":
            self.module.debug("Specified group is root. Doing nothing.")
            return 1
        else:
            self.module.debug("Creating group named " + fullpath)
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            parentpath, name = fullpath.rsplit('/', 1)
            parentgroup = self.get_group(parentpath)

            parentid = 1

            if parentpath == "":
                parentid = 1
            elif parentgroup:
                parentid = parentgroup["id"]
            else:
                parentid = self.create_group(parentpath)

            h = None

            # Determine if we're creating a group from host or hostgroup class
            if hasattr(self, '_build_host_group_hash'):
                h = self._build_host_group_hash(
                    fullpath,
                    self.description,
                    self.properties,
                    self.alertenable)
                h["name"] = name
                h["parentId"] = parentid
            else:
                h = {"name": name,
                     "parentId": parentid,
                     "alertEnable": True,
                     "description": ""}

            self.module.debug("Making RPC call to 'addHostGroup'")
            resp = json.loads(
                self.rpc("addHostGroup", h))

            if resp["status"] == 200:
                self.module.debug("RPC call succeeded")
                return resp["data"]["id"]
            elif resp["errmsg"] == "The record already exists":
                self.module.debug("The hostgroup already exists")
                group = self.get_group(fullpath)
                return group["id"]
            else:
                self.module.debug("RPC call failed")
                self.fail(
                    msg="Error: unable to create new hostgroup \"" + name +
                        "\".\n" + resp["errmsg"])

    def fail(self, msg):
        self.module.fail_json(msg=msg, changed=self.change)

    def exit(self, changed):
        self.module.debug("Changed: " + changed)
        self.module.exit_json(changed=changed)

    def output_info(self, info):
        self.module.debug("Registering properties as Ansible facts")
        self.module.exit_json(changed=False, ansible_facts=info)


class Host(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializer for the LogicMonitor host object"""
        self.change = False
        self.params = params
        self.collector = None

        LogicMonitor.__init__(self, module, **self.params)
        self.module.debug("Instantiating Host object")

        if self.params["hostname"]:
            self.module.debug("Hostname is " + self.params["hostname"])
            self.hostname = self.params['hostname']
        else:
            self.module.debug("No hostname specified. Using " + self.fqdn)
            self.hostname = self.fqdn

        if self.params["displayname"]:
            self.module.debug("Display name is " + self.params["displayname"])
            self.displayname = self.params['displayname']
        else:
            self.module.debug("No display name specified. Using " + self.fqdn)
            self.displayname = self.fqdn

        # Attempt to host information via display name of host name
        self.module.debug("Attempting to find host by displayname " +
                          self.displayname)
        info = self.get_host_by_displayname(self.displayname)

        if info is not None:
            self.module.debug("Host found by displayname")
            # Used the host information to grab the collector description
            # if not provided
            if (not hasattr(self.params, "collector") and
                    "agentDescription" in info):
                self.module.debug("Setting collector from host response. " +
                                  "Collector " + info["agentDescription"])
                self.params["collector"] = info["agentDescription"]
        else:
            self.module.debug("Host not found by displayname")

        # At this point, a valid collector description is required for success
        # Check that the description exists or fail
        if self.params["collector"]:
            self.module.debug("Collector specified is " +
                              self.params["collector"])
            self.collector = (self.get_collector_by_description(
                              self.params["collector"]))
        else:
            self.fail(msg="No collector specified.")

        # If the host wasn't found via displayname, attempt by hostname
        if info is None:
            self.module.debug("Attempting to find host by hostname " +
                              self.hostname)
            info = self.get_host_by_hostname(self.hostname, self.collector)

        self.info = info

    def get_properties(self):
        """Returns a hash of the properties
        associated with this LogicMonitor host"""
        self.module.debug("Running Host.get_properties...")

        if self.info:
            self.module.debug("Making RPC call to 'getHostProperties'")
            properties_json = (json.loads(self.rpc("getHostProperties",
                                                   {'hostId': self.info["id"],
                                                    "filterSystemProperties": True})))

            if properties_json["status"] == 200:
                self.module.debug("RPC call succeeded")
                return properties_json["data"]
            else:
                self.module.debug("Error: there was an issue retrieving the " +
                                  "host properties")
                self.module.debug(properties_json["errmsg"])

                self.fail(msg=properties_json["status"])
        else:
            self.module.debug(
                "Unable to find LogicMonitor host which matches " +
                self.displayname + " (" + self.hostname + ")"
            )
            return None

    def site_facts(self):
        """Output current properties information for the Host"""
        self.module.debug("Running Host.site_facts...")

        if self.info:
            self.module.debug("Host exists")
            props = self.get_properties()

            self.output_info(props)
        else:
            self.fail(msg="Error: Host doesn't exit.")


class Hostgroup(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializer for the LogicMonitor host object"""
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **self.params)
        self.module.debug("Instantiating Hostgroup object")

        self.fullpath = self.params["fullpath"]
        self.info = self.get_group(self.fullpath)

    def get_properties(self, final=False):
        """Returns a hash of the properties
        associated with this LogicMonitor host"""
        self.module.debug("Running Hostgroup.get_properties...")

        if self.info:
            self.module.debug("Group found")

            self.module.debug("Making RPC call to 'getHostGroupProperties'")
            properties_json = json.loads(self.rpc(
                "getHostGroupProperties",
                {'hostGroupId': self.info["id"],
                 "finalResult": final}))

            if properties_json["status"] == 200:
                self.module.debug("RPC call succeeded")
                return properties_json["data"]
            else:
                self.module.debug("RPC call failed")
                self.fail(msg=properties_json["status"])
        else:
            self.module.debug("Group not found")
            return None

    def site_facts(self):
        """Output current properties information for the Hostgroup"""
        self.module.debug("Running Hostgroup.site_facts...")

        if self.info:
            self.module.debug("Group exists")
            props = self.get_properties(True)

            self.output_info(props)
        else:
            self.fail(msg="Error: Group doesn't exit.")


def selector(module):
    """Figure out which object and which actions
    to take given the right parameters"""

    if module.params["target"] == "host":
        target = Host(module.params, module)
        target.site_facts()
    elif module.params["target"] == "hostgroup":
        # Validate target specific required parameters
        if module.params["fullpath"] is not None:
            target = Hostgroup(module.params, module)
            target.site_facts()
        else:
            module.fail_json(
                msg="Parameter 'fullpath' required for target 'hostgroup'")
    else:
        module.fail_json(
            msg="Error: Unexpected target \"" + module.params["target"] +
                "\" was specified.")


def main():
    TARGETS = [
        "host",
        "hostgroup"]

    module = AnsibleModule(
        argument_spec=dict(
            target=dict(required=True, default=None, choices=TARGETS),
            company=dict(required=True, default=None),
            user=dict(required=True, default=None),
            password=dict(required=True, default=None, no_log=True),

            collector=dict(required=False, default=None),
            hostname=dict(required=False, default=None),
            displayname=dict(required=False, default=None),
            fullpath=dict(required=False, default=None)
        ),
        supports_check_mode=True
    )

    selector(module)


if __name__ == "__main__":
    main()
