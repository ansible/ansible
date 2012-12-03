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

REPLACER = "#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_ARGS = "<<INCLUDE_ANSIBLE_MODULE_ARGS>>"
REPLACER_LANG = "<<INCLUDE_ANSIBLE_MODULE_LANG>>"

MODULE_COMMON = """

# == BEGIN DYNAMICALLY INSERTED CODE ==

MODULE_ARGS = <<INCLUDE_ANSIBLE_MODULE_ARGS>>
MODULE_LANG = <<INCLUDE_ANSIBLE_MODULE_LANG>>

BOOLEANS_TRUE = ['yes', 'on', '1', 'true', 1]
BOOLEANS_FALSE = ['no', 'off', '0', 'false', 0]
BOOLEANS = BOOLEANS_TRUE + BOOLEANS_FALSE

# ansible modules can be written in any language.  To simplify
# development of Python modules, the functions available here
# can be inserted in any module source automatically by including
# #<<INCLUDE_ANSIBLE_MODULE_COMMON>> on a blank line by itself inside
# of an ansible module. The source of this common code lives
# in lib/ansible/module_common.py

try:
    import json
except ImportError:
    import simplejson as json
import base64
import os
import re
import shlex
import subprocess
import sys
import syslog
import types
import time
import shutil
import stat
import stat
import grp
import pwd
import platform

HAVE_SELINUX=False
try:
    import selinux
    HAVE_SELINUX=True
except ImportError:
    pass

try:
    from hashlib import md5 as _md5
except ImportError:
    from md5 import md5 as _md5

try:
  from systemd import journal
  has_journal = True
except ImportError:
  import syslog
  has_journal = False

FILE_COMMON_ARGUMENTS=dict(
    src = dict(),
    mode = dict(),
    owner = dict(),
    group = dict(),
    seuser = dict(),
    serole = dict(),
    selevel = dict(),
    setype = dict(),
)

def get_platform():
    ''' what's the platform?  example: Linux is a platform. '''
    return platform.system()

def get_distribution():
    ''' return the distribution name '''
    if platform.system() == 'Linux':
        try:
            distribution = platform.linux_distribution()[0].capitalize
        except:
            # FIXME: MethodMissing, I assume?
            distribution = platform.dist()[0].capitalize
    else:
        distribution = None
    return distribution

def load_platform_subclass(cls, *args, **kwargs):
    ''' 
    used by modules like User to have different implementations based on detected platform.  See User
    module for an example.
    '''

    this_platform = get_platform()
    distribution = get_distribution()
    subclass = None
  
    # get the most specific superclass for this platform
    if distribution is not None:
        for sc in cls.__subclasses__():
            if sc.distribution is not None and sc.distribution == distribution and sc.platform == this_platform:
                subclass = sc
    if subclass is None:
        for sc in cls.__subclasses__():
            if sc.platform == this_platform and sc.distribution is None:
                subclass = sc
    if subclass is None:
        subclass = cls

    return super(cls, subclass).__new__(subclass)


class AnsibleModule(object):

    def __init__(self, argument_spec, bypass_checks=False, no_log=False,
        check_invalid_arguments=True, mutually_exclusive=None, required_together=None,
        required_one_of=None, add_file_common_args=False):

        '''
        common code for quickly building an ansible module in Python
        (although you can write modules in anything that can return JSON)
        see library/* for examples
        '''

        self.argument_spec = argument_spec

        if add_file_common_args:
            self.argument_spec.update(FILE_COMMON_ARGUMENTS)

        os.environ['LANG'] = MODULE_LANG
        (self.params, self.args) = self._load_params()

        self._legal_inputs = []
        self._handle_aliases()

        if check_invalid_arguments:
            self._check_invalid_arguments()

        self._set_defaults(pre=True)

        if not bypass_checks:
            self._check_required_arguments()
            self._check_argument_types()
            self._check_mutually_exclusive(mutually_exclusive)
            self._check_required_together(required_together)
            self._check_required_one_of(required_one_of)

        self._set_defaults(pre=False)
        if not no_log:
            self._log_invocation()

    def load_file_common_arguments(self, params):
        ''' 
        many modules deal with files, this encapsulates common
        options that the file module accepts such that it is directly
        available to all modules and they can share code.
        '''

        path = params.get('path', params.get('dest', None))
        if path is None:
            return {}

        mode   = params.get('mode', None)
        owner  = params.get('owner', None)
        group  = params.get('group', None)

        # selinux related options
        seuser    = params.get('seuser', None)
        serole    = params.get('serole', None)
        setype    = params.get('setype', None)
        selevel   = params.get('serange', 's0')
        secontext = [seuser, serole, setype]
    
        if self.selinux_mls_enabled():
            secontext.append(selevel)

        default_secontext = self.selinux_default_context(path)
        for i in range(len(default_secontext)):
            if i is not None and secontext[i] == '_default':
                secontext[i] = default_secontext[i]

        return dict(
            path=path, mode=mode, owner=owner, group=group, 
            seuser=seuser, serole=serole, setype=setype,
            selevel=selevel, secontext=secontext, 
        )


    # Detect whether using selinux that is MLS-aware.
    # While this means you can set the level/range with
    # selinux.lsetfilecon(), it may or may not mean that you
    # will get the selevel as part of the context returned
    # by selinux.lgetfilecon().

    def selinux_mls_enabled(self):
        if not HAVE_SELINUX:
            return False
        if selinux.is_selinux_mls_enabled() == 1:
            return True
        else:
            return False

    def selinux_enabled(self):
        if not HAVE_SELINUX:
            return False
        if selinux.is_selinux_enabled() == 1:
            return True
        else:
            return False

    # Determine whether we need a placeholder for selevel/mls
    def selinux_initial_context(self):
        context = [None, None, None]
        if self.selinux_mls_enabled():
            context.append(None)
        return context

    # If selinux fails to find a default, return an array of None
    def selinux_default_context(self, path, mode=0):
        context = self.selinux_initial_context()
        if not HAVE_SELINUX or not self.selinux_enabled():
            return context
        try:
            ret = selinux.matchpathcon(path, mode)
        except OSError:
            return context
        if ret[0] == -1:
            return context
        context = ret[1].split(':')
        return context

    def selinux_context(self, path):
        context = self.selinux_initial_context()
        if not HAVE_SELINUX or not self.selinux_enabled():
            return context
        try:
            ret = selinux.lgetfilecon(path)
        except:
            self.fail_json(path=path, msg='failed to retrieve selinux context')
        if ret[0] == -1:
            return context
        context = ret[1].split(':')
        return context

    def user_and_group(self, filename):
        st = os.stat(filename)
        uid = st.st_uid
        gid = st.st_gid
        try:    
            user = pwd.getpwuid(uid)[0]
        except KeyError:
            user = str(uid)
        try:    
            group = grp.getgrgid(gid)[0]
        except KeyError:
            group = str(gid)
        return (user, group)

    def set_context_if_different(self, path, context, changed):

        if not HAVE_SELINUX or not self.selinux_enabled():
            return changed 
        cur_context = self.selinux_context(path)
        new_context = list(cur_context)
        # Iterate over the current context instead of the
        # argument context, which may have selevel.

        for i in range(len(cur_context)):
            if context[i] is not None and context[i] != cur_context[i]:
                new_context[i] = context[i]
            if context[i] is None:
                new_context[i] = cur_context[i]
        if cur_context != new_context:
            try:    
                rc = selinux.lsetfilecon(path, ':'.join(new_context))
            except OSError:
                self.fail_json(path=path, msg='invalid selinux context', new_context=new_context, cur_context=cur_context, input_was=context)
            if rc != 0:
                self.fail_json(path=path, msg='set selinux context failed')
            changed = True
        return changed

    def set_owner_if_different(self, path, owner, changed):
        if owner is None:
            return changed
        user, group = self.user_and_group(path)
        if owner != user:
            try:
                uid = pwd.getpwnam(owner).pw_uid
            except KeyError:
                self.fail_json(path=path, msg='chown failed: failed to look up user %s' % owner)
            try:
                os.chown(path, uid, -1)
            except OSError:
                self.fail_json(path=path, msg='chown failed')
            changed = True
        return changed

    def set_group_if_different(self, path, group, changed):
        if group is None:
            return changed
        old_user, old_group = self.user_and_group(path)
        if old_group != group:
            try:
                gid = grp.getgrnam(group).gr_gid
            except KeyError:
                self.fail_json(path=path, msg='chgrp failed: failed to look up group %s' % group)
            try:
                os.chown(path, -1, gid)
            except OSError:
                self.fail_json(path=path, msg='chgrp failed')
            changed = True
        return changed

    def set_mode_if_different(self, path, mode, changed):
        if mode is None:
            return changed
        try:
            # FIXME: support English modes
            mode = int(mode, 8)
        except Exception, e:
            self.fail_json(path=path, msg='mode needs to be something octalish', details=str(e))

        st = os.stat(path)
        prev_mode = stat.S_IMODE(st[stat.ST_MODE])

        if prev_mode != mode:
            # FIXME: comparison against string above will cause this to be executed
            # every time
            try:
                os.chmod(path, mode)
            except Exception, e:
                self.fail_json(path=path, msg='chmod failed', details=str(e))

            st = os.stat(path)
            new_mode = stat.S_IMODE(st[stat.ST_MODE])

            if new_mode != prev_mode:
                changed = True
        return changed

    def set_file_attributes_if_different(self, file_args, changed):
        # set modes owners and context as needed
        changed = self.set_context_if_different(
            file_args['path'], file_args['secontext'], changed
        )
        changed = self.set_owner_if_different(
            file_args['path'], file_args['owner'], changed
        )
        changed = self.set_group_if_different(
            file_args['path'], file_args['group'], changed
        )
        changed = self.set_mode_if_different(
            file_args['path'], file_args['mode'], changed
        )
        return changed

    def set_directory_attributes_if_different(self, file_args, changed):
        changed = self.set_context_if_different(
            file_args['path'], file_args['secontext'], changed
        )
        changed = self.set_owner_if_different(
            file_args['path'], file_args['owner'], changed
        )
        changed = self.set_group_if_different(
            file_args['path'], file_args['group'], changed
        )
        changed = self.set_mode_if_different(
            file_args['path'], file_args['mode'], changed
        )
        return changed

    def add_path_info(self, kwargs):
        ''' 
        for results that are files, supplement the info about the file
        in the return path with stats about the file path. 
        '''

        path = kwargs.get('path', kwargs.get('dest', None))
        if path is None:
            return kwargs
        if os.path.exists(path):
            (user, group) = self.user_and_group(path)
            kwargs['owner']  = user
            kwargs['group'] = group
            st = os.stat(path)
            kwargs['mode']  = oct(stat.S_IMODE(st[stat.ST_MODE]))
            # secontext not yet supported
            if os.path.islink(path):
                kwargs['state'] = 'link'
            elif os.path.isdir(path):
                kwargs['state'] = 'directory'
            else:
                kwargs['state'] = 'file'
            if HAVE_SELINUX and self.selinux_enabled():
                kwargs['secontext'] = ':'.join(self.selinux_context(path))
        else:
            kwargs['state'] = 'absent'
        return kwargs


    def _handle_aliases(self):
        for (k,v) in self.argument_spec.iteritems():
            self._legal_inputs.append(k)
            aliases = v.get('aliases', None)
            default = v.get('default', None)
            required = v.get('required', False)
            if default is not None and required:
                # not alias specific but this is a good place to check this
                self.fail_json(msg="internal error: required and default are mutally exclusive for %s" % k)
            if aliases is None:
                continue
            if type(aliases) != list:
                self.fail_json(msg='internal error: aliases must be a list')
            for alias in aliases:
                self._legal_inputs.append(alias)
                if alias in self.params:
                    self.params[k] = self.params[alias]

    def _check_invalid_arguments(self):
        for (k,v) in self.params.iteritems():
            if k not in self._legal_inputs:
                self.fail_json(msg="unsupported parameter for module: %s" % k)

    def _count_terms(self, check):
        count = 0
        for term in check:
           if term in self.params:
               count += 1
        return count

    def _check_mutually_exclusive(self, spec):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check)
            if count > 1:
                self.fail_json(msg="parameters are mutually exclusive: %s" % check)

    def _check_required_one_of(self, spec):
        if spec is None:
            return
        for check in spec:
            count = self._count_terms(check)
            if count == 0:
                self.fail_json(msg="one of the following is required: %s" % check)

    def _check_required_together(self, spec):
        if spec is None:
            return
        for check in spec:
            counts = [ self.count_terms([field]) for field in check ]
            non_zero = [ c for c in counts if c > 0 ]
            if len(non_zero) > 0:
                if 0 in counts:
                    self.fail_json(msg="parameters are required together: %s" % check)

    def _check_required_arguments(self):
        ''' ensure all required arguments are present '''
        missing = []
        for (k,v) in self.argument_spec.iteritems():
            required = v.get('required', False)
            if required and k not in self.params:
                missing.append(k)
        if len(missing) > 0:
            self.fail_json(msg="missing required arguments: %s" % ",".join(missing))

    def _check_argument_types(self):
        ''' ensure all arguments have the requested values, and there are no stray arguments '''
        for (k,v) in self.argument_spec.iteritems():
            choices = v.get('choices',None)
            if choices is None:
                continue
            if type(choices) == list:
                if k in self.params:
                    if self.params[k] not in choices:
                        choices_str=",".join([str(c) for c in choices])
                        msg="value of %s must be one of: %s, got: %s" % (k, choices_str, self.params[k])
                        self.fail_json(msg=msg)
            else:
                self.fail_json(msg="internal error: do not know how to interpret argument_spec")

    def _set_defaults(self, pre=True):
         for (k,v) in self.argument_spec.iteritems():
             default = v.get('default', None)
             if pre == True:
                 # this prevents setting defaults on required items
                 if default is not None and k not in self.params:
                     self.params[k] = default
             else:
                 # make sure things without a default still get set None
                 if k not in self.params:
                     self.params[k] = default

    def _load_params(self):
        ''' read the input and return a dictionary and the arguments string '''
        args = MODULE_ARGS
        items   = shlex.split(args)
        params = {}
        for x in items:
            try:
                (k, v) = x.split("=",1)
            except:
                self.fail_json(msg="this module requires key=value arguments")
            params[k] = v
        return (params, args)

    def _log_invocation(self):
        ''' log that ansible ran the module '''
        # TODO: generalize a seperate log function and make log_invocation use it
        # Sanitize possible password argument when logging.
        log_args = dict()
        passwd_keys = ['password', 'login_password']
        for param in self.params:
            if param in passwd_keys:
                log_args[param] = 'NOT_LOGGING_PASSWORD'
            else:
                log_args[param] = self.params[param]

        if (has_journal):
            journal_args = ["MESSAGE=Ansible module invoked", "MODULE=%s" % os.path.basename(__file__)]
            for arg in log_args:
                journal_args.append(arg.upper() + "=" + str(log_args[arg]))
            journal.sendv(*journal_args)
        else:
            msg = ''
            syslog.openlog('ansible-%s' % os.path.basename(__file__), 0, syslog.LOG_USER)
            for arg in log_args:
                msg = msg + arg + '=' + str(log_args[arg]) + ' '
            if msg:
                syslog.syslog(syslog.LOG_NOTICE, 'Invoked with %s' % msg)
            else:
                syslog.syslog(syslog.LOG_NOTICE, 'Invoked')

    def get_bin_path(self, arg, required=False, opt_dirs=[]):
        '''
        find system executable in PATH.
        Optional arguments:
           - required:  if executable is not found and required is true, fail_json
           - opt_dirs:  optional list of directories to search in addition to PATH
        if found return full path; otherwise return None
        '''
        sbin_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
        paths = []
        for d in opt_dirs:
            if d is not None and os.path.exists(d):
                paths.append(d)
        paths += os.environ.get('PATH', '').split(':')
        bin_path = None
        # mangle PATH to include /sbin dirs
        for p in sbin_paths:
            if p not in paths and os.path.exists(p):
                paths.append(p)
        for d in paths:
            path = os.path.join(d, arg)
            if os.path.exists(path) and self.is_executable(path):
                bin_path = path
                break
        if required and bin_path is None:
            self.fail_json(msg='Failed to find required executable %s' % arg)
        return bin_path

    def boolean(self, arg):
        ''' return a bool for the arg '''
        if arg is None or type(arg) == bool:
            return arg
        if type(arg) in types.StringTypes:
            arg = arg.lower()
        if arg in BOOLEANS_TRUE:
            return True
        elif arg in BOOLEANS_FALSE:
            return False
        else:
            self.fail_json(msg='Boolean %s not in either boolean list' % arg)

    def jsonify(self, data):
        return json.dumps(data)

    def exit_json(self, **kwargs):
        ''' return from the module, without error '''
        self.add_path_info(kwargs)
        if not kwargs.has_key('changed'):
            kwargs['changed'] = False
        print self.jsonify(kwargs)
        sys.exit(0)

    def fail_json(self, **kwargs):
        ''' return from the module, with an error message '''
        self.add_path_info(kwargs)
        assert 'msg' in kwargs, "implementation error -- msg to explain the error is required"
        kwargs['failed'] = True
        print self.jsonify(kwargs)
        sys.exit(1)

    def is_executable(self, path):
        '''is the given path executable?'''
        return (stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
                or stat.S_IXGRP & os.stat(path)[stat.ST_MODE]
                or stat.S_IXOTH & os.stat(path)[stat.ST_MODE])

    def md5(self, filename):
        ''' Return MD5 hex digest of local file, or None if file is not present. '''
        if not os.path.exists(filename):
            return None
        if os.path.isdir(filename):
            self.fail_json(msg="attempted to take md5sum of directory: %s" % filename)
        digest = _md5()
        blocksize = 64 * 1024
        infile = open(filename, 'rb')
        block = infile.read(blocksize)
        while block:
            digest.update(block)
            block = infile.read(blocksize)
        infile.close()
        return digest.hexdigest()

    def backup_local(self, fn):
        '''make a date-marked backup of the specified file, return True or False on success or failure'''
        # backups named basename-YYYY-MM-DD@HH:MM~
        ext = time.strftime("%Y-%m-%d@%H:%M~", time.localtime(time.time()))
        backupdest = '%s.%s' % (fn, ext)

        try:
            shutil.copy2(fn, backupdest)
        except shutil.Error, e:
            self.fail_json(msg='Could not make backup of %s to %s: %s' % (fn, backupdest, e))
        return backupdest

    def atomic_replace(self, src, dest):
        '''atomically replace dest with src, copying attributes from dest'''
        if os.path.exists(dest):
            st = os.stat(dest)
            os.chmod(src, st.st_mode & 07777)
            try:
                os.chown(src, st.st_uid, st.st_gid)
            except OSError, e:
                if e.errno != errno.EPERM:
                    raise
            if self.selinux_enabled():
                context = self.selinux_context(dest)
                self.set_context_if_different(src, context, False)
        os.rename(src, dest)

# == END DYNAMICALLY INSERTED CODE ===

"""
