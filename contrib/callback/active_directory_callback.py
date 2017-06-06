# This plugin for ansible is intended to manage acquiring and destroying
# kerberos / windows domain credentials.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import subprocess
from subprocess import Popen, PIPE
from ansible import errors

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    """
    This callback module is intended to manage acquiring and disposing
    of kerberos / windows domain credentials.
    A new credential cache is created for each run and the contents
    of the cache are destroyed when the run completes.
    It needs to be able to find kinit, klist and kdestroy
    Because a ticket is good for all machines on a domain,
    a ticket is cached for the first host found from inventory.
    
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE= 'aggregate'
    CALLBACK_NAME = 'active_directory_callback'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):

        super(CallbackModule, self).__init__()

        self._display.vv('active_directory_callback: plugin activated')
        self.cache_count = 0

    def __del__(self):

        credential_cache = os.environ['KRB5CCNAME']
        self._display.vv("active_directory_callback: Leaving domains and removing all tickets from credential cache: %s" % (credential_cache))
        self._display.vv('active_directory_callback: plugin deactivated')
        self.destroy_all_tickets(credential_cache)

    def run_kerberos_command(self, command_and_args, password):

        try:
            cmd = subprocess.Popen(command_and_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if password:
               stdout, stderr = cmd.communicate('%s\n' % password)
            else:
               stdout, stderr = cmd.communicate()
            if stderr:
                stderr_lines = stderr.decode('ascii').splitlines()
                if stderr_lines:
                    self._display.vv( "active_directory_callback: STDERR Error when running %s - message was: %s" % (command_and_args[0], stderr_lines) )
            return cmd.returncode
        except OSError:
            raise errors.AnsibleError("%s is not installed in %s.  Please check you have installed krb-user/krb5-workstation and can run kinit, klist and kdestroy from the command line" % (command_and_args[0], command_and_args[1]))
        except IOError:
            raise errors.AnsibleError("could not authenticate as %s.  Please check winrm group vars are correctly configured." % (command_and_args[1]))

    def cache_new_ticket(self, userAtDomain, password):

        command_and_args = ['kinit', '%s' % (userAtDomain) ]
        result = self.run_kerberos_command(command_and_args, password)
        self._display.vv('active_directory_callback: cache new ticket return code was %s' % (result))
        if result == 0:
            self.cache_count += 1

    def destroy_all_tickets(self, credential_cache):

        command_and_args = ['kdestroy']
        self.run_kerberos_command(command_and_args, None)

    def set_ticket_cache(self):

        self.ticket_cache = '/tmp/krb5cc_ansible-%s' % (os.getpid())
        #print "active_directory_callback: Caching credentials to %s" % (ticket_cache)
        os.environ['KRB5CCNAME'] = self.ticket_cache

    def v2_playbook_on_play_start(self, *args, **kwargs):

        self._display.vv( "active_directory_callback: Checking for domains to join... " )
        self.set_ticket_cache()
        hosts = args[0].get_variable_manager()._inventory.get_hosts()
        for host in hosts:
            if self.cache_count > 0:
                return
            else:
                self._display.vv( "active_directory_callback: Considering host: %s" % (host))
                host_grp_vars = host.get_group_vars()
                if ('ansible_user' in host_grp_vars):
                    if ("@" in host_grp_vars['ansible_user']):
                        self._display.vv( "active_directory_callback: Host %s is configured for windows domain connection.  Looking for ticket for %s ..." % (host, host_grp_vars['ansible_user']))
                        self.cache_new_ticket(host_grp_vars['ansible_user'], host_grp_vars['ansible_password'])

        self._display.vv( "active_directory_callback: Completed windows domain join checking." )

