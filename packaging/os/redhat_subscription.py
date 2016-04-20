#!/usr/bin/python

# James Laska (jlaska@redhat.com)
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
module: redhat_subscription
short_description: Manage Red Hat Network registration and subscriptions using the C(subscription-manager) command
description:
    - Manage registration and subscription to the Red Hat Network entitlement platform.
version_added: "1.2"
author: "Barnaby Court (@barnabycourt)"
notes:
    - In order to register a system, subscription-manager requires either a username and password, or an activationkey.
requirements:
    - subscription-manager
options:
    state:
        description:
          - whether to register and subscribe (C(present)), or unregister (C(absent)) a system
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
    server_hostname:
        description:
            - Specify an alternative Red Hat Network server
        required: False
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    server_insecure:
        description:
            - Enable or disable https server certificate verification when connecting to C(server_hostname)
        required: False
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    rhsm_baseurl:
        description:
            - Specify CDN baseurl
        required: False
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    autosubscribe:
        description:
            - Upon successful registration, auto-consume available subscriptions
        required: False
        default: False
    activationkey:
        description:
            - supply an activation key for use with registration
        required: False
        default: null
    org_id:
        description:
            - Organisation ID to use in conjunction with activationkey
        required: False
        default: null
        version_added: "2.0"
    pool:
        description:
            - Specify a subscription pool name to consume.  Regular expressions accepted.
        required: False
        default: '^$'
    consumer_type:
        description:
            - The type of unit to register, defaults to system
        required: False
        default: null
        version_added: "2.1"
    consumer_name:
        description:
            - Name of the system to register, defaults to the hostname
        required: False
        default: null
        version_added: "2.1"
    consumer_id:
        description:
            - References an existing consumer ID to resume using a previous registration for this system. If the  system's identity certificate is lost or corrupted, this option allows it to resume using its previous identity and subscriptions. The default is to not specify a consumer ID so a new ID is created.
        required: False
        default: null
        version_added: "2.1"
'''

EXAMPLES = '''
# Register as user (joe_user) with password (somepass) and auto-subscribe to available content.
- redhat_subscription: state=present username=joe_user password=somepass autosubscribe=true

# Same as above but with pulling existing system data.
- redhat_subscription: state=present username=joe_user password=somepass
                       consumer_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Register with activationkey (1-222333444) and consume subscriptions matching
# the names (Red hat Enterprise Server) and (Red Hat Virtualization)
- redhat_subscription: state=present
                       activationkey=1-222333444
                       pool='^(Red Hat Enterprise Server|Red Hat Virtualization)$'

# Update the consumed subscriptions from the previous example (remove the Red
# Hat Virtualization subscription)
- redhat_subscription: state=present
                       activationkey=1-222333444
                       pool='^Red Hat Enterprise Server$'
'''

import os
import re
import types
import ConfigParser
import shlex


class RegistrationBase(object):
    def __init__(self, module, username=None, password=None):
        self.module = module
        self.username = username
        self.password = password

    def configure(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def enable(self):
        # Remove any existing redhat.repo
        redhat_repo = '/etc/yum.repos.d/redhat.repo'
        if os.path.isfile(redhat_repo):
            os.unlink(redhat_repo)

    def register(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def unregister(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def unsubscribe(self):
        raise NotImplementedError("Must be implemented by a sub-class")

    def update_plugin_conf(self, plugin, enabled=True):
        plugin_conf = '/etc/yum/pluginconf.d/%s.conf' % plugin
        if os.path.isfile(plugin_conf):
            cfg = ConfigParser.ConfigParser()
            cfg.read([plugin_conf])
            if enabled:
                cfg.set('main', 'enabled', 1)
            else:
                cfg.set('main', 'enabled', 0)
            fd = open(plugin_conf, 'rwa+')
            cfg.write(fd)
            fd.close()

    def subscribe(self, **kwargs):
        raise NotImplementedError("Must be implemented by a sub-class")


class Rhsm(RegistrationBase):
    def __init__(self, module, username=None, password=None):
        RegistrationBase.__init__(self, module, username, password)
        self.config = self._read_config()
        self.module = module

    def _read_config(self, rhsm_conf='/etc/rhsm/rhsm.conf'):
        '''
            Load RHSM configuration from /etc/rhsm/rhsm.conf.
            Returns:
             * ConfigParser object
        '''

        # Read RHSM defaults ...
        cp = ConfigParser.ConfigParser()
        cp.read(rhsm_conf)

        # Add support for specifying a default value w/o having to standup some configuration
        # Yeah, I know this should be subclassed ... but, oh well
        def get_option_default(self, key, default=''):
            sect, opt = key.split('.', 1)
            if self.has_section(sect) and self.has_option(sect, opt):
                return self.get(sect, opt)
            else:
                return default

        cp.get_option = types.MethodType(get_option_default, cp, ConfigParser.ConfigParser)

        return cp

    def enable(self):
        '''
            Enable the system to receive updates from subscription-manager.
            This involves updating affected yum plugins and removing any
            conflicting yum repositories.
        '''
        RegistrationBase.enable(self)
        self.update_plugin_conf('rhnplugin', False)
        self.update_plugin_conf('subscription-manager', True)

    def configure(self, **kwargs):
        '''
            Configure the system as directed for registration with RHN
            Raises:
              * Exception - if error occurs while running command
        '''
        args = ['subscription-manager', 'config']

        # Pass supplied **kwargs as parameters to subscription-manager.  Ignore
        # non-configuration parameters and replace '_' with '.'.  For example,
        # 'server_hostname' becomes '--system.hostname'.
        for k,v in kwargs.items():
            if re.search(r'^(system|rhsm)_', k):
                args.append('--%s=%s' % (k.replace('_','.'), v))

        self.module.run_command(args, check_rc=True)

    @property
    def is_registered(self):
        '''
            Determine whether the current system
            Returns:
              * Boolean - whether the current system is currently registered to
                          RHN.
        '''
        # Quick version...
        if False:
            return os.path.isfile('/etc/pki/consumer/cert.pem') and \
                   os.path.isfile('/etc/pki/consumer/key.pem')

        args = ['subscription-manager', 'identity']
        rc, stdout, stderr = self.module.run_command(args, check_rc=False)
        if rc == 0:
            return True
        else:
            return False

    def register(self, username, password, autosubscribe, activationkey, org_id,
                 consumer_type, consumer_name, consumer_id):
        '''
            Register the current system to the provided RHN server
            Raises:
              * Exception - if error occurs while running command
        '''
        args = ['subscription-manager', 'register']

        # Generate command arguments
        if activationkey:
            args.extend(['--activationkey', activationkey])
            if org_id:
                args.extend(['--org', org_id])
        else:
            if autosubscribe:
                args.append('--autosubscribe')
            if username:
                args.extend(['--username', username])
            if password:
                args.extend(['--password', password])
            if consumer_type:
                args.extend(['--type', consumer_type])
            if consumer_name:
                args.extend(['--name', consumer_name])
            if consumer_id:
                args.extend(['--consumerid', consumer_id])

        rc, stderr, stdout = self.module.run_command(args, check_rc=True)

    def unsubscribe(self, serials=None):
        '''
            Unsubscribe a system from subscribed channels
            Args:
              serials(list or None): list of serials to unsubscribe. If
                                     serials is none or an empty list, then
                                     all subscribed channels will be removed.
            Raises:
              * Exception - if error occurs while running command
        '''
        items = []
        if serials is not None and serials:
            items = ["--serial=%s" % s for s in serials]
        if serials is None:
            items = ["--all"]

        if items:
            args = ['subscription-manager', 'unsubscribe'] + items
            rc, stderr, stdout = self.module.run_command(args, check_rc=True)
        return serials

    def unregister(self):
        '''
            Unregister a currently registered system
            Raises:
              * Exception - if error occurs while running command
        '''
        args = ['subscription-manager', 'unregister']
        rc, stderr, stdout = self.module.run_command(args, check_rc=True)

    def subscribe(self, regexp):
        '''
            Subscribe current system to available pools matching the specified
            regular expression
            Raises:
              * Exception - if error occurs while running command
        '''

        # Available pools ready for subscription
        available_pools = RhsmPools(self.module)

        subscribed_pool_ids = []
        for pool in available_pools.filter(regexp):
            pool.subscribe()
            subscribed_pool_ids.append(pool.get_pool_id())
        return subscribed_pool_ids

    def update_subscriptions(self, regexp):
        changed=False
        consumed_pools = RhsmPools(self.module, consumed=True)
        pool_ids_to_keep = [p.get_pool_id() for p in consumed_pools.filter(regexp)]

        serials_to_remove=[p.Serial for p in consumed_pools if p.get_pool_id() not in pool_ids_to_keep]
        serials = self.unsubscribe(serials=serials_to_remove)

        subscribed_pool_ids = self.subscribe(regexp)

        if subscribed_pool_ids or serials:
            changed=True
        return {'changed': changed, 'subscribed_pool_ids': subscribed_pool_ids,
                'unsubscribed_serials': serials}



class RhsmPool(object):
    '''
        Convenience class for housing subscription information
    '''

    def __init__(self, module, **kwargs):
        self.module = module
        for k,v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        return str(self.__getattribute__('_name'))

    def get_pool_id(self):
        return getattr(self, 'PoolId', getattr(self, 'PoolID'))

    def subscribe(self):
        args = "subscription-manager subscribe --pool %s" % self.get_pool_id()
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)
        if rc == 0:
            return True
        else:
            return False


class RhsmPools(object):
    """
        This class is used for manipulating pools subscriptions with RHSM
    """
    def __init__(self, module, consumed=False):
        self.module = module
        self.products = self._load_product_list(consumed)

    def __iter__(self):
        return self.products.__iter__()

    def _load_product_list(self, consumed=False):
        """
            Loads list of all available or consumed pools for system in data structure

            Args:
                consumed(bool): if True list consumed  pools, else list available pools (default False)
        """
        args = "subscription-manager list"
        if consumed:
            args += " --consumed"
        else:
            args += " --available"
        rc, stdout, stderr = self.module.run_command(args, check_rc=True)

        products = []
        for line in stdout.split('\n'):
            # Remove leading+trailing whitespace
            line = line.strip()
            # An empty line implies the end of a output group
            if len(line) == 0:
                continue
            # If a colon ':' is found, parse
            elif ':' in line:
                (key, value) = line.split(':',1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
                if key in ['ProductName', 'SubscriptionName']:
                    # Remember the name for later processing
                    products.append(RhsmPool(self.module, _name=value, key=value))
                elif products:
                    # Associate value with most recently recorded product
                    products[-1].__setattr__(key, value)
                # FIXME - log some warning?
                #else:
                    # warnings.warn("Unhandled subscription key/value: %s/%s" % (key,value))
        return products

    def filter(self, regexp='^$'):
        '''
            Return a list of RhsmPools whose name matches the provided regular expression
        '''
        r = re.compile(regexp)
        for product in self.products:
            if r.search(product._name):
                yield product


def main():

    # Load RHSM configuration from file
    rhn = Rhsm(None)

    module = AnsibleModule(
                argument_spec = dict(
                    state = dict(default='present', choices=['present', 'absent']),
                    username = dict(default=None, required=False),
                    password = dict(default=None, required=False, no_log=True),
                    server_hostname = dict(default=rhn.config.get_option('server.hostname'), required=False),
                    server_insecure = dict(default=rhn.config.get_option('server.insecure'), required=False),
                    rhsm_baseurl = dict(default=rhn.config.get_option('rhsm.baseurl'), required=False),
                    autosubscribe = dict(default=False, type='bool'),
                    activationkey = dict(default=None, required=False),
                    org_id = dict(default=None, required=False),
                    pool = dict(default='^$', required=False, type='str'),
                    consumer_type = dict(default=None, required=False),
                    consumer_name = dict(default=None, required=False),
                    consumer_id = dict(default=None, required=False),
                )
            )

    rhn.module = module
    state = module.params['state']
    username = module.params['username']
    password = module.params['password']
    server_hostname = module.params['server_hostname']
    server_insecure = module.params['server_insecure']
    rhsm_baseurl = module.params['rhsm_baseurl']
    autosubscribe = module.params['autosubscribe'] == True
    activationkey = module.params['activationkey']
    org_id = module.params['org_id']
    pool = module.params['pool']
    consumer_type = module.params["consumer_type"]
    consumer_name = module.params["consumer_name"]
    consumer_id = module.params["consumer_id"]

    # Ensure system is registered
    if state == 'present':

        # Check for missing parameters ...
        if not (activationkey or username or password):
            module.fail_json(msg="Missing arguments, must supply an activationkey (%s) or username (%s) and password (%s)" % (activationkey, username, password))
        if not activationkey and not (username and password):
            module.fail_json(msg="Missing arguments, If registering without an activationkey, must supply username or password")

        # Register system
        if rhn.is_registered:
            if pool != '^$':
                try:
                    result = rhn.update_subscriptions(pool)
                except Exception, e:
                    module.fail_json(msg="Failed to update subscriptions for '%s': %s" % (server_hostname, e))
                else:
                    module.exit_json(**result)
            else:
                module.exit_json(changed=False, msg="System already registered.")
        else:
            try:
                rhn.enable()
                rhn.configure(**module.params)
                rhn.register(username, password, autosubscribe, activationkey, org_id,
                             consumer_type, consumer_name, consumer_id)
                subscribed_pool_ids = rhn.subscribe(pool)
            except Exception, e:
                module.fail_json(msg="Failed to register with '%s': %s" % (server_hostname, e))
            else:
                module.exit_json(changed=True,
                                 msg="System successfully registered to '%s'." % server_hostname,
                                 subscribed_pool_ids=subscribed_pool_ids)
    # Ensure system is *not* registered
    if state == 'absent':
        if not rhn.is_registered:
            module.exit_json(changed=False, msg="System already unregistered.")
        else:
            try:
                rhn.unsubscribe()
                rhn.unregister()
            except Exception, e:
                module.fail_json(msg="Failed to unregister: %s" % e)
            else:
                module.exit_json(changed=True, msg="System successfully unregistered from %s." % server_hostname)


# import module snippets
from ansible.module_utils.basic import *
main()
