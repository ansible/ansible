# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
# 
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, 
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright 
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice, 
#      this list of conditions and the following disclaimer in the documentation 
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

REPLACER = "#<<INCLUDE_ANSIBLE_MODULE_COMMON>>"
REPLACER_ARGS = "<<INCLUDE_ANSIBLE_MODULE_ARGS>>"
REPLACER_LANG = "<<INCLUDE_ANSIBLE_MODULE_LANG>>"
REPLACER_COMPLEX = "<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"

MODULE_COMMON = """

# == BEGIN DYNAMICALLY INSERTED CODE ==

MODULE_ARGS = <<INCLUDE_ANSIBLE_MODULE_ARGS>>
MODULE_LANG = <<INCLUDE_ANSIBLE_MODULE_LANG>>
MODULE_COMPLEX_ARGS = <<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>

BOOLEANS_TRUE = ['yes', 'on', '1', 'true', 1]
BOOLEANS_FALSE = ['no', 'off', '0', 'false', 0]
BOOLEANS = BOOLEANS_TRUE + BOOLEANS_FALSE

# ansible modules can be written in any language.  To simplify
# development of Python modules, the functions available here
# can be inserted in any module source automatically by including
# #<<INCLUDE_ANSIBLE_MODULE_COMMON>> on a blank line by itself inside
# of an ansible module. The source of this common code lives
# in lib/ansible/module_common.py

import os
import re
import shlex
import subprocess
import sys
import types
import time
import shutil
import stat
import traceback
import platform
import errno

try:
    import grp
    import pwd
except ImportError:
    pass

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        sys.stderr.write('Error: ansible requires a json module, none found!')
        sys.exit(1)
    except SyntaxError:
        sys.stderr.write('SyntaxError: probably due to json and python being for different versions')
        sys.exit(1)

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
  has_journal = False

try:
    import syslog
    has_syslog = True
except ImportError:
    has_syslog = False


FILE_COMMON_ARGUMENTS=dict(
    src = dict(),
    mode = dict(),
    owner = dict(),
    group = dict(),
    seuser = dict(),
    serole = dict(),
    selevel = dict(),
    setype = dict(),
    # not taken by the file module, but other modules call file so it must ignore them.
    content = dict(),
    backup = dict(),
    force = dict(),
)

def is_windows():
    return sys.platform == 'win32'

if is_windows():
    import ctypes
    from ctypes import wintypes

    _PSECURITY_DESCRIPTOR = ctypes.POINTER(wintypes.BYTE)
    _PSID = ctypes.POINTER(wintypes.BYTE)
    _PACL = ctypes.POINTER(wintypes.BYTE)
    _LPDWORD = ctypes.POINTER(wintypes.DWORD)
    _LPBOOL = ctypes.POINTER(wintypes.BOOL)
    _SECURITY_INFORMATION = wintypes.DWORD

    #privilege constants
    #http://msdn.microsoft.com/en-us/library/windows/desktop/bb530716
    _SE_TAKE_OWNERSHIP_NAME = 'SeTakeOwnershipPrivilege'
    _SE_RESTORE_NAME = 'SeRestorePrivilege'
    _SE_SECURITY_NAME = 'SeSecurityPrivilege'
    _SE_BACKUP_NAME = 'SeBackupPrivilege'

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379261
    class _LUID(ctypes.Structure):
        _fields_ = [
            ('LowPart', wintypes.DWORD),
            ('HighPart', wintypes.LONG)
        ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379263
    class _LUID_AND_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ('Luid', _LUID),
            ('Attributes', wintypes.DWORD)
        ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379630
    _ANYSIZE_ARRAY = 1
    class _TOKEN_PRIVILEGES(ctypes.Structure):
        _fields_ = [
            ('PrivilegeCount', wintypes.DWORD),
            ('Privileges', _LUID_AND_ATTRIBUTES * _ANYSIZE_ARRAY)
        ]

    #http://msdn.microsoft.com/en-us/library/cc234251.aspx
    _OWNER_SECURITY_INFORMATION = 0x00000001
    _GROUP_SECURITY_INFORMATION = 0x00000002
    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379593
    _SE_FILE_OBJECT = 1
    #winerror.h
    _ERROR_SUCCESS = 0
    #winnt.h
    _TOKEN_ADJUST_PRIVILEGES = 0x0020
    _SE_PRIVILEGE_ENABLED = 0x00000002L

    _advapi32 = ctypes.windll.advapi32
    _kernel32 = ctypes.windll.kernel32

    #http://msdn.microsoft.com/en-us/library/windows/desktop/ms683179
    _GetCurrentProcess = _kernel32.GetCurrentProcess
    _GetCurrentProcess.restype = wintypes.HANDLE
    _GetCurrentProcess.argtypes = []

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379166
    _LookupAccountSid = _advapi32.LookupAccountSidW
    _LookupAccountSid.restype = wintypes.BOOL
    _LookupAccountSid.argtypes = [
        wintypes.LPCWSTR, #System Name (in opt)
        _PSID, #SID (in)
        wintypes.LPCWSTR, #Name (out)
        _LPDWORD, #Name Size (in out)
        wintypes.LPCWSTR, #Domain(out_opt)
        _LPDWORD, #Domain Size (in out)
        _LPDWORD, #SID Type (out)
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379159
    _LookupAccountName = _advapi32.LookupAccountNameW
    _LookupAccountName.restype = wintypes.BOOL
    _LookupAccountName.argtypes =[
        wintypes.LPCWSTR, #System Name (in opt)
        wintypes.LPCWSTR, #Account Name (in)
        _PSID, #sid (out opt)
        _LPDWORD, # sid size (in out)
        wintypes.LPCWSTR, #Domain Name (out opt)
        _LPDWORD, #Domain size (in out)
        _LPDWORD, #SID type (out)
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa446645
    _GetNamedSecurityInfo = _advapi32.GetNamedSecurityInfoW
    _GetNamedSecurityInfo.restype = wintypes.DWORD
    _GetNamedSecurityInfo.argtypes = [
        wintypes.LPCWSTR, # object name (in)
        wintypes.DWORD, # object type
        _SECURITY_INFORMATION, # requested information
        ctypes.POINTER(_PSID), # owner (in opt)
        ctypes.POINTER(_PSID), # group (in opt)
        ctypes.POINTER(_PACL), # DACL (in opt)
        ctypes.POINTER(_PACL), # SACL (in opt)
        ctypes.POINTER(_PSECURITY_DESCRIPTOR), # security descriptor
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379579
    _SetNamedSecurityInfo = _advapi32.SetNamedSecurityInfoW
    _SetNamedSecurityInfo.restype = wintypes.DWORD
    _SetNamedSecurityInfo.argtypes = [
        wintypes.LPCWSTR, # object name (in)
        wintypes.DWORD, # Object type (in)
        _SECURITY_INFORMATION, # security information that will be set
        _PSID, # owner (out opt)
        _PSID, # primary group (out opt)
        _PACL, # DACL (out opt)
        _PACL, # SACL (out opt)
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa375202
    _AdjustTokenPrivileges = _advapi32.AdjustTokenPrivileges
    _AdjustTokenPrivileges.restype = wintypes.BOOL
    _AdjustTokenPrivileges.argtypes = [
        wintypes.HANDLE, #token handle (in)
        wintypes.BOOL, #disabe all (in)
        ctypes.POINTER(_TOKEN_PRIVILEGES), #new state (ino pt)
        wintypes.DWORD, # buffer length
        ctypes.POINTER(_TOKEN_PRIVILEGES), # previous state (out opt)
        ctypes.POINTER(wintypes.DWORD), #return length (out opt)
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379180
    _LookupPrivilegeValue = _advapi32.LookupPrivilegeValueW
    _LookupPrivilegeValue.restype = wintypes.BOOL #nonzero if succeeds
    _LookupPrivilegeValue.argtypes = [
        wintypes.LPCWSTR, # system name, null for local system
        wintypes.LPCWSTR, # privilege name (in)
        ctypes.POINTER(_LUID) # result luid (out)
    ]

    #http://msdn.microsoft.com/en-us/library/windows/desktop/aa379295
    _OpenProcessToken = _advapi32.OpenProcessToken
    _OpenProcessToken.restype = wintypes.BOOL
    _OpenProcessToken.argtypes = [
        wintypes.HANDLE, # process handle (in)
        wintypes.DWORD, # desired access (in)
        ctypes.POINTER(wintypes.HANDLE) # token handle (out)
    ]

    def _look_up_account_sid(sid):
        SIZE = 256
        name = ctypes.create_unicode_buffer(SIZE)
        domain = ctypes.create_unicode_buffer(SIZE)
        cch_name = wintypes.DWORD(SIZE)
        cch_domain = wintypes.DWORD(SIZE)
        sid_type = wintypes.DWORD()

        if _LookupAccountSid(None, sid, name, ctypes.byref(cch_name),
                             domain, ctypes.byref(cch_domain),
                             ctypes.byref(sid_type)):
            return name.value, domain.value, sid_type.value
        else:
            err, msg = wintypes.WinError()
            raise Exception('LookupAccountSid: {0}, {1}'.format(err, msg))

    def _look_up_account_name(name):
        SIZE = 256
        sid_array_type = wintypes.BYTE * SIZE
        sid = sid_array_type()
        sid = ctypes.cast(sid, _PSID)
        domain = ctypes.create_unicode_buffer(SIZE)
        cb_sid = wintypes.DWORD(SIZE)
        cch_domain = wintypes.DWORD(SIZE)
        sid_type = wintypes.DWORD()

        if _LookupAccountName(None, name, sid, ctypes.byref(cb_sid),
                              domain, ctypes.byref(cch_domain),
                              ctypes.byref(sid_type)):
            return sid, domain.value, sid_type.value
        else:
            err, msg = wintypes.WinError()
            raise Exception('_LookupAccountName: {0}, {1}'.format(err, msg))

    def _win_get_user_and_group(filename):
        _request = _OWNER_SECURITY_INFORMATION | _GROUP_SECURITY_INFORMATION
        owner_sid = _PSID()
        group_sid = _PSID()
        sd = _PSECURITY_DESCRIPTOR()
        ret = _GetNamedSecurityInfo(
            filename,
            _SE_FILE_OBJECT,
            _request,
            ctypes.byref(owner_sid),
            ctypes.byref(group_sid),
            None,
            None,
            ctypes.byref(sd)
        )
        if ret != _ERROR_SUCCESS:
            err, msg = wintypes.WinError()
            raise Exception('GetNamedSecurityInfo: {0}, {1}'.format(err, msg))
        uid_data = _look_up_account_sid(owner_sid)
        gid_data = _look_up_account_sid(group_sid)
        return uid_data, gid_data

    def _win_get_process_token():
        token = wintypes.HANDLE()
        ret = _OpenProcessToken(_GetCurrentProcess(),
                                _TOKEN_ADJUST_PRIVILEGES,
                                ctypes.byref(token))
        if ret == 0:
            err, msg = wintypes.WinError()
            raise Exception('OpenProcessToken: {0}, {1}'.format(err, msg))
        return token

    def _win_set_privilege(handle, privilege_name, enable):
        privilege_name = ctypes.create_unicode_buffer(privilege_name)
        tp = _TOKEN_PRIVILEGES()
        luid = _LUID()

        ret = _LookupPrivilegeValue(None, privilege_name, ctypes.byref(luid))
        if ret == 0:
            err, msg = wintypes.WinError()
            raise Exception('LookupPrivilegeValue: {0}, {1}'.format(err, msg))
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        if enable:
            tp.Privileges[0].Attributes = _SE_PRIVILEGE_ENABLED
        else:
            tp.Privileges[0].Attributes = 0

        ret = _AdjustTokenPrivileges(handle, 0, ctypes.byref(tp), 0, None, None)
        if ret == 0:
            err, msg = wintypes.WinError()
            raise Exception('AdjustTokenPrivileges: {0}, {1}'.format(err, msg))
        #the call may succeed, but this check really reveals the results
        rc, msg = ctypes.wintypes.WinError()
        if rc != 0:
            raise Exception('AdjustTokenPrivileges GLE: {0}, {1}'.format(rc, msg))
        return True

    def _win_set_owner(filename, owner_sid):
        token = _win_get_process_token()
        _win_set_privilege(token, _SE_TAKE_OWNERSHIP_NAME, True)
        _win_set_privilege(token, _SE_RESTORE_NAME, True)
        res = _SetNamedSecurityInfo(
            filename,
            _SE_FILE_OBJECT,
            _OWNER_SECURITY_INFORMATION,
            owner_sid,
            None,
            None,
            None
        )
        if res != _ERROR_SUCCESS:
            err, msg = wintypes.WinError()
            raise Exception('SetNamedSecurityInfo: {0}, {1}'.format(err, msg))

    def _win_set_group(filename, group_sid):
        token = _win_get_process_token()
        res = _SetNamedSecurityInfo(
            filename,
            _SE_FILE_OBJECT,
            _GROUP_SECURITY_INFORMATION,
            None,
            group_sid,
            None,
            None
        )
        if res != _ERROR_SUCCESS:
            err, msg = wintypes.WinError()
            raise Exception('SetNamedSecurityInfo: {0}, {1}'.format(err, msg))


def get_platform():
    ''' what's the platform?  example: Linux is a platform. '''
    return platform.system()

def get_distribution():
    ''' return the distribution name '''
    if platform.system() == 'Linux':
        try:
            distribution = platform.linux_distribution()[0].capitalize()
            if distribution == 'NA':
                if os.path.is_file('/etc/system-release'):
                    distribution = 'OtherLinux'
        except:
            # FIXME: MethodMissing, I assume?
            distribution = platform.dist()[0].capitalize()
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
        required_one_of=None, add_file_common_args=False, supports_check_mode=False):

        '''
        common code for quickly building an ansible module in Python
        (although you can write modules in anything that can return JSON)
        see library/* for examples
        '''

        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        self.check_mode = False
        
        self.aliases = {}
        
        if add_file_common_args:
            for k, v in FILE_COMMON_ARGUMENTS.iteritems():
                if k not in self.argument_spec:
                    self.argument_spec[k] = v

        os.environ['LANG'] = MODULE_LANG
        (self.params, self.args) = self._load_params()

        self._legal_inputs = [ 'CHECKMODE' ]
        
        self.aliases = self._handle_aliases()

        if check_invalid_arguments:
            self._check_invalid_arguments()
        self._check_for_check_mode()

        self._set_defaults(pre=True)

        if not bypass_checks:
            self._check_required_arguments()
            self._check_argument_values()
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

    def _to_filesystem_str(self, path):
        '''Returns filesystem path as a str, if it wasn't already.

        Used in selinux interactions because it cannot accept unicode
        instances, and specifying complex args in a playbook leaves
        you with unicode instances.  This method currently assumes
        that your filesystem encoding is UTF-8.

        '''
        if isinstance(path, unicode):
            path = path.encode("utf-8")
        return path

    # If selinux fails to find a default, return an array of None
    def selinux_default_context(self, path, mode=0):
        context = self.selinux_initial_context()
        if not HAVE_SELINUX or not self.selinux_enabled():
            return context
        try:
            ret = selinux.matchpathcon(self._to_filesystem_str(path), mode)
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
            ret = selinux.lgetfilecon(self._to_filesystem_str(path))
        except OSError, e:
            if e.errno == errno.ENOENT:
                self.fail_json(path=path, msg='path %s does not exist' % path)
            else:
                self.fail_json(path=path, msg='failed to retrieve selinux context')
        if ret[0] == -1:
            return context
        context = ret[1].split(':')
        return context

    def windows_log(self, module, msg):
            self.run_command(['eventcreate', '/ID', '1000',
                              '/T', 'INFORMATION',
                              '/L', 'APPLICATION',
                              '/D', msg,
                              '/SO', module])

    def user_and_group(self, filename):
        if is_windows():
            return self._win_user_and_group(filename)
        else:
            return self._nix_user_and_group(filename)

    def _nix_user_and_group(self, filename):
        filename = os.path.expanduser(filename)
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

    def _win_user_and_group(self, filename):
        filename = os.path.expanduser(filename)
        uid_data, gid_data = _win_get_user_and_group(filename)
        return uid_data[0], gid_data[0]

    def set_default_selinux_context(self, path, changed):
        if not HAVE_SELINUX or not self.selinux_enabled():
            return changed
        context = self.selinux_default_context(path)
        return self.set_context_if_different(path, context, False)

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
                if self.check_mode:
                    return True
                rc = selinux.lsetfilecon(self._to_filesystem_str(path),
                                         str(':'.join(new_context)))
            except OSError:
                self.fail_json(path=path, msg='invalid selinux context', new_context=new_context, cur_context=cur_context, input_was=context)
            if rc != 0:
                self.fail_json(path=path, msg='set selinux context failed')
            changed = True
        return changed

    def get_uid_by_name(self, name):
        if is_windows():
            return self._win_get_uid_by_name(name)
        else:
            return self._nix_get_uid_by_name(name)

    def get_gid_by_name(self, name):
        if is_windows():
            return self._win_get_gid_by_name(name)
        else:
            return self._nix_get_gid_by_name(name)

    def _nix_get_uid_by_name(self, name):
        return pwd.getpwnam(name).pw_uid

    def _nix_get_gid_by_name(self, name):
        return grp.getgrnam(name).gr_gid

    def chown(self, path, uid, gid):
        if is_windows():
            if uid != -1:
                _win_set_owner(path, uid)
            if gid != -1:
                _win_set_group(path, gid)
        else:
            os.chown(path, uid, gid)

    #on windows a file can be owned by a group and
    #have group set to user, so...
    def _win_get_uid_by_name(self, name):
        return _look_up_account_name(name)[0]
    _win_get_gid_by_name = _win_get_uid_by_name

    def set_owner_if_different(self, path, owner, changed):
        path = os.path.expanduser(path)
        if owner is None:
            return changed
        user, group = self.user_and_group(path)
        if owner != user:
            try:
                uid = self.get_uid_by_name(owner)
            except KeyError:
                self.fail_json(path=path, msg='chown failed: failed to look up user %s' % owner)
            if self.check_mode:
                return True
            try:
                self.chown(path, uid, -1)
            except OSError:
                self.fail_json(path=path, msg='chown failed')
            changed = True
        return changed

    def set_group_if_different(self, path, group, changed):
        path = os.path.expanduser(path)
        if group is None:
            return changed
        old_user, old_group = self.user_and_group(path)
        if old_group != group:
            if self.check_mode:
                return True
            try:
                gid = self.get_gid_by_name(group)
            except KeyError:
                self.fail_json(path=path, msg='chgrp failed: failed to look up group %s' % group)
            try:
                self.chown(path, -1, gid)
            except OSError:
                self.fail_json(path=path, msg='chgrp failed')
            changed = True
        return changed

    def set_mode_if_different(self, path, mode, changed):
        path = os.path.expanduser(path)
        if mode is None:
            return changed
        try:
            # FIXME: support English modes
            if not isinstance(mode, int):
                mode = int(mode, 8)
        except Exception, e:
            self.fail_json(path=path, msg='mode needs to be something octalish', details=str(e))

        st = os.stat(path)
        prev_mode = stat.S_IMODE(st[stat.ST_MODE])

        if prev_mode != mode:
            if self.check_mode:
                return True
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
            kwargs['size'] = st[stat.ST_SIZE]
        else:
            kwargs['state'] = 'absent'
        return kwargs


    def _handle_aliases(self):
        aliases_results = {} #alias:canon
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
                aliases_results[alias] = k
                if alias in self.params:
                    self.params[k] = self.params[alias]
        
        return aliases_results

    def _check_for_check_mode(self):
        for (k,v) in self.params.iteritems():
            if k == 'CHECKMODE':
                if not self.supports_check_mode:
                    self.exit_json(skipped=True, msg="remote module does not support check mode")
                if self.supports_check_mode:
                    self.check_mode = True

    def _check_invalid_arguments(self):
        for (k,v) in self.params.iteritems():
            if k == 'CHECKMODE':
                continue
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
                self.fail_json(msg="one of the following is required: %s" % ','.join(check))

    def _check_required_together(self, spec):
        if spec is None:
            return
        for check in spec:
            counts = [ self._count_terms([field]) for field in check ]
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

    def _check_argument_values(self):
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

    def _check_argument_types(self):
        ''' ensure all arguments have the requested type '''
        for (k, v) in self.argument_spec.iteritems():
            wanted = v.get('type', None)
            if wanted is None:
                continue
            if k not in self.params:
                continue

            value = self.params[k]
            is_invalid = False

            if wanted == 'str':
                if not isinstance(value, basestring):
                    self.params[k] = str(value)
            elif wanted == 'list':
                if not isinstance(value, list):
                    if isinstance(value, basestring):
                        self.params[k] = value.split(",")
                    else:
                        is_invalid = True
            elif wanted == 'dict':
                if not isinstance(value, dict):
                    if isinstance(value, basestring):
                        self.params[k] = dict([x.split("=", 1) for x in value.split(",")])
                    else:
                        is_invalid = True
            elif wanted == 'bool':
                if not isinstance(value, bool):
                    if isinstance(value, basestring):
                        self.params[k] = self.boolean(value)
                    else:
                        is_invalid = True
            elif wanted == 'int':
                if not isinstance(value, int):
                    if isinstance(value, basestring):
                        self.params[k] = int(value)
                    else:
                        is_invalid = True
            else:
                self.fail_json(msg="implementation error: unknown type %s requested for %s" % (wanted, k))

            if is_invalid:
                self.fail_json(msg="argument %s is of invalid type: %s, required: %s" % (k, type(value), wanted))

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
            except Exception, e:
                self.fail_json(msg="this module requires key=value arguments (%s)" % items)
            params[k] = v
        params2 = json.loads(MODULE_COMPLEX_ARGS)
        params2.update(params)
        return (params2, args)

    def _log_invocation(self):
        ''' log that ansible ran the module '''
        # TODO: generalize a separate log function and make log_invocation use it
        # Sanitize possible password argument when logging.
        log_args = dict()
        passwd_keys = ['password', 'login_password']
        
        for param in self.params:
            canon  = self.aliases.get(param, param)
            arg_opts = self.argument_spec.get(canon, {})
            no_log = arg_opts.get('no_log', False)
                
            if no_log:
                log_args[param] = 'NOT_LOGGING_PARAMETER'
            elif param in passwd_keys:
                log_args[param] = 'NOT_LOGGING_PASSWORD'
            else:
                log_args[param] = self.params[param]

        module = 'ansible-%s' % os.path.basename(__file__)
        msg = ''
        for arg in log_args:
            msg = msg + arg + '=' + str(log_args[arg]) + ' '
        if msg:
            msg = 'Invoked with %s' % msg
        else:
            msg = 'Invoked'

        if (has_journal):
            journal_args = ["MESSAGE=%s %s" % (module, msg)]
            journal_args.append("MODULE=%s" % os.path.basename(__file__))
            for arg in log_args:
                journal_args.append(arg.upper() + "=" + str(log_args[arg]))
            journal.sendv(*journal_args)
        elif has_syslog:
            syslog.openlog(module, 0, syslog.LOG_USER)
            syslog.syslog(syslog.LOG_NOTICE, msg)
        elif is_windows():
            self.windows_log(module, msg)

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
        paths += os.environ.get('PATH', '').split(os.pathsep)
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

    def from_json(self, data):
        return json.loads(data)

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
        if is_windows():
            self._win_atomic_replace(src, dest)
        else:
            self._nix_atomic_replace(src, dest)

    def _win_atomic_replace(self, src, dest):
        if os.path.exists(dest):
            st = os.stat(dest)
            os.chmod(src, st.st_mode & 07777)
            owner, group = self._win_user_and_group(dest)
            owner_sid = self._win_get_uid_by_name(owner)
            group_sid = self._win_get_gid_by_name(group)
            self.chown(src, owner_sid, group_sid)
            #no easy atomic replace on windows
            os.remove(dest)
        os.rename(src, dest)

    def _nix_atomic_replace(self, src, dest):
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
        else:
            if self.selinux_enabled():
                context = self.selinux_default_context(dest)
                self.set_context_if_different(src, context, False)
        os.rename(src, dest)

    def run_command(self, args, check_rc=False, close_fds=False, executable=None, data=None):
        '''
        Execute a command, returns rc, stdout, and stderr.
        args is the command to run
        If args is a list, the command will be run with shell=False.
        Otherwise, the command will be run with shell=True when args is a string.
        Other arguments:
        - check_rc (boolean)  Whether to call fail_json in case of
                              non zero RC.  Default is False.
        - close_fds (boolean) See documentation for subprocess.Popen().
                              Default is False.
        - executable (string) See documentation for subprocess.Popen().
                              Default is None.
        '''
        if isinstance(args, list):
            shell = False
        elif isinstance(args, basestring):
            shell = True
        else:
            msg = "Argument 'args' to run_command must be list or string"
            self.fail_json(rc=257, cmd=args, msg=msg)
        rc = 0
        msg = None
        st_in = None
        if data:
            st_in = subprocess.PIPE
        try:
            cmd = subprocess.Popen(args,
                                   executable=executable,
                                   shell=shell,
                                   close_fds=close_fds,
                                   stdin=st_in,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            if data:
                cmd.stdin.write(data)
                cmd.stdin.write('\\n')
            out, err = cmd.communicate()
            rc = cmd.returncode
        except (OSError, IOError), e:
            self.fail_json(rc=e.errno, msg=str(e), cmd=args)
        except:
            self.fail_json(rc=257, msg=traceback.format_exc(), cmd=args)
        if rc != 0 and check_rc:
            msg = err.rstrip()
            self.fail_json(cmd=args, rc=rc, stdout=out, stderr=err, msg=msg)
        return (rc, out, err)

    def pretty_bytes(self,size):
        ranges = (
                (1<<50L, 'ZB'),
                (1<<50L, 'EB'),
                (1<<50L, 'PB'),
                (1<<40L, 'TB'),
                (1<<30L, 'GB'),
                (1<<20L, 'MB'),
                (1<<10L, 'KB'),
                (1, 'Bytes')
            )
        for limit, suffix in ranges:
            if size >= limit:
                break
        return '%.2f %s' % (float(size)/ limit, suffix)

# == END DYNAMICALLY INSERTED CODE ===

"""
