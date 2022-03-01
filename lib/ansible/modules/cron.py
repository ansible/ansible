# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Dane Summers <dsummers@pinedesk.biz>
# Copyright: (c) 2013, Mike Grozak  <mike.grozak@gmail.com>
# Copyright: (c) 2013, Patrick Callahan <pmc@patrickcallahan.com>
# Copyright: (c) 2015, Evan Kaufman <evan@digitalflophouse.com>
# Copyright: (c) 2015, Luca Berruti <nadirio@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
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
  - When environment variables are managed, no comment line is added, but, when the module
    needs to find/check the state, it uses the "name" parameter to find the environment
    variable definition line.
  - When using symbols such as %, they must be properly escaped.
version_added: "0.9"
options:
  name:
    description:
      - Description of a crontab entry or, if env is set, the name of environment variable.
      - This parameter is always required as of ansible-core 2.12.
    type: str
    required: yes
  user:
    description:
      - The specific user whose crontab should be modified.
      - When unset, this parameter defaults to the current user.
    type: str
  job:
    description:
      - The command to execute or, if env is set, the value of environment variable.
      - The command should not contain line breaks.
      - Required if I(state=present).
    type: str
    aliases: [ value ]
  state:
    description:
      - Whether to ensure the job or environment variable is present or absent.
    type: str
    choices: [ absent, present ]
    default: present
  cron_file:
    description:
      - If specified, uses this file instead of an individual user's crontab.
        The assumption is that this file is exclusively managed by the module,
        do not use if the file contains multiple entries, NEVER use for /etc/crontab.
      - If this is a relative path, it is interpreted with respect to I(/etc/cron.d).
      - Many linux distros expect (and some require) the filename portion to consist solely
        of upper- and lower-case letters, digits, underscores, and hyphens.
      - Using this parameter requires you to specify the I(user) as well, unless I(state) is not I(present).
      - Either this parameter or I(name) is required
    type: path
  backup:
    description:
      - If set, create a backup of the crontab before it is modified.
        The location of the backup is returned in the C(backup_file) variable by this module.
    type: bool
    default: no
  minute:
    description:
      - Minute when the job should run (C(0-59), C(*), C(*/2), and so on).
    type: str
    default: "*"
  hour:
    description:
      - Hour when the job should run (C(0-23), C(*), C(*/2), and so on).
    type: str
    default: "*"
  day:
    description:
      - Day of the month the job should run (C(1-31), C(*), C(*/2), and so on).
    type: str
    default: "*"
    aliases: [ dom ]
  month:
    description:
      - Month of the year the job should run (C(1-12), C(*), C(*/2), and so on).
    type: str
    default: "*"
  weekday:
    description:
      - Day of the week that the job should run (C(0-6) for Sunday-Saturday, C(*), and so on).
    type: str
    default: "*"
    aliases: [ dow ]
  special_time:
    description:
      - Special time specification nickname.
    type: str
    choices: [ annually, daily, hourly, monthly, reboot, weekly, yearly ]
    version_added: "1.3"
  disabled:
    description:
      - If the job should be disabled (commented out) in the crontab.
      - Only has effect if I(state=present).
    type: bool
    default: no
    version_added: "2.0"
  env:
    description:
      - If set, manages a crontab's environment variable.
      - New variables are added on top of crontab.
      - I(name) and I(value) parameters are the name and the value of environment variable.
    type: bool
    default: false
    version_added: "2.1"
  insertafter:
    description:
      - Used with I(state=present) and I(env).
      - If specified, the environment variable will be inserted after the declaration of specified environment variable.
    type: str
    version_added: "2.1"
  insertbefore:
    description:
      - Used with I(state=present) and I(env).
      - If specified, the environment variable will be inserted before the declaration of specified environment variable.
    type: str
    version_added: "2.1"
requirements:
  - cron (any 'vixie cron' conformant variant, like cronie)
author:
  - Dane Summers (@dsummersl)
  - Mike Grozak (@rhaido)
  - Patrick Callahan (@dirtyharrycallahan)
  - Evan Kaufman (@EvanK)
  - Luca Berruti (@lberruti)
extends_documentation_fragment:
    - action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        support: full
        platforms: posix
'''

EXAMPLES = r'''
- name: Ensure a job that runs at 2 and 5 exists. Creates an entry like "0 5,2 * * ls -alh > /dev/null"
  ansible.builtin.cron:
    name: "check dirs"
    minute: "0"
    hour: "5,2"
    job: "ls -alh > /dev/null"

- name: 'Ensure an old job is no longer present. Removes any job that is prefixed by "#Ansible: an old job" from the crontab'
  ansible.builtin.cron:
    name: "an old job"
    state: absent

- name: Creates an entry like "@reboot /some/job.sh"
  ansible.builtin.cron:
    name: "a job for reboot"
    special_time: reboot
    job: "/some/job.sh"

- name: Creates an entry like "PATH=/opt/bin" on top of crontab
  ansible.builtin.cron:
    name: PATH
    env: yes
    job: /opt/bin

- name: Creates an entry like "APP_HOME=/srv/app" and insert it after PATH declaration
  ansible.builtin.cron:
    name: APP_HOME
    env: yes
    job: /srv/app
    insertafter: PATH

- name: Creates a cron file under /etc/cron.d
  ansible.builtin.cron:
    name: yum autoupdate
    weekday: "2"
    minute: "0"
    hour: "12"
    user: root
    job: "YUMINTERACTIVE=0 /usr/sbin/yum-autoupdate"
    cron_file: ansible_yum-autoupdate

- name: Removes a cron file from under /etc/cron.d
  ansible.builtin.cron:
    name: "yum autoupdate"
    cron_file: ansible_yum-autoupdate
    state: absent

- name: Removes "APP_HOME" environment variable from crontab
  ansible.builtin.cron:
    name: APP_HOME
    env: yes
    state: absent
'''

RETURN = r'''#'''

import os
import platform
import pwd
import re
import sys
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes, to_native
from ansible.module_utils.six.moves import shlex_quote


class CronTabError(Exception):
    pass


class CronTab(object):
    """
        CronTab object to write time based crontab file

        user      - the user of the crontab (defaults to current user)
        cron_file - a cron file under /etc/cron.d, or an absolute path
    """

    def __init__(self, module, user=None, cron_file=None):
        self.module = module
        self.user = user
        self.root = (os.getuid() == 0)
        self.lines = None
        self.ansible = "#Ansible: "
        self.n_existing = ''
        self.cron_cmd = self.module.get_bin_path('crontab', required=True)

        if cron_file:

            if os.path.isabs(cron_file):
                self.cron_file = cron_file
                self.b_cron_file = to_bytes(cron_file, errors='surrogate_or_strict')
            else:
                self.cron_file = os.path.join('/etc/cron.d', cron_file)
                self.b_cron_file = os.path.join(b'/etc/cron.d', to_bytes(cron_file, errors='surrogate_or_strict'))
        else:
            self.cron_file = None

        self.read()

    def read(self):
        # Read in the crontab from the system
        self.lines = []
        if self.cron_file:
            # read the cronfile
            try:
                f = open(self.b_cron_file, 'rb')
                self.n_existing = to_native(f.read(), errors='surrogate_or_strict')
                self.lines = self.n_existing.splitlines()
                f.close()
            except IOError:
                # cron file does not exist
                return
            except Exception:
                raise CronTabError("Unexpected error:", sys.exc_info()[0])
        else:
            # using safely quoted shell for now, but this really should be two non-shell calls instead.  FIXME
            (rc, out, err) = self.module.run_command(self._read_user_execute(), use_unsafe_shell=True)

            if rc != 0 and rc != 1:  # 1 can mean that there are no jobs.
                raise CronTabError("Unable to read crontab")

            self.n_existing = out

            lines = out.splitlines()
            count = 0
            for l in lines:
                if count > 2 or (not re.match(r'# DO NOT EDIT THIS FILE - edit the master and reinstall.', l) and
                                 not re.match(r'# \(/tmp/.*installed on.*\)', l) and
                                 not re.match(r'# \(.*version.*\)', l)):
                    self.lines.append(l)
                else:
                    pattern = re.escape(l) + '[\r\n]?'
                    self.n_existing = re.sub(pattern, '', self.n_existing, 1)
                count += 1

    def is_empty(self):
        if len(self.lines) == 0:
            return True
        else:
            for line in self.lines:
                if line.strip():
                    return False
            return True

    def write(self, backup_file=None):
        """
        Write the crontab to the system. Saves all information.
        """
        if backup_file:
            fileh = open(backup_file, 'wb')
        elif self.cron_file:
            fileh = open(self.b_cron_file, 'wb')
        else:
            filed, path = tempfile.mkstemp(prefix='crontab')
            os.chmod(path, int('0644', 8))
            fileh = os.fdopen(filed, 'wb')

        fileh.write(to_bytes(self.render()))
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
        except Exception:
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
                return "su %s -c '%s -l'" % (shlex_quote(self.user), shlex_quote(self.cron_cmd))
            elif platform.system() == 'AIX':
                return "%s -l %s" % (shlex_quote(self.cron_cmd), shlex_quote(self.user))
            elif platform.system() == 'HP-UX':
                return "%s %s %s" % (self.cron_cmd, '-l', shlex_quote(self.user))
            elif pwd.getpwuid(os.getuid())[0] != self.user:
                user = '-u %s' % shlex_quote(self.user)
        return "%s %s %s" % (self.cron_cmd, user, '-l')

    def _write_execute(self, path):
        """
        Return the command line for writing a crontab
        """
        user = ''
        if self.user:
            if platform.system() in ['SunOS', 'HP-UX', 'AIX']:
                return "chown %s %s ; su '%s' -c '%s %s'" % (
                    shlex_quote(self.user), shlex_quote(path), shlex_quote(self.user), self.cron_cmd, shlex_quote(path))
            elif pwd.getpwuid(os.getuid())[0] != self.user:
                user = '-u %s' % shlex_quote(self.user)
        return "%s %s %s" % (self.cron_cmd, user, shlex_quote(path))


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
            name=dict(type='str', required=True),
            user=dict(type='str'),
            job=dict(type='str', aliases=['value']),
            cron_file=dict(type='path'),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            backup=dict(type='bool', default=False),
            minute=dict(type='str', default='*'),
            hour=dict(type='str', default='*'),
            day=dict(type='str', default='*', aliases=['dom']),
            month=dict(type='str', default='*'),
            weekday=dict(type='str', default='*', aliases=['dow']),
            special_time=dict(type='str', choices=["reboot", "yearly", "annually", "monthly", "weekly", "daily", "hourly"]),
            disabled=dict(type='bool', default=False),
            env=dict(type='bool', default=False),
            insertafter=dict(type='str'),
            insertbefore=dict(type='str'),
        ),
        supports_check_mode=True,
        mutually_exclusive=[
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

        if cron_file == '/etc/crontab':
            module.fail_json(msg="Will not manage /etc/crontab via cron_file, see documentation.")

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
        diff['before'] = crontab.n_existing
        if crontab.cron_file:
            diff['before_header'] = crontab.cron_file
        else:
            if crontab.user:
                diff['before_header'] = 'crontab for user "%s"' % crontab.user
            else:
                diff['before_header'] = 'crontab'

    # --- user input validation ---

    if special_time and \
       (True in [(x != '*') for x in [minute, hour, day, month, weekday]]):
        module.fail_json(msg="You must specify time and date fields or special time.")

    # cannot support special_time on solaris
    if special_time and platform.system() == 'SunOS':
        module.fail_json(msg="Solaris does not support special_time=... or @reboot")

    if do_install:
        if cron_file and not user:
            module.fail_json(msg="To use cron_file=... parameter you must specify user=... as well")

        if job is None:
            module.fail_json(msg="You must specify 'job' to install a new cron job or variable")

        if (insertafter or insertbefore) and not env:
            module.fail_json(msg="Insertafter and insertbefore parameters are valid only with env=yes")

    # if requested make a backup before making a change
    if backup and not module.check_mode:
        (backuph, backup_file) = tempfile.mkstemp(prefix='crontab')
        crontab.write(backup_file)

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
                if crontab.cron_file and crontab.is_empty():
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

    # no changes to env/job, but existing crontab needs a terminating newline
    if not changed and crontab.n_existing != '':
        if not (crontab.n_existing.endswith('\r') or crontab.n_existing.endswith('\n')):
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
