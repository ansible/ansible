#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2012, Dane Summers <dsummers@pinedesk.biz>
# (c) 2013, Mike Grozak  <mike.grozak@gmail.com>
# (c) 2013, Patrick Callahan <pmc@patrickcallahan.com>
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
#
# Cron Plugin: The goal of this plugin is to provide an indempotent method for
# setting up cron jobs on a host. The script will play well with other manually
# entered crons. Each cron job entered will be preceded with a comment
# describing the job so that it can be found later, which is required to be
# present in order for this plugin to find/modify the job.
#
# This module is based on python-crontab by Martin Owens.
#

DOCUMENTATION = """
---
module: cron
short_description: Manage cron.d and crontab entries.
description:
  - Use this module to manage crontab entries. This module allows you to create named
    crontab entries, update, or delete them.
  - 'The module includes one line with the description of the crontab entry C("#Ansible: <name>")
    corresponding to the "name" passed to the module, which is used by future ansible/module calls
    to find/check the state.  The "name" parameter should be unique, and changing the "name" value
    will result in a new cron task being created (or a different one being removed)'
version_added: "0.9"
options:
  name:
    description:
      - Description of a crontab entry.
    default: null
    required: true
  user:
    description:
      - The specific user whose crontab should be modified.
    required: false
    default: root
  job:
    description:
      - The command to execute. Required if state=present.
    required: false
    default: null
  state:
    description:
      - Whether to ensure the job is present or absent.
    required: false
    default: present
    choices: [ "present", "absent" ]
  cron_file:
    description:
      - If specified, uses this file in cron.d instead of an individual user's crontab.
    required: false
    default: null
  backup:
    description:
      - If set, create a backup of the crontab before it is modified.
        The location of the backup is returned in the C(backup) variable by this module.
    required: false
    default: false
  minute:
    description:
      - Minute when the job should run ( 0-59, *, */2, etc )
    required: false
    default: "*"
  hour:
    description:
      - Hour when the job should run ( 0-23, *, */2, etc )
    required: false
    default: "*"
  day:
    description:
      - Day of the month the job should run ( 1-31, *, */2, etc )
    required: false
    default: "*"
    aliases: [ "dom" ]
  month:
    description:
      - Month of the year the job should run ( 1-12, *, */2, etc )
    required: false
    default: "*"
  weekday:
    description:
      - Day of the week that the job should run ( 0-6 for Sunday-Saturday, *, etc )
    required: false
    default: "*"
    aliases: [ "dow" ]
  reboot:
    description:
      - If the job should be run at reboot. This option is deprecated. Users should use special_time.
    version_added: "1.0"
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  special_time:
    description:
      - Special time specification nickname.
    version_added: "1.3"
    required: false
    default: null
    choices: [ "reboot", "yearly", "annually", "monthly", "weekly", "daily", "hourly" ]
requirements:
  - cron
author: Dane Summers
updates: [ 'Mike Grozak', 'Patrick Callahan' ]
"""

EXAMPLES = '''
# Ensure a job that runs at 2 and 5 exists.
# Creates an entry like "0 5,2 * * ls -alh > /dev/null"
- cron: name="check dirs" minute="0" hour="5,2" job="ls -alh > /dev/null"

# Ensure an old job is no longer present. Removes any job that is prefixed
# by "#Ansible: an old job" from the crontab
- cron: name="an old job" state=absent

# Creates an entry like "@reboot /some/job.sh"
- cron: name="a job for reboot" special_time=reboot job="/some/job.sh"

# Creates a cron file under /etc/cron.d
- cron: name="yum autoupdate" weekday="2" minute=0 hour=12
        user="root" job="YUMINTERACTIVE=0 /usr/sbin/yum-autoupdate"
        cron_file=ansible_yum-autoupdate

# Removes a cron file from under /etc/cron.d
- cron: cron_file=ansible_yum-autoupdate state=absent
'''

import os
import re
import tempfile
import platform
import pipes

CRONCMD = "/usr/bin/crontab"

class CronTabError(Exception):
    pass

class CronTab(object):
    """
        CronTab object to write time based crontab file

        user      - the user of the crontab (defaults to root)
        cron_file - a cron file under /etc/cron.d
    """
    def __init__(self, module, user=None, cron_file=None):
        self.module    = module
        self.user      = user
        self.root      = (os.getuid() == 0)
        self.lines     = None
        self.ansible   = "#Ansible: "

        # select whether we dump additional debug info through syslog
        self.syslogging = False

        if cron_file:
            self.cron_file = '/etc/cron.d/%s' % cron_file
        else:
            self.cron_file = None

        self.read()

    def read(self):
        # Read in the crontab from the system
        self.lines = []
        if self.cron_file:
            # read the cronfile
            try:
                f = open(self.cron_file, 'r')
                self.lines = f.read().splitlines()
                f.close()
            except IOError, e:
                # cron file does not exist
                return
            except:
                raise CronTabError("Unexpected error:", sys.exc_info()[0])
        else:
            # using safely quoted shell for now, but this really should be two non-shell calls instead.  FIXME
            (rc, out, err) = self.module.run_command(self._read_user_execute(), use_unsafe_shell=True)

            if rc != 0 and rc != 1: # 1 can mean that there are no jobs.
                raise CronTabError("Unable to read crontab")

            lines = out.splitlines()
            count = 0
            for l in lines:
                if count > 2 or (not re.match( r'# DO NOT EDIT THIS FILE - edit the master and reinstall.', l) and
                                 not re.match( r'# \(/tmp/.*installed on.*\)', l) and
                                 not re.match( r'# \(.*version.*\)', l)):
                    self.lines.append(l)
                count += 1

    def log_message(self, message):
        if self.syslogging:
            syslog.syslog(syslog.LOG_NOTICE, 'ansible: "%s"' % message)

    def is_empty(self):
        if len(self.lines) == 0:
            return True
        else:
            return False

    def write(self, backup_file=None):
        """
        Write the crontab to the system. Saves all information.
        """
        if backup_file:
            fileh = open(backup_file, 'w')
        elif self.cron_file:
            fileh = open(self.cron_file, 'w')
        else:
            filed, path = tempfile.mkstemp(prefix='crontab')
            fileh = os.fdopen(filed, 'w')

        fileh.write(self.render())
        fileh.close()

        # return if making a backup
        if backup_file:
            return

        # Add the entire crontab back to the user crontab
        if not self.cron_file:
            # quoting shell args for now but really this should be two non-shell calls.  FIXME
            (rc, out, err) = self.module.run_command(self._write_execute(path), use_unsafe_shell=True)
            os.unlink(path)

            if rc != 0:
                self.module.fail_json(msg=err)

    def add_job(self, name, job):
        # Add the comment
        self.lines.append("%s%s" % (self.ansible, name))

        # Add the job
        self.lines.append("%s" % (job))

    def update_job(self, name, job):
        return self._update_job(name, job, self.do_add_job)

    def do_add_job(self, lines, comment, job):
        lines.append(comment)

        lines.append("%s" % (job))

    def remove_job(self, name):
        return self._update_job(name, "", self.do_remove_job)

    def do_remove_job(self, lines, comment, job):
        return None

    def remove_job_file(self):
        try:
            os.unlink(self.cron_file)
            return True
        except OSError, e:
            # cron file does not exist
            return False
        except:
            raise CronTabError("Unexpected error:", sys.exc_info()[0])

    def find_job(self, name):
        comment = None
        for l in self.lines:
            if comment is not None:
                if comment == name:
                    return [comment, l]
                else:
                    comment = None
            elif re.match( r'%s' % self.ansible, l):
                comment = re.sub( r'%s' % self.ansible, '', l)

        return []

    def get_cron_job(self,minute,hour,day,month,weekday,job,special):
        if special:
            if self.cron_file:
                return "@%s %s %s" % (special, self.user, job)
            else:
                return "@%s %s" % (special, job)
        else:
            if self.cron_file:
                return "%s %s %s %s %s %s %s" % (minute,hour,day,month,weekday,self.user,job)
            else:
                return "%s %s %s %s %s %s" % (minute,hour,day,month,weekday,job)

        return None

    def get_jobnames(self):
        jobnames = []

        for l in self.lines:
            if re.match( r'%s' % self.ansible, l):
                jobnames.append(re.sub( r'%s' % self.ansible, '', l))

        return jobnames

    def _update_job(self, name, job, addlinesfunction):
        ansiblename = "%s%s" % (self.ansible, name)
        newlines = []
        comment = None

        for l in self.lines:
            if comment is not None:
                addlinesfunction(newlines, comment, job)
                comment = None
            elif l == ansiblename:
                comment = l
            else:
                newlines.append(l)

        self.lines = newlines

        if len(newlines) == 0:
            return True
        else:
            return False # TODO add some more error testing

    def render(self):
        """
        Render this crontab as it would be in the crontab.
        """
        crons = []
        for cron in self.lines:
            crons.append(cron)

        result = '\n'.join(crons)
        if result and result[-1] not in ['\n', '\r']:
            result += '\n'
        return result

    def _read_user_execute(self):
        """
        Returns the command line for reading a crontab
        """
        user = ''
        if self.user:
            if platform.system() == 'SunOS':
                return "su %s -c '%s -l'" % (pipes.quote(self.user), pipes.quote(CRONCMD))
            elif platform.system() == 'AIX':
                return "%s -l %s" % (pipes.quote(CRONCMD), pipes.quote(self.user))
            elif platform.system() == 'HP-UX':
                return "%s %s %s" % (CRONCMD , '-l', pipes.quote(self.user))
            else:
                user = '-u %s' % pipes.quote(self.user)
        return "%s %s %s" % (CRONCMD , user, '-l')

    def _write_execute(self, path):
        """
        Return the command line for writing a crontab
        """
        user = ''
        if self.user:
            if platform.system() in ['SunOS', 'HP-UX', 'AIX']:
                return "chown %s %s ; su '%s' -c '%s %s'" % (pipes.quote(self.user), pipes.quote(path), pipes.quote(self.user), CRONCMD, pipes.quote(path))
            else:
                user = '-u %s' % pipes.quote(self.user)
        return "%s %s %s" % (CRONCMD , user, pipes.quote(path))



#==================================================

def main():
    # The following example playbooks:
    #
    # - cron: name="check dirs" hour="5,2" job="ls -alh > /dev/null"
    #
    # - name: do the job
    #   cron: name="do the job" hour="5,2" job="/some/dir/job.sh"
    #
    # - name: no job
    #   cron: name="an old job" state=absent
    #
    # Would produce:
    # # Ansible: check dirs
    # * * 5,2 * * ls -alh > /dev/null
    # # Ansible: do the job
    # * * 5,2 * * /some/dir/job.sh

    module = AnsibleModule(
        argument_spec = dict(
            name=dict(required=True),
            user=dict(required=False),
            job=dict(required=False),
            cron_file=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            backup=dict(default=False, type='bool'),
            minute=dict(default='*'),
            hour=dict(default='*'),
            day=dict(aliases=['dom'], default='*'),
            month=dict(default='*'),
            weekday=dict(aliases=['dow'], default='*'),
            reboot=dict(required=False, default=False, type='bool'),
            special_time=dict(required=False,
                              default=None,
                              choices=["reboot", "yearly", "annually", "monthly", "weekly", "daily", "hourly"],
                              type='str')
        ),
        supports_check_mode = False,
    )

    name         = module.params['name']
    user         = module.params['user']
    job          = module.params['job']
    cron_file    = module.params['cron_file']
    state        = module.params['state']
    backup       = module.params['backup']
    minute       = module.params['minute']
    hour         = module.params['hour']
    day          = module.params['day']
    month        = module.params['month']
    weekday      = module.params['weekday']
    reboot       = module.params['reboot']
    special_time = module.params['special_time']
    do_install   = state == 'present'

    changed      = False
    res_args     = dict()

    # Ensure all files generated are only writable by the owning user.  Primarily relevant for the cron_file option.
    os.umask(022)
    crontab = CronTab(module, user, cron_file)

    if crontab.syslogging:
        syslog.openlog('ansible-%s' % os.path.basename(__file__))
        syslog.syslog(syslog.LOG_NOTICE, 'cron instantiated - name: "%s"' % name)

    # --- user input validation ---

    if (special_time or reboot) and \
       (True in [(x != '*') for x in [minute, hour, day, month, weekday]]):
        module.fail_json(msg="You must specify time and date fields or special time.")

    if cron_file and do_install:
        if not user:
            module.fail_json(msg="To use cron_file=... parameter you must specify user=... as well")

    if reboot and special_time:
        module.fail_json(msg="reboot and special_time are mutually exclusive")

    if name is None and do_install:
        module.fail_json(msg="You must specify 'name' to install a new cron job")

    if job is None and do_install:
        module.fail_json(msg="You must specify 'job' to install a new cron job")

    if job and name is None and not do_install:
        module.fail_json(msg="You must specify 'name' to remove a cron job")

    if reboot:
        if special_time:
            module.fail_json(msg="reboot and special_time are mutually exclusive")
        else:
            special_time = "reboot"

    # if requested make a backup before making a change
    if backup:
        (backuph, backup_file) = tempfile.mkstemp(prefix='crontab')
        crontab.write(backup_file)

    if crontab.cron_file and not name and not do_install:
        changed = crontab.remove_job_file()
        module.exit_json(changed=changed,cron_file=cron_file,state=state)

    job = crontab.get_cron_job(minute, hour, day, month, weekday, job, special_time)
    old_job = crontab.find_job(name)

    if do_install:
        if len(old_job) == 0:
            crontab.add_job(name, job)
            changed = True
        if len(old_job) > 0 and old_job[1] != job:
            crontab.update_job(name, job)
            changed = True
    else:
        if len(old_job) > 0:
            crontab.remove_job(name)
            changed = True

    res_args = dict(
        jobs = crontab.get_jobnames(), changed = changed
    )

    if changed:
        crontab.write()

    # retain the backup only if crontab or cron file have changed
    if backup:
        if changed:
            res_args['backup_file'] = backup_file
        else:
            os.unlink(backup_file)

    if cron_file:
        res_args['cron_file'] = cron_file

    module.exit_json(**res_args)

    # --- should never get here
    module.exit_json(msg="Unable to execute cron task.")

# import module snippets
from ansible.module_utils.basic import *

main()

