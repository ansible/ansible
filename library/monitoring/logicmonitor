#!/usr/bin/python

DOCUMENTATION = '''
---
module: logicmonitor
short_description: Manage your LogicMonitor account through Ansible Playbooks
description:
    - LogicMonitor is a hosted, full-stack, infrastructure monitoring platform.
    - This module manages hosts, host groups, and collectors within your LogicMonitor account.
version_added: "1.4"
author: Ethan Culler-Mayeno
notes: You must have an existing LogicMonitor account for this module to function.
requirements:
    - An existing LogicMonitor account
    - Currently supported operating systems:
        - Linux
options:
    target:
        description:
            - The LogicMonitor object you wish to manage.
        required: true
        default: null
        choices: ['collector', 'host', 'hostgroup']
    action:
        description:
            - The action you wish to perform on target
        required: true
        default: null
        choices: ['add', 'remove', 'sdt']
    company:
        description:
            - The LogicMonitor account company name. If you would log in to your account at "superheroes.logicmonitor.com" you would use "superheroes"
        required: true
        default: null
        choices: null
    user:
        description:
            - A LogicMonitor user name. The module will authenticate and perform actions on behalf of this user
        required: true 
        default: null
        choices: null
    password:
        description:
            - The password or md5 hash of the password for the chosen LogicMonitor User
            - If an md5 hash is used, the digest flag must be set to true
        required: true
        default: null
        choices: null
    digest:
        description:
            - Boolean flag to tell the module to treat the password as plaintext or md5 digest
            - If an md5 hash is used, the digest flag must be set to true
        required: false
        default: false
        choices: [true, false]
    collector:
        description:
            - The fully qualified domain name of a collector in your LogicMonitor account.
            - This is required for the creation of a LogicMonitor host (target=host action=add)
        required: false
        default: null
        choices: null
    hostname:
        description:
            - The hostname of a host in your LogicMonitor account, or the desired hostname of a device to add into monitoring.
            - Required for managing hosts (target=host)
        required: false
        default: 'hostname -f'
        choices: null
    displayname:
        description:
            - the display name of a host in your LogicMonitor account or the desired display name of a device to add into monitoring.
        required: false
        default: 'hostname -f'
        choices: null
    description:
        description:
            - The long text description of the object in your LogicMonitor account
            - Used when managing hosts and host groups (target=host or target=hostgroup)
        required: false
        default: ""
        choices: null
    properties:
        description:
            - A dictionary of properties to set on the LogicMonitor host or hostgroup.
            - Used when managing hosts and host groups (target=host or target=hostgroup)
            - This module will overwrite existing properties in your LogicMonitor account
        required: false
        default: {}
        choices: null
    groups:
        description:
            - The set of groups that the host should be a member of.
            - Used when managing LogicMonitor hosts (target=host)
        required: false
        default: []
        choices: null
    fullpath:
        description:
            - The fullpath of the hostgroup object you would like to manage
            - Recommend running on a single ansible host
            - Required for management of LogicMonitor host groups (target=hostgroup) 
        required: false
        default: null
        choices: null
    alertenable:
        description:
            - A boolean flag to turn on and off alerting for an object
        required: false
        default: true
        choices: [true, false]
    starttime:
        description:
            - The starttime for putting an object into Scheduled Down Time (maintenance mode)
            - Required for putting an object into SDT (action=sdt)
        required: false
        default: null
        choices: null
    duration:
        description:
            - The duration (minutes) an object should remain in Scheduled Down Time (maintenance mode)
            - Required for putting an object into SDT (action=sdt)
        required: false
        default: 30
        choices: null
'''

EXAMPLES='''
#example of adding a new LogicMonitor collector to these devices
---

- hosts: collectors
  user: root
  vars:
    company: 'yourcompany'
    user: 'mario'
    password: 'itsame.Mario!'
    digest: False
  tasks:
  - name: Deploy/verify LogicMonitor collectors
    logicmonitor: target=collector action=add company={{ company }} user={{ user }} password={{ password }}
          
#example of adding a host into monitoring
---

- hosts: collectors
  user: root
  vars:
    company: 'yourcompany'
    user: 'mario'
    password: 'itsame.Mario!'
    digest: False
  tasks:
  - name: Deploy LogicMonitor Host
    local_action:
      logicmonitor:
        target: host
        action: add
        collector: agent1.ethandev.com
        company: '{{ company }}'
        user: '{{ user }}'
        password: '{{ password }}'
        properties: {snmp.community: 'communitystr1'} 
        groups: ['/test/asdf', '/ans/ible']
          
#example of creating a hostgroup
---

- hosts: somemachine.superheroes.com
  user: root
  vars:
    company: 'yourcompany'
    user: 'mario'
    password: 'itsame.Mario!'
    digest: False
  tasks:
  - name: Create a host group
    logicmonitor:
      target: hostgroup
      action: add
      fullpath: '/worst/name/ever'
      company: '{{ company }}'
      user: '{{ user }}'
      password: '{{ password }}'
      properties: {snmp.community: 'communitystr2', mysql.user: 'superman'} 

'''

import urllib
import urlparse
import json
import sys
import os
import platform
import subprocess
import hashlib
import socket
import shlex
import datetime
from datetime import datetime, time, tzinfo, timedelta
from subprocess import call
from subprocess import Popen


class LogicMonitor(object):

    def __init__(self, module, **kwargs):
        self.module                 = module
        self.company                = kwargs["company"]
        self.user                   = kwargs["user"]
        self.password               = kwargs["password"]
        self.digest                 = module.boolean(kwargs['digest'])
        if self.digest:
            self.password_digest    = self.password
        else:
            m = hashlib.md5()
            m.update(self.password)
            self.password_digest    = m.hexdigest()
        self.fqdn           = socket.getfqdn()


    def rpc(self, action, params):
        """Make a call to the LogicMonitor RPC library and return the response"""
        param_str = urllib.urlencode(params)
        creds = urllib.urlencode({"c": self.company, "u": self.user, "pmd5": self.password_digest})
        if param_str:
            param_str = param_str + "&"
        param_str = param_str + creds
        try:
            f = urllib.urlopen("https://{0}.logicmonitor.com/santaba/rpc/{1}?{2}".format(self.company, action, param_str))
            return f.read()
        except IOError as ioe:
            print ioe
            sys.exit(1)

    def do(self, action, params):
        """Make a call to the LogicMonitor server \"do\" function"""
        param_str = urllib.urlencode(params)
        creds = urllib.urlencode({"c": self.company, "u": self.user, "pmd5": self.password_digest})
        if param_str:
            param_str = param_str + "&"
        param_str = param_str + creds
        try:
            f = urllib.urlopen("https://{0}.logicmonitor.com/santaba/do/{1}?{2}".format(self.company, action, param_str))
            return f.read()
        except IOError as ioe:
            print ioe
            sys.exit(1)
    
    
    def get_collectors(self):
        """Returns a JSON object containing a list of LogicMonitor collectors"""
        resp = self.rpc("getAgents", {})
        resp_json = json.loads(resp)
        if resp_json["status"] is 200:
             return resp_json["data"]
        else:
            self.module.fail_json(msg=resp)

    def get_host_by_hostname(self, hostname, collector):
        hostlist_json = json.loads(self.rpc("getHosts", {"hostGroupId": 1}))
        if collector is not None and hostlist_json["status"] == 200:
            hosts = hostlist_json["data"]["hosts"]
            for host in hosts:
                if host["hostName"] == hostname and host["agentId"] == collector["id"]:
                    return host
            return None
        else:
           return None

    def get_host_by_displayname(self, displayname):
        host_json = json.loads(self.rpc("getHost", {"displayName": displayname}))
        if host_json["status"] == 200:
            return host_json["data"]
        else:
           return None
    
    def get_collector_by_description(self, description):
        """return the collector json object for the collector with the matching FQDN (description) in your LogicMonitor account"""
        collector_list = self.get_collectors()
        if collector_list is not None:
            for collector in collector_list:
                if collector["description"] == description:
                    return collector
        return None
    
    def get_group(self, fullpath):
        """Return a JSON object with the current state of a group in your LogicMonitor account"""
        resp = json.loads(self.rpc("getHostGroups", {}))
        if resp["status"] == 200:
            groups = resp["data"]
            for group in groups:
                if group["fullPath"] == fullpath.lstrip('/'):
                    return group
        else:
           self.module.fail_json(msg="Error: Unable to retreive the list of host groups from the server.")
        return None
    
    def create_group(self, fullpath):
        """Recursively create a path of host groups. return value is the id of the newly created hostgroup in your LogicMonitor account"""
        if self.get_group(fullpath):
            return self.get_group(fullpath)["id"]
        parentpath, name = fullpath.rsplit('/', 1)
        parentgroup = self.get_group(parentpath)
        if fullpath == "/":
            return 1
        elif parentpath == "":
            parentid = 1
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            resp = json.loads(self.rpc("addHostGroup", {"name": name, "parentId": parentid, "alertEnable": True}))
            if resp["status"] == 200:
                return resp["data"]["id"]
            else:
               self.module.fail_json(msg="Error: unable to create new hostgroup.\n%s" % resp["errmsg"])
        elif parentgroup:
            parentid = parentgroup["id"]
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            #end if
            resp = json.loads(self.rpc("addHostGroup", {"name": name, "parentId": parentid, "alertEnable": True}))
            if resp["status"] == 200:
                return resp["data"]["id"]
            else:
               self.module.fail_json(msg="Error: unable to create new hostgroup.\n%s" % resp["errmsg"])
        else:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            #end if
            resp = json.loads(self.rpc("addHostGroup", {"name": name, "parentId": self.create_group(parentpath), "alertEnable": True}))
            if resp["status"] == 200:
                return resp["data"]["id"]
            else:
               self.module.fail_json(msg="Error: unable to create new hostgroup.\n%s" % resp["errmsg"])
    

class Collector(LogicMonitor):
    
    def __init__(self, module):
        """Initializor for the LogicMonitor Collector object"""
        LogicMonitor.__init__(self, module, **module.params)
        if self.module.params['description']:
            self.description    = self.module.params['description']
        else:
            self.description = self.fqdn
        self.info           = self._get()
        self.installdir     = "/usr/local/logicmonitor"
        self.change     = False
        if self.info is None:
            self.id         = None
        else:
            self.id         = self.info["id"]
        self.platform       = platform.system()
        self.is_64bits      = sys.maxsize > 2**32
        self.duration       = self.module.params['duration']
        self.starttime       = self.module.params['starttime']
    
    
    def create(self):
        """idempotent function to make sure that there is a running collector installed and registered in your LogicMonitor Account"""
        self._create()
        self.get_installer_binary()
        self.install()
        self.start()

    def destroy(self):
        """idempotent function to make sure that there is a running collector installed and registered in your LogicMonitor Account"""
        self.stop()
        self.uninstall()
        self._delete()
    
    def get_installer_binary(self):
        """Download the LogicMonitor collector installer binary"""
        arch = 32
        if self.is_64bits:
            arch = 64
        if self.platform == "Linux" and self.id is not None:
            installfilepath = self.installdir + "/logicmonitorsetup" + str(self.id) + "_" + str(arch) + ".bin"
            if not os.path.isfile(installfilepath):             #create the installer file and return the file object
                self.change = True #set change flag to show that something was update
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                with open(installfilepath, "w") as f:
                    installer = self.do("logicmonitorsetup", {"id": self.id, "arch": arch})
                    f.write(installer)
                f.closed
            return installfilepath
        elif self.id is None:
            self.module.fail_json(msg="Error: There is currently no collector associated with this device. To download the installer, first create a collector for this device.")
        elif self.platform != "Linux":
            self.module.fail_json(msg="Error: LogicMonitor Collector must be installed on a Linux device.")
        else:
            self.module.fail_json(msg="Error: Something went wrong. We were unable to retrieve the installer from the server")
    
    def install(self):
        """Execute the LogicMonitor installer if not already installed"""
        if self.platform == "Linux":
            installer = self.get_installer_binary()
            if not os.path.exists(self.installdir + "/agent") or (self._get()["platform"] != 'linux'):
                self.change = True #set change flag to show that something was update
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                os.chmod(installer, 755)
                output = call([installer, "-y"])
                if output != 0:
                    self.module.fail_json(msg="There was an issue installing the collector")
        else:
            self.module.fail_json(msg="Error: LogicMonitor Collector must be installed on a Linux device.")

    def uninstall(self):
        """Uninstall LogicMontitor collector from the system"""
        uninstallfile = self.installdir + "/agent/bin/uninstall.pl"
        if os.path.isfile(uninstallfile):
            self.change = True #set change flag to show that something was update
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            output = call([uninstallfile])
            if output != 0:
                self.module.fail_json(msg="There was an issue installing the collector")
        else:
            self.module.fail_json(msg="Unable to uninstall LogicMonitor Collector. Can not find LogicMonitor uninstaller.")
    
    def start(self):
        """Start the LogicMonitor collector"""
        if self.platform == "Linux":
            a = Popen(["service", "logicmonitor-agent", "status"], stdout=subprocess.PIPE)
            (aoutput, aerror) = a.communicate()
            if "is running" not in aoutput:
                self.change = True #set change flag to show that something was update
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                call(["service", "logicmonitor-agent", "start"])
            w = Popen(["service", "logicmonitor-watchdog", "status"], stdout=subprocess.PIPE)
            (woutput, werror) = w.communicate()
            if "is running" not in woutput:
                self.change = True #set change flag to show that something was update
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                call(["service", "logicmonitor-watchdog", "start"])
        else:
            self.module.fail_json(msg="Error: LogicMonitor Collector must be installed on a Linux device.")
    
    def restart(self):
        """Restart the LogicMonitor collector"""
        """Start the LogicMonitor collector"""
        if self.platform == "Linux":
            call(["service", "logicmonitor-agent", "restart"])
            call(["service", "logicmonitor-watchdog", "restart"])
        else:
            self.module.fail_json(msg="Error: LogicMonitor Collector must be installed on a Linux device.")

    
    def stop(self):
        """Stop the LogicMonitor collector"""
        if self.platform == "Linux":
            a = Popen(["service", "logicmonitor-agent", "status"], stdout=subprocess.PIPE)
            (aoutput, aerror) = a.communicate()
            if "is running" in aoutput:
                call(["service", "logicmonitor-agent", "stop"])
            w = Popen(["service", "logicmonitor-watchdog", "status"], stdout=subprocess.PIPE)
            (woutput, werror) = w.communicate()
            if "is running" in woutput:
                call(["service", "logicmonitor-watchdog", "stop"])
        else:
            self.module.fail_json(msg="Error: LogicMonitor Collector must be installed on a Linux device.")

    
    def sdt(self):
        self.change = True #set change flag to show that something was update
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        duration = self.duration
        starttime = self.starttime
        """create a scheduled down time (maintenance window) for this host"""
        accountresp = json.loads(self.rpc("getCompanySettings", {}))
        if accountresp["status"] == 200:
            offset = accountresp["data"]["offset"]
            if starttime:
                start = datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            else:
                start = datetime.utcnow()
            offsetstart = start + timedelta(0, offset)
            offsetend = offsetstart + timedelta(0, duration*60)
            resp = json.loads(self.rpc("setAgentSDT", {"agentId": self.id, "type": 1, "notifyCC": True,
            "year": offsetstart.year, "month": offsetstart.month-1, "day": offsetstart.day, "hour": offsetstart.hour, "minute": offsetstart.minute,
            "endYear": offsetend.year, "endMonth": offsetend.month-1, "endDay": offsetend.day, "endHour": offsetend.hour, "endMinute": offsetend.minute,
            }))
            if resp["status"] == 200:
                return resp["data"]
            else:
                return None
        else:
            self.module.fail_json(msg="Error: Unable to retrieve timezone offset")
    
    
    def _get(self):
        """Returns a JSON object representing the collector"""
        collector_list = self.get_collectors()
        if collector_list is not None:
            for collector in collector_list:
                if collector["description"] == self.description:
                    return collector
        return None
        
    def _create(self):
        """Create a new collector in the LogicMonitor account associated with this device"""
        ret = self._get()
        if ret is None:
            self.change = True #set change flag to show that something was update
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            create_json = json.loads(self.rpc("addAgent", {"autogen": True, "description": self.description}))
            if create_json["status"] is 200:
                self.info = create_json["data"]
                self.id = create_json["data"]["id"]
                return create_json["data"]
            else:
                self.module.fail_json(msg=json.dumps(msg=create_json))
        else:
            self.info = ret
            self.id = ret["id"]
            return ret

    def _delete(self):
        """Delete this collector from the associated LogicMonitor account"""
        if self._get is not None:
            delete_json = json.loads(self.rpc("deleteAgent", {"id": self.id}))
            if delete_json["status"] is 200:
                return delete_json["data"]
            else:
                self.module.fail_json(msg=json.dumps(msg=delete_json))
        else:
            return None


class Host(LogicMonitor):
    
    def __init__(self, module):
        """Initializor for the LogicMonitor host object"""
        LogicMonitor.__init__(self, module, **module.params)
        if self.module.params["collector"]:
            self.collector   = self.get_collector_by_description(self.module.params["collector"])
        else:
            self.collector   = None
        if self.module.params["hostname"]:
            self.hostname    = self.module.params['hostname']
        else:
            self.hostname    = self.fqdn
        if self.module.params["displayname"]:
            self.displayname = self.module.params['displayname']
        else:
            self.displayname = self.fqdn
        self.info = self.get_host_by_displayname(self.displayname) or self.get_host_by_hostname(self.hostname, self.collector)
        self.properties  = self.module.params["properties"]
        self.groups      = self.module.params["groups"]
        self.description = self.module.params["description"]
        self.alertenable = self.module.boolean(self.module.params["alertenable"])
        self.starttime   = self.module.params["starttime"]
        self.duration    = self.module.params["duration"]
        self.change = False
    
    
    def create(self):
        """Idemopotent function to create if missing, update if changed, or skip"""
        self.update()
    
    def get_properties(self):
        """Returns a hash of the properties associated with this LogicMonitor host"""
        if self.info:
            properties_json = json.loads(self.rpc("getHostProperties", {'hostId': self.info["id"], "filterSystemProperties": True, "finalResult": False}))
            if properties_json["status"] == 200:
                return properties_json["data"]
            else:
                print "Error: there was an issue retrieving the host properties"
                print json.dumps(properties_json)
                exit(properties_json["status"])
        else:
            print "Unable to find LogicMonitor host which matches {0} ({1})".format(self.displayname, self.hostname) 
            return None

    def set_properties(self, propertyhash):
        """update the host to have the properties contained in the property hash"""
        self.change = True
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        self.properties = propertyhash

    def add(self):
        """Add this device to monitoring in your LogicMonitor account"""
        if self.collector and not self.info:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            return self.rpc("addHost", self._buildhosthash( self.hostname, self.displayname, self.collector, self.description, self.groups, self.properties, self.alertenable))

    def update(self):
        """This method takes changes made to this host and applies them to the corresponding host in your LogicMonitor account."""
        if self.info:
            if self.is_changed():
                self.change = True
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                h =  self._buildhosthash( self.hostname, self.displayname, self.collector, self.description, self.groups, self.properties, self.alertenable)
                h["id"] = self.info["id"]
                resp = json.loads(self.rpc("updateHost", h))
                self.module.exit_json(changed=True, msg=json.dumps(resp))
                if resp["status"] == 200:
                    return resp["data"]
                else:
                    self.module.fail_json(msg="Error: unable to update the host.")
                    exit(resp["status"])
            else:
                return self.info
        else:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            return self.rpc("addHost", self._buildhosthash( self.hostname, self.displayname, self.collector, self.description, self.groups, self.properties, self.alertenable))
        
    def remove(self):
        """remove this host from your LogicMonitor account"""
        if self.info:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            return json.loads(self.rpc("deleteHost", {"id": self.info["id"], "deleteFromSystem": True, "hostGroupId": 1}))
    
    def is_changed(self):
        """Return true if the host doesn't match the LogicMonitor account"""
        ignore = ['system.categories', 'snmp.version']
        hostresp = self.get_host_by_displayname(self.displayname) or self.get_host_by_hostname(self.hostname)
        propresp = self.get_properties()
        if propresp and hostresp:
            if hostresp["alertEnable"] != self.alertenable or hostresp["description"] != self.description or hostresp["displayedAs"] != self.displayname or hostresp["agentId"] != self.collector["id"]:
                return True
            g = []
            fullpathinids = hostresp["fullPathInIds"]
            for path in fullpathinids:
                hgresp = json.loads(self.rpc("getHostGroup", {'hostGroupId': path[-1]}))
                if hgresp["status"] == 200 and hgresp["data"]["appliesTo"] == "":
                    g.append(path[-1])
            
            for group in self.groups:
                groupjson = self.get_group(group)
                if groupjson is None:
                    return True
                elif groupjson['id'] not in g:
                    return True
                else:
                    g.remove(groupjson['id'])
            if g != []:
                return True
            p = {}
            for prop in propresp:
                if prop["name"] not in ignore:
                    if "*******" in prop["value"] and self._verify_property(prop["name"]):
                        p[prop["name"]] = self.properties[prop["name"]]
                    else:
                        p[prop["name"]] = prop["value"]
            
            if p != self.properties:
                return True
        else:
            exit(1)
        return False
    
    def sdt(self):
        """create a scheduled down time (maintenance window) for this host"""
        duration = self.duration
        starttime = self.starttime
        self.change = True
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        accountresp = json.loads(self.rpc("getCompanySettings", {}))
        if accountresp["status"] == 200:
            offset = accountresp["data"]["offset"]
            if starttime:
                start = datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            else:
                start = datetime.utcnow()
            offsetstart = start + timedelta(0, offset)
            offsetend = offsetstart + timedelta(0, duration*60)
            resp = json.loads(self.rpc("setHostSDT", {"hostId": self.info["id"], "type": 1, "notifyCC": True,
            "year": offsetstart.year, "month": offsetstart.month - 1, "day": offsetstart.day, "hour": offsetstart.hour, "minute": offsetstart.minute,
            "endYear": offsetend.year, "endMonth": offsetend.month- 1, "endDay": offsetend.day, "endHour": offsetend.hour, "endMinute": offsetend.minute,
            }))
            if resp["status"] == 200:
                return resp["data"]
            else:
                return None
        else:
            self.module.fail_json("Error: Unable to retrieve timezone offset")
    
    
    def _buildhosthash(self, hostname, displayname, collector, description, groups, properties, alertenable):
        """Return a property formated hash for the creation of a host using the rpc function"""
        h = {}
        h["hostName"] = hostname
        h["displayedAs"] = displayname
        if collector:
            h["agentId"] = collector["id"]
        else:
           self.module.fail_json(msg="Error: Unable to build host hash. No collector found.")
        if description:
            h["description"] = description
        if groups != []:
            groupids = ""
            for group in groups:
                groupids = groupids + str(self.create_group(group)) + ","
            h["hostGroupIds"] = groupids.rstrip(',')
        if properties != {}:
            propnum = 0        
            for key, value in properties.iteritems():
                h["propName{0}".format(str(propnum))] = key
                h["propValue{0}".format(str(propnum))] = value
                propnum = propnum + 1
        h["alertEnable"] = alertenable
        return h
    
    def _verify_property(self, propname):
        """Check with LogicMonitor server to verify property is unchanged"""
        if self.info:
            if propname not in self.properties:
                return False
            else:
                resp = json.loads(self.rpc('verifyProperties', {"hostId": self.info["id"], "propName0": propname, "propValue0": self.properties[propname]}))
                if resp["status"] == 200:
                    return resp["data"]["match"]
                else:
                   self.module.fail_json(msg="Error: unable to get verification from server.\n%s" % resp["errmsg"])
        else:
           self.module.fail_json(msg="Error: Can not verify properties of a host which doesn't exist")
    

class Hostgroup(LogicMonitor):
    
    def __init__(self, module):
        """Initializor for the LogicMonitor host object"""
        LogicMonitor.__init__(self, module, **module.params)
        self.fullpath = self.module.params["fullpath"]
        self.info = self.get_group(self.fullpath)
        self.properties  = self.module.params["properties"]
        self.description = self.module.params["description"]
        self.alertenable = self.module.boolean(self.module.params["alertenable"])
        self.starttime   = self.module.params["starttime"]
        self.duration    = self.module.params["duration"]
        self.change = False
    

    def get_properties(self):
        """Returns a hash of the properties associated with this LogicMonitor host"""
        if self.info:
            properties_json = json.loads(self.rpc("getHostGroupProperties", {'hostGroupId': self.info["id"], "finalResult": False}))
            if properties_json["status"] == 200:
                return properties_json["data"]
            else:
                print "Error: there was an issue retrieving the host properties"
                print json.dumps(properties_json)
                exit(properties_json["status"])
        else:
            return None

    def set_properties(self, propertyhash):
        """update the host to have the properties contained in the property hash"""
        self.change = True
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        self.properties = propertyhash
    
    def add(self):
        """Idempotent function to ensure that the host group exists in your LogicMonitor account"""
        if self.info == None:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            hgid = self.create_group(self.fullpath)
            self.info = self.get_group(self.fullpath)
            return self.info
    
    def update(self):
        """Idempotent function to ensure the host group settings (alertenable, properties, etc) in the LogicMonitor account match the current object."""
        if self.fullpath == "/":
            if self.is_changed():
                h =  self._build_host_group_hash( self.fullpath, self.description, self.properties, self.alertenable)
                resp = json.loads(self.rpc("updateHostGroup", h))
                if resp["status"] == 200:
                    return resp["data"]
                else:
                    print "Error: unable to update the host."
                    exit(resp["status"])
        elif self.info:
            if self.is_changed():
                self.change = True
                if self.module.check_mode:
                    self.module.exit_json(changed=True)
                h =  self._build_host_group_hash( self.fullpath, self.description, self.properties, self.alertenable)
                h["id"] = self.info["id"]
                resp = json.loads(self.rpc("updateHostGroup", h))
                if resp["status"] == 200:
                    return resp["data"]
                else:
                    self.module.fail_json(msg="Error: Unable to update the host.\n{0}".format(json.dumps(resp)))
            else:
                return self.info
        else:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            return self.add()
        
    def remove(self):
        """Idempotent function to ensure the host group does not exist in your LogicMonitor account"""
        if self.info:
            self.change = True
            if self.module.check_mode:
                self.module.exit_json(changed=True)
            resp = json.loads(self.rpc("deleteHostGroup", {"hgId": self.info["id"]}))
    
    def is_changed(self):
        """Return true if the host doesn't match the LogicMonitor account"""
        ignore = []
        group = self.get_group(self.fullpath)
        properties = self.get_properties()
        if properties is not None and group is not None:
            if group["alertEnable"] != self.alertenable:
                return True
            if group["description"] != self.description:
                return True
            p = {}
            for prop in properties:
                if prop["name"] not in ignore:
                    if "*******" in prop["value"] and self._verify_property(prop["name"]):
                        p[prop["name"]] = self.properties[prop["name"]]
                    else:
                        p[prop["name"]] = prop["value"]
            if set(p) != set(self.properties):
                return True
        return False
    
    def sdt(self, duration=30, starttime=None):
        """create a scheduled down time (maintenance window) for this host"""
        self.change = True
        if self.module.check_mode:
            self.module.exit_json(changed=True)
        accountresp = json.loads(self.rpc("getCompanySettings", {}))
        if accountresp["status"] == 200:
            offset = accountresp["data"]["offset"]
            if starttime:
                start = datetime.strptime(starttime, '%Y-%m-%d %H:%M')
            else:
                start = datetime.utcnow()
            offsetstart = start + timedelta(0, offset)
            offsetend = offsetstart + timedelta(0, duration*60)
            resp = json.loads(self.rpc("setHostGroupSDT", {"hostGroupId": self.info["id"], "type": 1, "dataSourceId": 0,
            "year": offsetstart.year, "month": offsetstart.month-1, "day": offsetstart.day, "hour": offsetstart.hour, "minute": offsetstart.minute,
            "endYear": offsetend.year, "endMonth": offsetend.month-1, "endDay": offsetend.day, "endHour": offsetend.hour, "endMinute": offsetend.minute,
            }))
            if resp["status"] == 200:
                return resp["data"]
            else:
                return None
        else:
            self.module.fail_json(msg="Error: Unable to retrieve timezone from server")

    def create(self):
        """Wrapper for self.update()"""
        self.update()
    
    
    def _build_host_group_hash(self, fullpath, description, properties, alertenable):
        """Return a property formated hash for the creation of a hostgroup using the rpc function"""
        h = {}
        if fullpath == "/":
            h["id"] = 1
        else:
            parentpath, name = fullpath.rsplit('/', 1)
            parent = self.get_group(parentpath)
            if parent:
                h["parentID"] = parent["id"]
            else:
                h["parentID"] = 1
            h["name"] = name
        if description:
            h["description"] = description
        if properties != {}:
            propnum = 0
            for key, value in properties.iteritems():
                h["propName{0}".format(str(propnum))] = key
                h["propValue{0}".format(str(propnum))] = value
                propnum = propnum + 1
        h["alertEnable"] = alertenable
        return h

    def _verify_property(self, propname):
        """Check with LogicMonitor server to verify property is unchanged"""
        if self.info:
            if propname not in self.properties:
                return False
            else:
                resp = json.loads(self.rpc('verifyProperties', {"hostGroupId": self.info["id"], "propName0": propname, "propValue0": self.properties[propname]}))
                if resp["status"] == 200:
                    return resp["data"]["match"]
                else:
                    self.module.fail_json(msg="Error: unable to get verification from server.")
        else:
            self.module.fail_json(msg="Error: Can not verify properties of a hostgroup which doesn't exist")


#========================================


def selector(module):
    """Figure out which object and which actions to take given the right parameters"""
    if module.params['target'] == 'collector':
        target = Collector(module)
    elif module.params['target'] == 'host':
        target = Host(module)
    elif module.params['target'] == 'hostgroup':
        target = Hostgroup(module)
    else: #handles the EOTW case
        module.fail_json(msg="Error: Something very strange happened. An unexpected target was specified.")
    
    if module.params['action'] == 'add':
        action = target.create
    elif module.params['action'] == 'remove':
        action = target.remove
    elif module.params['action'] == 'sdt':
        action = target.sdt
    else:
        module.fail_json(msg="Error: Something very strange happened. An unexpected action was specified.")
    
    exit_code = action()
    module.exit_json(changed=target.change)
        

def main():
    TARGETS=[
        'collector',
        'host',
        'hostgroup',
    ]
    
    ACTIONS=[
        'add',
        'remove',
        'sdt',
    ]
    
    module = AnsibleModule(
        argument_spec = dict(
            target=dict(required=True, default=None, choices=TARGETS),
            action=dict(required=True, default=None, choices=ACTIONS),
            company=dict(required=True, default=None),
            user=dict(required=True, default=None),
            password=dict(required=True, default=None),
            digest=dict(required=False, default=False, choices=BOOLEANS),
            collector=dict(required=False, default=None),
            hostname=dict(required=False, default=None),
            displayname=dict(required=False, default=None),
            description=dict(required=False, default=""),
            properties=dict(type='dict', required=False, default={}),
            groups=dict(type='list', required=False, default=[]),
            fullpath=dict(required=False, default=None),
            alertenable=dict(required=False, default=True, choices=BOOLEANS),
            starttime=dict(required=False, default=None),
            duration=dict(required=False, default=30),
        ),
        supports_check_mode=True
    )
    selector(module)

# include magic from lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()