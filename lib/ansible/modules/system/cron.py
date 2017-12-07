#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dane Summers <dsummers@pinedesk.biz>
# Copyright: (c) 2013, Mike Grozak  <mike.grozak@gmail.com>
# Copyright: (c) 2013, Patrick Callahan <pmc@patrickcallahan.com>
# Copyright: (c) 2015, Evan Kaufman <evan@digitalflophouse.com>
# Copyright: (c) 2015, Luca Berruti <nadirio@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cron
short_description: Manage cron.d and crontab entries
description:
  - Use this module to manage crontab and environment variables entries. This module allows
    you to create environment variables and named crontab entries, update, or delete them.
  - 'When crontab jobs are managed: the module includes one line with the description of the
    crontab entry C("#Ansible: <name>") corresponding to the "name" passed to the module,
    which is used by future ansible/module calls to find/check the state. The "name"
    parameter should be unique, and changing the "name" value will result in a new cron
    task being created (or a different one being removed).'
  - 'When environment variables are managed: no comment line is added, but, when the module
    needs to find/check the state, it uses the "name" parameter to find the environment
    variable definition line.'
  - 'When using symbols such as %, they must be properly escaped.'
version_added: "0.9"
options:
  name:
    description:
      - Description of a crontab entry or, if env is set, the name of environment variable.
        Required if state=absent. Note that if name is not set and state=present, then a
        new crontab entry will always be created, regardless of existing ones.
  user:
    description:
      - The specific user whose crontab should be modified.
    default: root
  job:
    description:
      - The command to execute or, if env is set, the value of environment variable.
        The command should not contain line breaks.
        Required if state=present.
    aliases: [ value ]
  state:
    description:
      - Whether to ensure the job or environment variable is present or absent.
    choices: [ absent, present ]
    default: present
  cron_file:
    description:
      - If specified, uses this file instead of an individual user's crontab.
        If this is a relative path, it is interpreted with respect to
        /etc/cron.d. (If it is absolute, it will typically be /etc/crontab).
        Many linux distros expect (and some require) the filename portion to consist solely
        of upper- and lower-case letters, digits, underscores, and hyphens.
        To use the C(cron_file) parameter you must specify the C(user) as well.
  backup:
    description:
      - If set, create a backup of the crontab before it is modified.
        The location of the backup is returned in the C(backup_file) variable by this module.
    type: bool
    default: 'no'
  minute:
    description:
      - Minute when the job should run ( 0-59, *, */2, etc )
    default: "*"
  hour:
    description:
      - Hour when the job should run ( 0-23, *, */2, etc )
    default: "*"
  day:
    description:
      - Day of the month the job should run ( 1-31, *, */2, etc )
    default: "*"
    aliases: [ dom ]
  month:
    description:
      - Month of the year the job should run ( 1-12, *, */2, etc )
    default: "*"
  weekday:
    description:
      - Day of the week that the job should run ( 0-6 for Sunday-Saturday, *, etc )
    default: "*"
    aliases: [ dow ]
  reboot:
    description:
      - If the job should be run at reboot. This option is deprecated. Users should use special_time.
    version_added: "1.0"
    type: bool
    default: "no"
  special_time:
    description:
      - Special time specification nickname.
    choices: [ reboot, yearly, annually, monthly, weekly, daily, hourly ]
    version_added: "1.3"
  disabled:
    description:
      - If the job should be disabled (commented out) in the crontab.
      - Only has effect if C(state=present).
    type: bool
    default: 'no'
    version_added: "2.0"
  env:
    description:
      - If set, manages a crontab's environment variable. New variables are added on top of crontab.
        "name" and "value" parameters are the name and the value of environment variable.
    type: bool
    default: "no"
    version_added: "2.1"
  insertafter:
    description:
      - Used with C(state=present) and C(env). If specified, the environment variable will be
        inserted after the declaration of specified environment variable.
    version_added: "2.1"
  insertbefore:
    description:
      - Used with C(state=present) and C(env). If specified, the environment variable will be
        inserted before the declaration of specified environment variable.
    version_added: "2.1"
requirements:
  - cron
author:
    - Dane Summers (@dsummersl)
    - Mike Grozak
    - Patrick Callahan
    - Evan Kaufman (@EvanK)
    - Luca Berruti (@lberruti)
"""

EXAMPLES = '''
# Ensure a job that runs at 2 and 5 exists.
# Creates an entry like "0 5,2 * * ls -alh > /dev/null"
- cron:
    name: "check dirs"
    minute: "0"
    hour: "5,2"
    job: "ls -alh > /dev/null"

# Ensure an old job is no longer present. Removes any job that is prefixed
# by "#Ansible: an old job" from the crontab
- cron:
    name: "an old job"
    state: absent

# Creates an entry like "@reboot /some/job.sh"
- cron:
    name: "a job for reboot"
    special_time: reboot
    job: "/some/job.sh"

# Creates an entry like "PATH=/opt/bin" on top of crontab
- cron:
    name: PATH
    env: yes
    value: /opt/bin

# Creates an entry like "APP_HOME=/srv/app" and insert it after PATH
# declaration
- cron:
    name: APP_HOME
    env: yes
    value: /srv/app
    insertafter: PATH

# Creates a cron file under /etc/cron.d
- cron:
    name: yum autoupdate
    weekday: 2
    minute: 0
    hour: 12
    user: root
    job: "YUMINTERACTIVE: 0 /usr/sbin/yum-autoupdate"
    cron_file: ansible_yum-autoupdate

# Removes a cron file from under /etc/cron.d
- cron:
    name: "yum autoupdate"
    cron_file: ansible_yum-autoupdate
    state: absent

# Removes "APP_HOME" environment variable from crontab
- cron:
    name: APP_HOME
    env: yes
    state: absent
'''

import os
import platform
import pipes
import pwd
import re
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule, get_platform


CRONCMD = "/usr/bin/crontab"


class CronTabError(Exception):
    pass


class CronTab(object):
    """
        CronTab object to write time based crontab file

        user      - the user of the crontab (defaults to root)
        cron_file - a cron file under /etc/cron.d, or an absolute path
    """

    def __init__(self, module, user=None, cron_file=None):
        self.module = module
        self.user = user
        self.root = (os.getuid() == 0)
        self.lines = None
        self.ansible = "#Ansible: "
        self.existing = ''

        if cron_file:
            if os.path.isabs(cron_file):
                self.cron_file = cron_file
            else:
                self.cron_file = os.path.join('/etc/cron.d', cron_file)
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
                self.existing = f.read()
                self.lines = self.existing.splitlines()
                f.close()
            except IOError:
                # cron file does not exist
                return
            except:
                raise CronTabError("Unexpected error:", sys.exc_info()[0])
        else:
            # using safely quoted shell for now, but this really should be two non-shell calls instead.  FIXME
            (rc, out, err) = self.module.run_command(self._read_user_execute(), use_unsafe_shell=True)

            if rc != 0 and rc != 1:  # 1 can mean that there are no jobs.
                raise CronTabError("Unable to read crontab")

            self.existing = out

            lines = out.splitlines()
            count = 0
            for l in lines:
                if count > 2 or (not re.match(r'# DO NOT EDIT THIS FILE - edit the master and reinstall.', l) and
                                 not re.match(r'# \(/tmp/.*installed on.*\)', l) and
                                 not re.match(r'# \(.*version.*\)', l)):
                    self.lines.append(l)
                else:
                    pattern = re.escape(l) + '[\r\n]?'
                    self.existing = re.sub(pattern, '', self.existing, 1)
                count += 1

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
            os.chmod(path, int('0644', 8))
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

        # set SELinux permissions
        if self.module.selinux_enabled() and self.cron_file:
            self.module.set_default_selinux_context(self.cron_file, False)

    def do_comment(self, name):
        return "%s%s" % (self.ansible, name)

    def add_job(self, name, job):
        # Add the comment
        self.lines.append(self.do_comment(name))

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

    def add_env(self, decl, insertafter=None, insertbefore=None):
        if not (insertafter or insertbefore):
            self.lines.insert(0, decl)
            return

        if insertafter:
            other_name = insertafter
        elif insertbefore:
            other_name = insertbefore
        other_decl = self.find_env(other_name)
        if len(other_decl) > 0:
            if insertafter:
                index = other_decl[0] + 1
            elif insertbefore:
                index = other_decl[0]
            self.lines.insert(index, decl)
            return

        self.module.fail_json(msg="Variable named '%s' not found." % other_name)

    def update_env(self, name, decl):
        return self._update_env(name, decl, self.do_add_env)

    def do_add_env(self, lines, decl):
        lines.append(decl)

    def remove_env(self, name):
        return self._update_env(name, '', self.do_remove_env)

    def do_remove_env(self, lines, decl):
        return None

    def remove_job_file(self):
        try:
            os.unlink(self.cron_file)
            return True
        except OSError:
            # cron file does not exist
            return False
        except:
            raise CronTabError("Unexpected error:", sys.exc_info()[0])

    def find_job(self, name, job=None):
        # attempt to find job by 'Ansible:' header comment
        comment = None
        for l in self.lines:
            if comment is not None:
                if comment == name:
                    return [comment, l]
                else:
                    comment = None
            elif re.match(r'%s' % self.ansible, l):
                comment = re.sub(r'%s' % self.ansible, '', l)

        # failing that, attempt to find job by exact match
        if job:
            for i, l in enumerate(self.lines):
                if l == job:
                    # if no leading ansible header, insert one
                    if not re.match(r'%s' % self.ansible, self.lines[i - 1]):
                        self.lines.insert(i, self.do_comment(name))
                        return [self.lines[i], l, True]
                    # if a leading blank ansible header AND job has a name, update header
                    elif name and self.lines[i - 1] == self.do_comment(None):
                        self.lines[i - 1] = self.do_comment(name)
                        return [self.lines[i - 1], l, True]

        return []

    def find_env(self, name):
        for index, l in enumerate(self.lines):
            if re.match(r'^%s=' % name, l):
                return [index, l]

        return []

    def get_cron_job(self, minute, hour, day, month, weekday, job, special, disabled):
        # normalize any leading/trailing newlines (ansible/ansible-modules-core#3791)
        job = job.strip('\r\n')

        if disabled:
            disable_prefix = '#'
        else:
            disable_prefix = ''

        if special:
            if self.cron_file:
                return "%s@%s %s %s" % (disable_prefix, special, self.user, job)
            else:
                return "%s@%s %s" % (disable_prefix, special, job)
        else:
            if self.cron_file:
                return "%s%s %s %s %s %s %s %s" % (disable_prefix, minute, hour, day, month, weekday, self.user, job)
            else:
                return "%s%s %s %s %s %s %s" % (disable_prefix, minute, hour, day, month, weekday, job)

    def get_jobnames(self):
        jobnames = []

        for l in self.lines:
            if re.match(r'%s' % self.ansible, l):
                jobnames.append(re.sub(r'%s' % self.ansible, '', l))

        return jobnames

    def get_envnames(self):
        envnames = []

        for l in self.lines:
            if re.match(r'^\S+=', l):
                envnames.append(l.split('=')[0])

        return envnames

    def _update_job(self, name, job, addlinesfunction):
        ansiblename = self.do_comment(name)
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
            return False  # TODO add some more error testing

    def _update_env(self, name, decl, addenvfunction):
        newlines = []

        for l in self.lines:
            if re.match(r'^%s=' % name, l):
                addenvfunction(newlines, decl)
            else:
                newlines.append(l)

        self.lines = newlines

    def render(self):
        """
        Render this crontab as it would be in the crontab.
        """
        crons = []
        for cron in self.lines:
            crons.append(cron)

        result = '\n'.join(crons)
        if result:
            result = result.rstrip('\r\n') + '\n'
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
                return "%s %s %s" % (CRONCMD, '-l', pipes.quote(self.user))
            elif pwd.getpwuid(os.getuid())[0] != self.user:
                user = '-u %s' % pipes.quote(self.user)
        return "%s %s %s" % (CRONCMD, user, '-l')

    def _write_execute(self, path):
        """
        Return the command line for writing a crontab
        """
        user = ''
        if self.user:
            if platform.system() in ['SunOS', 'HP-UX', 'AIX']:
                return "chown %s %s ; su '%s' -c '%s %s'" % (pipes.quote(self.user), pipes.quote(path), pipes.quote(self.user), CRONCMD, pipes.quote(path))
            elif pwd.getpwuid(os.getuid())[0] != self.user:
                user = '-u %s' % pipes.quote(self.user)
        return "%s %s %s" % (CRONCMD, user, pipes.quote(path))


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
    # - name: sets env
    #   cron: name="PATH" env=yes value="/bin:/usr/bin"
    #
    # Would produce:
    # PATH=/bin:/usr/bin
    # # Ansible: check dirs
    # * * 5,2 * * ls -alh > /dev/null
    # # Ansible: do the job
    # * * 5,2 * * /some/dir/job.sh

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str'),
            user=dict(type='str'),
            job=dict(type='str', aliases=['value']),
            cron_file=dict(type='str'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            backup=dict(type='bool', default=False),
            minute=dict(type='str', default='*'),
            hour=dict(type='str', default='*'),
            day=dict(type='str', default='*', aliases=['dom']),
            month=dict(type='str', default='*'),
            weekday=dict(type='str', default='*', aliases=['dow']),
            reboot=dict(type='bool', default=False),
            special_time=dict(type='str', choices=["reboot", "yearly", "annually", "monthly", "weekly", "daily", "hourly"]),
            disabled=dict(type='bool', default=False),
            env=dict(type='bool'),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
            ['reboot', 'special_time'],
            ['insertafter', 'insertbefore'],
        ],
    )

    name = module.params['name']
    user = module.params['user']
    job = module.params['job']
    cron_file = module.params['cron_file']
    state = module.params['state']
    backup = module.params['backup']
    minute = module.params['minute']
    hour = module.params['hour']
    day = module.params['day']
    month = module.params['month']
    weekday = module.params['weekday']
    reboot = module.params['reboot']
    special_time = module.params['special_time']
    disabled = module.params['disabled']
    env = module.params['env']
    insertafter = module.params['insertafter']
    insertbefore = module.params['insertbefore']
    do_install = state == 'present'

    changed = False
    res_args = dict()
    warnings = list()

    if cron_file:
        cron_file_basename = os.path.basename(cron_file)
        if not re.search(r'^[A-Z0-9_-]+$', cron_file_basename, re.I):
            warnings.append('Filename portion of cron_file ("%s") should consist' % cron_file_basename +
                            ' solely of upper- and lower-case letters, digits, underscores, and hyphens')

    # Ensure all files generated are only writable by the owning user.  Primarily relevant for the cron_file option.
    os.umask(int('022', 8))
    crontab = CronTab(module, user, cron_file)

    module.debug('cron instantiated - name: "%s"' % name)

    if module._diff:
        diff = dict()
        diff['before'] = crontab.existing
        if crontab.cron_file:
            diff['before_header'] = crontab.cron_file
        else:
            if crontab.user:
                diff['before_header'] = 'crontab for user "%s"' % crontab.user
            else:
                diff['before_header'] = 'crontab'

    # --- user input validation ---

    if (special_time or reboot) and \
       (True in [(x != '*') for x in [minute, hour, day, month, weekday]]):
        module.fail_json(msg="You must specify time and date fields or special time.")

    # cannot support special_time on solaris
    if (special_time or reboot) and get_platform() == 'SunOS':
        module.fail_json(msg="Solaris does not support special_time=... or @reboot")

    if cron_file and do_install:
        if not user:
            module.fail_json(msg="To use cron_file=... parameter you must specify user=... as well")

    if job is None and do_install:
        module.fail_json(msg="You must specify 'job' to install a new cron job or variable")

    if (insertafter or insertbefore) and not env and do_install:
        module.fail_json(msg="Insertafter and insertbefore parameters are valid only with env=yes")

    if reboot:
        special_time = "reboot"

    # if requested make a backup before making a change
    if backup and not module.check_mode:
        (backuph, backup_file) = tempfile.mkstemp(prefix='crontab')
        crontab.write(backup_file)

    if crontab.cron_file and not name and not do_install:
        if module._diff:
            diff['after'] = ''
            diff['after_header'] = '/dev/null'
        else:
            diff = dict()
        if module.check_mode:
            changed = os.path.isfile(crontab.cron_file)
        else:
            changed = crontab.remove_job_file()
        module.exit_json(changed=changed, cron_file=cron_file, state=state, diff=diff)

    if env:
        if ' ' in name:
            module.fail_json(msg="Invalid name for environment variable")
        decl = '%s="%s"' % (name, job)
        old_decl = crontab.find_env(name)

        if do_install:
            if len(old_decl) == 0:
                crontab.add_env(decl, insertafter, insertbefore)
                changed = True
            if len(old_decl) > 0 and old_decl[1] != decl:
                crontab.update_env(name, decl)
                changed = True
        else:
            if len(old_decl) > 0:
                crontab.remove_env(name)
                changed = True
    else:
        if do_install:
            for char in ['\r', '\n']:
                if char in job.strip('\r\n'):
                    warnings.append('Job should not contain line breaks')
                    break

            job = crontab.get_cron_job(minute, hour, day, month, weekday, job, special_time, disabled)
            old_job = crontab.find_job(name, job)

            if len(old_job) == 0:
                crontab.add_job(name, job)
                changed = True
            if len(old_job) > 0 and old_job[1] != job:
                crontab.update_job(name, job)
                changed = True
            if len(old_job) > 2:
                crontab.update_job(name, job)
                changed = True
        else:
            old_job = crontab.find_job(name)

            if len(old_job) > 0:
                crontab.remove_job(name)
                changed = True

    # no changes to env/job, but existing crontab needs a terminating newline
    if not changed and not crontab.existing == '':
        if not (crontab.existing.endswith('\r') or crontab.existing.endswith('\n')):
            changed = True

    res_args = dict(
        jobs=crontab.get_jobnames(),
        envs=crontab.get_envnames(),
        warnings=warnings,
        changed=changed
    )

    if changed:
        if not module.check_mode:
            crontab.write()
        if module._diff:
            diff['after'] = crontab.render()
            if crontab.cron_file:
                diff['after_header'] = crontab.cron_file
            else:
                if crontab.user:
                    diff['after_header'] = 'crontab for user "%s"' % crontab.user
                else:
                    diff['after_header'] = 'crontab'

            res_args['diff'] = diff

    # retain the backup only if crontab or cron file have changed
    if backup and not module.check_mode:
        if changed:
            res_args['backup_file'] = backup_file
        else:
            os.unlink(backup_file)

    if cron_file:
        res_args['cron_file'] = cron_file

    module.exit_json(**res_args)

    # --- should never get here
    module.exit_json(msg="Unable to execute cron task.")


if __name__ == '__main__':
    main()
