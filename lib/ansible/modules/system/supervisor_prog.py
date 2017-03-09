#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: supervisor_prog
short_description: Create/Change/Delete a supervisord-managed program
description:
  - Manage the state of a supervisord program.  *** This module assumes supervisor configs are stored in /etc/supervisor.d ***
version_added: "0.9"
author: Guy Matz (guymatz@github)
options:
  name:
    description:
      - The name of the program to manage.
    required: true
    default: null
  command:
    description:
      - The exectuable program for supervisor to manage
    required: true
    default: null
  numprocs:
    description:
      - Supervisor will start as many instances as named by numprocs
    required: false
    default: 1
  numprocs_start:
    description:
      - number at which numprocs starts
    required: false
    default: 0
  priority:
    description:
      - the relative start priority
    required: false
    default: 999
  autostart:
    description:
      - start at supervisord start
    required: false
    default: true
  autorestart:
    description:
      - The process will restart when the program exits
    required: false
    default: true
    choices: [true, false, unexpected]
  startsecs:
    description:
      - number of seconds which the program needs to stay running after a startup to consider the start successful.
    required: false
    default: 1
  startretries:
    description:
      - max # of serial start failures
    required: false
    default: 3
  exitcodes:
    description:
      - list of expected exit codes for process
    required: false
    default: 0,2
  stopsignal:
    description:
      - signal used to kill process
    required: false
    default: TERM
  stopwaitsecs:
    description:
      - max num secs to wait before SIGKILL
    required: false
    default: 10
  stopasgroup:
    description:
      - causes supervisor to send the stop signal to the whole process group
    required: false
    default: false
  killasgroup:
    description:
      - causes supervisor to send the kill signal to the whole process group
    required: false
    default: false
  user:
    description:
      - setuid to this UNIX account to run the program
    required: true
    default: null
  redirect_stderr:
    description:
      - whether to combine logs?
    required: false
    choices: [true, false]
    default: false
  stdout_logfile:
    description:
      - location of out log
    required: false
    default: AUTO
  stdout_logfile_maxbytes:
    description:
      - Max # of bytes for stdout_logfile before it is rotated
    required: false
    default: 50MB
  stdout_logfile_backups:
    description:
      - Number of stdout_logfile backups to keep around
    required: false
    default: 10
  stdout_capture_maxbytes:
    description:
      - Max number of bytes written to capture FIFO when process is in “stdout capture mode”
    required: false
    default: 0
  stdout_events_enabled:
    description:
      - If true, PROCESS_LOG_STDOUT events will be emitted when the process writes to its stdout file
    required: false
    default: 0
  stderr_logfile:
    description:
      - location of err log
    required: false
    default: AUTO
  stderr_logfile_maxbytes:
    description:
      - Max # of bytes for stderr_logfile before it is rotated
    required: false
    default: 50MB
  stderr_logfile_backups:
    description:
      - Number of stderr_logfile backups to keep around
    required: false
    default: 10
  stderr_capture_maxbytes:
    description:
      - Max number of bytes written to capture FIFO when process is in “stderr capture mode”
    required: false
    default: 0
  stderr_events_enabled:
    description:
      - If true, PROCESS_LOG_STDOUT events will be emitted when the process writes to its stderr file
    required: false
    default: 0
  environment:
    description:
      - A list of key/value pairs in the form KEY="val",KEY2="val2" that will be placed in the child process’ environment
    required: false
    default: null
  directory:
    description:
      - Directory for supervisor to run program from?
    required: false
    default: null
  umask:
    description:
      - An octal number (e.g. 002, 022) representing the umask of the process.
    required: false
    default: null
  serverurl:
    description:
      - The URL passed in the environment to the subprocess process as SUPERVISOR_SERVER_URL
    required: false
    default: AUTO
  group:
    description:
      - The superisor group this program should belong to
    required: false
    default: null
  supervisor_conf:
    description:
      - location of supervisor config file
    required: false
    default: /etc/supervisor.conf
  supervisor_d:
    description:
      - location of supervisor program files
    required: false
    default: /etc/supervisor.d
  use_include:
    description:
      - use the include path specified, regardless of what's in the actual config
    default: false
    choices: [true, false]
  state:
    description:
      - The state of the policy.
    default: present
    choices: [present, absent]
'''

EXAMPLES = '''
- name: ensure the default vhost contains the HA policy via a dict
  supervisor_program: name=foo command='/opt/somewheres/special.py'

- name: One more example here
  supervisor_program: name=foo command='/opt/somewheres/special.py'
'''
from ConfigParser import RawConfigParser
import os

class SupervisorConfigParser(RawConfigParser):

    def __str__(self):
        out = ''

        for section in sorted(self.sections()):
            out = "%s\n%s" % (out, section)
            for i in sorted(self.items(section)):
                item = "%s=%s" % (i[0], i[1]) # convert tuple to key=value
                out = "%s\n%s" % (out, str(item))
        return out

class SupervisorProgram(object):
    def __init__(self, module, name):
        self._module = module
        self._supervisor_conf = module.params['supervisor_conf']
        self._supervisor_d = module.params['supervisor_d']
        self._group = module.params['group']
        self._name = name
        self._command = module.params['command']
        self._numprocs = module.params['numprocs']
        self._numprocs_start = module.params['numprocs_start']
        self._priority = module.params['priority']
        self._autostart = module.params['autostart']
        self._autorestart = module.params['autorestart']
        self._startsecs = module.params['startsecs']
        self._startretries = module.params['startretries']
        self._exitcodes = module.params['exitcodes']
        self._stopsignal = module.params['stopsignal']
        self._stopwaitsecs = module.params['stopwaitsecs']
        self._stopasgroup = module.params['stopasgroup']
        self._killasgroup = module.params['killasgroup']
        self._user = module.params['user']
        self._redirect_stderr = module.params['redirect_stderr']
        self._stdout_logfile = module.params['stdout_logfile']
        self._stdout_logfile_maxbytes = module.params['stdout_logfile_maxbytes']
        self._stdout_logfile_backups = module.params['stdout_logfile_backups']
        self._stdout_capture_maxbytes = module.params['stdout_capture_maxbytes']
        self._stdout_events_enabled = module.params['stdout_events_enabled']
        self._stderr_logfile = module.params['stderr_logfile']
        self._stderr_logfile_maxbytes = module.params['stderr_logfile_maxbytes']
        self._stderr_logfile_backups = module.params['stderr_logfile_backups']
        self._stderr_capture_maxbytes = module.params['stderr_capture_maxbytes']
        self._stderr_events_enabled = module.params['stderr_events_enabled']
        self._environment = module.params['environment']
        self._directory = module.params['directory']
        self._umask = module.params['umask']
        self._serverurl = module.params['serverurl']

    def conf_has_include(self):
        conf = self.get_main_config()
        if conf.has_section('include'):
            return True
        else:
            return False

    def get_config(self, config_file):
        conf = SupervisorConfigParser()
        try:
            conf.read( config_file )
        except Error, e:
                raise(e)
        finally:
            return conf

    def get_main_config_file(self):
        if self._supervisor_conf:
            return self._supervisor_conf
        config_file = False
        locations = [
                # rhel
                '/etc/supervisord.conf',
                # debian (as far as I know
                '/etc/supervisor/supervisord.conf'
                # does anyone use any other OS'es?
                ]

        for path in locations:
            if os.path.exists(path):
                return path

        return config_file # :-(

    def get_main_config(self):
        return self.get_config( self.get_main_config_file() )


    def create_config(self):
        new_config = ''
        #create_section(option, value)
        possible_options = {
                'name': self._name,
                'command': self._command,
                'process_name': self._name,
                'numprocs': self._numprocs,
                'numprocs_start': self._numprocs_start,
                'priority': self._priority,
                'autostart': self._autostart,
                'autorestart': self._autorestart,
                'startsecs': self._startsecs,
                'startretries': self._startretries,
                'exitcodes': self._exitcodes,
                'stopsignal': self._stopsignal,
                'stopwaitsecs': self._stopwaitsecs,
                'stopasgroup': self._stopasgroup,
                'killasgroup': self._killasgroup,
                'user': self._user,
                'redirect_stderr': self._redirect_stderr,
                'stdout_logfile': self._stdout_logfile,
                'stdout_logfile_maxbytes': self._stdout_logfile_maxbytes,
                'stdout_logfile_backups': self._stdout_logfile_backups,
                'stdout_capture_maxbytes': self._stdout_capture_maxbytes,
                'stdout_events_enabled': self._stdout_events_enabled,
                'stderr_logfile': self._stderr_logfile,
                'stderr_logfile_maxbytes': self._stderr_logfile_maxbytes,
                'stderr_logfile_backups': self._stderr_logfile_backups,
                'stderr_capture_maxbytes': self._stderr_capture_maxbytes,
                'stderr_events_enabled': self._stderr_events_enabled,
                'environment': self._environment,
                'directory': self._directory,
                'umask': self._umask,
                'serverurl': self._serverurl
            }
        c = SupervisorConfigParser()
        section = 'program:%s' % self._name
        c.add_section(section)
        for o in possible_options.keys():
            if possible_options[o]:
                c.set(section, o, possible_options[o])
        return c


class SupervisorWithInclude(SupervisorProgram):
    def __init__(self, module, name):
        SupervisorProgram.__init__(self, module, name)

    def get_conf_include_path(self):
        if self._supervisor_d:
            return self._supervisor_d
        conf = self.get_main_config()
        path = conf.get('include', 'files')
        return path.rpartition('/')[0] # chops off the /*.conf at the end

    def check_for_program_conf(self):
        program_file = "%s.conf" % self._name
        if self._supervisor_d:
            program_file = os.path.join(self._supervisor_d, program_file)
        else:
            include_path = self.get_conf_include_path()
            program_file = os.path.join(self.get_conf_include_path(),
                                         program_file)

        if os.path.isfile( program_file ):
            return True
        else:
            return False

    def del_program_conf(self):
        program_file = "%s.conf" % self._name
        if self._supervisor_d:
            os.remove( os.path.join(self._supervisor_d, program_file) )
        else:
            os.remove( os.path.join(self.get_conf_include_path(),
                                        program_file) )

    def get_program_config(self):
        prog_conf = os.path.join(self.get_conf_include_path(),
                                        self._name + ".conf")
        return str(self.get_config(prog_conf))

    def set_config(self, new_config):
        prog_conf = os.path.join(self. get_conf_include_path(),
                                        self._name + ".conf")
        with open(prog_conf, 'w') as cfile:
            new_config.write(cfile)
            
    def conf_has_group(self):
        group = 'group:%s' % self._group
        group_conf = os.path.join(self. get_conf_include_path(),
                                        self._group + ".conf")
        c = self.get_config(group_conf)
        # Check if a section for the group exists
        if c.has_section(group):
            return True
        return False

    def add_group(self):
        group = 'group:' + self._group
        group_conf = os.path.join(self. get_conf_include_path(),
                                        self._group + ".conf")
        c = self.get_config(group_conf)
        # Check if a section for the group exists
        if c.has_section(group):
            return False
        c.add_section(group)
        with open(group_conf, 'w') as file:
            c.write(file)

    def has_prog_in_group(self):
        group = 'group:' + self._group
        group_conf = os.path.join(self. get_conf_include_path(),
                                        self._group + ".conf")
        c = self.get_config(group_conf)
        if not c.has_option(group, 'programs'):
            return False
        programs = c.get(group, 'programs').split(',')
        if self._name in programs:
            return True
        return False

    def add_to_group(self):
        group = 'group:' + self._group
        group_conf = os.path.join(self. get_conf_include_path(),
                                        self._group + ".conf")
        c = self.get_config(group_conf)
        if not c.has_option(group, 'programs'):
            c.set(group, 'programs', self._name)
        else:
            programs = c.get(group, 'programs').split(',')
            programs.append(self._name)
            c.set(group, 'programs', ",".join(programs) )
        with open(group_conf, 'w') as file:
            c.write(file)
        return True

    def del_from_group(self):
        group = 'group:' + self._group
        group_conf = os.path.join(self. get_conf_include_path(),
                                        self._group + ".conf")
        c = self.get_config(group_conf)
        # Check if a section for the group exists
        if c.has_section(group):
            programs = c.get(group, 'programs').split(',')
            # if this program is the only one, then remove the section
            if len(programs) <= 1:
                c.remove_section(group)
            elif self._name in programs:
                programs.remove(self._name)
                c.set(group, 'programs', ",".join(programs) )
            else:
                return False
            with open(group_conf, 'w') as file:
                c.write(file)
            return True

class SupervisorNoInclude(SupervisorProgram):
    def __init__(self, module, name):
        SupervisorProgram.__init__(self, module, name)

    def check_for_program_conf(self):
        program = "program:%s" % self._name
        config = self.get_main_config()
        if config.has_section(program):
            return True
        else:
            return False

    def del_program_conf(self):
        program = "program:%s" % self._name
        config = self.get_main_config()
        config.remove_section(program)
        with open(self.get_main_config_file(), 'w') as cfile:
            config.write(cfile)

    def get_program_config(self):
        main_conf = self.get_main_config()
        try:
            program_section = "program:%s" % self._name
            prog_conf = main_conf.__str__(program_section)
            return prog_conf
        except:
            return False

    def set_config(self, new_config):
        # Need to implement this . . .
        print("WE SHOULD NOT HAVE GOTTEN HERE!!")
            
    # TODO - needs to be recoded for SupervisorNoInclude class to work correctly
    def add_group(self):
        group = 'group:' + self._group
        c = self.get_main_config()
        # Check if a section for the group exists
        if c.has_section(group):
            return False
        c.add_section(group)
        with open(self.get_main_config_file(), 'w') as file:
            c.write(file)

    # TODO - needs to be recoded for SupervisorNoInclude class to work correctly
    def has_prog_in_group(self):
        group = 'group:' + self._group
        c = SupervisorConfigParser()
        c.read(self.get_main_config_file())
        if not c.has_option(group, 'programs'):
            return False
        programs = c.get(group, 'programs').split(',')
        if self._name in programs:
            return True
        return False

    # TODO - needs to be recoded for SupervisorNoInclude class to work correctly
    def add_to_group(self):
        group = 'group:' + self._group
        c = SupervisorConfigParser()
        c.read(self.get_main_config_file())
        if not c.has_option(group, 'programs'):
            c.set(group, 'programs', self._name)
        else:
            programs = c.get(group, 'programs').split(',')
            programs.append(self._name)
            c.set(group, 'programs', ",".join(programs) )
        with open(self.get_main_config_file(), 'w') as file:
            c.write(file)
        return True

    # TODO - needs to be recoded for SupervisorNoInclude class to work correctly
    def del_from_group(self):
        group = 'group:' + self._group
        c = self.get_main_config()
        # Check if a section for the group exists
        if c.has_section(group):
            programs = c.get(group, 'programs').split(',')
            # if this program is the only one, then remove the section
            if len(programs) <= 1:
                c.remove_section(group)
            elif self._name in programs:
                programs.remove(self._name)
                c.set(group, 'programs', ",".join(programs) )
            else:
                return False
            with open(self.get_main_config_file(), 'w') as file:
                c.write(file)
            return True

# main
def conf_has_include(supervisor_config_file):
    conf = SupervisorConfigParser()
    conf.read(supervisor_config_file)
    if conf.has_section('include'):
        return True
    else:
        return False


def main():
    arg_spec = dict(
        name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        supervisor_conf=dict(required=False),
        supervisor_d=dict(required=False),
        group=dict(required=False),
        command=dict(required=True),
        numprocs=dict(required=False),
        numprocs_start=dict(required=False),
        priority=dict(required=False),
        autostart=dict(required=False),
        autorestart=dict(required=False, choices=['true','false','unexpected']),
        startsecs=dict(required=False),
        startretries=dict(required=False),
        exitcodes=dict(required=False),
        stopsignal=dict(required=False),
        stopwaitsecs=dict(required=False),
        stopasgroup=dict(required=False),
        killasgroup=dict(required=False),
        user=dict(required=True),
        redirect_stderr=dict(required=False, default="false", choices=BOOLEANS),
        stdout_logfile=dict(required=False),
        stdout_logfile_maxbytes=dict(required=False),
        stdout_logfile_backups=dict(required=False),
        stdout_capture_maxbytes=dict(required=False),
        stdout_events_enabled=dict(required=False),
        stderr_logfile=dict(required=False),
        stderr_logfile_maxbytes=dict(required=False),
        stderr_logfile_backups=dict(required=False),
        stderr_capture_maxbytes=dict(required=False),
        stderr_events_enabled=dict(required=False),
        environment=dict(required=False),
        directory=dict(required=False),
        umask=dict(required=False),
        serverurl=dict(required=False),
        # This will be needed(?) when SupervisorWithInclude is implemented
        use_include=dict(default=False, required=False, choices=BOOLEANS),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    state = module.params['state']
    group = module.params['group']
    use_include = module.params['use_include']

    # Figure out which config file to use
    supervisor_main_config = False
    if module.params['supervisor_conf']:
        supervisor_main_config = module.params['supervisor_conf']
    else:
        locations = [
                # rhel
                '/etc/supervisord.conf',
                # debian (as far as I know
                '/etc/supervisor/supervisord.conf'
                # does anyone use any other OS'es?
                ]
        for path in locations:
            if os.path.exists(path):
                supervisor_main_config = path
                break

    # If we can't find config, we cannot do much
    if not supervisor_main_config:
        module.fail_json(msg="I cannot find a supervisor config file in the usual places")

    # Determine which class to use
    if use_include:
        supervisor = SupervisorWithInclude(module, name)
    elif conf_has_include(supervisor_main_config):
        supervisor = SupervisorWithInclude(module, name)
    else:
        supervisor = SupervisorNoInclude(module, name)

    # main
    changed = False
    if state == 'absent':
        if supervisor.check_for_program_conf():
            supervisor.del_program_conf()
            changed = True
        if group is not None and supervisor.conf_has_group():
            supervisor.del_from_group()
            changed = True
    else:
        new_conf = supervisor.create_config()
        if supervisor.get_program_config() != str(new_conf):
            supervisor.set_config(new_conf)
            changed = True
        if group is not None and not supervisor.conf_has_group():
            supervisor.add_group()
        if group is not None and not supervisor.has_prog_in_group():
            supervisor.add_to_group()
            changed = True

    module.exit_json(changed=changed, name=name, state=state)

# import module snippets
from ansible.module_utils.basic import *
main()
