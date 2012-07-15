# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

################################################

import multiprocessing
import signal
import os
import pwd
import Queue
import random
import traceback
import tempfile
import time
import base64
import getpass
import codecs

import ansible.constants as C 
import ansible.inventory
from ansible import utils
from ansible import errors
import poller
import connection
from ansible import callbacks as ans_callbacks
    
HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

################################################

def _executor_hook(job_queue, result_queue):
    ''' callback used by multiprocessing pool '''

    # attempt workaround of https://github.com/newsapps/beeswithmachineguns/issues/17
    # does not occur for everyone, some claim still occurs on newer paramiko
    # this function not present in CentOS 6
    if HAS_ATFORK:
        atfork()

    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            job = job_queue.get(block=False)
            runner, host = job
            result_queue.put(runner._executor(host))
        except Queue.Empty:
            pass
        except:
            traceback.print_exc()
 
################################################

class ReturnData(object):

    __slots__ = [ 'result', 'comm_ok', 'host' ]

    def __init__(self, host=None, result=None, comm_ok=True):
        self.host = host
        self.result = result
        self.comm_ok = comm_ok

        if type(self.result) in [ str, unicode ]:
            self.result = utils.parse_json(self.result)

        if host is None:
            raise Exception("host not set")
        if type(self.result) != dict:
            raise Exception("dictionary result expected")

    def communicated_ok(self):
        return self.comm_ok

    def is_successful(self):
        if not self.comm_ok:
            return False
        else:
            if 'failed' in self.result:
                return False
            if self.result.get('rc',0) != 0:
                return False
            return True

class Runner(object):

    def __init__(self, 
        host_list=C.DEFAULT_HOST_LIST, module_path=C.DEFAULT_MODULE_PATH,
        module_name=C.DEFAULT_MODULE_NAME, module_args=C.DEFAULT_MODULE_ARGS, 
        forks=C.DEFAULT_FORKS, timeout=C.DEFAULT_TIMEOUT, 
        pattern=C.DEFAULT_PATTERN, remote_user=C.DEFAULT_REMOTE_USER, 
        remote_pass=C.DEFAULT_REMOTE_PASS, remote_port=C.DEFAULT_REMOTE_PORT, 
        private_key_file=C.DEFAULT_PRIVATE_KEY_FILE, sudo_pass=C.DEFAULT_SUDO_PASS, 
        background=0, basedir=None, setup_cache=None, 
        transport=C.DEFAULT_TRANSPORT, conditional='True', callbacks=None, 
        verbose=False, sudo=False, sudo_user=C.DEFAULT_SUDO_USER,
        module_vars=None, is_playbook=False, inventory=None):

        """
        host_list    : path to a host list file, like /etc/ansible/hosts
        module_path  : path to modules, like /usr/share/ansible
        module_name  : which module to run (string)
        module_args  : args to pass to the module (string)
        forks        : desired level of paralellism (hosts to run on at a time)
        timeout      : connection timeout, such as a SSH timeout, in seconds
        pattern      : pattern or groups to select from in inventory
        remote_user  : connect as this remote username
        remote_pass  : supply this password (if not using keys)
        remote_port  : use this default remote port (if not set by the inventory system)
        private_key_file  : use this private key as your auth key
        sudo_user    : If you want to sudo to a user other than root.
        sudo_pass    : sudo password if using sudo and sudo requires a password
        background   : run asynchronously with a cap of this many # of seconds (if not 0)
        basedir      : paths used by modules if not absolute are relative to here
        setup_cache  : this is a internalism that is going away
        transport    : transport mode (paramiko, local)
        conditional  : only execute if this string, evaluated, is True
        callbacks    : output callback class
        sudo         : log in as remote user and immediately sudo to root
        module_vars  : provides additional variables to a template.
        is_playbook  : indicates Runner is being used by a playbook.  affects behavior in various ways.
        inventory    : inventory object, if host_list is not provided
        """

        if setup_cache is None:
            setup_cache = {}
        if basedir is None: 
            basedir = os.getcwd()

        if callbacks is None:
            callbacks = ans_callbacks.DefaultRunnerCallbacks()
        self.callbacks = callbacks

        self.generated_jid = str(random.randint(0, 999999999999))

        self.sudo_user = sudo_user
        self.transport = transport
        self.connector = connection.Connection(self, self.transport, self.sudo_user)

        if inventory is None:
            self.inventory = ansible.inventory.Inventory(host_list)
        else:
            self.inventory = inventory

        if module_vars is None:
            module_vars = {}

        self.setup_cache = setup_cache
        self.conditional = conditional
        self.module_path = module_path
        self.module_name = module_name
        self.forks       = int(forks)
        self.pattern     = pattern
        self.module_args = module_args
        self.module_vars = module_vars
        self.timeout     = timeout
        self.verbose     = verbose
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.remote_port = remote_port
        self.private_key_file = private_key_file
        self.background  = background
        self.basedir     = basedir
        self.sudo        = sudo
        self.sudo_pass   = sudo_pass
        self.is_playbook = is_playbook

        euid = pwd.getpwuid(os.geteuid())[0]
        if self.transport == 'local' and self.remote_user != euid:
            raise errors.AnsibleError("User mismatch: expected %s, but is %s" % (self.remote_user, euid))
        if type(self.module_args) not in [str, unicode, dict]:
            raise errors.AnsibleError("module_args must be a string or dict: %s" % self.module_args)
        if self.transport == 'ssh' and self.remote_pass:
            raise errors.AnsibleError("SSH transport does not support remote passwords, only keys or agents")

        self._tmp_paths  = {}
        random.seed()

    # *****************************************************

    def _delete_remote_files(self, conn, files):
        ''' deletes one or more remote files '''

        if type(files) == str:
            files = [ files ]
        for filename in files:
            if filename.find('/tmp/') == -1:
                raise Exception("not going to happen")
            self._low_level_exec_command(conn, "rm -rf %s" % filename, None)

    # *****************************************************

    def _transfer_module(self, conn, tmp, module):
        ''' transfers a module file to the remote side to execute it, but does not execute it yet '''

        outpath = self._copy_module(conn, tmp, module)
        self._low_level_exec_command(conn, "chmod +x %s" % outpath, tmp)
        return outpath

    # *****************************************************

    def _transfer_str(self, conn, tmp, name, data):
        ''' transfer string to remote file '''

        if type(data) == dict:
            data = utils.jsonify(data)

        afd, afile = tempfile.mkstemp()
        afo = os.fdopen(afd, 'w')
        afo.write(data.encode("utf8"))
        afo.flush()
        afo.close()

        remote = os.path.join(tmp, name)
        conn.put_file(afile, remote)
        os.unlink(afile)
        return remote

    # *****************************************************

    def _add_setup_vars(self, inject, args):
        ''' setup module variables need special handling '''

        is_dict = False
        if type(args) == dict:
            is_dict = True

        # TODO: keep this as a dict through the whole path to simplify this code
        for (k,v) in inject.iteritems():
            if not k.startswith('facter_') and not k.startswith('ohai_') and not k.startswith('ansible_'):
                if not is_dict:
                    if str(v).find(" ") != -1:
                        v = "\"%s\"" % v
                    args += " %s=%s" % (k, str(v).replace(" ","~~~"))
                else:
                    args[k]=v
        return args   
 
    # *****************************************************
    
    def _execute_module(self, conn, tmp, remote_module_path, args, 
        async_jid=None, async_module=None, async_limit=None):

        items = self.module_vars.get('items', None)
        if items is None or len(items) == 0:
            # executing a single item
            return self._execute_module_internal(
                conn, tmp, remote_module_path, args, 
                async_jid=async_jid, async_module=async_module, async_limit=async_limit
            )
        else:
            # executing using with_items, so make multiple calls
            # TODO: refactor
            aggregrate = {}
            all_comm_ok = True
            all_changed = False
            all_failed = False
            results = []
            for x in items:
                self.module_vars['item'] = x
                result = self._execute_module_internal(
                        conn, tmp, remote_module_path, args, 
                        async_jid=async_jid, async_module=async_module, async_limit=async_limit
                )
                results.append(result.result)
                if result.comm_ok == False:
                    all_comm_ok = False
                    break
                for x in results:
                    if x.get('changed') == True: 
                        all_changed = True
                    if (x.get('failed') == True) or (('rc' in x) and (x['rc'] != 0)):
                        all_failed = True   
                        break
            msg = 'All items succeeded'
            if all_failed:
                msg = "One or more items failed."
            rd_result = dict(
                failed = all_failed,
                changed = all_changed,
                results = results,
                msg = msg               
            )
            if not all_failed:
                del rd_result['failed']
            return ReturnData(host=conn.host, comm_ok=all_comm_ok, result=rd_result)
 
    # *****************************************************

    def _execute_module_internal(self, conn, tmp, remote_module_path, args, 
        async_jid=None, async_module=None, async_limit=None):

        ''' runs a module that has already been transferred '''

        inject = self.setup_cache.get(conn.host,{}).copy()
        host_variables = self.inventory.get_variables(conn.host)
        inject.update(host_variables)
        inject.update(self.module_vars)

        group_hosts = {}
        for g in self.inventory.groups:
            group_hosts[g.name] = map((lambda x: x.get_variables()),g.hosts)

        inject['groups'] = group_hosts

        if self.module_name == 'setup':
            if not args:
                args = {}
            args = self._add_setup_vars(inject, args)

        if type(args) == dict:
            args = utils.jsonify(args,format=True)

        args = utils.template(args, inject, self.setup_cache)

        module_name_tail = remote_module_path.split("/")[-1]

        argsfile = self._transfer_str(conn, tmp, 'arguments', args)
        if async_jid is None:
            cmd = "%s %s" % (remote_module_path, argsfile)
        else:
            cmd = " ".join([str(x) for x in [remote_module_path, async_jid, async_limit, async_module, argsfile]])

        res = self._low_level_exec_command(conn, cmd, tmp, sudoable=True)

        return ReturnData(host=conn.host, result=res)

    # *****************************************************

    def _add_result_to_setup_cache(self, conn, result):
        ''' allows discovered variables to be used in templates and action statements '''

        host = conn.host
        if 'ansible_facts' in result:
            var_result = result['ansible_facts']
        else:
            var_result = {}

        # note: do not allow variables from playbook to be stomped on
        # by variables coming up from facter/ohai/etc.  They
        # should be prefixed anyway
        if not host in self.setup_cache:
            self.setup_cache[host] = {}
        for (k, v) in var_result.iteritems():
            if not k in self.setup_cache[host]:
                self.setup_cache[host][k] = v

    # *****************************************************

    def _execute_raw(self, conn, tmp):
        ''' execute a non-module command for bootstrapping, or if there's no python on a device '''
        stdout = self._low_level_exec_command( conn, self.module_args, tmp, sudoable = True )
        data = dict(stdout=stdout)
        return ReturnData(host=conn.host, result=data)

    # ***************************************************

    def _execute_normal_module(self, conn, tmp, module_name):
        ''' transfer & execute a module that is not 'copy' or 'template' '''

        # shell and command are the same module
        if module_name == 'shell':
            module_name = 'command'
            self.module_args += " #USE_SHELL"

        module = self._transfer_module(conn, tmp, module_name)
        exec_rc = self._execute_module(conn, tmp, module, self.module_args)
        if exec_rc.is_successful():
            self._add_result_to_setup_cache(conn, exec_rc.result)
        return exec_rc

    # *****************************************************

    def _execute_async_module(self, conn, tmp, module_name):
        ''' transfer the given module name, plus the async module, then run it '''

        # shell and command module are the same
        module_args = self.module_args
        if module_name == 'shell':
            module_name = 'command'
            module_args += " #USE_SHELL"

        async  = self._transfer_module(conn, tmp, 'async_wrapper')
        module = self._transfer_module(conn, tmp, module_name)

        return self._execute_module(conn, tmp, async, module_args,
           async_module=module, 
           async_jid=self.generated_jid, 
           async_limit=self.background
        )

    # *****************************************************

    def _execute_copy(self, conn, tmp):
        ''' handler for file transfer operations '''

        # load up options
        options = utils.parse_kv(self.module_args)
        source = options.get('src', None)
        dest   = options.get('dest', None)
        if (source is None and not 'first_available_file' in self.module_vars) or dest is None:
            result=dict(failed=True, msg="src and dest are required")
            return ReturnData(host=conn.host, result=result)

        # apply templating to source argument
        inject = self.setup_cache.get(conn.host,{})
        
        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        if 'first_available_file' in self.module_vars:
            found = False
            for fn in self.module_vars.get('first_available_file'):
                fn = utils.template(fn, inject, self.setup_cache)
                if os.path.exists(fn):
                    source = fn
                    found = True
                    break
            if not found:
                results=dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(host=conn.host, results=results)
        
        if self.module_vars is not None:
            inject.update(self.module_vars)

        source = utils.template(source, inject, self.setup_cache)
        source = utils.path_dwim(self.basedir, source)

        local_md5 = utils.md5(source)
        if local_md5 is None:
            result=dict(failed=True, msg="could not find src=%s" % source)
            return ReturnData(host=conn.host, result=result)
            
        remote_md5 = self._remote_md5(conn, tmp, dest) 

        exec_rc = None 
        if local_md5 != remote_md5:
            # transfer the file to a remote tmp location
            tmp_src = tmp + source.split('/')[-1]
            conn.put_file(source, tmp_src)

            # install the copy  module
            self.module_name = 'copy'
            module = self._transfer_module(conn, tmp, 'copy')

            # run the copy module
            args = "src=%s dest=%s" % (tmp_src, dest)
            exec_rc = self._execute_module(conn, tmp, module, args)
        else:
            # no need to transfer the file, already correct md5
            result = dict(changed=False, md5sum=remote_md5, transferred=False)
            exec_rc = ReturnData(host=conn.host, result=result)

        if exec_rc.is_successful():
            return self._chain_file_module(conn, tmp, exec_rc, options)
        else:
            return exec_rc

    # *****************************************************

    def _execute_fetch(self, conn, tmp):
        ''' handler for fetch operations '''

        # load up options
        options = utils.parse_kv(self.module_args)
        source = options.get('src', None)
        dest = options.get('dest', None)
        if source is None or dest is None:
            results = dict(failed=True, msg="src and dest are required")
            return ReturnData(host=conn.host, result=results)

        # apply templating to source argument
        inject = self.setup_cache.get(conn.host,{})
        if self.module_vars is not None:
            inject.update(self.module_vars)
        source = utils.template(source, inject, self.setup_cache)

        # apply templating to dest argument
        dest = utils.template(dest, inject, self.setup_cache)
       
        # files are saved in dest dir, with a subdir for each host, then the filename
        dest   = "%s/%s/%s" % (utils.path_dwim(self.basedir, dest), conn.host, source)
        dest   = dest.replace("//","/")

        # compare old and new md5 for support of change hooks
        local_md5 = utils.md5(dest)
        remote_md5 = self._remote_md5(conn, tmp, source)

        if remote_md5 == '0':
            result = dict(msg="missing remote file", changed=False)
            return ReturnData(host=conn.host, result=result)
        elif remote_md5 != local_md5:
            # create the containing directories, if needed
            if not os.path.isdir(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))

            # fetch the file and check for changes
            conn.fetch_file(source, dest)
            new_md5 = utils.md5(dest)
            if new_md5 != remote_md5:
                result = dict(failed=True, msg="md5 mismatch", md5sum=new_md5)
                return ReturnData(host=conn.host, result=result)
            result = dict(changed=True, md5sum=new_md5)
            return ReturnData(host=conn.host, result=result)
        else:
            result = dict(changed=False, md5sum=local_md5)
            return ReturnData(host=conn.host, result=result)
        
        
    # *****************************************************

    def _chain_file_module(self, conn, tmp, exec_rc, options):

        ''' handles changing file attribs after copy/template operations '''

        old_changed = exec_rc.result.get('changed', False)
        module = self._transfer_module(conn, tmp, 'file')
        args = ' '.join([ "%s=%s" % (k,v) for (k,v) in options.items() ])
        exec_rc2 = self._execute_module(conn, tmp, module, args)

        new_changed = False
        if exec_rc2.is_successful():
            new_changed = exec_rc2.result.get('changed', False)
            exec_rc.result.update(exec_rc2.result)

        if old_changed or new_changed:
            exec_rc.result['changed'] = True

        return exec_rc

    # *****************************************************

    def _execute_template(self, conn, tmp):
        ''' handler for template operations '''

        if not self.is_playbook:
            raise errors.AnsibleError("in current versions of ansible, templates are only usable in playbooks")

        # load up options
        options  = utils.parse_kv(self.module_args)
        source   = options.get('src', None)
        dest     = options.get('dest', None)
        metadata = options.get('metadata', None)
        if (source is None and 'first_available_file' not in self.module_vars) or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(host=conn.host, comm_ok=False, result=result)

        # apply templating to source argument so vars can be used in the path
        inject = self.setup_cache.get(conn.host,{})

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        if 'first_available_file' in self.module_vars:
            found = False
            for fn in self.module_vars.get('first_available_file'):
                fn = utils.template(fn, inject, self.setup_cache)
                if os.path.exists(fn):
                    source = fn
                    found = True
                    break
            if not found:
                result = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(host=conn.host, comm_ok=False, result=result)

        if self.module_vars is not None:
            inject.update(self.module_vars)

        source = utils.template(source, inject, self.setup_cache)

        # install the template module
        copy_module = self._transfer_module(conn, tmp, 'copy')

        # template the source data locally
        try:
            resultant = utils.template_from_file(self.basedir, source, inject, self.setup_cache)
        except Exception, e:
            result = dict(failed=True, msg=str(e))
            return ReturnData(host=conn.host, comm_ok=False, result=result)

        xfered = self._transfer_str(conn, tmp, 'source', resultant)
            
        # run the COPY module
        args = "src=%s dest=%s" % (xfered, dest)
        exec_rc = self._execute_module(conn, tmp, copy_module, args)
 
        # modify file attribs if needed
        if exec_rc.comm_ok:
            return self._chain_file_module(conn, tmp, exec_rc, options)
        else:
            return exec_rc

    # *****************************************************

    def _execute_assemble(self, conn, tmp):
        ''' handler for assemble operations '''
        module_name = 'assemble'
        options = utils.parse_kv(self.module_args)
        module = self._transfer_module(conn, tmp, module_name)
        exec_rc = self._execute_module(conn, tmp, module, self.module_args)

        if exec_rc.is_successful():
            return self._chain_file_module(conn, tmp, exec_rc, options)
        else:
            return exec_rc

    # *****************************************************

    def _executor(self, host):
        try:
            exec_rc = self._executor_internal(host)
            if type(exec_rc) != ReturnData:
                raise Exception("unexpected return type: %s" % type(exec_rc))
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

    def _executor_internal(self, host):
        ''' callback executed in parallel for each host. returns (hostname, connected_ok, extra) '''

        host_variables = self.inventory.get_variables(host)
        port = host_variables.get('ansible_ssh_port', self.remote_port)

        inject = self.setup_cache.get(host,{}).copy()
        inject.update(host_variables)
        inject.update(self.module_vars)

        conditional = utils.template(self.conditional, inject, self.setup_cache)
        if not eval(conditional):
            result = utils.jsonify(dict(skipped=True))
            self.callbacks.on_skipped(host)
            return ReturnData(host=host, result=result)

        conn = None
        try:
            conn = self.connector.connect(host, port)
        except errors.AnsibleConnectionFailed, e:
            result = dict(failed=True, msg="FAILED: %s" % str(e))
            return ReturnData(host=host, comm_ok=False, result=result)

        module_name = utils.template(self.module_name, inject, self.setup_cache)

        tmp = self._make_tmp_path(conn)
        result = None

        if self.module_name == 'copy':
            result = self._execute_copy(conn, tmp)
        elif self.module_name == 'fetch':
            result = self._execute_fetch(conn, tmp)
        elif self.module_name == 'template':
            result = self._execute_template(conn, tmp)
        elif self.module_name == 'raw':
            result = self._execute_raw(conn, tmp)
        elif self.module_name == 'assemble':
            result = self._execute_assemble(conn, tmp)
        else:
            if self.background == 0:
                result = self._execute_normal_module(conn, tmp, module_name)
            else:
                result = self._execute_async_module(conn, tmp, module_name)

        self._delete_remote_files(conn, tmp)
        conn.close()

        if not result.comm_ok:
            # connection or parsing errors...
            self.callbacks.on_unreachable(host, result.result)
        else:
            data = result.result
            if 'skipped' in data:
                self.callbacks.on_skipped(result.host)
            elif not result.is_successful():
                self.callbacks.on_failed(result.host, result.result)
            else:
                self.callbacks.on_ok(result.host, result.result)

        return result

    # *****************************************************

    def _low_level_exec_command(self, conn, cmd, tmp, sudoable=False):
        ''' execute a command string over SSH, return the output '''
        sudo_user = self.sudo_user
        stdin, stdout, stderr = conn.exec_command(cmd, tmp, sudo_user, sudoable=sudoable)
        out=None

        if type(stdout) != str:
            out="\n".join(stdout.readlines())
        else:
            out=stdout

        # sudo mode paramiko doesn't capture stderr, so not relaying here either...
        return out 

    # *****************************************************

    def _remote_md5(self, conn, tmp, path):
        ''' 
        takes a remote md5sum without requiring python, and returns 0 if the
        file does not exist
        '''
        test = "[[ -r %s ]]" % path
        md5s = [
            "(%s && /usr/bin/md5sum %s 2>/dev/null)" % (test,path),
            "(%s && /sbin/md5sum -q %s 2>/dev/null)" % (test,path),
            "(%s && /usr/bin/digest -a md5 -v %s 2>/dev/null)" % (test,path)
        ]
        cmd = " || ".join(md5s)
        cmd = "%s || (echo \"0 %s\")" % (cmd, path)
        remote_md5 = self._low_level_exec_command(conn, cmd, tmp, True).split()[0]
        return remote_md5

    # *****************************************************

    def _make_tmp_path(self, conn):
        ''' make and return a temporary path on a remote box '''

        basefile = 'ansible-%s-%s' % (time.time(), random.randint(0, 2**48))
        basetmp = os.path.join(C.DEFAULT_REMOTE_TMP, basefile)
        if self.remote_user == 'root':
            basetmp = os.path.join('/var/tmp', basefile)

        cmd = 'mkdir -p %s' % basetmp
        if self.remote_user != 'root':
            cmd += ' && chmod a+x %s' % basetmp
        cmd += ' && echo %s' % basetmp

        result = self._low_level_exec_command(conn, cmd, None, sudoable=False)
        cleaned = result.split("\n")[0].strip() + '/'
        return cleaned


    # *****************************************************

    def _copy_module(self, conn, tmp, module):
        ''' transfer a module over SFTP, does not run it '''

        if module.startswith("/"):
            raise errors.AnsibleFileNotFound("%s is not a module" % module)

        # Search module path(s) for named module.
        for module_path in self.module_path.split(os.pathsep):
            in_path = os.path.expanduser(os.path.join(module_path, module))
            if os.path.exists(in_path):
                break
        else:
            raise errors.AnsibleFileNotFound("module %s not found in %s" % (module, self.module_path))

        out_path = os.path.join(tmp, module)

        # use the correct python interpreter for the host
        host_variables = self.inventory.get_variables(conn.host)
        if 'ansible_python_interpreter' in host_variables:
            interpreter = host_variables['ansible_python_interpreter']
            with open(in_path) as f:
                module_lines = f.readlines()
            if '#!' and 'python' in module_lines[0]:
                module_lines[0] = "#!%s" % interpreter
            self._transfer_str(conn, tmp, module, '\n'.join(module_lines))
        else:
            conn.put_file(in_path, out_path)

        return out_path

    # *****************************************************

    def _parallel_exec(self, hosts):
        ''' handles mulitprocessing when more than 1 fork is required '''

        job_queue = multiprocessing.Manager().Queue()
        [job_queue.put(i) for i in hosts]

        result_queue = multiprocessing.Manager().Queue()

        workers = []
        for i in range(self.forks):
            prc = multiprocessing.Process(target=_executor_hook,
                args=(job_queue, result_queue))
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
        while not result_queue.empty():
            results.append(result_queue.get(block=False))
        return results

    # *****************************************************

    def _partition_results(self, results):
        ''' seperate results by ones we contacted & ones we didn't '''

        results2 = dict(contacted={}, dark={})

        if results is None:
            return None

        for result in results:
            host = result.host
            if host is None:
                raise Exception("internal error, host not set")
            if result.communicated_ok():
                results2["contacted"][host] = result.result
            else:
                results2["dark"][host] = result.result

        # hosts which were contacted but never got a chance to return
        for host in self.inventory.list_hosts(self.pattern):
            if not (host in results2['dark'] or host in results2['contacted']):
                results2["dark"][host] = {}

        return results2

    # *****************************************************

    def run(self):
        ''' xfer & run module on all matched hosts '''
       
        # find hosts that match the pattern
        hosts = self.inventory.list_hosts(self.pattern)
        if len(hosts) == 0:
            self.callbacks.on_no_hosts()
            return dict(contacted={}, dark={})
 
        hosts = [ (self,x) for x in hosts ]
        results = None
        if self.forks > 1:
            results = self._parallel_exec(hosts)
        else:
            results = [ self._executor(h[1]) for h in hosts ]
        return self._partition_results(results)

    def run_async(self, time_limit):
        ''' Run this module asynchronously and return a poller. '''
        self.background = time_limit
        results = self.run()

        return results, poller.AsyncPoller(results, self)

