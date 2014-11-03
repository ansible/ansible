# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import multiprocessing
import signal
import os
import pwd
import Queue
import random
import traceback
import tempfile
import time
import collections
import socket
import base64
import sys
import pipes
import jinja2
import subprocess
import getpass

import ansible.constants as C
import ansible.inventory
from ansible import utils
from ansible.utils import template
from ansible.utils import check_conditional
from ansible.utils import string_functions
from ansible import errors
from ansible import module_common
import poller
import connection
from return_data import ReturnData
from ansible.callbacks import DefaultRunnerCallbacks, vv
from ansible.module_common import ModuleReplacer
from ansible.module_utils.splitter import split_args, unquote
from ansible.cache import FactCache
from ansible.utils import update_hash

module_replacer = ModuleReplacer(strip_comments=False)

try:
    from hashlib import md5 as _md5
except ImportError:
    from md5 import md5 as _md5

HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

multiprocessing_runner = None

OUTPUT_LOCKFILE  = tempfile.TemporaryFile()
PROCESS_LOCKFILE = tempfile.TemporaryFile()

################################################

def _executor_hook(job_queue, result_queue, new_stdin):

    # attempt workaround of https://github.com/newsapps/beeswithmachineguns/issues/17
    # this function also not present in CentOS 6
    if HAS_ATFORK:
        atfork()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            host = job_queue.get(block=False)
            return_data = multiprocessing_runner._executor(host, new_stdin)
            result_queue.put(return_data)
        except Queue.Empty:
            pass
        except:
            traceback.print_exc()

class HostVars(dict):
    ''' A special view of vars_cache that adds values from the inventory when needed. '''

    def __init__(self, vars_cache, inventory, vault_password=None):
        self.vars_cache = vars_cache
        self.inventory = inventory
        self.lookup = {}
        self.update(vars_cache)
        self.vault_password = vault_password

    def __getitem__(self, host):
        if host not in self.lookup:
            result = self.inventory.get_variables(host, vault_password=self.vault_password).copy()
            result.update(self.vars_cache.get(host, {}))
            self.lookup[host] = template.template('.', result, self.vars_cache)
        return self.lookup[host]


class Runner(object):
    ''' core API interface to ansible '''

    # see bin/ansible for how this is used...

    def __init__(self,
        host_list=C.DEFAULT_HOST_LIST,      # ex: /etc/ansible/hosts, legacy usage
        module_path=None,                   # ex: /usr/share/ansible
        module_name=C.DEFAULT_MODULE_NAME,  # ex: copy
        module_args=C.DEFAULT_MODULE_ARGS,  # ex: "src=/tmp/a dest=/tmp/b"
        forks=C.DEFAULT_FORKS,              # parallelism level
        timeout=C.DEFAULT_TIMEOUT,          # SSH timeout
        pattern=C.DEFAULT_PATTERN,          # which hosts?  ex: 'all', 'acme.example.org'
        remote_user=C.DEFAULT_REMOTE_USER,  # ex: 'username'
        remote_pass=C.DEFAULT_REMOTE_PASS,  # ex: 'password123' or None if using key
        remote_port=None,                   # if SSH on different ports
        private_key_file=C.DEFAULT_PRIVATE_KEY_FILE, # if not using keys/passwords
        sudo_pass=C.DEFAULT_SUDO_PASS,      # ex: 'password123' or None
        background=0,                       # async poll every X seconds, else 0 for non-async
        basedir=None,                       # directory of playbook, if applicable
        setup_cache=None,                   # used to share fact data w/ other tasks
        vars_cache=None,                    # used to store variables about hosts
        transport=C.DEFAULT_TRANSPORT,      # 'ssh', 'paramiko', 'local'
        conditional='True',                 # run only if this fact expression evals to true
        callbacks=None,                     # used for output
        sudo=False,                         # whether to run sudo or not
        sudo_user=C.DEFAULT_SUDO_USER,      # ex: 'root'
        module_vars=None,                   # a playbooks internals thing
        default_vars=None,                  # ditto
        extra_vars=None,                    # extra vars specified with he playbook(s)
        is_playbook=False,                  # running from playbook or not?
        inventory=None,                     # reference to Inventory object
        subset=None,                        # subset pattern
        check=False,                        # don't make any changes, just try to probe for potential changes
        diff=False,                         # whether to show diffs for template files that change
        environment=None,                   # environment variables (as dict) to use inside the command
        complex_args=None,                  # structured data in addition to module_args, must be a dict
        error_on_undefined_vars=C.DEFAULT_UNDEFINED_VAR_BEHAVIOR, # ex. False
        accelerate=False,                   # use accelerated connection
        accelerate_ipv6=False,              # accelerated connection w/ IPv6
        accelerate_port=None,               # port to use with accelerated connection
        su=False,                           # Are we running our command via su?
        su_user=None,                       # User to su to when running command, ex: 'root'
        su_pass=C.DEFAULT_SU_PASS,
        vault_pass=None,
        run_hosts=None,                     # an optional list of pre-calculated hosts to run on
        no_log=False,                       # option to enable/disable logging for a given task
        run_once=False,                     # option to enable/disable host bypass loop for a given task
        sudo_exe=C.DEFAULT_SUDO_EXE,        # ex: /usr/local/bin/sudo
        ):

        # used to lock multiprocess inputs and outputs at various levels
        self.output_lockfile  = OUTPUT_LOCKFILE
        self.process_lockfile = PROCESS_LOCKFILE

        if not complex_args:
            complex_args = {}

        # storage & defaults
        self.check            = check
        self.diff             = diff
        self.setup_cache      = utils.default(setup_cache, lambda: ansible.cache.FactCache())
        self.vars_cache       = utils.default(vars_cache, lambda: collections.defaultdict(dict))
        self.basedir          = utils.default(basedir, lambda: os.getcwd())
        self.callbacks        = utils.default(callbacks, lambda: DefaultRunnerCallbacks())
        self.generated_jid    = str(random.randint(0, 999999999999))
        self.transport        = transport
        self.inventory        = utils.default(inventory, lambda: ansible.inventory.Inventory(host_list))

        self.module_vars      = utils.default(module_vars, lambda: {})
        self.default_vars     = utils.default(default_vars, lambda: {})
        self.extra_vars       = utils.default(extra_vars, lambda: {})

        self.always_run       = None
        self.connector        = connection.Connector(self)
        self.conditional      = conditional
        self.delegate_to      = None
        self.module_name      = module_name
        self.forks            = int(forks)
        self.pattern          = pattern
        self.module_args      = module_args
        self.timeout          = timeout
        self.remote_user      = remote_user
        self.remote_pass      = remote_pass
        self.remote_port      = remote_port
        self.private_key_file = private_key_file
        self.background       = background
        self.sudo             = sudo
        self.sudo_user_var    = sudo_user
        self.sudo_user        = None
        self.sudo_pass        = sudo_pass
        self.is_playbook      = is_playbook
        self.environment      = environment
        self.complex_args     = complex_args
        self.error_on_undefined_vars = error_on_undefined_vars
        self.accelerate       = accelerate
        self.accelerate_port  = accelerate_port
        self.accelerate_ipv6  = accelerate_ipv6
        self.callbacks.runner = self
        self.su               = su
        self.su_user_var      = su_user
        self.su_user          = None
        self.su_pass          = su_pass
        self.omit_token       = '__omit_place_holder__%s' % _md5(os.urandom(64)).hexdigest()
        self.vault_pass       = vault_pass
        self.no_log           = no_log
        self.run_once         = run_once
        self.sudo_exe         = sudo_exe

        if self.transport == 'smart':
            # If the transport is 'smart', check to see if certain conditions
            # would prevent us from using ssh, and fallback to paramiko.
            # 'smart' is the default since 1.2.1/1.3
            self.transport = "ssh"
            if sys.platform.startswith('darwin') and self.remote_pass:
                # due to a current bug in sshpass on OSX, which can trigger
                # a kernel panic even for non-privileged users, we revert to
                # paramiko on that OS when a SSH password is specified
                self.transport = "paramiko"
            else:
                # see if SSH can support ControlPersist if not use paramiko
                cmd = subprocess.Popen(['ssh','-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = cmd.communicate()
                if "Bad configuration option" in err:
                    self.transport = "paramiko"

        # save the original transport, in case it gets
        # changed later via options like accelerate
        self.original_transport = self.transport

        # misc housekeeping
        if subset and self.inventory._subset is None:
            # don't override subset when passed from playbook
            self.inventory.subset(subset)

        # If we get a pre-built list of hosts to run on, from say a playbook, use them.
        # Also where we will store the hosts to run on once discovered
        self.run_hosts = run_hosts

        if self.transport == 'local':
            self.remote_user = pwd.getpwuid(os.geteuid())[0]

        if module_path is not None:
            for i in module_path.split(os.pathsep):
                utils.plugins.module_finder.add_directory(i)

        utils.plugins.push_basedir(self.basedir)

        # ensure we are using unique tmp paths
        random.seed()
    # *****************************************************

    def _complex_args_hack(self, complex_args, module_args):
        """
        ansible-playbook both allows specifying key=value string arguments and complex arguments
        however not all modules use our python common module system and cannot
        access these.  An example might be a Bash module.  This hack allows users to still pass "args"
        as a hash of simple scalars to those arguments and is short term.  We could technically
        just feed JSON to the module, but that makes it hard on Bash consumers.  The way this is implemented
        it does mean values in 'args' have LOWER priority than those on the key=value line, allowing
        args to provide yet another way to have pluggable defaults.
        """
        if complex_args is None:
            return module_args
        if not isinstance(complex_args, dict):
            raise errors.AnsibleError("complex arguments are not a dictionary: %s" % complex_args)
        for (k,v) in complex_args.iteritems():
            if isinstance(v, basestring):
                module_args = "%s=%s %s" % (k, pipes.quote(v), module_args)
        return module_args

    # *****************************************************

    def _transfer_str(self, conn, tmp, name, data):
        ''' transfer string to remote file '''

        if type(data) == dict:
            data = utils.jsonify(data)

        afd, afile = tempfile.mkstemp()
        afo = os.fdopen(afd, 'w')
        try:
            if not isinstance(data, unicode):
                #ensure the data is valid UTF-8
                data.decode('utf-8')
            else:
                data = data.encode('utf-8')
            afo.write(data)
        except:
            raise errors.AnsibleError("failure encoding into utf-8")
        afo.flush()
        afo.close()

        remote = conn.shell.join_path(tmp, name)
        try:
            conn.put_file(afile, remote)
        finally:
            os.unlink(afile)
        return remote

    # *****************************************************

    def _compute_environment_string(self, conn, inject=None):
        ''' what environment variables to use when running the command? '''

        enviro = {}
        if self.environment:
            enviro = template.template(self.basedir, self.environment, inject, convert_bare=True)
            enviro = utils.safe_eval(enviro)
            if type(enviro) != dict:
                raise errors.AnsibleError("environment must be a dictionary, received %s" % enviro)

        return conn.shell.env_prefix(**enviro)

    # *****************************************************

    def _compute_delegate(self, password, remote_inject):

        """ Build a dictionary of all attributes for the delegate host """

        delegate = {}

        # allow delegated host to be templated
        delegate['inject'] = remote_inject.copy()

        # set any interpreters
        interpreters = []
        for i in delegate['inject']:
            if i.startswith("ansible_") and i.endswith("_interpreter"):
                interpreters.append(i)
        for i in interpreters:
            del delegate['inject'][i]
        port = C.DEFAULT_REMOTE_PORT

        # get the vars for the delegate by its name
        try:
            this_info = delegate['inject']['hostvars'][self.delegate_to]
        except:
            # make sure the inject is empty for non-inventory hosts
            this_info = {}

        # get the real ssh_address for the delegate
        # and allow ansible_ssh_host to be templated
        delegate['ssh_host'] = template.template(
                                   self.basedir,
                                   this_info.get('ansible_ssh_host', self.delegate_to),
                                   this_info,
                                   fail_on_undefined=True
                               )

        delegate['port'] = this_info.get('ansible_ssh_port', port)
        delegate['user'] = self._compute_delegate_user(self.delegate_to, delegate['inject'])
        delegate['pass'] = this_info.get('ansible_ssh_pass', password)
        delegate['private_key_file'] = this_info.get('ansible_ssh_private_key_file', self.private_key_file)
        delegate['transport'] = this_info.get('ansible_connection', self.transport)
        delegate['sudo_pass'] = this_info.get('ansible_sudo_pass', self.sudo_pass)

        # Last chance to get private_key_file from global variables.
        # this is useful if delegated host is not defined in the inventory
        if delegate['private_key_file'] is None:
            delegate['private_key_file'] = remote_inject.get('ansible_ssh_private_key_file', None)

        if delegate['private_key_file'] is not None:
            delegate['private_key_file'] = os.path.expanduser(delegate['private_key_file'])

        for i in this_info:
            if i.startswith("ansible_") and i.endswith("_interpreter"):
                delegate['inject'][i] = this_info[i]

        return delegate

    def _compute_delegate_user(self, host, inject):

        """ Calculate the remote user based on an order of preference """

        # inventory > playbook > original_host

        actual_user = inject.get('ansible_ssh_user', self.remote_user)
        thisuser = None

        if host in inject['hostvars']:
            if inject['hostvars'][host].get('ansible_ssh_user'):
                # user for delegate host in inventory
                thisuser = inject['hostvars'][host].get('ansible_ssh_user')
        else:
            # look up the variables for the host directly from inventory
            try:
                host_vars = self.inventory.get_variables(host, vault_password=self.vault_pass)
                if 'ansible_ssh_user' in host_vars:
                    thisuser = host_vars['ansible_ssh_user']
            except Exception, e:
                # the hostname was not found in the inventory, so
                # we just ignore this and try the next method
                pass

        if thisuser is None and self.remote_user:
            # user defined by play/runner
            thisuser = self.remote_user

        if thisuser is not None:
            actual_user = thisuser
        else:
            # fallback to the inventory user of the play host
            #actual_user = inject.get('ansible_ssh_user', actual_user)
            actual_user = inject.get('ansible_ssh_user', self.remote_user)

        return actual_user

    def _count_module_args(self, args, allow_dupes=False):
        '''
        Count the number of k=v pairs in the supplied module args. This is
        basically a specialized version of parse_kv() from utils with a few
        minor changes.
        '''
        options = {}
        if args is not None:
            try:
                vargs = split_args(args)
            except Exception, e:
                if "unbalanced jinja2 block or quotes" in str(e):
                    raise errors.AnsibleError("error parsing argument string '%s', try quoting the entire line." % args)
                else:
                    raise
            for x in vargs:
                quoted = x.startswith('"') and x.endswith('"') or x.startswith("'") and x.endswith("'")
                if "=" in x and not quoted:
                    k, v = x.split("=",1)
                    is_shell_module = self.module_name in ('command', 'shell')
                    is_shell_param = k in ('creates', 'removes', 'chdir', 'executable')
                    if k in options and not allow_dupes:
                        if not(is_shell_module and not is_shell_param):
                            raise errors.AnsibleError("a duplicate parameter was found in the argument string (%s)" % k)
                    if is_shell_module and is_shell_param or not is_shell_module:
                        options[k] = v
        return len(options)


    # *****************************************************

    def _execute_module(self, conn, tmp, module_name, args,
        async_jid=None, async_module=None, async_limit=None, inject=None, persist_files=False, complex_args=None, delete_remote_tmp=True):

        ''' transfer and run a module along with its arguments on the remote side'''

        # hack to support fireball mode
        if module_name == 'fireball':
            args = "%s password=%s" % (args, base64.b64encode(str(utils.key_for_hostname(conn.host))))
            if 'port' not in args:
                args += " port=%s" % C.ZEROMQ_PORT

        (
        module_style,
        shebang,
        module_data
        ) = self._configure_module(conn, module_name, args, inject, complex_args)

        # a remote tmp path may be necessary and not already created
        if self._late_needs_tmp_path(conn, tmp, module_style):
            tmp = self._make_tmp_path(conn)

        remote_module_path = conn.shell.join_path(tmp, module_name)

        if (module_style != 'new'
           or async_jid is not None
           or not conn.has_pipelining
           or not C.ANSIBLE_SSH_PIPELINING
           or C.DEFAULT_KEEP_REMOTE_FILES
           or self.su):
            self._transfer_str(conn, tmp, module_name, module_data)

        environment_string = self._compute_environment_string(conn, inject)

        if "tmp" in tmp and ((self.sudo and self.sudo_user != 'root') or (self.su and self.su_user != 'root')):
            # deal with possible umask issues once sudo'ed to other user
            self._remote_chmod(conn, 'a+r', remote_module_path, tmp)

        cmd = ""
        in_data = None
        if module_style != 'new':
            if 'CHECKMODE=True' in args:
                # if module isn't using AnsibleModuleCommon infrastructure we can't be certain it knows how to
                # do --check mode, so to be safe we will not run it.
                return ReturnData(conn=conn, result=dict(skipped=True, msg="cannot yet run check mode against old-style modules"))
            elif 'NO_LOG' in args:
                return ReturnData(conn=conn, result=dict(skipped=True, msg="cannot use no_log: with old-style modules"))

            args = template.template(self.basedir, args, inject)

            # decide whether we need to transfer JSON or key=value
            argsfile = None
            if module_style == 'non_native_want_json':
                if complex_args:
                    complex_args.update(utils.parse_kv(args))
                    argsfile = self._transfer_str(conn, tmp, 'arguments', utils.jsonify(complex_args))
                else:
                    argsfile = self._transfer_str(conn, tmp, 'arguments', utils.jsonify(utils.parse_kv(args)))

            else:
                argsfile = self._transfer_str(conn, tmp, 'arguments', args)

            if (self.sudo and self.sudo_user != 'root') or (self.su and self.su_user != 'root'):
                # deal with possible umask issues once sudo'ed to other user
                self._remote_chmod(conn, 'a+r', argsfile, tmp)

            if async_jid is None:
                cmd = "%s %s" % (remote_module_path, argsfile)
            else:
                cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module, argsfile]])
        else:
            if async_jid is None:
                if conn.has_pipelining and C.ANSIBLE_SSH_PIPELINING and not C.DEFAULT_KEEP_REMOTE_FILES and not self.su:
                    in_data = module_data
                else:
                    cmd = "%s" % (remote_module_path)
            else:
                cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module]])

        if not shebang:
            raise errors.AnsibleError("module is missing interpreter line")

        rm_tmp = None
        if "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if not self.sudo or self.su or self.sudo_user == 'root' or self.su_user == 'root':
                # not sudoing or sudoing to root, so can cleanup files in the same step
                rm_tmp = tmp

        cmd = conn.shell.build_module_command(environment_string, shebang, cmd, rm_tmp)
        cmd = cmd.strip()

        sudoable = True
        if module_name == "accelerate":
            # always run the accelerate module as the user
            # specified in the play, not the sudo_user
            sudoable = False

        if self.su:
            res = self._low_level_exec_command(conn, cmd, tmp, su=True, in_data=in_data)
        else:
            res = self._low_level_exec_command(conn, cmd, tmp, sudoable=sudoable, in_data=in_data)

        if "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES and not persist_files and delete_remote_tmp:
            if (self.sudo and self.sudo_user != 'root') or (self.su and self.su_user != 'root'):
            # not sudoing to root, so maybe can't delete files as that other user
            # have to clean up temp files as original user in a second step
                cmd2 = conn.shell.remove(tmp, recurse=True)
                self._low_level_exec_command(conn, cmd2, tmp, sudoable=False)

        data = utils.parse_json(res['stdout'], from_remote=True, no_exceptions=True)
        if 'parsed' in data and data['parsed'] == False:
            data['msg'] += res['stderr']
        return ReturnData(conn=conn, result=data)

    # *****************************************************

    def _executor(self, host, new_stdin):
        ''' handler for multiprocessing library '''

        try:
            fileno = sys.stdin.fileno()
        except ValueError:
            fileno = None

        try:
            self._new_stdin = new_stdin
            if not new_stdin and fileno is not None:
                try:
                    self._new_stdin = os.fdopen(os.dup(fileno))
                except OSError, e:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass

            exec_rc = self._executor_internal(host, new_stdin)
            if type(exec_rc) != ReturnData:
                raise Exception("unexpected return type: %s" % type(exec_rc))
            # redundant, right?
            if not exec_rc.comm_ok:
                self.callbacks.on_unreachable(host, exec_rc.result)
            return exec_rc
        except errors.AnsibleError, ae:
            msg = str(ae)
            self.callbacks.on_unreachable(host, msg)
            return ReturnData(host=host, comm_ok=False, result=dict(failed=True, msg=msg))
        except Exception:
            msg = traceback.format_exc()
            self.callbacks.on_unreachable(host, msg)
            return ReturnData(host=host, comm_ok=False, result=dict(failed=True, msg=msg))

    # *****************************************************

    def get_combined_cache(self):
        # merge the VARS and SETUP caches for this host
        combined_cache = self.setup_cache.copy()
        return utils.merge_hash(combined_cache, self.vars_cache)

    def get_inject_vars(self, host):
        host_variables = self.inventory.get_variables(host, vault_password=self.vault_pass)
        combined_cache = self.get_combined_cache()

        # use combined_cache and host_variables to template the module_vars
        # we update the inject variables with the data we're about to template
        # since some of the variables we'll be replacing may be contained there too
        module_vars_inject = utils.combine_vars(host_variables, combined_cache.get(host, {}))
        module_vars_inject = utils.combine_vars(self.module_vars, module_vars_inject)
        module_vars = template.template(self.basedir, self.module_vars, module_vars_inject)

        # remove bad variables from the module vars, which may be in there due
        # the way role declarations are specified in playbooks
        if 'tags' in module_vars:
            del module_vars['tags']
        if 'when' in module_vars:
            del module_vars['when']

        # start building the dictionary of injected variables
        inject = {}

        # default vars are the lowest priority
        inject = utils.combine_vars(inject, self.default_vars)
        # next come inventory variables for the host
        inject = utils.combine_vars(inject, host_variables)
        # then the setup_cache which contains facts gathered
        inject = utils.combine_vars(inject, self.setup_cache.get(host, {}))
        # followed by vars (vars, vars_files, vars/main.yml)
        inject = utils.combine_vars(inject, self.vars_cache.get(host, {}))
        # then come the module variables
        inject = utils.combine_vars(inject, module_vars)
        # and finally -e vars are the highest priority
        inject = utils.combine_vars(inject, self.extra_vars)
        # and then special vars
        inject.setdefault('ansible_ssh_user', self.remote_user)
        inject['group_names']  = host_variables.get('group_names', [])
        inject['groups']       = self.inventory.groups_list()
        inject['vars']         = self.module_vars
        inject['defaults']     = self.default_vars
        inject['environment']  = self.environment
        inject['playbook_dir'] = os.path.abspath(self.basedir)
        inject['omit']         = self.omit_token
        inject['combined_cache'] = combined_cache

        return inject

    def _executor_internal(self, host, new_stdin):
        ''' executes any module one or more times '''

        inject = self.get_inject_vars(host)
        hostvars = HostVars(inject['combined_cache'], self.inventory, vault_password=self.vault_pass)
        inject['hostvars'] = hostvars

        host_connection = inject.get('ansible_connection', self.transport)
        if host_connection in [ 'paramiko', 'ssh', 'accelerate' ]:
            port = hostvars.get('ansible_ssh_port', self.remote_port)
            if port is None:
                port = C.DEFAULT_REMOTE_PORT
        else:
            # fireball, local, etc
            port = self.remote_port

        if self.inventory.basedir() is not None:
            inject['inventory_dir'] = self.inventory.basedir()

        if self.inventory.src() is not None:
            inject['inventory_file'] = self.inventory.src()

        # could be already set by playbook code
        inject.setdefault('ansible_version', utils.version_info(gitinfo=False))

        # allow with_foo to work in playbooks...
        items = None
        items_plugin = self.module_vars.get('items_lookup_plugin', None)

        if items_plugin is not None and items_plugin in utils.plugins.lookup_loader:

            basedir = self.basedir
            if '_original_file' in inject:
                basedir = os.path.dirname(inject['_original_file'])
                filesdir = os.path.join(basedir, '..', 'files')
                if os.path.exists(filesdir):
                    basedir = filesdir

            try:
                items_terms = self.module_vars.get('items_lookup_terms', '')
                items_terms = template.template(basedir, items_terms, inject)
                items = utils.plugins.lookup_loader.get(items_plugin, runner=self, basedir=basedir).run(items_terms, inject=inject)
            except errors.AnsibleUndefinedVariable, e:
                if 'has no attribute' in str(e):
                    # the undefined variable was an attribute of a variable that does
                    # exist, so try and run this through the conditional check to see
                    # if the user wanted to skip something on being undefined
                    if utils.check_conditional(self.conditional, self.basedir, inject, fail_on_undefined=True):
                        # the conditional check passed, so we have to fail here
                        raise
                    else:
                        # the conditional failed, so we skip this task
                        result = utils.jsonify(dict(changed=False, skipped=True))
                        self.callbacks.on_skipped(host, None)
                        return ReturnData(host=host, result=result)

            # strip out any jinja2 template syntax within
            # the data returned by the lookup plugin
            items = utils._clean_data_struct(items, from_remote=True)
            if type(items) != list:
                raise errors.AnsibleError("lookup plugins have to return a list: %r" % items)

            if len(items) and utils.is_list_of_strings(items) and self.module_name in [ 'apt', 'yum', 'pkgng', 'zypper' ]:
                # hack for apt, yum, and pkgng so that with_items maps back into a single module call
                use_these_items = []
                for x in items:
                    inject['item'] = x
                    if not self.conditional or utils.check_conditional(self.conditional, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars):
                        use_these_items.append(x)
                inject['item'] = ",".join(use_these_items)
                items = None

        def _safe_template_complex_args(args, inject):
            # Ensure the complex args here are a dictionary, but
            # first template them if they contain a variable

            returned_args = args
            if isinstance(args, basestring):
                # If the complex_args were evaluated to a dictionary and there are
                # more keys in the templated version than the evaled version, some
                # param inserted additional keys (the template() call also runs
                # safe_eval on the var if it looks like it's a datastructure). If the
                # evaled_args are not a dict, it's most likely a whole variable (ie.
                # args: {{var}}), in which case there's no way to detect the proper
                # count of params in the dictionary.

                templated_args = template.template(self.basedir, args, inject, convert_bare=True)
                evaled_args = utils.safe_eval(args)

                if isinstance(evaled_args, dict) and len(evaled_args) > 0 and len(evaled_args) != len(templated_args):
                    raise errors.AnsibleError("a variable tried to insert extra parameters into the args for this task")

                # set the returned_args to the templated_args
                returned_args = templated_args

            # and a final check to make sure the complex args are a dict
            if returned_args is not None and not isinstance(returned_args, dict):
                raise errors.AnsibleError("args must be a dictionary, received %s" % returned_args)

            return returned_args

        # logic to decide how to run things depends on whether with_items is used
        if items is None:
            complex_args = _safe_template_complex_args(self.complex_args, inject)
            return self._executor_internal_inner(host, self.module_name, self.module_args, inject, port, complex_args=complex_args)
        elif len(items) > 0:

            # executing using with_items, so make multiple calls
            # TODO: refactor

            if self.background > 0:
                raise errors.AnsibleError("lookup plugins (with_*) cannot be used with async tasks")

            all_comm_ok = True
            all_changed = False
            all_failed = False
            results = []
            for x in items:
                # use a fresh inject for each item
                this_inject = inject.copy()
                this_inject['item'] = x

                complex_args = _safe_template_complex_args(self.complex_args, this_inject)

                result = self._executor_internal_inner(
                     host,
                     self.module_name,
                     self.module_args,
                     this_inject,
                     port,
                     complex_args=complex_args
                )
                results.append(result.result)
                if result.comm_ok == False:
                    all_comm_ok = False
                    all_failed = True
                    break
                for x in results:
                    if x.get('changed') == True:
                        all_changed = True
                    if (x.get('failed') == True) or ('failed_when_result' in x and [x['failed_when_result']] or [('rc' in x) and (x['rc'] != 0)])[0]:
                        all_failed = True
                        break
            msg = 'All items completed'
            if all_failed:
                msg = "One or more items failed."
            rd_result = dict(failed=all_failed, changed=all_changed, results=results, msg=msg)
            if not all_failed:
                del rd_result['failed']
            return ReturnData(host=host, comm_ok=all_comm_ok, result=rd_result)
        else:
            self.callbacks.on_skipped(host, None)
            return ReturnData(host=host, comm_ok=True, result=dict(changed=False, skipped=True))

    # *****************************************************

    def _executor_internal_inner(self, host, module_name, module_args, inject, port, is_chained=False, complex_args=None):
        ''' decides how to invoke a module '''

        # late processing of parameterized sudo_user (with_items,..)
        if self.sudo_user_var is not None:
            self.sudo_user = template.template(self.basedir, self.sudo_user_var, inject)
        if self.su_user_var is not None:
            self.su_user = template.template(self.basedir, self.su_user_var, inject)

        # module_name may be dynamic (but cannot contain {{ ansible_ssh_user }})
        module_name  = template.template(self.basedir, module_name, inject)

        if module_name in utils.plugins.action_loader:
            if self.background != 0:
                raise errors.AnsibleError("async mode is not supported with the %s module" % module_name)
            handler = utils.plugins.action_loader.get(module_name, self)
        elif self.background == 0:
            handler = utils.plugins.action_loader.get('normal', self)
        else:
            handler = utils.plugins.action_loader.get('async', self)

        if type(self.conditional) != list:
            self.conditional = [ self.conditional ]

        for cond in self.conditional:

            if not utils.check_conditional(cond, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars):
                result = utils.jsonify(dict(changed=False, skipped=True))
                self.callbacks.on_skipped(host, inject.get('item',None))
                return ReturnData(host=host, result=result)

        if getattr(handler, 'setup', None) is not None:
            handler.setup(module_name, inject)
        conn = None
        actual_host = inject.get('ansible_ssh_host', host)
        # allow ansible_ssh_host to be templated
        actual_host = template.template(self.basedir, actual_host, inject, fail_on_undefined=True)
        actual_port = port
        actual_user = inject.get('ansible_ssh_user', self.remote_user)
        actual_pass = inject.get('ansible_ssh_pass', self.remote_pass)
        actual_transport = inject.get('ansible_connection', self.transport)
        actual_private_key_file = inject.get('ansible_ssh_private_key_file', self.private_key_file)
        actual_private_key_file = template.template(self.basedir, actual_private_key_file, inject, fail_on_undefined=True)
        self.sudo = utils.boolean(inject.get('ansible_sudo', self.sudo))
        self.sudo_user = inject.get('ansible_sudo_user', self.sudo_user)
        self.sudo_pass = inject.get('ansible_sudo_pass', self.sudo_pass)
        self.su = inject.get('ansible_su', self.su)
        self.su_pass = inject.get('ansible_su_pass', self.su_pass)
        self.sudo_exe = inject.get('ansible_sudo_exe', self.sudo_exe)

        # select default root user in case self.sudo requested
        # but no user specified; happens e.g. in host vars when
        # just ansible_sudo=True is specified
        if self.sudo and self.sudo_user is None:
            self.sudo_user = 'root'

        if actual_private_key_file is not None:
            actual_private_key_file = os.path.expanduser(actual_private_key_file)

        if self.accelerate and actual_transport != 'local':
            #Fix to get the inventory name of the host to accelerate plugin
            if inject.get('ansible_ssh_host', None):
                self.accelerate_inventory_host = host
            else:
                self.accelerate_inventory_host = None
            # if we're using accelerated mode, force the
            # transport to accelerate
            actual_transport = "accelerate"
            if not self.accelerate_port:
                self.accelerate_port = C.ACCELERATE_PORT

        actual_port = inject.get('ansible_ssh_port', port)

        # the delegated host may have different SSH port configured, etc
        # and we need to transfer those, and only those, variables
        self.delegate_to = inject.get('delegate_to', None)
        if self.delegate_to:
            self.delegate_to = template.template(self.basedir, self.delegate_to, inject)

        if self.delegate_to is not None:
            delegate = self._compute_delegate(actual_pass, inject)
            actual_transport = delegate['transport']
            actual_host = delegate['ssh_host']
            actual_port = delegate['port']
            actual_user = delegate['user']
            actual_pass = delegate['pass']
            actual_private_key_file = delegate['private_key_file']
            self.sudo_pass = delegate['sudo_pass']
            inject = delegate['inject']

        # user/pass may still contain variables at this stage
        actual_user = template.template(self.basedir, actual_user, inject)
        actual_pass = template.template(self.basedir, actual_pass, inject)
        self.sudo_pass = template.template(self.basedir, self.sudo_pass, inject)

        # make actual_user available as __magic__ ansible_ssh_user variable
        inject['ansible_ssh_user'] = actual_user

        try:
            if actual_transport == 'accelerate':
                # for accelerate, we stuff both ports into a single
                # variable so that we don't have to mangle other function
                # calls just to accommodate this one case
                actual_port = [actual_port, self.accelerate_port]
            elif actual_port is not None:
                actual_port = int(template.template(self.basedir, actual_port, inject))
        except ValueError, e:
            result = dict(failed=True, msg="FAILED: Configured port \"%s\" is not a valid port, expected integer" % actual_port)
            return ReturnData(host=host, comm_ok=False, result=result)

        try:
            conn = self.connector.connect(actual_host, actual_port, actual_user, actual_pass, actual_transport, actual_private_key_file)
            if self.delegate_to or host != actual_host:
                conn.delegate = host

            default_shell = getattr(conn, 'default_shell', '')
            shell_type = inject.get('ansible_shell_type')
            if not shell_type:
                if default_shell:
                    shell_type = default_shell
                else:
                    shell_type = os.path.basename(C.DEFAULT_EXECUTABLE)

            shell_plugin = utils.plugins.shell_loader.get(shell_type)
            if shell_plugin is None:
                shell_plugin = utils.plugins.shell_loader.get('sh')
            conn.shell = shell_plugin

        except errors.AnsibleConnectionFailed, e:
            result = dict(failed=True, msg="FAILED: %s" % str(e))
            return ReturnData(host=host, comm_ok=False, result=result)

        tmp = ''
        # action plugins may DECLARE via TRANSFERS_FILES = True that they need a remote tmp path working dir
        if self._early_needs_tmp_path(module_name, handler):
            tmp = self._make_tmp_path(conn)

        # allow module args to work as a dictionary
        # though it is usually a string
        if isinstance(module_args, dict):
            module_args = utils.serialize_args(module_args)

        # render module_args and complex_args templates
        try:
            # When templating module_args, we need to be careful to ensure
            # that no variables inadvertantly (or maliciously) add params
            # to the list of args. We do this by counting the number of k=v
            # pairs before and after templating.
            num_args_pre = self._count_module_args(module_args, allow_dupes=True)
            module_args = template.template(self.basedir, module_args, inject, fail_on_undefined=self.error_on_undefined_vars)
            num_args_post = self._count_module_args(module_args)
            if num_args_pre != num_args_post:
                raise errors.AnsibleError("A variable inserted a new parameter into the module args. " + \
                                          "Be sure to quote variables if they contain equal signs (for example: \"{{var}}\").")
            # And we also make sure nothing added in special flags for things
            # like the command/shell module (ie. #USE_SHELL)
            if '#USE_SHELL' in module_args:
                raise errors.AnsibleError("A variable tried to add #USE_SHELL to the module arguments.")
            complex_args = template.template(self.basedir, complex_args, inject, fail_on_undefined=self.error_on_undefined_vars)
        except jinja2.exceptions.UndefinedError, e:
            raise errors.AnsibleUndefinedVariable("One or more undefined variables: %s" % str(e))

        # filter omitted arguments out from complex_args
        if complex_args:
            complex_args = dict(filter(lambda x: x[1] != self.omit_token, complex_args.iteritems()))

        # Filter omitted arguments out from module_args.
        # We do this with split_args instead of parse_kv to ensure
        # that things are not unquoted/requoted incorrectly
        args = split_args(module_args)
        final_args = []
        for arg in args:
            if '=' in arg:
                k,v = arg.split('=', 1)
                if unquote(v) != self.omit_token:
                    final_args.append(arg)
            else:
                # not a k=v param, append it
                final_args.append(arg)
        module_args = ' '.join(final_args)

        result = handler.run(conn, tmp, module_name, module_args, inject, complex_args)
        # Code for do until feature
        until = self.module_vars.get('until', None)
        if until is not None and result.comm_ok:
            inject[self.module_vars.get('register')] = result.result

            cond = template.template(self.basedir, until, inject, expand_lists=False)
            if not utils.check_conditional(cond,  self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars):
                retries = self.module_vars.get('retries')
                delay   = self.module_vars.get('delay')
                for x in range(1, int(retries) + 1):
                    # template the delay, cast to float and sleep
                    delay = template.template(self.basedir, delay, inject, expand_lists=False)
                    delay = float(delay)
                    time.sleep(delay)
                    tmp = ''
                    if self._early_needs_tmp_path(module_name, handler):
                        tmp = self._make_tmp_path(conn)
                    result = handler.run(conn, tmp, module_name, module_args, inject, complex_args)
                    result.result['attempts'] = x
                    vv("Result from run %i is: %s" % (x, result.result))
                    inject[self.module_vars.get('register')] = result.result
                    cond = template.template(self.basedir, until, inject, expand_lists=False)
                    if utils.check_conditional(cond, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars):
                        break
                if result.result['attempts'] == retries and not utils.check_conditional(cond, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars):
                    result.result['failed'] = True
                    result.result['msg'] = "Task failed as maximum retries was encountered"
            else:
                result.result['attempts'] = 0
        conn.close()

        if not result.comm_ok:
            # connection or parsing errors...
            self.callbacks.on_unreachable(host, result.result)
        else:
            data = result.result

            # https://github.com/ansible/ansible/issues/4958
            if hasattr(sys.stdout, "isatty"):
                if "stdout" in data and sys.stdout.isatty():
                    if not string_functions.isprintable(data['stdout']):
                        data['stdout'] = ''

            if 'item' in inject:
                result.result['item'] = inject['item']

            result.result['invocation'] = dict(
                module_args=module_args,
                module_name=module_name
            )

            changed_when = self.module_vars.get('changed_when')
            failed_when = self.module_vars.get('failed_when')
            if (changed_when is not None or failed_when is not None) and self.background == 0:
                register = self.module_vars.get('register')
                if register is not None:
                    if 'stdout' in data:
                        data['stdout_lines'] = data['stdout'].splitlines()
                    inject[register] = data
                # only run the final checks if the async_status has finished,
                # or if we're not running an async_status check at all
                if (module_name == 'async_status' and "finished" in data) or module_name != 'async_status':
                    if changed_when is not None and 'skipped' not in data:
                        data['changed'] = utils.check_conditional(changed_when, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars)
                    if failed_when is not None and 'skipped' not in data:
                        data['failed_when_result'] = data['failed'] = utils.check_conditional(failed_when, self.basedir, inject, fail_on_undefined=self.error_on_undefined_vars)


            if is_chained:
                # no callbacks
                return result
            if 'skipped' in data:
                self.callbacks.on_skipped(host, inject.get('item',None))

            if self.no_log:
                data = utils.censor_unlogged_data(data)

            if not result.is_successful():
                ignore_errors = self.module_vars.get('ignore_errors', False)
                self.callbacks.on_failed(host, data, ignore_errors)
            else:
                if self.diff:
                    self.callbacks.on_file_diff(conn.host, result.diff)
                self.callbacks.on_ok(host, data)

        return result

    def _early_needs_tmp_path(self, module_name, handler):
        ''' detect if a tmp path should be created before the handler is called '''
        if module_name in utils.plugins.action_loader:
          return getattr(handler, 'TRANSFERS_FILES', False)
        # other modules never need tmp path at early stage
        return False

    def _late_needs_tmp_path(self, conn, tmp, module_style):
        if "tmp" in tmp:
            # tmp has already been created
            return False
        if not conn.has_pipelining or not C.ANSIBLE_SSH_PIPELINING or C.DEFAULT_KEEP_REMOTE_FILES or self.su:
            # tmp is necessary to store module source code
            return True
        if not conn.has_pipelining:
            # tmp is necessary to store the module source code
            # or we want to keep the files on the target system
            return True
        if module_style != "new":
            # even when conn has pipelining, old style modules need tmp to store arguments
            return True
        return False


    # *****************************************************

    def _low_level_exec_command(self, conn, cmd, tmp, sudoable=False,
                                executable=None, su=False, in_data=None):
        ''' execute a command string over SSH, return the output '''

        if not cmd:
            # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
            return dict(stdout='', stderr='')

        if executable is None:
            executable = C.DEFAULT_EXECUTABLE

        sudo_user = self.sudo_user
        su_user = self.su_user

        # compare connection user to (su|sudo)_user and disable if the same
        # assume connection type is local if no user attribute
        this_user = getattr(conn, 'user', getpass.getuser())
        if (not su and this_user == sudo_user) or (su and this_user == su_user):
            sudoable = False
            su = False

        if su:
            rc, stdin, stdout, stderr = conn.exec_command(cmd,
                                                          tmp,
                                                          su=su,
                                                          su_user=su_user,
                                                          executable=executable,
                                                          in_data=in_data)
        else:
            rc, stdin, stdout, stderr = conn.exec_command(cmd,
                                                          tmp,
                                                          sudo_user,
                                                          sudoable=sudoable,
                                                          executable=executable,
                                                          in_data=in_data)

        if type(stdout) not in [ str, unicode ]:
            out = ''.join(stdout.readlines())
        else:
            out = stdout

        if type(stderr) not in [ str, unicode ]:
            err = ''.join(stderr.readlines())
        else:
            err = stderr

        if rc is not None:
            return dict(rc=rc, stdout=out, stderr=err)
        else:
            return dict(stdout=out, stderr=err)

    # *****************************************************

    def _remote_chmod(self, conn, mode, path, tmp, sudoable=False, su=False):
        ''' issue a remote chmod command '''
        cmd = conn.shell.chmod(mode, path)
        return self._low_level_exec_command(conn, cmd, tmp, sudoable=sudoable, su=su)

    # *****************************************************

    def _remote_md5(self, conn, tmp, path):
        ''' takes a remote md5sum without requiring python, and returns 1 if no file '''
        cmd = conn.shell.md5(path)
        data = self._low_level_exec_command(conn, cmd, tmp, sudoable=True)
        data2 = utils.last_non_blank_line(data['stdout'])
        try:
            if data2 == '':
                # this may happen if the connection to the remote server
                # failed, so just return "INVALIDMD5SUM" to avoid errors
                return "INVALIDMD5SUM"
            else:
                return data2.split()[0]
        except IndexError:
            sys.stderr.write("warning: md5sum command failed unusually, please report this to the list so it can be fixed\n")
            sys.stderr.write("command: %s\n" % md5s)
            sys.stderr.write("----\n")
            sys.stderr.write("output: %s\n" % data)
            sys.stderr.write("----\n")
            # this will signal that it changed and allow things to keep going
            return "INVALIDMD5SUM"

    # *****************************************************

    def _make_tmp_path(self, conn):
        ''' make and return a temporary path on a remote box '''
        basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        use_system_tmp = False
        if (self.sudo and self.sudo_user != 'root') or (self.su and self.su_user != 'root'):
            use_system_tmp = True

        tmp_mode = None
        if self.remote_user != 'root' or ((self.sudo and self.sudo_user != 'root') or (self.su and self.su_user != 'root')):
            tmp_mode = 'a+rx'

        cmd = conn.shell.mkdtemp(basefile, use_system_tmp, tmp_mode)
        result = self._low_level_exec_command(conn, cmd, None, sudoable=False)

        # error handling on this seems a little aggressive?
        if result['rc'] != 0:
            if result['rc'] == 5:
                output = 'Authentication failure.'
            elif result['rc'] == 255 and self.transport in ['ssh']:
                if utils.VERBOSITY > 3:
                    output = 'SSH encountered an unknown error. The output was:\n%s' % (result['stdout']+result['stderr'])
                else:
                    output = 'SSH encountered an unknown error during the connection. We recommend you re-run the command using -vvvv, which will enable SSH debugging output to help diagnose the issue'
            elif 'No space left on device' in result['stderr']:
                output = result['stderr']
            else:
                output = 'Authentication or permission failure.  In some cases, you may have been able to authenticate and did not have permissions on the remote directory. Consider changing the remote temp path in ansible.cfg to a path rooted in "/tmp". Failed command was: %s, exited with result %d' % (cmd, result['rc'])
            if 'stdout' in result and result['stdout'] != '':
                output = output + ": %s" % result['stdout']
            raise errors.AnsibleError(output)

        rc = conn.shell.join_path(utils.last_non_blank_line(result['stdout']).strip(), '')
        # Catch failure conditions, files should never be
        # written to locations in /.
        if rc == '/':
            raise errors.AnsibleError('failed to resolve remote temporary directory from %s: `%s` returned empty string' % (basetmp, cmd))
        return rc

    # *****************************************************

    def _remove_tmp_path(self, conn, tmp_path):
        ''' Remove a tmp_path. '''
        if "-tmp-" in tmp_path:
            cmd = conn.shell.remove(tmp_path, recurse=True)
            self._low_level_exec_command(conn, cmd, None, sudoable=False)
            # If we have gotten here we have a working ssh configuration.
            # If ssh breaks we could leave tmp directories out on the remote system.

    # *****************************************************

    def _copy_module(self, conn, tmp, module_name, module_args, inject, complex_args=None):
        ''' transfer a module over SFTP, does not run it '''
        (
        module_style,
        module_shebang,
        module_data
        ) = self._configure_module(conn, module_name, module_args, inject, complex_args)
        module_remote_path = conn.shell.join_path(tmp, module_name)

        self._transfer_str(conn, tmp, module_name, module_data)

        return (module_remote_path, module_style, module_shebang)

    # *****************************************************

    def _configure_module(self, conn, module_name, module_args, inject, complex_args=None):
        ''' find module and configure it '''

        # Search module path(s) for named module.
        module_suffixes = getattr(conn, 'default_suffixes', None)
        module_path = utils.plugins.module_finder.find_plugin(module_name, module_suffixes, transport=self.transport)
        if module_path is None:
            module_path2 = utils.plugins.module_finder.find_plugin('ping', module_suffixes)
            if module_path2 is not None:
                raise errors.AnsibleFileNotFound("module %s not found in configured module paths" % (module_name))
            else:
                raise errors.AnsibleFileNotFound("module %s not found in configured module paths.  Additionally, core modules are missing. If this is a checkout, run 'git submodule update --init --recursive' to correct this problem." % (module_name))


        # insert shared code and arguments into the module
        (module_data, module_style, module_shebang) = module_replacer.modify_module(
            module_path, complex_args, module_args, inject
        )

        return (module_style, module_shebang, module_data)


    # *****************************************************


    def _parallel_exec(self, hosts):
        ''' handles mulitprocessing when more than 1 fork is required '''

        manager = multiprocessing.Manager()
        job_queue = manager.Queue()
        for host in hosts:
            job_queue.put(host)
        result_queue = manager.Queue()

        try:
            fileno = sys.stdin.fileno()
        except ValueError:
            fileno = None

        workers = []
        for i in range(self.forks):
            new_stdin = None
            if fileno is not None:
                try:
                    new_stdin = os.fdopen(os.dup(fileno))
                except OSError, e:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass
            prc = multiprocessing.Process(target=_executor_hook,
                args=(job_queue, result_queue, new_stdin))
            prc.start()
            workers.append(prc)

        try:
            for worker in workers:
                worker.join()
        except KeyboardInterrupt:
            for worker in workers:
                worker.terminate()
                worker.join()

        results = []
        try:
            while not result_queue.empty():
                results.append(result_queue.get(block=False))
        except socket.error:
            raise errors.AnsibleError("<interrupted>")
        return results

    # *****************************************************

    def _partition_results(self, results):
        ''' separate results by ones we contacted & ones we didn't '''

        if results is None:
            return None
        results2 = dict(contacted={}, dark={})

        for result in results:
            host = result.host
            if host is None:
                raise Exception("internal error, host not set")
            if result.communicated_ok():
                results2["contacted"][host] = result.result
            else:
                results2["dark"][host] = result.result

        # hosts which were contacted but never got a chance to return
        for host in self.run_hosts:
            if not (host in results2['dark'] or host in results2['contacted']):
                results2["dark"][host] = {}
        return results2

    # *****************************************************

    def run(self):
        ''' xfer & run module on all matched hosts '''

        # find hosts that match the pattern
        if not self.run_hosts:
            self.run_hosts = self.inventory.list_hosts(self.pattern)
        hosts = self.run_hosts
        if len(hosts) == 0:
            self.callbacks.on_no_hosts()
            return dict(contacted={}, dark={})

        global multiprocessing_runner
        multiprocessing_runner = self
        results = None

        # Check if this is an action plugin. Some of them are designed
        # to be ran once per group of hosts. Example module: pause,
        # run once per hostgroup, rather than pausing once per each
        # host.
        p = utils.plugins.action_loader.get(self.module_name, self)

        if self.forks == 0 or self.forks > len(hosts):
            self.forks = len(hosts)

        if (p and (getattr(p, 'BYPASS_HOST_LOOP', None)) or self.run_once):

            # Expose the current hostgroup to the bypassing plugins
            self.host_set = hosts
            # We aren't iterating over all the hosts in this
            # group. So, just pick the first host in our group to
            # construct the conn object with.
            result_data = self._executor(hosts[0], None).result
            # Create a ResultData item for each host in this group
            # using the returned result. If we didn't do this we would
            # get false reports of dark hosts.
            results = [ ReturnData(host=h, result=result_data, comm_ok=True) \
                           for h in hosts ]
            del self.host_set

        elif self.forks > 1:
            try:
                results = self._parallel_exec(hosts)
            except IOError, ie:
                print ie.errno
                if ie.errno == 32:
                    # broken pipe from Ctrl+C
                    raise errors.AnsibleError("interrupted")
                raise
        else:
            results = [ self._executor(h, None) for h in hosts ]

        return self._partition_results(results)

    # *****************************************************

    def run_async(self, time_limit):
        ''' Run this module asynchronously and return a poller. '''

        self.background = time_limit
        results = self.run()
        return results, poller.AsyncPoller(results, self)

    # *****************************************************

    def noop_on_check(self, inject):
        ''' Should the runner run in check mode or not ? '''

        # initialize self.always_run on first call
        if self.always_run is None:
            self.always_run = self.module_vars.get('always_run', False)
            self.always_run = check_conditional(
                self.always_run, self.basedir, inject, fail_on_undefined=True)

        return (self.check and not self.always_run)
