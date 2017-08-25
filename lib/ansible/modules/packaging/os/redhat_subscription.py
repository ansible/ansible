#!/usr/bin/python

# James Laska (jlaska@redhat.com)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: redhat_subscription
short_description: Manage registration and subscriptions to RHSM using the C(subscription-manager) command
description:
    - Manage registration and subscription to the Red Hat Subscription Management entitlement platform using the C(subscription-manager) command
version_added: "1.2"
author: "Barnaby Court (@barnabycourt)"
options:
    state:
        description:
          - Set whether to register and subscribe (C(present)) or unregister (C(absent)) a system.
        choices: [ "present", "absent" ]
        default: "present"
    username:
        description:
            - Username for access.redhat.com or Sat6
    password:
        description:
            - Password for access.redhat.com or Sat6
    server_hostname:
        description:
            - Specify an alternative Red Hat Subscription Management or Sat6 server.
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    server_insecure:
        description:
            - Enable or disable HTTPS server certificate verification when connecting to C(server_hostname)
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    rhsm_baseurl:
        description:
            - Specify CDN baseurl
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
    server_proxy_hostname:
        description:
            - Specify a HTTP proxy hostname
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
        version_added: "2.4"
    server_proxy_port:
        description:
            - Specify a HTTP proxy port
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
        version_added: "2.4"
    server_proxy_user:
        description:
            - Specify a user for HTTP proxy with basic authentication
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
        version_added: "2.4"
    server_proxy_password:
        description:
            - Specify a password for HTTP proxy with basic authentication
        required: False
        default: Current value from C(/etc/rhsm/rhsm.conf) is the default
        version_added: "2.4"
    auto_attach:
        description:
            - Upon successful registration, auto-consume available subscriptions
            - Added in favor of depracated autosubscribe in 2.5.
        default: False
        type: bool
        version_added: "2.5"
        aliases: [autosubscribe]
    activationkey:
        description:
            - supply an activation key for use with registration
    org_id:
        description:
            - Organization ID to use in conjunction with activationkey
        version_added: "2.0"
    environment:
        description:
            - Register with a specific environment in the destination org. Used with Red Hat Satellite 6.x or Katello
        version_added: "2.2"
    pool:
        description:
            - |
              Specify a subscription pool name to consume. Regular expressions accepted. Use I(pool_ids) instead if
              possible, as it is much faster.
            - Mutually exclusive with I(pool_ids).
        default: '^$'
    pool_ids:
        description:
            - |
              Specify subscription pool IDs to consume. Prefer over I(pool) when possible as this is much faster.
              A pool ID may be specified as a C(string) - just the pool ID (ex. C(0123456789abcdef0123456789abcdef)),
              or as a C(dict) with the pool ID as the key, and a quantity as the value (ex.
              C(0123456789abcdef0123456789abcdef: 2). If the quantity is provided, it is used to consume multiple
              entitlements from a pool. (The pool must support this).
            - Mutually exclusive with I(pool).
        default: []
        version_added: "2.4"
    consumer_type:
        description:
            - The type of unit to register; defaults to system.
        version_added: "2.1"
    consumer_name:
        description:
            - Name of the system to register; defaults to the hostname.
        version_added: "2.1"
    consumer_id:
        description:
            - |
              References an existing consumer ID to resume using a previous registration
              for this system. If the system's identity certificate is lost or corrupted,
              this option allows it to resume using its previous identity and subscriptions.
              The default is to not specify a consumer ID so a new ID is created.
        version_added: "2.1"
    force_register:
        description:
            -  Register the system even if it is already registered
        default: False
        type: bool
        version_added: "2.2"
notes:
    - In order to register a system, subscription-manager requires either a username and password, or an activationkey and an Organization ID.
requirements:
    - subscription-manager
'''

EXAMPLES = '''
- name: Register as user (joe_user) with password (somepass) and auto-subscribe to available content.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    auto_attach: true

- name: Same as above but subscribe to a specific pool by ID.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    pool_ids: 0123456789abcdef0123456789abcdef

- name: Register and subscribe to multiple pools.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    pool_ids:
      - 0123456789abcdef0123456789abcdef
      - 1123456789abcdef0123456789abcdef

- name: Same as above but consume multiple entitlements.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    pool_ids:
      - 0123456789abcdef0123456789abcdef: 2
      - 1123456789abcdef0123456789abcdef: 4

- name: Register and pull existing system data.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    consumer_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

- name: Register with activationkey and consume subscriptions matching Red Hat Enterprise Server or Red Hat Virtualization
  redhat_subscription:
    state: present
    activationkey: 1-222333444
    org_id: 222333444
    pool: '^(Red Hat Enterprise Server|Red Hat Virtualization)$'

- name: Update the consumed subscriptions from the previous example (remove Red Hat Virtualization subscription)
  redhat_subscription:
    state: present
    activationkey: 1-222333444
    org_id: 222333444
    pool: '^Red Hat Enterprise Server$'

- name: Register as user credentials into given environment (against Red Hat Satellite 6.x), and auto-subscribe.
  redhat_subscription:
    state: present
    username: joe_user
    password: somepass
    environment: Library
    auto_attach: true
'''

RETURN = '''
subscribed_pool_ids:
    description: List of pool IDs to which system is now subscribed
    returned: success
    type: complex
    contains: {
        "8a85f9815ab905d3015ab928c7005de4": "1"
    }
'''

import os
import re
import shutil
import tempfile
import types

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six.moves import configparser


SUBMAN_CMD = None


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
            tmpfd, tmpfile = tempfile.mkstemp()
            shutil.copy2(plugin_conf, tmpfile)
            cfg = configparser.ConfigParser()
            cfg.read([tmpfile])

            if enabled:
                cfg.set('main', 'enabled', 1)
            else:
                cfg.set('main', 'enabled', 0)

            fd = open(tmpfile, 'w+')
            cfg.write(fd)
            fd.close()
            self.module.atomic_move(tmpfile, plugin_conf)

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
        cp = configparser.ConfigParser()
        cp.read(rhsm_conf)

        # Add support for specifying a default value w/o having to standup some configuration
        # Yeah, I know this should be subclassed ... but, oh well
        def get_option_default(self, key, default=''):
            sect, opt = key.split('.', 1)
            if self.has_section(sect) and self.has_option(sect, opt):
                return self.get(sect, opt)
            else:
                return default

        cp.get_option = types.MethodType(get_option_default, cp, configparser.ConfigParser)

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
            Configure the system as directed for registration with RHSM
            Raises:
              * Exception - if error occurs while running command
        '''
        args = [SUBMAN_CMD, 'config']

        # Pass supplied **kwargs as parameters to subscription-manager.  Ignore
        # non-configuration parameters and replace '_' with '.'.  For example,
        # 'server_hostname' becomes '--server.hostname'.
        for k, v in kwargs.items():
            if re.search(r'^(server|rhsm)_', k):
                args.append('--%s=%s' % (k.replace('_', '.', 1), v))

        self.module.run_command(args, check_rc=True)

    @property
    def is_registered(self):
        '''
            Determine whether the current system is registered to RHSM.
            Returns:
              * Boolean - whether the current system is registered to
                          RHSM.
        '''

        args = [SUBMAN_CMD, 'identity']
        rc, stdout, stderr = self.module.run_command(args, check_rc=False)
        if rc == 0:
            return True
        else:
            return False

    def register(self, username, password, auto_attach, activationkey, org_id,
                 consumer_type, consumer_name, consumer_id, force_register, environment,
                 rhsm_baseurl, server_insecure, server_hostname, server_proxy_hostname,
                 server_proxy_port, server_proxy_user, server_proxy_password):
        '''
            Register the current system to the provided RHSM or Sat6 server
            Raises:
              * Exception - if error occurs while running command
        '''
        args = [SUBMAN_CMD, 'register']

        # Generate command arguments
        if force_register:
            args.extend(['--force'])

        if rhsm_baseurl:
            args.extend(['--baseurl', rhsm_baseurl])

        if server_insecure:
            args.extend(['--insecure'])

        if server_hostname:
            args.extend(['--serverurl', server_hostname])

        if activationkey:
            args.extend(['--activationkey', activationkey])
            args.extend(['--org', org_id])
        else:
            if auto_attach:
                args.append('--auto-attach')
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
            if environment:
                args.extend(['--environment', environment])
            if server_proxy_hostname and server_proxy_port:
                args.extend(['--proxy', server_proxy_hostname + ':' + server_proxy_port])
            if server_proxy_user:
                args.extend(['--proxyuser', server_proxy_user])
            if server_proxy_password:
                args.extend(['--proxypassword', server_proxy_password])

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
            args = [SUBMAN_CMD, 'unsubscribe'] + items
            rc, stderr, stdout = self.module.run_command(args, check_rc=True)
        return serials

    def unregister(self):
        '''
            Unregister a currently registered system
            Raises:
              * Exception - if error occurs while running command
        '''
        args = [SUBMAN_CMD, 'unregister']
        rc, stderr, stdout = self.module.run_command(args, check_rc=True)
        self.update_plugin_conf('rhnplugin', False)
        self.update_plugin_conf('subscription-manager', False)

    def get_matching_pools(self, regexp):
        '''
            Get list of pools available for subscription.
            Match regexp against available pool IDs first. If any pool IDs
            match, return those immediately.

            If no pool IDs match, then match regexp against available pool
            product names. Note that this can still easily match many pools.
            Then subscribe to those pools.

            Since a pool is a more specific match, we only fall back to
            matching against names if we didn't match pool IDs.

            Returns:
              * List - Matching pools
        '''
        available_pools = RhsmPools(self.module)

        # See https://github.com/ansible/ansible/issues/19466
        # Try to match pools whose pool ID matches regexp
        # This round, we are checking the pool ID ONLY
        matching_pools = list(available_pools.filter_pools(regexp))
        if not matching_pools:
            # We didn't match any pool IDs.
            # Now try to match pools based on product name.
            # Note: This can match lots of product names.
            matching_pools = list(available_pools.filter_products(regexp))

        return matching_pools

    def get_unavailable_pool_ids(self, pool_ids):
        '''
            Get list of requested pool IDs that are unavailable for
            subscription.

            Returns:
              * List - Unavailable pool IDs (sublist of requested pool IDs)
        '''
        available_pools = RhsmPools(self.module)
        available_pool_ids = [pool.get_pool_id() for pool in available_pools]
        unavailable_pool_ids = []

        for pool_id in pool_ids:
            if pool_id not in available_pool_ids:
                unavailable_pool_ids.append(pool_id)

        return unavailable_pool_ids

    def subscribe(self, regexp, matching_pools=None):
        '''
            Subscribe current system to available pools matching the specified
            regular expression.

            Returns:
              * List - subscribed pool IDs
            Raises:
              * Exception - if error occurs while running command, or no
                available pools match regexp
        '''
        if matching_pools is None:
            # Not initially registered or force-register is enabled
            matching_pools = self.get_matching_pools()
            if matching_pools is None:
                # We didn't match anything in previous step
                raise Exception("No matching pools for regexp '%s'" % regexp)

        subscribed_pool_ids = []
        for pool in matching_pools:
            pool.subscribe()
            subscribed_pool_ids.append(pool.get_pool_id())

        return subscribed_pool_ids

    def subscribe_by_pool_ids(self, pool_ids):
        '''
            Subscribe current system to available pools with pool IDs matching
            the specified list of pool IDs
            Returns:
              * List - subscribed pool IDs
            Raises:
              * Exception - if error occurs while running command, or any of
                the listed pool IDs are unavailable
        '''
        unavailable_pool_ids = self.get_unavailable_pool_ids()

        if unavailable_pool_ids:
            raise Exception('Pool IDs %s not available' % unavailable_pool_ids)

        for pool_id, quantity in pool_ids.items():
            args = [SUBMAN_CMD, 'attach', '--pool', pool_id, '--quantity', quantity]
            rc, stderr, stdout = self.module.run_command(args, check_rc=True)

        return pool_ids

    def update_subscriptions(self, regexp):
        '''
            Ensure subscribed to all pools matching regexp, and not subscribed
            to any that do not.

            Fall back to matching regexp against product names if no pool IDs
            are matched.

            Run if system is already registered and force-register is not
            enabled.

            Raises:
              * Exception - if error occurs while running command, or no pools
                match regexp
        '''
        changed = False
        matching_pools = self.get_matching_pools(self, regexp)

        if not matching_pools:
            raise Exception("No matching subscriptions for regexp '%s'" % regexp)

        consumed_pools = RhsmPools(self.module, consumed=True)

        pool_ids_to_keep = [p.get_pool_id() for p in consumed_pools.filter_pools(regexp)]
        pool_ids_to_keep.extend([p.get_pool_id() for p in consumed_pools.filter_products(regexp)])

        # Remove nonmatching serials first in case site is running low on
        # subscriptions.
        serials_to_remove = [p.Serial for p in consumed_pools if p.get_pool_id() not in pool_ids_to_keep]
        serials = self.unsubscribe(serials=serials_to_remove)

        subscribed_pool_ids = self.subscribe(regexp, matching_pools)

        if subscribed_pool_ids or serials:
            changed = True

        return {'changed': changed, 'subscribed_pool_ids': subscribed_pool_ids,
                'unsubscribed_serials': serials}

    def update_subscriptions_by_pool_ids(self, pool_ids):
        changed = False

        unavailable_pool_ids = self.get_unavailable_pool_ids(pool_ids)
        if unavailable_pool_ids:
            raise Exception('Pool IDs %s not available' % unavailable_pool_ids)

        consumed_pools = RhsmPools(self.module, consumed=True)
        existing_pools = {}
        for p in consumed_pools:
            existing_pools[p.get_pool_id()] = p.QuantityUsed

        missing_pools = {}
        for pool_id, quantity in pool_ids.items():
            if existing_pools.get(pool_id, 0) != quantity:
                missing_pools[pool_id] = quantity

        serials_to_remove = [p.Serial for p in consumed_pools if pool_ids.get(p.get_pool_id(), 0) != p.QuantityUsed]
        serials = self.unsubscribe(serials=serials_to_remove)

        self.subscribe_by_pool_ids(missing_pools)

        if missing_pools or serials:
            changed = True
        return {'changed': changed, 'subscribed_pool_ids': missing_pools.keys(),
                'unsubscribed_serials': serials}


class RhsmPool(object):
    '''
        Convenience class for housing subscription information
    '''

    def __init__(self, module, **kwargs):
        self.module = module
        for k, v in kwargs.items():
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
                (key, value) = line.split(':', 1)
                key = key.strip().replace(" ", "")  # To unify
                value = value.strip()
                if key in ['ProductName', 'SubscriptionName']:
                    # Remember the name for later processing
                    products.append(RhsmPool(self.module, _name=value, key=value))
                elif products:
                    # Associate value with most recently recorded product
                    products[-1].__setattr__(key, value)
                # FIXME - log some warning?
                # else:
                    # warnings.warn("Unhandled subscription key/value: %s/%s" % (key,value))
        return products

    def filter_pools(self, regexp='^$'):
        '''
            Return a list of RhsmPools whose pool id matches the provided regular expression
        '''
        r = re.compile(regexp)
        for product in self.products:
            if r.search(product.get_pool_id()):
                yield product

    def filter_products(self, regexp='^$'):
        '''
            Return a list of RhsmPools whose product name matches the provided regular expression
        '''
        r = re.compile(regexp)
        for product in self.products:
            if r.search(product._name):
                yield product


def main():

    # Load RHSM configuration from file
    rhsm = Rhsm(None)

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            username=dict(default=None),
            password=dict(default=None, no_log=True),
            server_hostname=dict(default=rhsm.config.get_option('server.hostname')),
            server_insecure=dict(default=rhsm.config.get_option('server.insecure')),
            rhsm_baseurl=dict(default=rhsm.config.get_option('rhsm.baseurl')),
            auto_attach=dict(aliases=['autosubscribe'], default=False, type='bool'),
            activationkey=dict(default=None),
            org_id=dict(default=None),
            environment=dict(default=None),
            pool=dict(default='^$'),
            pool_ids=dict(default=[], type='list'),
            consumer_type=dict(default=None),
            consumer_name=dict(default=None),
            consumer_id=dict(default=None),
            force_register=dict(default=False, type='bool'),
            server_proxy_hostname=dict(default=rhsm.config.get_option('server.proxy_hostname')),
            server_proxy_port=dict(default=rhsm.config.get_option('server.proxy_port')),
            server_proxy_user=dict(default=rhsm.config.get_option('server.proxy_user')),
            server_proxy_password=dict(default=rhsm.config.get_option('server.proxy_password'),
                                       no_log=True),
        ),
        required_together=[['username', 'password'], ['activationkey', 'org_id'],
                           ['server_proxy_hostname', 'server_proxy_port'], ['server_proxy_user', 'server_proxy_password']],
        mutually_exclusive=[['username', 'activationkey'], ['pool', 'pool_ids']],
        required_if=[['state', 'present', ['username', 'activationkey'], True]],
    )

    rhsm.module = module
    state = module.params['state']
    username = module.params['username']
    password = module.params['password']
    server_hostname = module.params['server_hostname']
    server_insecure = module.params['server_insecure']
    rhsm_baseurl = module.params['rhsm_baseurl']
    auto_attach = module.params['auto_attach']
    activationkey = module.params['activationkey']
    org_id = module.params['org_id']
    environment = module.params['environment']
    pool = module.params['pool']
    pool_ids = {}
    for value in module.params['pool_ids']:
        if isinstance(value, dict):
            if len(value) != 1:
                module.fail_json(msg='Unable to parse pool_ids option.')
            pool_id, quantity = value.items()[0]
        else:
            pool_id, quantity = value, 1
        pool_ids[pool_id] = str(quantity)
    consumer_type = module.params['consumer_type']
    consumer_name = module.params['consumer_name']
    consumer_id = module.params['consumer_id']
    force_register = module.params['force_register']
    server_proxy_hostname = module.params['server_proxy_hostname']
    server_proxy_port = module.params['server_proxy_port']
    server_proxy_user = module.params['server_proxy_user']
    server_proxy_password = module.params['server_proxy_password']

    global SUBMAN_CMD
    SUBMAN_CMD = module.get_bin_path('subscription-manager', True)

    # Ensure system is registered
    if state == 'present':

        # Register system
        if rhsm.is_registered and not force_register:
            if pool != '^$' or pool_ids:
                try:
                    if pool_ids:
                        result = rhsm.update_subscriptions_by_pool_ids(pool_ids)
                    else:
                        result = rhsm.update_subscriptions(pool)
                except Exception as e:
                    module.fail_json(msg="Failed to update subscriptions for '%s': %s" % (server_hostname, e))
                else:
                    module.exit_json(**result)
            else:
                module.exit_json(changed=False, msg="System already registered.")
        else:
            try:
                rhsm.enable()
                rhsm.configure(**module.params)
                rhsm.register(username, password, auto_attach, activationkey, org_id,
                              consumer_type, consumer_name, consumer_id, force_register,
                              environment, rhsm_baseurl, server_insecure, server_hostname,
                              server_proxy_hostname, server_proxy_port, server_proxy_user, server_proxy_password)
                if pool_ids:
                    subscribed_pool_ids = rhsm.subscribe_by_pool_ids(pool_ids)
                else:
                    subscribed_pool_ids = rhsm.subscribe(pool)
            except Exception as e:
                module.fail_json(msg="Failed to register with '%s': %s" % (server_hostname, e))
            else:
                module.exit_json(changed=True,
                                 msg="System successfully registered to '%s'." % server_hostname,
                                 subscribed_pool_ids=subscribed_pool_ids)
    # Ensure system is *not* registered
    if state == 'absent':
        if not rhsm.is_registered:
            module.exit_json(changed=False, msg="System already unregistered.")
        else:
            try:
                rhsm.unsubscribe()
                rhsm.unregister()
            except Exception as e:
                module.fail_json(msg="Failed to unregister: %s" % e)
            else:
                module.exit_json(changed=True, msg="System successfully unregistered from %s." % server_hostname)


if __name__ == '__main__':
    main()
