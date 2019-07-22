#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) James Laska
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: rhn_register
short_description: Manage Red Hat Network registration using the C(rhnreg_ks) command
description:
    - Manage registration to the Red Hat Network.
version_added: "1.2"
author:
- James Laska (@jlaska)
notes:
    - This is for older Red Hat products. You probably want the M(redhat_subscription) module instead.
    - In order to register a system, C(rhnreg_ks) requires either a username and password, or an activationkey.
requirements:
    - rhnreg_ks
    - either libxml2 or lxml
options:
    state:
        description:
          - Whether to register (C(present)), or unregister (C(absent)) a system.
        type: str
        choices: [ absent, present ]
        default: present
    username:
        description:
            - Red Hat Network username.
        type: str
    password:
        description:
            - Red Hat Network password.
        type: str
    server_url:
        description:
            - Specify an alternative Red Hat Network server URL.
            - The default is the current value of I(serverURL) from C(/etc/sysconfig/rhn/up2date).
        type: str
    activationkey:
        description:
            - Supply an activation key for use with registration.
        type: str
    profilename:
        description:
            - Supply an profilename for use with registration.
        type: str
        version_added: "2.0"
    ca_cert:
        description:
            - Supply a custom ssl CA certificate file for use with registration.
        type: path
        version_added: "2.1"
        aliases: [ sslcacert ]
    systemorgid:
        description:
            - Supply an organizational id for use with registration.
        type: str
        version_added: "2.1"
    channels:
        description:
            - Optionally specify a list of channels to subscribe to upon successful registration.
        type: list
        default: []
    enable_eus:
        description:
            - If C(no), extended update support will be requested.
        type: bool
        default: no
    nopackages:
        description:
            - If C(yes), the registered node will not upload its installed packages information to Satellite server.
        type: bool
        default: no
        version_added: "2.5"
'''

EXAMPLES = r'''
- name: Unregister system from RHN
  rhn_register:
    state: absent
    username: joe_user
    password: somepass

- name: Register as user with password and auto-subscribe to available content
  rhn_register:
    state: present
    username: joe_user
    password: somepass

- name: Register with activationkey and enable extended update support
  rhn_register:
    state: present
    activationkey: 1-222333444
    enable_eus: yes

- name: Register with activationkey and set a profilename which may differ from the hostname
  rhn_register:
    state: present
    activationkey: 1-222333444
    profilename: host.example.com.custom

- name: Register as user with password against a satellite server
  rhn_register:
    state: present
    username: joe_user
    password: somepass
    server_url: https://xmlrpc.my.satellite/XMLRPC

- name: Register as user with password and enable channels
  rhn_register:
    state: present
    username: joe_user
    password: somepass
    channels: rhel-x86_64-server-6-foo-1,rhel-x86_64-server-6-bar-1
'''

RETURN = r'''
# Default return values
'''

import os
import sys

# Attempt to import rhn client tools
sys.path.insert(0, '/usr/share/rhn')
try:
    import up2date_client
    import up2date_client.config
    HAS_UP2DATE_CLIENT = True
except ImportError:
    HAS_UP2DATE_CLIENT = False

# INSERT REDHAT SNIPPETS
from ansible.module_utils import redhat
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves import urllib, xmlrpc_client


class Rhn(redhat.RegistrationBase):

    def __init__(self, module=None, username=None, password=None):
        redhat.RegistrationBase.__init__(self, module, username, password)
        self.config = self.load_config()
        self.server = None
        self.session = None

    def logout(self):
        if self.session is not None:
            self.server.auth.logout(self.session)

    def load_config(self):
        '''
            Read configuration from /etc/sysconfig/rhn/up2date
        '''
        if not HAS_UP2DATE_CLIENT:
            return None

        config = up2date_client.config.initUp2dateConfig()

        return config

    @property
    def server_url(self):
        return self.config['serverURL']

    @property
    def hostname(self):
        '''
            Return the non-xmlrpc RHN hostname.  This is a convenience method
            used for displaying a more readable RHN hostname.

            Returns: str
        '''
        url = urllib.parse.urlparse(self.server_url)
        return url[1].replace('xmlrpc.', '')

    @property
    def systemid(self):
        systemid = None
        xpath_str = "//member[name='system_id']/value/string"

        if os.path.isfile(self.config['systemIdPath']):
            fd = open(self.config['systemIdPath'], 'r')
            xml_data = fd.read()
            fd.close()

            # Ugh, xml parsing time ...
            # First, try parsing with libxml2 ...
            if systemid is None:
                try:
                    import libxml2
                    doc = libxml2.parseDoc(xml_data)
                    ctxt = doc.xpathNewContext()
                    systemid = ctxt.xpathEval(xpath_str)[0].content
                    doc.freeDoc()
                    ctxt.xpathFreeContext()
                except ImportError:
                    pass

            # m-kay, let's try with lxml now ...
            if systemid is None:
                try:
                    from lxml import etree
                    root = etree.fromstring(xml_data)
                    systemid = root.xpath(xpath_str)[0].text
                except ImportError:
                    raise Exception('"libxml2" or "lxml" is required for this module.')

            # Strip the 'ID-' prefix
            if systemid is not None and systemid.startswith('ID-'):
                systemid = systemid[3:]

        return int(systemid)

    @property
    def is_registered(self):
        '''
            Determine whether the current system is registered.

            Returns: True|False
        '''
        return os.path.isfile(self.config['systemIdPath'])

    def configure_server_url(self, server_url):
        '''
            Configure server_url for registration
        '''

        self.config.set('serverURL', server_url)
        self.config.save()

    def enable(self):
        '''
            Prepare the system for RHN registration.  This includes ...
             * enabling the rhnplugin yum plugin
             * disabling the subscription-manager yum plugin
        '''
        redhat.RegistrationBase.enable(self)
        self.update_plugin_conf('rhnplugin', True)
        self.update_plugin_conf('subscription-manager', False)

    def register(self, enable_eus=False, activationkey=None, profilename=None, sslcacert=None, systemorgid=None, nopackages=False):
        '''
            Register system to RHN.  If enable_eus=True, extended update
            support will be requested.
        '''
        register_cmd = ['/usr/sbin/rhnreg_ks', '--force']
        if self.username:
            register_cmd.extend(['--username', self.username, '--password', self.password])
        if self.server_url:
            register_cmd.extend(['--serverUrl', self.server_url])
        if enable_eus:
            register_cmd.append('--use-eus-channel')
        if nopackages:
            register_cmd.append('--nopackages')
        if activationkey is not None:
            register_cmd.extend(['--activationkey', activationkey])
        if profilename is not None:
            register_cmd.extend(['--profilename', profilename])
        if sslcacert is not None:
            register_cmd.extend(['--sslCACert', sslcacert])
        if systemorgid is not None:
            register_cmd.extend(['--systemorgid', systemorgid])
        rc, stdout, stderr = self.module.run_command(register_cmd, check_rc=True)

    def api(self, method, *args):
        '''
            Convenience RPC wrapper
        '''
        if self.server is None:
            if self.hostname != 'rhn.redhat.com':
                url = "https://%s/rpc/api" % self.hostname
            else:
                url = "https://xmlrpc.%s/rpc/api" % self.hostname
            self.server = xmlrpc_client.ServerProxy(url)
            self.session = self.server.auth.login(self.username, self.password)

        func = getattr(self.server, method)
        return func(self.session, *args)

    def unregister(self):
        '''
            Unregister a previously registered system
        '''

        # Initiate RPC connection
        self.api('system.deleteSystems', [self.systemid])

        # Remove systemid file
        os.unlink(self.config['systemIdPath'])

    def subscribe(self, channels):
        if not channels:
            return

        if self._is_hosted():
            current_channels = self.api('channel.software.listSystemChannels', self.systemid)
            new_channels = [item['channel_label'] for item in current_channels]
            new_channels.extend(channels)
            return self.api('channel.software.setSystemChannels', self.systemid, list(new_channels))

        else:
            current_channels = self.api('channel.software.listSystemChannels', self.systemid)
            current_channels = [item['label'] for item in current_channels]
            new_base = None
            new_childs = []
            for ch in channels:
                if ch in current_channels:
                    continue
                if self.api('channel.software.getDetails', ch)['parent_channel_label'] == '':
                    new_base = ch
                else:
                    if ch not in new_childs:
                        new_childs.append(ch)
            out_base = 0
            out_childs = 0

            if new_base:
                out_base = self.api('system.setBaseChannel', self.systemid, new_base)

            if new_childs:
                out_childs = self.api('system.setChildChannels', self.systemid, new_childs)

            return out_base and out_childs

    def _is_hosted(self):
        '''
            Return True if we are running against Hosted (rhn.redhat.com) or
            False otherwise (when running against Satellite or Spacewalk)
        '''
        return 'rhn.redhat.com' in self.hostname


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            server_url=dict(type='str'),
            activationkey=dict(type='str', no_log=True),
            profilename=dict(type='str'),
            ca_cert=dict(type='path', aliases=['sslcacert']),
            systemorgid=dict(type='str'),
            enable_eus=dict(type='bool', default=False),
            nopackages=dict(type='bool', default=False),
            channels=dict(type='list', default=[]),
        ),
        # username/password is required for state=absent, or if channels is not empty
        # (basically anything that uses self.api requires username/password) but it doesnt
        # look like we can express that with required_if/required_together/mutually_exclusive

        # only username+password can be used for unregister
        required_if=[['state', 'absent', ['username', 'password']]],
    )

    if not HAS_UP2DATE_CLIENT:
        module.fail_json(msg="Unable to import up2date_client.  Is 'rhn-client-tools' installed?")

    server_url = module.params['server_url']
    username = module.params['username']
    password = module.params['password']

    state = module.params['state']
    activationkey = module.params['activationkey']
    profilename = module.params['profilename']
    sslcacert = module.params['ca_cert']
    systemorgid = module.params['systemorgid']
    channels = module.params['channels']
    enable_eus = module.params['enable_eus']
    nopackages = module.params['nopackages']

    rhn = Rhn(module=module, username=username, password=password)

    # use the provided server url and persist it to the rhn config.
    if server_url:
        rhn.configure_server_url(server_url)

    if not rhn.server_url:
        module.fail_json(
            msg="No serverURL was found (from either the 'server_url' module arg or the config file option 'serverURL' in /etc/sysconfig/rhn/up2date)"
        )

    # Ensure system is registered
    if state == 'present':

        # Check for missing parameters ...
        if not (activationkey or rhn.username or rhn.password):
            module.fail_json(msg="Missing arguments, must supply an activationkey (%s) or username (%s) and password (%s)" % (activationkey, rhn.username,
                                                                                                                              rhn.password))
        if not activationkey and not (rhn.username and rhn.password):
            module.fail_json(msg="Missing arguments, If registering without an activationkey, must supply username or password")

        # Register system
        if rhn.is_registered:
            module.exit_json(changed=False, msg="System already registered.")

        try:
            rhn.enable()
            rhn.register(enable_eus, activationkey, profilename, sslcacert, systemorgid, nopackages)
            rhn.subscribe(channels)
        except Exception as exc:
            module.fail_json(msg="Failed to register with '%s': %s" % (rhn.hostname, exc))
        finally:
            rhn.logout()

        module.exit_json(changed=True, msg="System successfully registered to '%s'." % rhn.hostname)

    # Ensure system is *not* registered
    if state == 'absent':
        if not rhn.is_registered:
            module.exit_json(changed=False, msg="System already unregistered.")

        if not (rhn.username and rhn.password):
            module.fail_json(msg="Missing arguments, the system is currently registered and unregistration requires a username and password")

        try:
            rhn.unregister()
        except Exception as exc:
            module.fail_json(msg="Failed to unregister: %s" % exc)
        finally:
            rhn.logout()

        module.exit_json(changed=True, msg="System successfully unregistered from %s." % rhn.hostname)


if __name__ == '__main__':
    main()
