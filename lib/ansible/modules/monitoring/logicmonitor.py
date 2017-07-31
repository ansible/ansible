#!/usr/bin/python

# LogicMonitor Ansible module for managing Collectors, Hosts and Hostgroups
# Copyright (C) 2015  LogicMonitor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

RETURN = '''
---
success:
    description: flag indicating that execution was successful
    returned: success
    type: boolean
    sample: True
...
'''


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: logicmonitor
short_description: Manage your LogicMonitor account through Ansible Playbooks
description:
  - LogicMonitor is a hosted, full-stack, infrastructure monitoring platform.
  - This module manages hosts, host groups, and collectors within your LogicMonitor account.
version_added: "2.2"
author: [Ethan Culler-Mayeno (@ethanculler), Jeff Wozniak (@woz5999)]
notes:
  - You must have an existing LogicMonitor account for this module to function.
requirements: ["An existing LogicMonitor account", "Linux"]
options:
  target:
    description:
      - The type of LogicMonitor object you wish to manage.
      - "Collector: Perform actions on a LogicMonitor collector."
      - NOTE You should use Ansible service modules such as M(service) or M(supervisorctl) for managing the Collector 'logicmonitor-agent' and
        'logicmonitor-watchdog' services. Specifically, you'll probably want to start these services after a Collector add and stop these services
        before a Collector remove.
      - "Host: Perform actions on a host device."
      - "Hostgroup: Perform actions on a LogicMonitor host group."
      - >
        NOTE Host and Hostgroup tasks should always be performed via delegate_to: localhost. There are no benefits to running these tasks on the
        remote host and doing so will typically cause problems.
    required: true
    default: null
    choices: ['collector', 'host', 'datsource', 'hostgroup']
  action:
    description:
      - The action you wish to perform on target.
      - "Add: Add an object to your LogicMonitor account."
      - "Remove: Remove an object from your LogicMonitor account."
      - "Update: Update properties, description, or groups (target=host) for an object in your LogicMonitor account."
      - "SDT: Schedule downtime for an object in your LogicMonitor account."
    required: true
    default: null
    choices: ['add', 'remove', 'update', 'sdt']
  company:
    description:
      - The LogicMonitor account company name. If you would log in to your account at "superheroes.logicmonitor.com" you would use "superheroes."
    required: true
    default: null
  user:
    description:
      - A LogicMonitor user name. The module will authenticate and perform actions on behalf of this user.
    required: true
    default: null
  password:
    description:
        - The password of the specified LogicMonitor user
    required: true
    default: null
  collector:
    description:
      - The fully qualified domain name of a collector in your LogicMonitor account.
      - This is required for the creation of a LogicMonitor host (target=host action=add).
      - This is required for updating, removing or scheduling downtime for hosts if 'displayname' isn't
        specified (target=host action=update action=remove action=sdt).
    required: false
    default: null
  hostname:
    description:
      - The hostname of a host in your LogicMonitor account, or the desired hostname of a device to manage.
      - Optional for managing hosts (target=host).
    required: false
    default: 'hostname -f'
  displayname:
    description:
      - The display name of a host in your LogicMonitor account or the desired display name of a device to manage.
      - Optional for managing hosts (target=host).
    required: false
    default: 'hostname -f'
  description:
    description:
      - The long text description of the object in your LogicMonitor account.
      - Optional for managing hosts and host groups (target=host or target=hostgroup; action=add or action=update).
    required: false
    default: ""
  properties:
    description:
      - A dictionary of properties to set on the LogicMonitor host or host group.
      - Optional for managing hosts and host groups (target=host or target=hostgroup; action=add or action=update).
      - This parameter will add or update existing properties in your LogicMonitor account.
    required: false
    default: {}
  groups:
    description:
        - A list of groups that the host should be a member of.
        - Optional for managing hosts (target=host; action=add or action=update).
    required: false
    default: []
  id:
    description:
      - ID of the datasource to target.
      - Required for management of LogicMonitor datasources (target=datasource).
    required: false
    default: null
  fullpath:
    description:
      - The fullpath of the host group object you would like to manage.
      - Recommend running on a single Ansible host.
      - Required for management of LogicMonitor host groups (target=hostgroup).
    required: false
    default: null
  alertenable:
    description:
      - A boolean flag to turn alerting on or off for an object.
      - Optional for managing all hosts (action=add or action=update).
    required: false
    default: true
    choices: [true, false]
  starttime:
    description:
      - The time that the Scheduled Down Time (SDT) should begin.
      - Optional for managing SDT (action=sdt).
      - Y-m-d H:M
    required: false
    default: Now
  duration:
    description:
      - The duration (minutes) of the Scheduled Down Time (SDT).
      - Optional for putting an object into SDT (action=sdt).
    required: false
    default: 30
...
'''
EXAMPLES = '''
# example of adding a new LogicMonitor collector to these devices
---
- hosts: collectors
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Deploy/verify LogicMonitor collectors
    become: yes
    logicmonitor:
      target: collector
      action: add
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'

#example of adding a list of hosts into monitoring
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Deploy LogicMonitor Host
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: host
      action: add
      collector: mycompany-Collector
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      groups: /servers/production,/datacenter1
      properties:
        snmp.community: secret
        dc: 1
        type: prod
    delegate_to: localhost

#example of putting a datasource in SDT
---
- hosts: localhost
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: SDT a datasource
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: datasource
      action: sdt
      id: 123
      duration: 3000
      starttime: '2017-03-04 05:06'
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'

#example of creating a hostgroup
---
- hosts: localhost
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Create a host group
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: add
      fullpath: /servers/development
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties:
        snmp.community: commstring
        type: dev

#example of putting a list of hosts into SDT
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: SDT hosts
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: host
      action: sdt
      duration: 3000
      starttime: '2016-11-10 09:08'
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      collector: mycompany-Collector
    delegate_to: localhost

#example of putting a host group in SDT
---
- hosts: localhost
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: SDT a host group
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: sdt
      fullpath: /servers/development
      duration: 3000
      starttime: '2017-03-04 05:06'
      company=: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'

#example of updating a list of hosts
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Update a list of hosts
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: host
      action: update
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      collector: mycompany-Collector
      groups: /servers/production,/datacenter5
      properties:
        snmp.community: commstring
        dc: 5
    delegate_to: localhost

#example of updating a hostgroup
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Update a host group
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: update
      fullpath: /servers/development
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties:
        snmp.community: hg
        type: dev
        status: test
    delegate_to: localhost

#example of removing a list of hosts from monitoring
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Remove LogicMonitor hosts
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: host
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      collector: mycompany-Collector
    delegate_to: localhost

#example of removing a host group
---
- hosts: hosts
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Remove LogicMonitor development servers hostgroup
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      fullpath: /servers/development
    delegate_to: localhost
  - name: Remove LogicMonitor servers hostgroup
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      fullpath: /servers
    delegate_to: localhost
  - name: Remove LogicMonitor datacenter1 hostgroup
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      fullpath: /datacenter1
    delegate_to: localhost
  - name: Remove LogicMonitor datacenter5 hostgroup
    # All tasks except for target=collector should use delegate_to: localhost
    logicmonitor:
      target: hostgroup
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      fullpath: /datacenter5
    delegate_to: localhost

### example of removing a new LogicMonitor collector to these devices
---
- hosts: collectors
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Remove LogicMonitor collectors
    become: yes
    logicmonitor:
      target: collector
      action: remove
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'

#complete example
---
- hosts: localhost
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Create a host group
    logicmonitor:
      target: hostgroup
      action: add
      fullpath: /servers/production/database
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties:
        snmp.community: commstring
  - name: SDT a host group
    logicmonitor:
      target: hostgroup
      action: sdt
      fullpath: /servers/production/web
      duration: 3000
      starttime: '2012-03-04 05:06'
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'

- hosts: collectors
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: Deploy/verify LogicMonitor collectors
    logicmonitor:
      target: collector
      action: add
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
  - name: Place LogicMonitor collectors into 30 minute Scheduled downtime
    logicmonitor:
      target: collector
      action: sdt
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
  - name: Deploy LogicMonitor Host
    logicmonitor:
      target: host
      action: add
      collector: agent1.ethandev.com
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties:
        snmp.community: commstring
        dc: 1
      groups: /servers/production/collectors, /datacenter1
    delegate_to: localhost

- hosts: database-servers
  remote_user: '{{ username }}'
  vars:
    company: mycompany
    user: myusername
    password: mypassword
  tasks:
  - name: deploy logicmonitor hosts
    logicmonitor:
      target: host
      action: add
      collector: monitoring.dev.com
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties:
        snmp.community: commstring
        type: db
        dc: 1
      groups: /servers/production/database, /datacenter1
    delegate_to: localhost
  - name: schedule 5 hour downtime for 2012-11-10 09:08
    logicmonitor:
      target: host
      action: sdt
      duration: 3000
      starttime: '2012-11-10 09:08'
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
    delegate_to: localhost
'''

import datetime
import os
import platform
import socket
import sys
import types

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import open_url


HAS_LIB_JSON = True
try:
    import json
    # Detect the python-json library which is incompatible
    # Look for simplejson if that's the case
    try:
        if (
            not isinstance(json.loads, types.FunctionType) or
            not isinstance(json.dumps, types.FunctionType)
        ):
            raise ImportError
    except AttributeError:
        raise ImportError
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        HAS_LIB_JSON = False
    except SyntaxError:
        HAS_LIB_JSON = False



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
                          "/rpc/" + action + "\nException" + str(ioe))

    def do(self, action, params):
        """Make a call to the LogicMonitor
         server \"do\" function"""
        self.module.debug("Running LogicMonitor.do...")

        param_str = urlencode(params)
        creds = (urlencode(
            {"c": self.company,
                "u": self.user,
                "p": self.password}))

        if param_str:
            param_str = param_str + "&"
        param_str = param_str + creds

        try:
            self.module.debug("Attempting to open URL: " +
                              "https://" + self.company + "." + self.lm_url +
                              "/do/" + action + "?" + param_str)
            f = open_url(
                "https://" + self.company + "." + self.lm_url +
                "/do/" + action + "?" + param_str)
            return f.read()
        except IOError as ioe:
            self.fail(msg="Error: Exception making RPC call to " +
                          "https://" + self.company + "." + self.lm_url +
                          "/do/" + action + "\nException" + str(ioe))

    def get_collectors(self):
        """Returns a JSON object containing a list of
        LogicMonitor collectors"""
        self.module.debug("Running LogicMonitor.get_collectors...")

        self.module.debug("Making RPC call to 'getAgents'")
        resp = self.rpc("getAgents", {})
        resp_json = json.loads(resp)

        if resp_json["status"] is 200:
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
            self.module.debug("Looking for collector with description {0}" +
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
            self.module.debug("Group {0} exists." + fullpath)
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
                    msg="Error: unable to create new hostgroup \"" +
                        name + "\".\n" + resp["errmsg"])

    def fail(self, msg):
        self.module.fail_json(msg=msg, changed=self.change, failed=True)

    def exit(self, changed):
        self.module.debug("Changed: " + changed)
        self.module.exit_json(changed=changed, success=True)

    def output_info(self, info):
        self.module.debug("Registering properties as Ansible facts")
        self.module.exit_json(changed=False, ansible_facts=info)


class Collector(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor Collector object"""
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **params)
        self.module.debug("Instantiating Collector object")

        if self.params['description']:
            self.description = self.params['description']
        else:
            self.description = self.fqdn

        self.info = self._get()
        self.installdir = "/usr/local/logicmonitor"
        self.platform = platform.system()
        self.is_64bits = sys.maxsize > 2**32
        self.duration = self.params['duration']
        self.starttime = self.params['starttime']

        if self.info is None:
            self.id = None
        else:
            self.id = self.info["id"]

    def create(self):
        """Idempotent function to make sure that there is
        a running collector installed and registered"""
        self.module.debug("Running Collector.create...")

        self._create()
        self.get_installer_binary()
        self.install()

    def remove(self):
        """Idempotent function to make sure that there is
        not a running collector installed and registered"""
        self.module.debug("Running Collector.destroy...")

        self._unreigster()
        self.uninstall()

    def get_installer_binary(self):
        """Download the LogicMonitor collector installer binary"""
        self.module.debug("Running Collector.get_installer_binary...")

        arch = 32

        if self.is_64bits:
            self.module.debug("64 bit system")
            arch = 64
        else:
            self.module.debug("32 bit system")

        if self.platform == "Linux" and self.id is not None:
            self.module.debug("Platform is Linux")
            self.module.debug("Agent ID is " + str(self.id))

            installfilepath = (self.installdir +
                               "/logicmonitorsetup" +
                               str(self.id) + "_" + str(arch) +
                               ".bin")

            self.module.debug("Looking for existing installer at " +
                              installfilepath)
            if not os.path.isfile(installfilepath):
                self.module.debug("No previous installer found")
                self.module.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                self.module.debug("Downloading installer file")
                # attempt to create the install dir before download
                self.module.run_command("mkdir " + self.installdir)

                try:
                    installer = (self.do("logicmonitorsetup",
                                         {"id": self.id,
                                          "arch": arch}))
                    with open(installfilepath, "w") as write_file:
                        write_file.write(installer)
                except:
                    self.fail(msg="Unable to open installer file for writing")
            else:
                self.module.debug("Collector installer already exists")
                return installfilepath

        elif self.id is None:
            self.fail(
                msg="Error: There is currently no collector " +
                    "associated with this device. To download " +
                    " the installer, first create a collector " +
                    "for this device.")
        elif self.platform != "Linux":
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")
        else:
            self.fail(
                msg="Error: Unable  to retrieve the installer from the server")

    def install(self):
        """Execute the LogicMonitor installer if not
        already installed"""
        self.module.debug("Running Collector.install...")

        if self.platform == "Linux":
            self.module.debug("Platform is Linux")

            installer = self.get_installer_binary()

            if self.info is None:
                self.module.debug("Retrieving collector information")
                self.info = self._get()

            if not os.path.exists(self.installdir + "/agent"):
                self.module.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                self.module.debug("Setting installer file permissions")
                os.chmod(installer, 484)  # decimal for 0o744

                self.module.debug("Executing installer")
                ret_code, out, err = self.module.run_command(installer + " -y")

                if ret_code != 0:
                    self.fail(msg="Error: Unable to install collector: " + err)
                else:
                    self.module.debug("Collector installed successfully")
            else:
                self.module.debug("Collector already installed")
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device")

    def uninstall(self):
        """Uninstall LogicMontitor collector from the system"""
        self.module.debug("Running Collector.uninstall...")

        uninstallfile = self.installdir + "/agent/bin/uninstall.pl"

        if os.path.isfile(uninstallfile):
            self.module.debug("Collector uninstall file exists")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.module.debug("Running collector uninstaller")
            ret_code, out, err = self.module.run_command(uninstallfile)

            if ret_code != 0:
                self.fail(
                    msg="Error: Unable to uninstall collector: " + err)
            else:
                self.module.debug("Collector successfully uninstalled")
        else:
            if os.path.exists(self.installdir + "/agent"):
                (self.fail(
                    msg="Unable to uninstall LogicMonitor " +
                    "Collector. Can not find LogicMonitor " +
                    "uninstaller."))

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        self.module.debug("Running Collector.sdt...")

        self.module.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offsetstart = starttime

        if starttime:
            self.module.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            self.module.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            self.module.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                self.module.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"agentId": self.id,
             "type": 1,
             "notifyCC": True,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        self.module.debug("Making RPC call to 'setAgentSDT'")
        resp = json.loads(self.rpc("setAgentSDT", h))

        if resp["status"] == 200:
            self.module.debug("RPC call succeeded")
            return resp["data"]
        else:
            self.module.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])

    def site_facts(self):
        """Output current properties information for the Collector"""
        self.module.debug("Running Collector.site_facts...")

        if self.info:
            self.module.debug("Collector exists")
            props = self.get_properties(True)

            self.output_info(props)
        else:
            self.fail(msg="Error: Collector doesn't exit.")

    def _get(self):
        """Returns a JSON object representing this collector"""
        self.module.debug("Running Collector._get...")
        collector_list = self.get_collectors()

        if collector_list is not None:
            self.module.debug("Collectors returned")
            for collector in collector_list:
                if collector["description"] == self.description:
                    return collector
        else:
            self.module.debug("No collectors returned")
            return None

    def _create(self):
        """Create a new collector in the associated
        LogicMonitor account"""
        self.module.debug("Running Collector._create...")

        if self.platform == "Linux":
            self.module.debug("Platform is Linux")
            ret = self.info or self._get()

            if ret is None:
                self.change = True
                self.module.debug("System changed")

                if self.check_mode:
                    self.exit(changed=True)

                h = {"autogen": True,
                     "description": self.description}

                self.module.debug("Making RPC call to 'addAgent'")
                create = (json.loads(self.rpc("addAgent", h)))

                if create["status"] is 200:
                    self.module.debug("RPC call succeeded")
                    self.info = create["data"]
                    self.id = create["data"]["id"]
                    return create["data"]
                else:
                    self.fail(msg=create["errmsg"])
            else:
                self.info = ret
                self.id = ret["id"]
                return ret
        else:
            self.fail(
                msg="Error: LogicMonitor Collector must be " +
                "installed on a Linux device.")

    def _unreigster(self):
        """Delete this collector from the associated
        LogicMonitor account"""
        self.module.debug("Running Collector._unreigster...")

        if self.info is None:
            self.module.debug("Retrieving collector information")
            self.info = self._get()

        if self.info is not None:
            self.module.debug("Collector found")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.module.debug("Making RPC call to 'deleteAgent'")
            delete = json.loads(self.rpc("deleteAgent",
                                         {"id": self.id}))

            if delete["status"] is 200:
                self.module.debug("RPC call succeeded")
                return delete
            else:
                # The collector couldn't unregister. Start the service again
                self.module.debug("Error unregistering collecting. " +
                                  delete["errmsg"])
                self.fail(msg=delete["errmsg"])
        else:
            self.module.debug("Collector not found")
            return None


class Host(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor host object"""
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
            self.module.debug(
                "Collector specified is " +
                self.params["collector"]
            )
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
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]
        self.alertenable = self.params["alertenable"]
        if self.params["groups"] is not None:
            self.groups = self._strip_groups(self.params["groups"])
        else:
            self.groups = None

    def create(self):
        """Idemopotent function to create if missing,
        update if changed, or skip"""
        self.module.debug("Running Host.create...")

        self.update()

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

    def set_properties(self, propertyhash):
        """update the host to have the properties
        contained in the property hash"""
        self.module.debug("Running Host.set_properties...")
        self.module.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        self.module.debug("Assigning property hash to host object")
        self.properties = propertyhash

    def add(self):
        """Add this device to monitoring
        in your LogicMonitor account"""
        self.module.debug("Running Host.add...")

        if self.collector and not self.info:
            self.module.debug("Host not registered. Registering.")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            h = self._build_host_hash(
                self.hostname,
                self.displayname,
                self.collector,
                self.description,
                self.groups,
                self.properties,
                self.alertenable)

            self.module.debug("Making RPC call to 'addHost'")
            resp = json.loads(self.rpc("addHost", h))

            if resp["status"] == 200:
                self.module.debug("RPC call succeeded")
                return resp["data"]
            else:
                self.module.debug("RPC call failed")
                self.module.debug(resp)
                return resp["errmsg"]
        elif self.collector is None:
            self.fail(msg="Specified collector doesn't exist")
        else:
            self.module.debug("Host already registered")

    def update(self):
        """This method takes changes made to this host
        and applies them to the corresponding host
        in your LogicMonitor account."""
        self.module.debug("Running Host.update...")

        if self.info:
            self.module.debug("Host already registed")
            if self.is_changed():
                self.module.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                h = (self._build_host_hash(
                     self.hostname,
                     self.displayname,
                     self.collector,
                     self.description,
                     self.groups,
                     self.properties,
                     self.alertenable))
                h["id"] = self.info["id"]
                h["opType"] = "replace"

                self.module.debug("Making RPC call to 'updateHost'")
                resp = json.loads(self.rpc("updateHost", h))

                if resp["status"] == 200:
                    self.module.debug("RPC call succeeded")
                else:
                    self.module.debug("RPC call failed")
                    self.fail(msg="Error: unable to update the host.")
            else:
                self.module.debug(
                    "Host properties match supplied properties. " +
                    "No changes to make."
                )
                return self.info
        else:
            self.module.debug("Host not registed. Registering")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            return self.add()

    def remove(self):
        """Remove this host from your LogicMonitor account"""
        self.module.debug("Running Host.remove...")

        if self.info:
            self.module.debug("Host registered")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.module.debug("Making RPC call to 'deleteHost'")
            resp = json.loads(self.rpc("deleteHost",
                                       {"hostId": self.info["id"],
                                        "deleteFromSystem": True,
                                        "hostGroupId": 1}))

            if resp["status"] == 200:
                self.module.debug(resp)
                self.module.debug("RPC call succeeded")
                return resp
            else:
                self.module.debug("RPC call failed")
                self.module.debug(resp)
                self.fail(msg=resp["errmsg"])

        else:
            self.module.debug("Host not registered")

    def is_changed(self):
        """Return true if the host doesn't
        match the LogicMonitor account"""
        self.module.debug("Running Host.is_changed")

        ignore = ['system.categories', 'snmp.version']

        hostresp = self.get_host_by_displayname(self.displayname)

        if hostresp is None:
            hostresp = self.get_host_by_hostname(self.hostname, self.collector)

        if hostresp:
            self.module.debug("Comparing simple host properties")
            if hostresp["alertEnable"] != self.alertenable:
                return True

            if hostresp["description"] != self.description:
                return True

            if hostresp["displayedAs"] != self.displayname:
                return True

            if (self.collector and
               hasattr(self.collector, "id") and
               hostresp["agentId"] != self.collector["id"]):
                return True

            self.module.debug("Comparing groups.")
            if self._compare_groups(hostresp) is True:
                return True

            propresp = self.get_properties()

            if propresp:
                self.module.debug("Comparing properties.")
                if self._compare_props(propresp, ignore) is True:
                    return True
            else:
                self.fail(
                    msg="Error: Unknown error retrieving host properties")

            return False
        else:
            self.fail(msg="Error: Unknown error retrieving host information")

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        self.module.debug("Running Host.sdt...")
        if self.info:
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            duration = self.duration
            starttime = self.starttime
            offset = starttime

            if starttime:
                self.module.debug("Start time specified")
                start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
                offsetstart = start
            else:
                self.module.debug("No start time specified. Using default.")
                start = datetime.datetime.utcnow()

                # Use user UTC offset
                self.module.debug("Making RPC call to 'getTimeZoneSetting'")
                accountresp = (json.loads(self.rpc("getTimeZoneSetting", {})))

                if accountresp["status"] == 200:
                    self.module.debug("RPC call succeeded")

                    offset = accountresp["data"]["offset"]
                    offsetstart = start + datetime.timedelta(0, offset)
                else:
                    self.fail(
                        msg="Error: Unable to retrieve timezone offset")

            offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

            h = {"hostId": self.info["id"],
                 "type": 1,
                 "year": offsetstart.year,
                 "month": offsetstart.month - 1,
                 "day": offsetstart.day,
                 "hour": offsetstart.hour,
                 "minute": offsetstart.minute,
                 "endYear": offsetend.year,
                 "endMonth": offsetend.month - 1,
                 "endDay": offsetend.day,
                 "endHour": offsetend.hour,
                 "endMinute": offsetend.minute}

            self.module.debug("Making RPC call to 'setHostSDT'")
            resp = (json.loads(self.rpc("setHostSDT", h)))

            if resp["status"] == 200:
                self.module.debug("RPC call succeeded")
                return resp["data"]
            else:
                self.module.debug("RPC call failed")
                self.fail(msg=resp["errmsg"])
        else:
            self.fail(msg="Error: Host doesn't exit.")

    def site_facts(self):
        """Output current properties information for the Host"""
        self.module.debug("Running Host.site_facts...")

        if self.info:
            self.module.debug("Host exists")
            props = self.get_properties()

            self.output_info(props)
        else:
            self.fail(msg="Error: Host doesn't exit.")

    def _build_host_hash(self,
                         hostname,
                         displayname,
                         collector,
                         description,
                         groups,
                         properties,
                         alertenable):
        """Return a property formatted hash for the
        creation of a host using the rpc function"""
        self.module.debug("Running Host._build_host_hash...")

        h = {}
        h["hostName"] = hostname
        h["displayedAs"] = displayname
        h["alertEnable"] = alertenable

        if collector:
            self.module.debug("Collector property exists")
            h["agentId"] = collector["id"]
        else:
            self.fail(
                msg="Error: No collector found. Unable to build host hash.")

        if description:
            h["description"] = description

        if groups is not None and groups is not []:
            self.module.debug("Group property exists")
            groupids = ""

            for group in groups:
                groupids = groupids + str(self.create_group(group)) + ","

            h["hostGroupIds"] = groupids.rstrip(',')

        if properties is not None and properties is not {}:
            self.module.debug("Properties hash exists")
            propnum = 0
            for key, value in properties.items():
                h["propName" + str(propnum)] = key
                h["propValue" + str(propnum)] = value
                propnum = propnum + 1

        return h

    def _verify_property(self, propname):
        """Check with LogicMonitor server to
        verify property is unchanged"""
        self.module.debug("Running Host._verify_property...")

        if self.info:
            self.module.debug("Host is registered")
            if propname not in self.properties:
                self.module.debug("Property " + propname + " does not exist")
                return False
            else:
                self.module.debug("Property " + propname + " exists")
                h = {"hostId": self.info["id"],
                     "propName0": propname,
                     "propValue0": self.properties[propname]}

                self.module.debug("Making RCP call to 'verifyProperties'")
                resp = json.loads(self.rpc('verifyProperties', h))

                if resp["status"] == 200:
                    self.module.debug("RPC call succeeded")
                    return resp["data"]["match"]
                else:
                    self.fail(
                        msg="Error: unable to get verification " +
                            "from server.\n%s" % resp["errmsg"])
        else:
            self.fail(
                msg="Error: Host doesn't exist. Unable to verify properties")

    def _compare_groups(self, hostresp):
        """Function to compare the host's current
        groups against provided groups"""
        self.module.debug("Running Host._compare_groups")

        g = []
        fullpathinids = hostresp["fullPathInIds"]
        self.module.debug("Building list of groups")
        for path in fullpathinids:
            if path != []:
                h = {'hostGroupId': path[-1]}

                hgresp = json.loads(self.rpc("getHostGroup", h))

                if (hgresp["status"] == 200 and
                   hgresp["data"]["appliesTo"] == ""):

                    g.append(path[-1])

        if self.groups is not None:
            self.module.debug("Comparing group lists")
            for group in self.groups:
                groupjson = self.get_group(group)

                if groupjson is None:
                    self.module.debug("Group mismatch. No result.")
                    return True
                elif groupjson['id'] not in g:
                    self.module.debug("Group mismatch. ID doesn't exist.")
                    return True
                else:
                    g.remove(groupjson['id'])

            if g != []:
                self.module.debug("Group mismatch. New ID exists.")
                return True
            self.module.debug("Groups match")

    def _compare_props(self, propresp, ignore):
        """Function to compare the host's current
        properties against provided properties"""
        self.module.debug("Running Host._compare_props...")
        p = {}

        self.module.debug("Creating list of properties")
        for prop in propresp:
            if prop["name"] not in ignore:
                if ("*******" in prop["value"] and
                   self._verify_property(prop["name"])):
                    p[prop["name"]] = self.properties[prop["name"]]
                else:
                    p[prop["name"]] = prop["value"]

        self.module.debug("Comparing properties")
        # Iterate provided properties and compare to received properties
        for prop in self.properties:
            if (prop not in p or
               p[prop] != self.properties[prop]):
                self.module.debug("Properties mismatch")
                return True
        self.module.debug("Properties match")

    def _strip_groups(self, groups):
        """Function to strip whitespace from group list.
        This function provides the user some flexibility when
        formatting group arguments """
        self.module.debug("Running Host._strip_groups...")
        return map(lambda x: x.strip(), groups)


class Datasource(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor Datasource object"""
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **params)
        self.module.debug("Instantiating Datasource object")

        self.id = self.params["id"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]

    def sdt(self):
        """Create a scheduled down time
        (maintenance window) for this host"""
        self.module.debug("Running Datasource.sdt...")

        self.module.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offsetstart = starttime

        if starttime:
            self.module.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            self.module.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            self.module.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                self.module.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"hostDataSourceId": self.id,
             "type": 1,
             "notifyCC": True,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        self.module.debug("Making RPC call to 'setHostDataSourceSDT'")
        resp = json.loads(self.rpc("setHostDataSourceSDT", h))

        if resp["status"] == 200:
            self.module.debug("RPC call succeeded")
            return resp["data"]
        else:
            self.module.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])


class Hostgroup(LogicMonitor):

    def __init__(self, params, module=None):
        """Initializor for the LogicMonitor host object"""
        self.change = False
        self.params = params

        LogicMonitor.__init__(self, module, **self.params)
        self.module.debug("Instantiating Hostgroup object")

        self.fullpath = self.params["fullpath"]
        self.info = self.get_group(self.fullpath)
        self.properties = self.params["properties"]
        self.description = self.params["description"]
        self.starttime = self.params["starttime"]
        self.duration = self.params["duration"]
        self.alertenable = self.params["alertenable"]

    def create(self):
        """Wrapper for self.update()"""
        self.module.debug("Running Hostgroup.create...")
        self.update()

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

    def set_properties(self, propertyhash):
        """Update the host to have the properties
        contained in the property hash"""
        self.module.debug("Running Hostgroup.set_properties")

        self.module.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        self.module.debug("Assigning property has to host object")
        self.properties = propertyhash

    def add(self):
        """Idempotent function to ensure that the host
        group exists in your LogicMonitor account"""
        self.module.debug("Running Hostgroup.add")

        if self.info is None:
            self.module.debug("Group doesn't exist. Creating.")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.create_group(self.fullpath)
            self.info = self.get_group(self.fullpath)

            self.module.debug("Group created")
            return self.info
        else:
            self.module.debug("Group already exists")

    def update(self):
        """Idempotent function to ensure the host group settings
        (alertenable, properties, etc) in the
        LogicMonitor account match the current object."""
        self.module.debug("Running Hostgroup.update")

        if self.info:
            if self.is_changed():
                self.module.debug("System changed")
                self.change = True

                if self.check_mode:
                    self.exit(changed=True)

                h = self._build_host_group_hash(
                    self.fullpath,
                    self.description,
                    self.properties,
                    self.alertenable)
                h["opType"] = "replace"

                if self.fullpath != "/":
                    h["id"] = self.info["id"]

                self.module.debug("Making RPC call to 'updateHostGroup'")
                resp = json.loads(self.rpc("updateHostGroup", h))

                if resp["status"] == 200:
                    self.module.debug("RPC call succeeded")
                    return resp["data"]
                else:
                    self.module.debug("RPC call failed")
                    self.fail(msg="Error: Unable to update the " +
                              "host.\n" + resp["errmsg"])
            else:
                self.module.debug(
                    "Group properties match supplied properties. " +
                    "No changes to make"
                )
                return self.info
        else:
            self.module.debug("Group doesn't exist. Creating.")

            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            return self.add()

    def remove(self):
        """Idempotent function to ensure the host group
        does not exist in your LogicMonitor account"""
        self.module.debug("Running Hostgroup.remove...")

        if self.info:
            self.module.debug("Group exists")
            self.module.debug("System changed")
            self.change = True

            if self.check_mode:
                self.exit(changed=True)

            self.module.debug("Making RPC call to 'deleteHostGroup'")
            resp = json.loads(self.rpc("deleteHostGroup",
                                       {"hgId": self.info["id"]}))

            if resp["status"] == 200:
                self.module.debug(resp)
                self.module.debug("RPC call succeeded")
                return resp
            elif resp["errmsg"] == "No such group":
                self.module.debug("Group doesn't exist")
            else:
                self.module.debug("RPC call failed")
                self.module.debug(resp)
                self.fail(msg=resp["errmsg"])
        else:
            self.module.debug("Group doesn't exist")

    def is_changed(self):
        """Return true if the host doesn't match
        the LogicMonitor account"""
        self.module.debug("Running Hostgroup.is_changed...")

        ignore = []
        group = self.get_group(self.fullpath)
        properties = self.get_properties()

        if properties is not None and group is not None:
            self.module.debug("Comparing simple group properties")
            if (group["alertEnable"] != self.alertenable or
               group["description"] != self.description):

                return True

            p = {}

            self.module.debug("Creating list of properties")
            for prop in properties:
                if prop["name"] not in ignore:
                    if ("*******" in prop["value"] and
                       self._verify_property(prop["name"])):

                        p[prop["name"]] = (
                            self.properties[prop["name"]])
                    else:
                        p[prop["name"]] = prop["value"]

            self.module.debug("Comparing properties")
            if set(p) != set(self.properties):
                return True
        else:
            self.module.debug("No property information received")
            return False

    def sdt(self, duration=30, starttime=None):
        """Create a scheduled down time
        (maintenance window) for this host"""
        self.module.debug("Running Hostgroup.sdt")

        self.module.debug("System changed")
        self.change = True

        if self.check_mode:
            self.exit(changed=True)

        duration = self.duration
        starttime = self.starttime
        offset = starttime

        if starttime:
            self.module.debug("Start time specified")
            start = datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            offsetstart = start
        else:
            self.module.debug("No start time specified. Using default.")
            start = datetime.datetime.utcnow()

            # Use user UTC offset
            self.module.debug("Making RPC call to 'getTimeZoneSetting'")
            accountresp = json.loads(self.rpc("getTimeZoneSetting", {}))

            if accountresp["status"] == 200:
                self.module.debug("RPC call succeeded")

                offset = accountresp["data"]["offset"]
                offsetstart = start + datetime.timedelta(0, offset)
            else:
                self.fail(
                    msg="Error: Unable to retrieve timezone offset")

        offsetend = offsetstart + datetime.timedelta(0, int(duration)*60)

        h = {"hostGroupId": self.info["id"],
             "type": 1,
             "year": offsetstart.year,
             "month": offsetstart.month-1,
             "day": offsetstart.day,
             "hour": offsetstart.hour,
             "minute": offsetstart.minute,
             "endYear": offsetend.year,
             "endMonth": offsetend.month-1,
             "endDay": offsetend.day,
             "endHour": offsetend.hour,
             "endMinute": offsetend.minute}

        self.module.debug("Making RPC call to setHostGroupSDT")
        resp = json.loads(self.rpc("setHostGroupSDT", h))

        if resp["status"] == 200:
            self.module.debug("RPC call succeeded")
            return resp["data"]
        else:
            self.module.debug("RPC call failed")
            self.fail(msg=resp["errmsg"])

    def site_facts(self):
        """Output current properties information for the Hostgroup"""
        self.module.debug("Running Hostgroup.site_facts...")

        if self.info:
            self.module.debug("Group exists")
            props = self.get_properties(True)

            self.output_info(props)
        else:
            self.fail(msg="Error: Group doesn't exit.")

    def _build_host_group_hash(self,
                               fullpath,
                               description,
                               properties,
                               alertenable):
        """Return a property formatted hash for the
        creation of a hostgroup using the rpc function"""
        self.module.debug("Running Hostgroup._build_host_hash")

        h = {}
        h["alertEnable"] = alertenable

        if fullpath == "/":
            self.module.debug("Group is root")
            h["id"] = 1
        else:
            self.module.debug("Determining group path")
            parentpath, name = fullpath.rsplit('/', 1)
            parent = self.get_group(parentpath)

            h["name"] = name

            if parent:
                self.module.debug("Parent group " +
                                  str(parent["id"]) + " found.")
                h["parentID"] = parent["id"]
            else:
                self.module.debug("No parent group found. Using root.")
                h["parentID"] = 1

        if description:
            self.module.debug("Description property exists")
            h["description"] = description

        if properties != {}:
            self.module.debug("Properties hash exists")
            propnum = 0
            for key, value in properties.items():
                h["propName" + str(propnum)] = key
                h["propValue" + str(propnum)] = value
                propnum = propnum + 1

        return h

    def _verify_property(self, propname):
        """Check with LogicMonitor server
        to verify property is unchanged"""
        self.module.debug("Running Hostgroup._verify_property")

        if self.info:
            self.module.debug("Group exists")
            if propname not in self.properties:
                self.module.debug("Property " + propname + " does not exist")
                return False
            else:
                self.module.debug("Property " + propname + " exists")
                h = {"hostGroupId": self.info["id"],
                     "propName0": propname,
                     "propValue0": self.properties[propname]}

                self.module.debug("Making RCP call to 'verifyProperties'")
                resp = json.loads(self.rpc('verifyProperties', h))

                if resp["status"] == 200:
                    self.module.debug("RPC call succeeded")
                    return resp["data"]["match"]
                else:
                    self.fail(
                        msg="Error: unable to get verification " +
                            "from server.\n%s" % resp["errmsg"])
        else:
            self.fail(
                msg="Error: Group doesn't exist. Unable to verify properties")


def selector(module):
    """Figure out which object and which actions
    to take given the right parameters"""

    if module.params["target"] == "collector":
        target = Collector(module.params, module)
    elif module.params["target"] == "host":
        # Make sure required parameter collector is specified
        if ((module.params["action"] == "add" or
            module.params["displayname"] is None) and
           module.params["collector"] is None):
            module.fail_json(
                msg="Parameter 'collector' required.")

        target = Host(module.params, module)
    elif module.params["target"] == "datasource":
        # Validate target specific required parameters
        if module.params["id"] is not None:
            # make sure a supported action was specified
            if module.params["action"] == "sdt":
                target = Datasource(module.params, module)
            else:
                errmsg = ("Error: Unexpected action \"" +
                          module.params["action"] + "\" was specified.")
                module.fail_json(msg=errmsg)

    elif module.params["target"] == "hostgroup":
        # Validate target specific required parameters
        if module.params["fullpath"] is not None:
            target = Hostgroup(module.params, module)
        else:
            module.fail_json(
                msg="Parameter 'fullpath' required for target 'hostgroup'")
    else:
        module.fail_json(
            msg="Error: Unexpected target \"" + module.params["target"] +
                "\" was specified.")

    if module.params["action"].lower() == "add":
        action = target.create
    elif module.params["action"].lower() == "remove":
        action = target.remove
    elif module.params["action"].lower() == "sdt":
        action = target.sdt
    elif module.params["action"].lower() == "update":
        action = target.update
    else:
        errmsg = ("Error: Unexpected action \"" + module.params["action"] +
                  "\" was specified.")
        module.fail_json(msg=errmsg)

    action()
    module.exit_json(changed=target.change)


def main():
    TARGETS = [
        "collector",
        "host",
        "datasource",
        "hostgroup"]

    ACTIONS = [
        "add",
        "remove",
        "sdt",
        "update"]

    module = AnsibleModule(
        argument_spec=dict(
            target=dict(required=True, default=None, choices=TARGETS),
            action=dict(required=True, default=None, choices=ACTIONS),
            company=dict(required=True, default=None),
            user=dict(required=True, default=None),
            password=dict(required=True, default=None, no_log=True),

            collector=dict(required=False, default=None),
            hostname=dict(required=False, default=None),
            displayname=dict(required=False, default=None),
            id=dict(required=False, default=None),
            description=dict(required=False, default=""),
            fullpath=dict(required=False, default=None),
            starttime=dict(required=False, default=None),
            duration=dict(required=False, default=30),
            properties=dict(required=False, default={}, type="dict"),
            groups=dict(required=False, default=[], type="list"),
            alertenable=dict(required=False, default="true", type="bool")
        ),
        supports_check_mode=True
    )

    if HAS_LIB_JSON is not True:
        module.fail_json(msg="Unable to load JSON library")

    selector(module)


if __name__ == "__main__":
    main()
