#!/usr/bin/python
# Copyright (c) 2017 DST Systems, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: jboss_config
short_description: manage JBoss configuration via the JBoss REST management API
description:
  - Manage JBoss configuration via the JBoss REST management API.
version_added: "2.5"
author: Raymond Pieterick(@rpieterick)
options:
  url:
    description:
      - JBoss REST management API URL
    aliases: ["mgmt_url"]
    required: true
  url_username:
    description:
      - JBoss management user
    aliases: ["mgmt_user"]
    required: true
  url_password:
    description:
      - JBoss management password
    aliases: ["mgmt_password"]
    required: true
  json_address:
    description:
      - Value of address parameter for the REST call.  Expects a list.
    required: false
    default: []
  json_config:
    description:
      - A dictionary of keys and values structured like the JSON returned by the REST management API.
    required: true
  include_defaults:
    description:
      - Use default values for undefined attributes in the current configuration when comparing it to json_config.
    required: false
    default: false
  reload:
    description:
      - Reload the configuration if changes made by the task or a previous task require a reload.
        There are known issues with native AJP connectors not reloading successfully, so there is also a restart option.
    required: false
    default: false
  reload_timeout:
    description:
      - The module will go into a wait loop after a reload or restart until the management API is accessible again.
        This is the wait timeout in seconds.
    required: false
    default: 60
  restart:
    description:
      - Restart the JVM if changes made by the task or a previous task require a reload.
    required: false
    default: false
  state:
    choices: [ "present", "absent", "ensure" ]
    description:
      - For "present", verify the keys specified in json_config exist and have the values specified.
        Add any missing keys and set/update any missing/differing values.
        For "absent", verify the keys specified in json_config do not exist.
        If the key in the current configuration only has a value (no subkeys) it will be undefined.
        If the key in the current configuration has subkeys it will be deleted recursively.
        For "ensure", verify values in the current configuration match the values specified in json_config.
        Unlike "present" this state only updates values for existing keys.
        It does not add keys and does not fail if keys do not exist.
    required: false
    default: present
  timeout:
    description:
      - Timeout in seconds for each RESTful API call.
    required: false
    default: 30
'''

EXAMPLES = '''
    - name: disable datasource
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem","datasources"]
        json_config: {
                "xa-data-source": {
                    "appdb": {
                        "enabled": false
                    }
                }
            }
        state: ensure
    - name: remove datasource
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem","datasources"]
        json_config: {
                "xa-data-source": {
                    "appdb": null
                }
            }
        restart: true
        state: absent
    - name: jdbc driver
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem","datasources"]
        json_config: {
                "jdbc-driver": {
                    "mysql": {
                        "driver-class-name": "com.mysql.jdbc.Driver",
                        "driver-module-name": "com.mysql",
                        "driver-name": "mysql",
                        "driver-xa-datasource-class-name": "com.mysql.jdbc.jdbc2.optional.MysqlXADataSource"
                    }
                }
            }
        state: present
    - name: datasource
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem","datasources"]
        json_config: {
                "xa-data-source": {
                    "appdb": {
                        "background-validation": true,
                        "background-validation-millis": 240000,
                        "driver-name": "mysql",
                        "enabled": true,
                        "exception-sorter-class-name": "org.jboss.jca.adapters.jdbc.extensions.mysql.MySQLExceptionSorter",
                        "jndi-name": "java:/jdbc/appdb",
                        "max-pool-size": "${appdb.max.pool.size:20}",
                        "password": "${app2db.password:password}",
                        "use-java-context": false,
                        "user-name": "${appdb.username:username}",
                        "valid-connection-checker-class-name": "org.jboss.jca.adapters.jdbc.extensions.mysql.MySQLValidConnectionChecker",
                        "validate-on-match": false,
                        "xa-datasource-properties": {
                            "URL": {
                                "value": "${app2db.datasource.url:url}"
                            }
                        }
                    }
                }
            }
        state: present
    - name: update datasource
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem","datasources"]
        json_config: {
                "xa-data-source": {
                    "appdb": {
                        "password": "${appdb.password:password}",
                        "statistics-enabled": true,
                        "xa-datasource-properties": {
                            "URL": {
                                "value": "${appdb.datasource.url:url}"
                            }
                        }
                    }
                }
            }
        restart: true
        state: present
    - name: remove jaxrs subsystem
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: []
        json_config: {
                "subsystem": {
                    "jaxrs": null
                }
            }
        state: absent
    - name: remove jaxrs extension
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: []
        json_config: {
                "extension": {
                    "org.jboss.as.jaxrs": null
                }
            }
        state: absent
    - name: remove system properties
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: []
        json_config: {
                "system-property": {
                    "org.apache.coyote.ajp.MAX_PACKET_SIZE": null,
                    "org.apache.coyote.http11.Http11Protocol.MAX_HEADER_SIZE": null
                }
            }
        state: absent
    - name: system properties
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: []
        json_config: {
                "system-property": {
                    "org.apache.coyote.ajp.MAX_PACKET_SIZE": {
                        "value": "16380"
                    },
                    "org.apache.coyote.http11.Http11Protocol.MAX_HEADER_SIZE": {
                        "value": "65535"
                    }
                }
            }
        state: present
    - name: security domain
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: ["subsystem", "security"]
        json_config: {
                "security-domain": {
                    "AppLogin": {
                        "authentication": {
                            "classic": {
                                "login-modules": [{
                                    "code": "com.something.authentication.AppLoginModule",
                                    "flag": "required",
                                    "module": null,
                                    "module-options": {
                                        "application.name": "jboss",
                                        "application.password": "jboss",
                                        "crowd.server.url": "http://localhost:8080/app/"
                                    }
                                }]
                            }
                        },
                        "cache-type": "default"
                    }
                }
            }
        state: present
    - name: smtp socket binding
      jboss_config:
        mgmt_url: http://localhost:9990/management
        mgmt_user: admin
        mgmt_password: password
        json_address: []
        json_config: {
                "socket-binding-group": {
                    "standard-sockets": {
                        "remote-destination-outbound-socket-binding": {
                            "mail-smtp": {
                                "host": "localhost",
                                "port": 25
                            }
                        }
                    }
                }
            }
        state: present
'''

RETURN = '''
changed:
    description: True, if changes were made to the configuration.
    returned: always
    type: bool
    sample: "false"
reload_required:
    description: True, if a reload is required for the configuration changes to take effect.
    returned: success
    type: bool
    sample: "false"
reloaded:
    description: True, if the configuration was reloaded.
    returned: success
    type: bool
    sample: "false"
response:
    description: Body of the response if any from the management API.
    returned: failure
    type: string
    sample: ""
result:
    description: Dictionary of any changes made to the configuration.
    returned: success
    type: dict
    contains:
        added:
            description: List of dictionaries for keys and values that were added.
            returned: success
            type: complex
            contains:
                address:
                    description: List for the location of the change.
                    returned: success
                    type: list
                    sample: ["system-property", "org.apache.coyote.ajp.MAX_PACKET_SIZE"]
                new:
                    description: Dictionary of keys and values that were added.
                    returned: success
                    type: dict
                    sample: {
                            "value": "16380"
                        }
        removed:
            description: List of dictionaries for keys that were recursively removed and values that were undefined.
            returned: success
            type: complex
            contains:
                address:
                    description: List for the location of the change.
                    returned: success
                    type: list
                    sample: ["system-property", "org.apache.coyote.ajp.MAX_PACKET_SIZE"]
                new:
                    description: Dictionary of values that were undefined or null if the key was removed.
                    returned: success
                    type: dict
                    sample: null
                old:
                    description: Dictionary of the affected keys and values prior to the change.
                    returned: success
                    type: dict
                    sample: {
                            "value": "16380"
                        }
        updated:
            description: List of dictionaries for values that were changed.
            returned: success
            type: complex
            contains:
                address:
                    description: List for the location of the change.
                    returned: success
                    type: list
                    sample: ["subsystem", "datasources", "xa-data-source", "appdb"]
                new:
                    description: Dictionary of the new values.
                    returned: success
                    type: dict
                    sample: {
                            "enabled": false
                        }
                old:
                    description: Dictionary of the old values.
                    returned: success
                    type: dict
                    sample: {
                            "enabled": true
                        }
'''

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from datetime import datetime, timedelta
from time import sleep


class Diff(object):
    def __init__(self, new, old):
        self._new = new
        self._newkeys = set(new.keys())
        self._old = old
        self._oldkeys = set(old.keys())
        self._commonkeys = self._newkeys & self._oldkeys
        self._commonvals = set()
        for key in self._commonkeys:
            if _value(self._new[key]) == _value(self._old[key]):
                self._commonvals.add(key)


    def added(self):
        return self._newkeys - self._commonkeys


    def removed(self):
        return self._oldkeys - self._commonkeys


    def modified(self):
        return self._commonkeys - self._commonvals


    def unmodified(self):
        return self._commonvals


class JBossConfig(object):
    def __init__(self, module, url, timeout):
        self.changes =  dict(
                        added = list(),
                        updated = list(),
                        removed = list()
                    )
        self.check_mode = module.check_mode
        self.reload_required = False
        self.module = module
        self.url = url
        self.include_defaults = module.params['include_defaults']
        self.reload = module.params['reload']
        self.reload_timeout = module.params['reload_timeout']
        self.restart = module.params['restart']
        self.timeout = timeout
        self.body = {
                        "operation": "composite",
                        "address": [],
                        "steps": []
                    }
        self.headers = {'Content-Type':'application/json'}
    
    
    def _add_steps(self, address, new, old):
        d = Diff(new, old)
        for key in list(d.added() | d.modified()):
            if key not in old:
                addsubkeys = []
                if key == "value":
                    step =  {
                                "operation": "add",
                                "address": address,
                                "value": _value(new[key])
                            }
                elif _not_dict(new[key]):
                    step =  {
                                "operation": "write-attribute",
                                "address": address,
                                "name": key,
                                "value": _value(new[key])
                            }
                else:
                    step =  {
                                "operation": "add",
                                "address": address + [key]
                            }
                    for subkey in new[key]:
                        if _not_dict(new[key][subkey]):
                            step[subkey] = _value(new[key][subkey])
                        else:
                            addsubkeys.append(subkey)
                self.body["steps"].append(step)
                for subkey in addsubkeys:
                    self._add_steps(address + [key] + [subkey], new[key][subkey], dict())
            elif isinstance(new[key], dict):
                if isinstance(old[key], dict):
                    self._add_steps(address + [key], new[key], old[key])
                else:
                    self._add_steps(address + [key], new[key], dict())
        return


    def _changes(self, body):
        if body['operation'] == "add":
            del body['operation']
            del body['address']
            return body
        elif body['operation'] == "write-attribute":
            return body['value']
        elif body['operation'] == "remove":
            return None
        elif body['operation'] == "undefine-attribute":
            return None
        else:
            msg="Unknown operation '" + body['operation'] + "'.  Could not determine changes."
            self.module.fail_json(msg=msg, response="")


    def _post(self, body):
        if not self.check_mode:
            resp, info = fetch_url(self.module, self.url, data=json.dumps(body), headers=self.headers,
                                   method='POST', timeout=self.timeout)

            try:
                content = resp.read()
            except:
                content = info.pop('body', '')

            if info['status'] == 200:
                respdict = json.loads(content)
                if ('response-headers' in respdict and 'process-state' in respdict['response-headers']
                    and respdict['response-headers']['process-state'] == "reload-required"):
                    self.reload_required = True

        if self.check_mode or info['status'] == 200:
            if body['operation'] == "composite":
                return body
            else:
                return self._changes(body)
        else:
            msg = info.pop('msg', 'Operation ' + body['operation'] + ' failed with HTTP status' + str(info['status']))
            self.module.fail_json(msg=msg, response=content)


    def add(self, address, new, old):
        self._add_steps(address, new, old)
        ret = self._post(self.body)
        if 'operation' in ret and ret['operation'] == "composite":
            for step in ret['steps']:
                self.changes['added'].append(
                        dict(
                            address = step['address'],
                            new = self._changes(step)
                        )
                    )
        return ret


    def do_reload(self):
        reload_timeout = timedelta(seconds=self.reload_timeout)
        if self.restart:
            body =  {
                        "operation": "shutdown",
                        "address": [],
                        "restart": True
                    }
        else:
            body =  {
                        "operation": "reload",
                        "address": []
                    }
        resp, info = fetch_url(self.module, self.url, data=json.dumps(body), headers=self.headers,
                               method='POST', timeout=self.timeout)

        try:
            content = resp.read()
        except:
            content = info.pop('body', '')

        if info['status'] == 200:
            body =  {
                        "operation": "read-resource",
                        "address": []
                    }
            begintime = datetime.now()
            info['status'] = 503

            while info['status'] != 200 and (datetime.now() - reload_timeout) < begintime:
                sleep(5)
                resp, info = fetch_url(self.module, self.url, data=json.dumps(body), headers=self.headers,
                                       method='POST', timeout=self.timeout)

                try:
                    content = resp.read()
                except AttributeError:
                    content = info.pop('body', '')

            if info['status'] == 200:
                return True
            else:
                msg = 'Exceeded reload_timeout.  '
                msg += info.pop('msg', 'Operation ' + body['operation'] + ' failed with HTTP status' + str(info['status']))
                self.module.fail_json(msg=msg, response=content)
                
        else:
            msg = info.pop('msg', 'Operation ' + body['operation'] + ' failed with HTTP status' + str(info['status']))
            self.module.fail_json(msg=msg, response=content)


    def read_resource(self, address, new):
        body =  {
                    "operation": "read-resource",
                    "address": address,
                    "include-defaults": self.include_defaults,
                    "json.pretty": 0,
                    "recursive-depth": _json_depth(new)
                }
        resp, info = fetch_url(self.module, self.url, data=json.dumps(body), headers=self.headers,
                               method='POST', timeout=self.timeout)

        try:
            content = resp.read()
        except:
            content = info.pop('body', '')

        if info['status'] == 200:
            respdict = json.loads(content)
            if 'result' in respdict:
                return respdict['result']
            else:
                msg = 'Response from ' + body['operation'] + ' operation is missing result key'
                self.module.fail_json(msg=msg, response=content)
        else:
            msg = info.pop('msg', 'Operation ' + body['operation'] + ' failed with HTTP status' + str(info['status']))
            self.module.fail_json(msg=msg, response=content)


    def remove(self, address, new, old):
        d = Diff(new, old)
        for key in list(d.modified() | d.unmodified()):
            if key in old and old[key] is not None and not isinstance(new[key], dict):
                chgdict = dict()
                chgdict['old'] = _value(old[key])
                if key == "value":
                    body =  {
                                "operation": "remove",
                                "address": address
                            }
                    chgdict['new'] = self._post(body)
                elif not isinstance(old[key], dict):
                    body =  {
                                "operation": "undefine-attribute",
                                "address": address,
                                "name": key
                            }
                    chgdict['new'] = dict()
                    chgdict['new'][key] = self._post(body)
                    chgdict['old'] = dict()
                    chgdict['old'][key] = _value(old[key])
                else:
                    body =  {
                                "operation": "remove",
                                "address": address + [key]
                            }
                    chgdict['new'] = self._post(body)
                chgdict['address'] = body['address']
                self.changes['removed'].append(chgdict)
            elif isinstance(new[key], dict) and isinstance(old[key], dict):
                self.remove(address + [key], new[key], old[key])
        return


    def update(self, address, new, old):
        d = Diff(new, old)
        for key in list(d.modified()):
            chgdict = dict()
            if key == "value" and _value(new[key]) != _value(old[key]):
                body =  {
                            "operation": "remove",
                            "address": address
                        }
                self._post(body)
                body =  {
                            "operation": "add",
                            "address": address,
                            "value": _value(new[key])
                        }
                chgdict['new'] = self._post(body)
                chgdict['old'] = dict()
                chgdict['old']["value"] = _value(old[key])
            elif _not_dict(old[key]) and _not_dict(new[key]) and _value(new[key]) != _value(old[key]):
                body =  {
                            "operation": "write-attribute",
                            "address": address,
                            "name": key,
                            "value": _value(new[key])
                        }
                chgdict['new'] = dict()
                chgdict['new'][key] = self._post(body)
                chgdict['old'] = dict()
                chgdict['old'][key] = _value(old[key])
            elif isinstance(new[key], dict) and isinstance(old[key], dict):
                self.update(address + [key], new[key], old[key])

            if chgdict:
                chgdict['address'] = address
                self.changes['updated'].append(chgdict)
        return


def _json_depth(val):
    if type(val) is dict and val:
        keys = val.keys()
        if 'value' in keys:
            keys.remove('value')
        if 'EXPRESSION_VALUE' in keys:
            keys.remove('EXPRESSION_VALUE')
        if keys:
            return 1 + max(_json_depth(val[k]) for k in keys)
    return 0


def _not_dict(val):
    if not isinstance(val, dict) or 'EXPRESSION_VALUE' in val:
        return True
    else:
        return False


def _value(val):
    if isinstance(val, dict):
        if 'EXPRESSION_VALUE' in val:
            return val['EXPRESSION_VALUE']
        else:
            for key in val.keys():
                val[key] = _value(val[key])
    return val


def jboss_config_present(module, url, json_address, new_config, timeout):
    jbosscfg = JBossConfig(module, url, timeout)
    old_config = jbosscfg.read_resource(json_address, new_config)

    d = Diff(new_config, old_config)
    reload_required = False
    reloaded = False
    
    if not d.added() and not d.modified():
        module.exit_json(changed=False, result=jbosscfg.changes, reload_required=reload_required, reloaded=reloaded)
    else:
        if module.params['state'] == "present":
            jbosscfg.add(json_address, new_config, old_config)
        jbosscfg.update(json_address, new_config, old_config)
    
    if not jbosscfg.changes['added'] and not jbosscfg.changes['updated']:
        module.exit_json(changed=False, result=jbosscfg.changes, reload_required=reload_required, reloaded=reloaded)
    else:
        if jbosscfg.reload_required and (jbosscfg.reload or jbosscfg.restart):
            reloaded = jbosscfg.do_reload()
        elif not jbosscfg.check_mode:
            reload_required = jbosscfg.reload_required
        module.exit_json(changed=True, result=jbosscfg.changes, reload_required=reload_required, reloaded=reloaded)


def jboss_config_absent(module, url, json_address, new_config, timeout):
    jbosscfg = JBossConfig(module, url, timeout)
    old_config = jbosscfg.read_resource(json_address, new_config)

    jbosscfg = JBossConfig(module, url, timeout)
    reload_required = False
    reloaded = False

    jbosscfg.remove(json_address, new_config, old_config)
    
    if not jbosscfg.changes['removed']:
        module.exit_json(changed=False, result=jbosscfg.changes, reload_required=reload_required, reloaded=reloaded)
    else:
        if jbosscfg.reload_required and (jbosscfg.reload or jbosscfg.restart):
            reloaded = jbosscfg.do_reload()
        elif not jbosscfg.check_mode:
            reload_required = jbosscfg.reload_required
        module.exit_json(changed=True, result=jbosscfg.changes, reload_required=reload_required, reloaded=reloaded)


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(dict(
        url = dict(required=True, aliases=['mgmt_url']),
        url_username = dict(required=True, aliases=['mgmt_user']),
        url_password = dict(required=True, aliases=['mgmt_password'], no_log=True),
        json_address = dict(default=[], type='list'),
        json_config = dict(required=True, type='dict'),
        include_defaults = dict(default=False, type='bool'),
        reload = dict(default=False, type='bool'),
        reload_timeout = dict(default=60, type='int'),
        restart = dict(default=False, type='bool'),
        state = dict(
            choices=['present', 'ensure', 'absent'],
            default='present',
            type='str'
        ),
        timeout = dict(required=False, default=30, type='int'),
    ))

    choice_map = dict(
        present=jboss_config_present,
        ensure=jboss_config_present,
        absent=jboss_config_absent,
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        check_invalid_arguments=False,
        add_file_common_args=False,
        supports_check_mode=True
    )

    url = module.params['url']
    json_address = module.params['json_address']
    json_config = module.params['json_config']
    timeout = module.params['timeout']
    
    choice_map.get(
        module.params['state']
    )(module, url, json_address, json_config, timeout)


# import module snippets
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
