#!/usr/bin/python

# (c) James Laska
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

DOCUMENTATION = '''
---
module: rhn_register
short_description: Manage Red Hat Network registration using the C(rhnreg_ks) command
description:
    - Manage registration to the Red Hat Network.
version_added: "1.2"
author: James Laska
notes:
    - In order to register a system, rhnreg_ks requires either a username and password, or an activationkey.
requirements:
    - rhnreg_ks
options:
    state:
        description:
          - whether to register (C(present)), or unregister (C(absent)) a system
        required: false
        choices: [ "present", "absent" ]
        default: "present"
    username:
        description:
            - Red Hat Network username
        required: False
        default: null
    password:
        description:
            - Red Hat Network password
        required: False
        default: null
    server_url:
        description:
            - Specify an alternative Red Hat Network server URL
        required: False
        default: Current value of I(serverURL) from C(/etc/sysconfig/rhn/up2date) is the default
    activationkey:
        description:
            - supply an activation key for use with registration
        required: False
        default: null
    channels:
        description:
            - Optionally specify a list of comma-separated channels to subscribe to upon successful registration.
        required: false
        default: []
'''

EXAMPLES = '''
# Unregister system from RHN.
- rhn_register: state=absent username=joe_user password=somepass

# Register as user (joe_user) with password (somepass) and auto-subscribe to available content.
- rhn_register: state=present username=joe_user password=somepass

# Register with activationkey (1-222333444) and enable extended update support.
- rhn_register: state=present activationkey=1-222333444 enable_eus=true

# Register as user (joe_user) with password (somepass) against a satellite
# server specified by (server_url).
- rhn_register: >
    state=present
    username=joe_user
    password=somepass
    server_url=https://xmlrpc.my.satellite/XMLRPC

# Register as user (joe_user) with password (somepass) and enable
# channels (rhel-x86_64-server-6-foo-1) and (rhel-x86_64-server-6-bar-1).
- rhn_register: state=present username=joe_user
                password=somepass
                channels=rhel-x86_64-server-6-foo-1,rhel-x86_64-server-6-bar-1
'''

import sys
import types
import xmlrpclib
import urlparse

# Attempt to import rhn client tools
sys.path.insert(0, '/usr/share/rhn')
try:
    import up2date_client
    import up2date_client.config
except ImportError, e:
    module.fail_json(msg="Unable to import up2date_client.  Is 'rhn-client-tools' installed?\n%s" % e)

# INSERT REDHAT SNIPPETS
from ansible.module_utils.redhat import *
# INSERT COMMON SNIPPETS
from ansible.module_utils.basic import *

class Rhn(RegistrationBase):

    def __init__(self, username=None, password=None):
        RegistrationBase.__init__(self, username, password)
        self.config = self.load_config()

    def load_config(self):
        '''
            Read configuration from /etc/sysconfig/rhn/up2date
        '''
        self.config = up2date_client.config.initUp2dateConfig()

        # Add support for specifying a default value w/o having to standup some
        # configuration.  Yeah, I know this should be subclassed ... but, oh
        # well
        def get_option_default(self, key, default=''):
            # ignore pep8 W601 errors for this line
            # setting this to use 'in' does not work in the rhn library
            if self.has_key(key):
                return self[key]
            else:
                return default

        self.config.get_option = types.MethodType(get_option_default, self.config, up2date_client.config.Config)

        return self.config

    @property
    def hostname(self):
        '''
            Return the non-xmlrpc RHN hostname.  This is a convenience method
            used for displaying a more readable RHN hostname.

            Returns: str
        '''
        url = urlparse.urlparse(self.config['serverURL'])
        return url[1].replace('xmlrpc.','')

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
                    pass

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

    def configure(self, server_url):
        '''
            Configure system for registration
        '''

        self.config.set('serverURL', server_url)
        self.config.save()

    def enable(self):
        '''
            Prepare the system for RHN registration.  This includes ...
             * enabling the rhnplugin yum plugin
             * disabling the subscription-manager yum plugin
        '''
        RegistrationBase.enable(self)
        self.update_plugin_conf('rhnplugin', True)
        self.update_plugin_conf('subscription-manager', False)

    def register(self, enable_eus=False, activationkey=None):
        '''
            Register system to RHN.  If enable_eus=True, extended update
            support will be requested.
        '''
        register_cmd = "/usr/sbin/rhnreg_ks --username='%s' --password='%s' --force" % (self.username, self.password)
        if self.module.params.get('server_url', None):
            register_cmd += " --serverUrl=%s" % self.module.params.get('server_url')
        if enable_eus:
            register_cmd += " --use-eus-channel"
        if activationkey is not None:
            register_cmd += " --activationkey '%s'" % activationkey
        # FIXME - support --profilename
        # FIXME - support --systemorgid
        rc, stdout, stderr = self.module.run_command(register_cmd, check_rc=True, use_unsafe_shell=True)

    def api(self, method, *args):
        '''
            Convenience RPC wrapper
        '''
        if not hasattr(self, 'server') or self.server is None:
            if self.hostname != 'rhn.redhat.com':
                url = "https://%s/rpc/api" % self.hostname
            else:
                url = "https://xmlrpc.%s/rpc/api" % self.hostname
            self.server = xmlrpclib.Server(url, verbose=0)
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

    def subscribe(self, channels=[]):
        if len(channels) <= 0:
            return
        current_channels = self.api('channel.software.listSystemChannels', self.systemid)
        new_channels = [item['channel_label'] for item in current_channels]
        new_channels.extend(channels)
        return self.api('channel.software.setSystemChannels', self.systemid, new_channels)

    def _subscribe(self, channels=[]):
        '''
            Subscribe to requested yum repositories using 'rhn-channel' command
        '''
        rhn_channel_cmd = "rhn-channel --user='%s' --password='%s'" % (self.username, self.password)
        rc, stdout, stderr = self.module.run_command(rhn_channel_cmd + " --available-channels", check_rc=True)

        # Enable requested repoid's
        for wanted_channel in channels:
            # Each inserted repo regexp will be matched. If no match, no success.
            for available_channel in stdout.rstrip().split('\n'): # .rstrip() because of \n at the end -> empty string at the end
                if re.search(wanted_repo, available_channel):
                    rc, stdout, stderr = self.module.run_command(rhn_channel_cmd + " --add --channel=%s" % available_channel, check_rc=True)

def main():

    # Read system RHN configuration
    rhn = Rhn()

    module = AnsibleModule(
                argument_spec = dict(
                    state = dict(default='present', choices=['present', 'absent']),
                    username = dict(default=None, required=False),
                    password = dict(default=None, required=False),
                    server_url = dict(default=rhn.config.get_option('serverURL'), required=False),
                    activationkey = dict(default=None, required=False),
                    enable_eus = dict(default=False, type='bool'),
                    channels = dict(default=[], type='list'),
                )
            )

    state = module.params['state']
    rhn.username = module.params['username']
    rhn.password = module.params['password']
    rhn.configure(module.params['server_url'])
    activationkey = module.params['activationkey']
    channels = module.params['channels']
    rhn.module = module

    # Ensure system is registered
    if state == 'present':

        # Check for missing parameters ...
        if not (activationkey or rhn.username or rhn.password):
            module.fail_json(msg="Missing arguments, must supply an activationkey (%s) or username (%s) and password (%s)" % (activationkey, rhn.username, rhn.password))
        if not activationkey and not (rhn.username and rhn.password):
            module.fail_json(msg="Missing arguments, If registering without an activationkey, must supply username or password")

        # Register system
        if rhn.is_registered:
            module.exit_json(changed=False, msg="System already registered.")
        else:
            try:
                rhn.enable()
                rhn.register(module.params['enable_eus'] == True, activationkey)
                rhn.subscribe(channels)
            except Exception, e:
                module.fail_json(msg="Failed to register with '%s': %s" % (rhn.hostname, e))

            module.exit_json(changed=True, msg="System successfully registered to '%s'." % rhn.hostname)

    # Ensure system is *not* registered
    if state == 'absent':
        if not rhn.is_registered:
            module.exit_json(changed=False, msg="System already unregistered.")
        else:
            try:
                rhn.unregister()
            except Exception, e:
                module.fail_json(msg="Failed to unregister: %s" % e)

            module.exit_json(changed=True, msg="System successfully unregistered from %s." % rhn.hostname)


main()
