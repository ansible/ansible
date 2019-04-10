#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is largely copied from the Nagios module included in the
# Func project. Original copyright follows:
#
# func-nagios - Schedule downtime and enables/disable notifications
# Copyright 2011, Red Hat, Inc.
# Tim Bielawa <tbielawa@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nagios
short_description: Perform common tasks in Nagios related to downtime and notifications.
description:
  - "The C(nagios) module has two basic functions: scheduling downtime and toggling alerts for services or hosts."
  - All actions require the I(host) parameter to be given explicitly. In playbooks you can use the C({{inventory_hostname}}) variable to refer
    to the host the playbook is currently running on.
  - You can specify multiple services at once by separating them with commas, .e.g., C(services=httpd,nfs,puppet).
  - When specifying what service to handle there is a special service value, I(host), which will handle alerts/downtime for the I(host itself),
    e.g., C(service=host). This keyword may not be given with other services at the same time.
    I(Setting alerts/downtime for a host does not affect alerts/downtime for any of the services running on it.) To schedule downtime for all
    services on particular host use keyword "all", e.g., C(service=all).
  - When using the C(nagios) module you will need to specify your Nagios server using the C(delegate_to) parameter.
version_added: "0.7"
options:
  action:
    description:
      - Action to take.
      - servicegroup options were added in 2.0.
      - delete_downtime options were added in 2.2.
    required: true
    choices: [ "downtime", "delete_downtime", "enable_alerts", "disable_alerts", "silence", "unsilence",
               "silence_nagios", "unsilence_nagios", "command", "servicegroup_service_downtime",
               "servicegroup_host_downtime" ]
  host:
    description:
      - Host to operate on in Nagios.
  cmdfile:
    description:
      - Path to the nagios I(command file) (FIFO pipe).
        Only required if auto-detection fails.
    default: auto-detected
  author:
    description:
     - Author to leave downtime comments as.
       Only usable with the C(downtime) action.
    default: Ansible
  comment:
    version_added: "2.0"
    description:
     - Comment for C(downtime) action.
    default: Scheduling downtime
  minutes:
    description:
      - Minutes to schedule downtime for.
      - Only usable with the C(downtime) action.
    default: 30
  services:
    description:
      - What to manage downtime/alerts for. Separate multiple services with commas.
        C(service) is an alias for C(services).
        B(Required) option when using the C(downtime), C(enable_alerts), and C(disable_alerts) actions.
    aliases: [ "service" ]
    required: true
  servicegroup:
    version_added: "2.0"
    description:
      - The Servicegroup we want to set downtimes/alerts for.
        B(Required) option when using the C(servicegroup_service_downtime) amd C(servicegroup_host_downtime).
  command:
    description:
      - The raw command to send to nagios, which
        should not include the submitted time header or the line-feed
        B(Required) option when using the C(command) action.
    required: true

author: "Tim Bielawa (@tbielawa)"
'''

EXAMPLES = '''
# set 30 minutes of apache downtime
- nagios:
    action: downtime
    minutes: 30
    service: httpd
    host: '{{ inventory_hostname }}'

# schedule an hour of HOST downtime
- nagios:
    action: downtime
    minutes: 60
    service: host
    host: '{{ inventory_hostname }}'

# schedule an hour of HOST downtime, with a comment describing the reason
- nagios:
    action: downtime
    minutes: 60
    service: host
    host: '{{ inventory_hostname }}'
    comment: Rebuilding machine

# schedule downtime for ALL services on HOST
- nagios:
    action: downtime
    minutes: 45
    service: all
    host: '{{ inventory_hostname }}'

# schedule downtime for a few services
- nagios:
    action: downtime
    services: frob,foobar,qeuz
    host: '{{ inventory_hostname }}'

# set 30 minutes downtime for all services in servicegroup foo
- nagios:
    action: servicegroup_service_downtime
    minutes: 30
    servicegroup: foo
    host: '{{ inventory_hostname }}'

# set 30 minutes downtime for all host in servicegroup foo
- nagios:
    action: servicegroup_host_downtime
    minutes: 30
    servicegroup: foo
    host: '{{ inventory_hostname }}'

# delete all downtime for a given host
- nagios:
    action: delete_downtime
    host: '{{ inventory_hostname }}'
    service: all

# delete all downtime for HOST with a particular comment
- nagios:
    action: delete_downtime
    host: '{{ inventory_hostname }}'
    service: host
    comment: Planned maintenance

# enable SMART disk alerts
- nagios:
    action: enable_alerts
    service: smart
    host: '{{ inventory_hostname }}'

# "two services at once: disable httpd and nfs alerts"
- nagios:
    action: disable_alerts
    service: httpd,nfs
    host: '{{ inventory_hostname }}'

# disable HOST alerts
- nagios:
    action: disable_alerts
    service: host
    host: '{{ inventory_hostname }}'

# silence ALL alerts
- nagios:
    action: silence
    host: '{{ inventory_hostname }}'

# unsilence all alerts
- nagios:
    action: unsilence
    host: '{{ inventory_hostname }}'

# SHUT UP NAGIOS
- nagios:
    action: silence_nagios

# ANNOY ME NAGIOS
- nagios:
    action: unsilence_nagios

# command something
- nagios:
    action: command
    command: DISABLE_FAILURE_PREDICTION
'''

import types
import time
import os.path

from ansible.module_utils.basic import AnsibleModule


######################################################################

def which_cmdfile():
    locations = [
        # rhel
        '/etc/nagios/nagios.cfg',
        # debian
        '/etc/nagios3/nagios.cfg',
        # older debian
        '/etc/nagios2/nagios.cfg',
        # bsd, solaris
        '/usr/local/etc/nagios/nagios.cfg',
        # groundwork it monitoring
        '/usr/local/groundwork/nagios/etc/nagios.cfg',
        # open monitoring distribution
        '/omd/sites/oppy/tmp/nagios/nagios.cfg',
        # ???
        '/usr/local/nagios/etc/nagios.cfg',
        '/usr/local/nagios/nagios.cfg',
        '/opt/nagios/etc/nagios.cfg',
        '/opt/nagios/nagios.cfg',
        # icinga on debian/ubuntu
        '/etc/icinga/icinga.cfg',
        # icinga installed from source (default location)
        '/usr/local/icinga/etc/icinga.cfg',
    ]

    for path in locations:
        if os.path.exists(path):
            for line in open(path):
                if line.startswith('command_file'):
                    return line.split('=')[1].strip()

    return None

######################################################################


def main():
    ACTION_CHOICES = [
        'downtime',
        'delete_downtime',
        'silence',
        'unsilence',
        'enable_alerts',
        'disable_alerts',
        'silence_nagios',
        'unsilence_nagios',
        'command',
        'servicegroup_host_downtime',
        'servicegroup_service_downtime',
    ]

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, default=None, choices=ACTION_CHOICES),
            author=dict(default='Ansible'),
            comment=dict(default='Scheduling downtime'),
            host=dict(required=False, default=None),
            servicegroup=dict(required=False, default=None),
            minutes=dict(default=30, type='int'),
            cmdfile=dict(default=which_cmdfile()),
            services=dict(default=None, aliases=['service']),
            command=dict(required=False, default=None),
        )
    )

    action = module.params['action']
    host = module.params['host']
    servicegroup = module.params['servicegroup']
    minutes = module.params['minutes']
    services = module.params['services']
    cmdfile = module.params['cmdfile']
    command = module.params['command']

    ##################################################################
    # Required args per action:
    # downtime = (minutes, service, host)
    # (un)silence = (host)
    # (enable/disable)_alerts = (service, host)
    # command = command
    #
    # AnsibleModule will verify most stuff, we need to verify
    # 'minutes' and 'service' manually.

    ##################################################################
    if action not in ['command', 'silence_nagios', 'unsilence_nagios']:
        if not host:
            module.fail_json(msg='no host specified for action requiring one')
    ######################################################################
    if action == 'downtime':
        # Make sure there's an actual service selected
        if not services:
            module.fail_json(msg='no service selected to set downtime for')
        # Make sure minutes is a number
        try:
            m = int(minutes)
            if not isinstance(m, types.IntType):
                module.fail_json(msg='minutes must be a number')
        except Exception:
            module.fail_json(msg='invalid entry for minutes')

    ######################################################################
    if action == 'delete_downtime':
        # Make sure there's an actual service selected
        if not services:
            module.fail_json(msg='no service selected to set downtime for')

    ######################################################################

    if action in ['servicegroup_service_downtime', 'servicegroup_host_downtime']:
        # Make sure there's an actual servicegroup selected
        if not servicegroup:
            module.fail_json(msg='no servicegroup selected to set downtime for')
        # Make sure minutes is a number
        try:
            m = int(minutes)
            if not isinstance(m, types.IntType):
                module.fail_json(msg='minutes must be a number')
        except Exception:
            module.fail_json(msg='invalid entry for minutes')

    ##################################################################
    if action in ['enable_alerts', 'disable_alerts']:
        if not services:
            module.fail_json(msg='a service is required when setting alerts')

    if action in ['command']:
        if not command:
            module.fail_json(msg='no command passed for command action')
    ##################################################################
    if not cmdfile:
        module.fail_json(msg='unable to locate nagios.cfg')

    ##################################################################
    ansible_nagios = Nagios(module, **module.params)
    if module.check_mode:
        module.exit_json(changed=True)
    else:
        ansible_nagios.act()
    ##################################################################


######################################################################
class Nagios(object):
    """
    Perform common tasks in Nagios related to downtime and
    notifications.

    The complete set of external commands Nagios handles is documented
    on their website:

    http://old.nagios.org/developerinfo/externalcommands/commandlist.php

    Note that in the case of `schedule_svc_downtime`,
    `enable_svc_notifications`, and `disable_svc_notifications`, the
    service argument should be passed as a list.
    """

    def __init__(self, module, **kwargs):
        self.module = module
        self.action = kwargs['action']
        self.author = kwargs['author']
        self.comment = kwargs['comment']
        self.host = kwargs['host']
        self.servicegroup = kwargs['servicegroup']
        self.minutes = int(kwargs['minutes'])
        self.cmdfile = kwargs['cmdfile']
        self.command = kwargs['command']

        if (kwargs['services'] is None) or (kwargs['services'] == 'host') or (kwargs['services'] == 'all'):
            self.services = kwargs['services']
        else:
            self.services = kwargs['services'].split(',')

        self.command_results = []

    def _now(self):
        """
        The time in seconds since 12:00:00AM Jan 1, 1970
        """

        return int(time.time())

    def _write_command(self, cmd):
        """
        Write the given command to the Nagios command file
        """

        try:
            fp = open(self.cmdfile, 'w')
            fp.write(cmd)
            fp.flush()
            fp.close()
            self.command_results.append(cmd.strip())
        except IOError:
            self.module.fail_json(msg='unable to write to nagios command file',
                                  cmdfile=self.cmdfile)

    def _fmt_dt_str(self, cmd, host, duration, author=None,
                    comment=None, start=None,
                    svc=None, fixed=1, trigger=0):
        """
        Format an external-command downtime string.

        cmd - Nagios command ID
        host - Host schedule downtime on
        duration - Minutes to schedule downtime for
        author - Name to file the downtime as
        comment - Reason for running this command (upgrade, reboot, etc)
        start - Start of downtime in seconds since 12:00AM Jan 1 1970
          Default is to use the entry time (now)
        svc - Service to schedule downtime for, omit when for host downtime
        fixed - Start now if 1, start when a problem is detected if 0
        trigger - Optional ID of event to start downtime from. Leave as 0 for
          fixed downtime.

        Syntax: [submitted] COMMAND;<host_name>;[<service_description>]
        <start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;
        <comment>
        """

        entry_time = self._now()
        if start is None:
            start = entry_time

        hdr = "[%s] %s;%s;" % (entry_time, cmd, host)
        duration_s = (duration * 60)
        end = start + duration_s

        if not author:
            author = self.author

        if not comment:
            comment = self.comment

        if svc is not None:
            dt_args = [svc, str(start), str(end), str(fixed), str(trigger),
                       str(duration_s), author, comment]
        else:
            # Downtime for a host if no svc specified
            dt_args = [str(start), str(end), str(fixed), str(trigger),
                       str(duration_s), author, comment]

        dt_arg_str = ";".join(dt_args)
        dt_str = hdr + dt_arg_str + "\n"

        return dt_str

    def _fmt_dt_del_str(self, cmd, host, svc=None, start=None, comment=None):
        """
        Format an external-command downtime deletion string.

        cmd - Nagios command ID
        host - Host to remove scheduled downtime from
        comment - Reason downtime was added (upgrade, reboot, etc)
        start - Start of downtime in seconds since 12:00AM Jan 1 1970
        svc - Service to remove downtime for, omit to remove all downtime for the host

        Syntax: [submitted] COMMAND;<host_name>;
        [<service_desription>];[<start_time>];[<comment>]
        """

        entry_time = self._now()
        hdr = "[%s] %s;%s;" % (entry_time, cmd, host)

        if comment is None:
            comment = self.comment

        dt_del_args = []
        if svc is not None:
            dt_del_args.append(svc)
        else:
            dt_del_args.append('')

        if start is not None:
            dt_del_args.append(str(start))
        else:
            dt_del_args.append('')

        if comment is not None:
            dt_del_args.append(comment)
        else:
            dt_del_args.append('')

        dt_del_arg_str = ";".join(dt_del_args)
        dt_del_str = hdr + dt_del_arg_str + "\n"

        return dt_del_str

    def _fmt_notif_str(self, cmd, host=None, svc=None):
        """
        Format an external-command notification string.

        cmd - Nagios command ID.
        host - Host to en/disable notifications on.. A value is not required
          for global downtime
        svc - Service to schedule downtime for. A value is not required
          for host downtime.

        Syntax: [submitted] COMMAND;<host_name>[;<service_description>]
        """

        entry_time = self._now()
        notif_str = "[%s] %s" % (entry_time, cmd)
        if host is not None:
            notif_str += ";%s" % host

            if svc is not None:
                notif_str += ";%s" % svc

        notif_str += "\n"

        return notif_str

    def schedule_svc_downtime(self, host, services=None, minutes=30):
        """
        This command is used to schedule downtime for a particular
        service.

        During the specified downtime, Nagios will not send
        notifications out about the service.

        Syntax: SCHEDULE_SVC_DOWNTIME;<host_name>;<service_description>
        <start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;
        <comment>
        """

        cmd = "SCHEDULE_SVC_DOWNTIME"

        if services is None:
            services = []

        for service in services:
            dt_cmd_str = self._fmt_dt_str(cmd, host, minutes, svc=service)
            self._write_command(dt_cmd_str)

    def schedule_host_downtime(self, host, minutes=30):
        """
        This command is used to schedule downtime for a particular
        host.

        During the specified downtime, Nagios will not send
        notifications out about the host.

        Syntax: SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>
        """

        cmd = "SCHEDULE_HOST_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, host, minutes)
        self._write_command(dt_cmd_str)

    def schedule_host_svc_downtime(self, host, minutes=30):
        """
        This command is used to schedule downtime for
        all services associated with a particular host.

        During the specified downtime, Nagios will not send
        notifications out about the host.

        SCHEDULE_HOST_SVC_DOWNTIME;<host_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>
        """

        cmd = "SCHEDULE_HOST_SVC_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, host, minutes)
        self._write_command(dt_cmd_str)

    def delete_host_downtime(self, host, services=None, comment=None):
        """
        This command is used to remove scheduled downtime for a particular
        host.

        Syntax: DEL_DOWNTIME_BY_HOST_NAME;<host_name>;
        [<service_desription>];[<start_time>];[<comment>]
        """

        cmd = "DEL_DOWNTIME_BY_HOST_NAME"

        if services is None:
            dt_del_cmd_str = self._fmt_dt_del_str(cmd, host, comment=comment)
            self._write_command(dt_del_cmd_str)
        else:
            for service in services:
                dt_del_cmd_str = self._fmt_dt_del_str(cmd, host, svc=service, comment=comment)
                self._write_command(dt_del_cmd_str)

    def schedule_hostgroup_host_downtime(self, hostgroup, minutes=30):
        """
        This command is used to schedule downtime for all hosts in a
        particular hostgroup.

        During the specified downtime, Nagios will not send
        notifications out about the hosts.

        Syntax: SCHEDULE_HOSTGROUP_HOST_DOWNTIME;<hostgroup_name>;<start_time>;
        <end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
        """

        cmd = "SCHEDULE_HOSTGROUP_HOST_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, hostgroup, minutes)
        self._write_command(dt_cmd_str)

    def schedule_hostgroup_svc_downtime(self, hostgroup, minutes=30):
        """
        This command is used to schedule downtime for all services in
        a particular hostgroup.

        During the specified downtime, Nagios will not send
        notifications out about the services.

        Note that scheduling downtime for services does not
        automatically schedule downtime for the hosts those services
        are associated with.

        Syntax: SCHEDULE_HOSTGROUP_SVC_DOWNTIME;<hostgroup_name>;<start_time>;
        <end_time>;<fixed>;<trigger_id>;<duration>;<author>;<comment>
        """

        cmd = "SCHEDULE_HOSTGROUP_SVC_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, hostgroup, minutes)
        self._write_command(dt_cmd_str)

    def schedule_servicegroup_host_downtime(self, servicegroup, minutes=30):
        """
        This command is used to schedule downtime for all hosts in a
        particular servicegroup.

        During the specified downtime, Nagios will not send
        notifications out about the hosts.

        Syntax: SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;<servicegroup_name>;
        <start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;
        <comment>
        """

        cmd = "SCHEDULE_SERVICEGROUP_HOST_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, servicegroup, minutes)
        self._write_command(dt_cmd_str)

    def schedule_servicegroup_svc_downtime(self, servicegroup, minutes=30):
        """
        This command is used to schedule downtime for all services in
        a particular servicegroup.

        During the specified downtime, Nagios will not send
        notifications out about the services.

        Note that scheduling downtime for services does not
        automatically schedule downtime for the hosts those services
        are associated with.

        Syntax: SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;<servicegroup_name>;
        <start_time>;<end_time>;<fixed>;<trigger_id>;<duration>;<author>;
        <comment>
        """

        cmd = "SCHEDULE_SERVICEGROUP_SVC_DOWNTIME"
        dt_cmd_str = self._fmt_dt_str(cmd, servicegroup, minutes)
        self._write_command(dt_cmd_str)

    def disable_host_svc_notifications(self, host):
        """
        This command is used to prevent notifications from being sent
        out for all services on the specified host.

        Note that this command does not disable notifications from
        being sent out about the host.

        Syntax: DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>
        """

        cmd = "DISABLE_HOST_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, host)
        self._write_command(notif_str)

    def disable_host_notifications(self, host):
        """
        This command is used to prevent notifications from being sent
        out for the specified host.

        Note that this command does not disable notifications for
        services associated with this host.

        Syntax: DISABLE_HOST_NOTIFICATIONS;<host_name>
        """

        cmd = "DISABLE_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, host)
        self._write_command(notif_str)

    def disable_svc_notifications(self, host, services=None):
        """
        This command is used to prevent notifications from being sent
        out for the specified service.

        Note that this command does not disable notifications from
        being sent out about the host.

        Syntax: DISABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
        """

        cmd = "DISABLE_SVC_NOTIFICATIONS"

        if services is None:
            services = []

        for service in services:
            notif_str = self._fmt_notif_str(cmd, host, svc=service)
            self._write_command(notif_str)

    def disable_servicegroup_host_notifications(self, servicegroup):
        """
        This command is used to prevent notifications from being sent
        out for all hosts in the specified servicegroup.

        Note that this command does not disable notifications for
        services associated with hosts in this service group.

        Syntax: DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
        """

        cmd = "DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, servicegroup)
        self._write_command(notif_str)

    def disable_servicegroup_svc_notifications(self, servicegroup):
        """
        This command is used to prevent notifications from being sent
        out for all services in the specified servicegroup.

        Note that this does not prevent notifications from being sent
        out about the hosts in this servicegroup.

        Syntax: DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
        """

        cmd = "DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, servicegroup)
        self._write_command(notif_str)

    def disable_hostgroup_host_notifications(self, hostgroup):
        """
        Disables notifications for all hosts in a particular
        hostgroup.

        Note that this does not disable notifications for the services
        associated with the hosts in the hostgroup - see the
        DISABLE_HOSTGROUP_SVC_NOTIFICATIONS command for that.

        Syntax: DISABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
        """

        cmd = "DISABLE_HOSTGROUP_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, hostgroup)
        self._write_command(notif_str)

    def disable_hostgroup_svc_notifications(self, hostgroup):
        """
        Disables notifications for all services associated with hosts
        in a particular hostgroup.

        Note that this does not disable notifications for the hosts in
        the hostgroup - see the DISABLE_HOSTGROUP_HOST_NOTIFICATIONS
        command for that.

        Syntax: DISABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
        """

        cmd = "DISABLE_HOSTGROUP_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, hostgroup)
        self._write_command(notif_str)

    def enable_host_notifications(self, host):
        """
        Enables notifications for a particular host.

        Note that this command does not enable notifications for
        services associated with this host.

        Syntax: ENABLE_HOST_NOTIFICATIONS;<host_name>
        """

        cmd = "ENABLE_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, host)
        self._write_command(notif_str)

    def enable_host_svc_notifications(self, host):
        """
        Enables notifications for all services on the specified host.

        Note that this does not enable notifications for the host.

        Syntax: ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>
        """

        cmd = "ENABLE_HOST_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, host)
        nagios_return = self._write_command(notif_str)

        if nagios_return:
            return notif_str
        else:
            return "Fail: could not write to the command file"

    def enable_svc_notifications(self, host, services=None):
        """
        Enables notifications for a particular service.

        Note that this does not enable notifications for the host.

        Syntax: ENABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>
        """

        cmd = "ENABLE_SVC_NOTIFICATIONS"

        if services is None:
            services = []

        nagios_return = True
        return_str_list = []
        for service in services:
            notif_str = self._fmt_notif_str(cmd, host, svc=service)
            nagios_return = self._write_command(notif_str) and nagios_return
            return_str_list.append(notif_str)

        if nagios_return:
            return return_str_list
        else:
            return "Fail: could not write to the command file"

    def enable_hostgroup_host_notifications(self, hostgroup):
        """
        Enables notifications for all hosts in a particular hostgroup.

        Note that this command does not enable notifications for
        services associated with the hosts in this hostgroup.

        Syntax: ENABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>
        """

        cmd = "ENABLE_HOSTGROUP_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, hostgroup)
        nagios_return = self._write_command(notif_str)

        if nagios_return:
            return notif_str
        else:
            return "Fail: could not write to the command file"

    def enable_hostgroup_svc_notifications(self, hostgroup):
        """
        Enables notifications for all services that are associated
        with hosts in a particular hostgroup.

        Note that this does not enable notifications for the hosts in
        this hostgroup.

        Syntax: ENABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>
        """

        cmd = "ENABLE_HOSTGROUP_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, hostgroup)
        nagios_return = self._write_command(notif_str)

        if nagios_return:
            return notif_str
        else:
            return "Fail: could not write to the command file"

    def enable_servicegroup_host_notifications(self, servicegroup):
        """
        Enables notifications for all hosts that have services that
        are members of a particular servicegroup.

        Note that this command does not enable notifications for
        services associated with the hosts in this servicegroup.

        Syntax: ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>
        """

        cmd = "ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, servicegroup)
        nagios_return = self._write_command(notif_str)

        if nagios_return:
            return notif_str
        else:
            return "Fail: could not write to the command file"

    def enable_servicegroup_svc_notifications(self, servicegroup):
        """
        Enables notifications for all services that are members of a
        particular servicegroup.

        Note that this does not enable notifications for the hosts in
        this servicegroup.

        Syntax: ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>
        """

        cmd = "ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS"
        notif_str = self._fmt_notif_str(cmd, servicegroup)
        nagios_return = self._write_command(notif_str)

        if nagios_return:
            return notif_str
        else:
            return "Fail: could not write to the command file"

    def silence_host(self, host):
        """
        This command is used to prevent notifications from being sent
        out for the host and all services on the specified host.

        This is equivalent to calling disable_host_svc_notifications
        and disable_host_notifications.

        Syntax: DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>
        Syntax: DISABLE_HOST_NOTIFICATIONS;<host_name>
        """

        cmd = [
            "DISABLE_HOST_SVC_NOTIFICATIONS",
            "DISABLE_HOST_NOTIFICATIONS"
        ]
        nagios_return = True
        return_str_list = []
        for c in cmd:
            notif_str = self._fmt_notif_str(c, host)
            nagios_return = self._write_command(notif_str) and nagios_return
            return_str_list.append(notif_str)

        if nagios_return:
            return return_str_list
        else:
            return "Fail: could not write to the command file"

    def unsilence_host(self, host):
        """
        This command is used to enable notifications for the host and
        all services on the specified host.

        This is equivalent to calling enable_host_svc_notifications
        and enable_host_notifications.

        Syntax: ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>
        Syntax: ENABLE_HOST_NOTIFICATIONS;<host_name>
        """

        cmd = [
            "ENABLE_HOST_SVC_NOTIFICATIONS",
            "ENABLE_HOST_NOTIFICATIONS"
        ]
        nagios_return = True
        return_str_list = []
        for c in cmd:
            notif_str = self._fmt_notif_str(c, host)
            nagios_return = self._write_command(notif_str) and nagios_return
            return_str_list.append(notif_str)

        if nagios_return:
            return return_str_list
        else:
            return "Fail: could not write to the command file"

    def silence_nagios(self):
        """
        This command is used to disable notifications for all hosts and services
        in nagios.

        This is a 'SHUT UP, NAGIOS' command
        """
        cmd = 'DISABLE_NOTIFICATIONS'
        self._write_command(self._fmt_notif_str(cmd))

    def unsilence_nagios(self):
        """
        This command is used to enable notifications for all hosts and services
        in nagios.

        This is a 'OK, NAGIOS, GO'' command
        """
        cmd = 'ENABLE_NOTIFICATIONS'
        self._write_command(self._fmt_notif_str(cmd))

    def nagios_cmd(self, cmd):
        """
        This sends an arbitrary command to nagios

        It prepends the submitted time and appends a \n

        You just have to provide the properly formatted command
        """

        pre = '[%s]' % int(time.time())

        post = '\n'
        cmdstr = '%s %s%s' % (pre, cmd, post)
        self._write_command(cmdstr)

    def act(self):
        """
        Figure out what you want to do from ansible, and then do the
        needful (at the earliest).
        """
        # host or service downtime?
        if self.action == 'downtime':
            if self.services == 'host':
                self.schedule_host_downtime(self.host, self.minutes)
            elif self.services == 'all':
                self.schedule_host_svc_downtime(self.host, self.minutes)
            else:
                self.schedule_svc_downtime(self.host,
                                           services=self.services,
                                           minutes=self.minutes)

        elif self.action == 'delete_downtime':
            if self.services == 'host':
                self.delete_host_downtime(self.host)
            elif self.services == 'all':
                self.delete_host_downtime(self.host, comment='')
            else:
                self.delete_host_downtime(self.host, services=self.services)

        elif self.action == "servicegroup_host_downtime":
            if self.servicegroup:
                self.schedule_servicegroup_host_downtime(servicegroup=self.servicegroup, minutes=self.minutes)
        elif self.action == "servicegroup_service_downtime":
            if self.servicegroup:
                self.schedule_servicegroup_svc_downtime(servicegroup=self.servicegroup, minutes=self.minutes)

        # toggle the host AND service alerts
        elif self.action == 'silence':
            self.silence_host(self.host)

        elif self.action == 'unsilence':
            self.unsilence_host(self.host)

        # toggle host/svc alerts
        elif self.action == 'enable_alerts':
            if self.services == 'host':
                self.enable_host_notifications(self.host)
            elif self.services == 'all':
                self.enable_host_svc_notifications(self.host)
            else:
                self.enable_svc_notifications(self.host,
                                              services=self.services)

        elif self.action == 'disable_alerts':
            if self.services == 'host':
                self.disable_host_notifications(self.host)
            elif self.services == 'all':
                self.disable_host_svc_notifications(self.host)
            else:
                self.disable_svc_notifications(self.host,
                                               services=self.services)
        elif self.action == 'silence_nagios':
            self.silence_nagios()

        elif self.action == 'unsilence_nagios':
            self.unsilence_nagios()

        elif self.action == 'command':
            self.nagios_cmd(self.command)

        # wtf?
        else:
            self.module.fail_json(msg="unknown action specified: '%s'" %
                                      self.action)

        self.module.exit_json(nagios_commands=self.command_results,
                              changed=True)


if __name__ == '__main__':
    main()
