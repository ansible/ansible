# -*- coding: utf-8 -*-
#
# (c) 2017, Yassine Azzouz <yassine.azzouz@gmail.com>
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import re
import stat
import json
import ast
import os.path as osp
from subprocess import call, Popen, PIPE

try:
    from pywhdfs.client import WebHDFSClient
    from pywhdfs.utils.utils import HdfsError
except ImportError:
    has_pywhdfs = False
else:
    has_pywhdfs = True

try:
    import requests_kerberos as rk
except ImportError:
    has_kerberos_ext = False
else:
    has_kerberos_ext = True

AVAILABLE_HASH_ALGORITHMS = dict()
try:
    import hashlib

    # python 2.7.9+ and 2.7.0+
    for attribute in ('available_algorithms', 'algorithms'):
        algorithms = getattr(hashlib, attribute, None)
        if algorithms:
            break
    if algorithms is None:
        # python 2.5+
        algorithms = ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512')
    for algorithm in algorithms:
        AVAILABLE_HASH_ALGORITHMS[algorithm] = getattr(hashlib, algorithm)
except ImportError:
    import sha
    AVAILABLE_HASH_ALGORITHMS = {'sha1': sha.sha}
    try:
        import md5
        AVAILABLE_HASH_ALGORITHMS['md5'] = md5.md5
    except ImportError:
        pass


PERM_BITS = 0o7777          # file mode permission bits
EXEC_PERM_BITS = 0o0111     # execute permission bits
DEFAULT_PERM = 0o666        # default file permission bits


def _check_required_if(module, spec):
        ''' ensure that parameters which conditionally required are present '''
        if spec is None:
            return
        for (key, val, requirements) in spec:
            missing = []
            if key in module.params and module.params[key] == val:
                for check in requirements:
                    count = module._count_terms((check,))
                    if count == 0:
                        missing.append(check)
            if len(missing) > 0:
                hdfs_fail_json(msg="%s is %s but the following are missing: %s" % (key, val, ','.join(missing)))


def _check_invalid_if(module, spec):
        ''' ensure that parameters which conditionally required are present '''
        if spec is None:
            return
        for (key, val, requirements) in spec:
            invalids = []
            if key in module.params and module.params[key] == val:
                for check in requirements:
                    count = module._count_terms(check)
                    if count != 0:
                        invalids.append(check)
            if len(invalids) > 0:
                hdfs_fail_json(msg="%s is %s but the following are present: %s" % (key, val, ','.join(invalids)))


def _check_required_one_of_if(module, spec):
        ''' ensure that parameters which conditionally required are present '''
        if spec is None:
            return
        for (key, val, requirements) in spec:
            missing = []
            if key in module.params and module.params[key] == val:
                for check in requirements:
                    count = module._count_terms(check)
                    if count == 0:
                        missing.append(check)
            if len(missing) == 1:
                hdfs_fail_json(msg="%s is %s but one of the following are missing: %s" % (key, val, ','.join(missing)))


def hdfs_argument_spec():
    return dict(
        # Dtermines which type of client we will actually user : InsecureClient, TokenClient or KerberosClient
        authentication=dict(choices=['none', 'kerberos', 'token'], default='none'),
        # When security is off, the authenticated user is the username specified in the user.name query parameter, specified by this parameter.
        # Defaults to the current user's (as determined by `whoami`).
        user=dict(required=False, default=None),
        # When security is on, the authentication is performed against a kerberos server with the principal, specified by this parameter.
        principal=dict(required=False, default=None),
        # User to proxy as, theorically make sense only with authentication but works for both secure and Insecure.
        proxy=dict(required=False, default=None),
        # You can use either a keytab or a password for kerberos authentication.
        password=dict(required=False, default=None, no_log=True),
        keytab=dict(required=False, default=None, no_log=True),
        # When security is on you can use a delegation token instead of having to authenticate every time with kerberos.
        token=dict(required=False, default=None, no_log=True),
        # a json spec of the nameservice to use, create the spec in yml then use the to_json filter
        nameservices=dict(required=True, type='str'),
        # For secure connections whether to verify or not the server certificate
        verify=dict(required=False, default=False, type='bool'),
        # For secure connections the server certificate file(trust store) to trust.
        truststore=dict(required=False, default=None, no_log=True),
        # Connection timeouts, forwarded to the request handler. How long to wait for the server to send data before giving up,
        timeout=dict(required=False, default=None, type='float'),
        # Root path, this will be prefixed to all HDFS paths passed to the client. If the root is relative,
        # the path will be assumed relative to the user's home directory.
        root=dict(required=False, default=None),
    )


def hdfs_required_together():
    return []


def hdfs_mutually_exclusive():
    return [
        ['password', 'keytab'],
        ['user', 'principal'],
        ['token', 'principal'],
        ['token', 'user'],
        ['token', 'password'],
        ['token', 'keytab']
    ]


def hdfs_required_one_of_if():
    return [
        ('authentication', 'kerberos', ['password', 'keytab']),
    ]


def hdfs_required_if():
    return [
        ('authentication', 'kerberos', ['principal']),
        ('authentication', 'token', ['token']),
    ]


def hdfs_invalid_if():
    return [
        ('verify', False, ['truststore']),
        ('authentication', 'none', ['principal', 'password', 'keytab', 'token']),
        ('authentication', 'token', ['principal', 'password', 'keytab', 'user']),
        ('authentication', 'kerberos', ['token', 'user']),
    ]


def kinit(principal, password=None, keytab=None):
    kinit = '/usr/bin/kinit'
    if password is not None:
        kinit_args = [kinit, principal]
        try:
            kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            kinit.stdin.write('%s\n' % password)
            kinit.wait()
        except Exception:
            raise
    elif keytab is not None:
        kinit_args = [kinit, '-kt', keytab, principal]
        try:
            kinit = Popen(kinit_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            kinit.wait()
        except Exception:
            raise
    else:
        raise ValueError("Kerberos authentication need either a password or a keytab.")


def kdestroy():
    try:
        kdestroy = '/usr/bin/kdestroy'
        kdestroy_args = [kdestroy, '-q', '-A']
        kdestroy = Popen(kdestroy_args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        kdestroy.wait()
    except Exception:
        raise


class HDFSAnsibleModule(object):
    def __init__(self, module, bypass_checks=False, required_if=None, required_one_of_if=None, invalid_if=None):
        self.module = module

        self.file_cleanup_onfail = []
        self.file_restore_onfail = []
        self.local_file_cleanup_onfail = []
        self.local_file_restore_onfail = []

        if not has_pywhdfs:
            self.hdfs_fail_json(msg="python library pywhdfs required: pip install pywhdfs")

        authentication = self.module.params.get('authentication')
        if not has_kerberos_ext and authentication == 'kerberos':
            self.hdfs_fail_json(msg="python library requests-kerberos required: pip install requests-kerberos")

        self.hdfs_required_if = hdfs_required_if()
        self.hdfs_required_one_of_if = hdfs_required_one_of_if()
        self.hdfs_invalid_if = hdfs_invalid_if()

        if required_if is not None:
            self.hdfs_required_if.extend(required_if)
        if required_one_of_if is not None:
            self.hdfs_required_one_of_if.extend(required_one_of_if)
        if invalid_if is not None:
            self.hdfs_invalid_if.extend(invalid_if)

        # Need to be performed here since ansible does not provide yet a way to check
        # required one of with if
        if not bypass_checks:
            _check_required_if(module, self.hdfs_required_if)
            _check_required_one_of_if(module, self.hdfs_required_one_of_if)
            _check_invalid_if(module, self.hdfs_invalid_if)

        # Request a TGT if the authentication uses kerberos
        if authentication == 'kerberos':
            principal = module.params['principal']
            password = module.params['password']
            keytab = module.params['keytab']
            try:
                kinit(principal, password, keytab)
            except Exception as e:
                self.hdfs_fail_json(msg="Kerberos authentication failed: %s." % e)

        # Get the client
        try:
            self.client = self.get_client()
        except Exception as e:
            self.hdfs_fail_json(msg="Error instantiating pywhdfs client: %s." % e)

    def __del__(self):
        authentication = self.module.params.get('authentication')
        if authentication == 'kerberos':
            try:
                kdestroy()
            except Exception as e:
                self.hdfs_fail_json(msg="failed to clean kerberos TGT: %s." % e)

    '''
       Note: about error handling and clean up.

       This seems to be the safest way to do cleanup in ansible
       typically to clean up you need to throw errors on the low level
       functions then catch it on every calling function and do the clean up
       most functions fail the module and do not throw errors so the calling function can not
       do the clean up.
    '''
    def hdfs_fail_json(self, **kwargs):
        self.on_fail()
        self.module.fail_json(**kwargs)

    def cleanup_on_failure(self, path):
        self.file_cleanup_onfail.append(path)

    def restore_on_failure(self, restore_path, backup_path):
        self.file_restore_onfail.append((restore_path, backup_path))

    def local_cleanup_on_failure(self, path):
        self.local_file_cleanup_onfail.append(path)

    def local_restore_on_failure(self, restore_path, backup_path):
        self.local_file_restore_onfail.append((restore_path, backup_path))

    def on_fail(self):
        if self.local_file_cleanup_onfail is not None and len(self.local_file_cleanup_onfail) != 0:
            for f in self.local_file_cleanup_onfail:
                try:
                    if osp.exists(f):
                        if not osp.isdir(f):
                            os.remove(f)
                        else:
                            os.removedirs(f)
                except:
                    pass

        if self.local_file_restore_onfail is not None and len(self.local_file_restore_onfail) != 0:
            for restore_path, backup_path in self.local_file_cleanup_onfail:
                try:
                    if osp.exists(restore_path):
                        if not osp.isdir(restore_path):
                            os.remove(restore_path)
                        else:
                            os.removedirs(restore_path)
                    if osp.exists(backup_path):
                        os.rename(backup_path, restore_path)
                except:
                    pass

        if self.file_cleanup_onfail is not None and len(self.file_cleanup_onfail) != 0:
            for f in self.file_cleanup_onfail:
                try:
                    if self.isdir(f):
                        self.client.delete(f, recursive=True)
                    else:
                        self.client.delete(f)
                except:
                    pass

        if self.file_restore_onfail is not None and len(self.file_restore_onfail) != 0:
            for restore_path, backup_path in self.file_cleanup_onfail:
                try:
                    self.client.delete(restore_path)
                    self.client.rename(backup_path, restore_path)
                except:
                    pass

    def _parse_nameservice_parameter(self, nameservice):
        if not isinstance(nameservice, dict):
            # well not a dict nor a list then it is just a urls string most likely
            return {
                'urls': [url for url in re.split(r',|;', str(nameservice).strip(' ').strip('"').strip('\''))],
                'mounts': ['/'],
            }
        else:
            # nameservice is just a dict
            if "urls" in nameservice:
                if isinstance(nameservice["urls"], list):
                    urls = [str(url).strip(' ').strip('"').strip('\'') for url in nameservice["urls"]]
                else:
                    urls = [str(url) for url in re.split(r',|;', str(nameservice["urls"]).strip(' ').strip('"').strip('\''))]
            else:
                raise HdfsError('missing urls parameter in namespace %s.', nameservice)
            if "mounts" in nameservice:
                if isinstance(nameservice["mounts"], list):
                    # list of mounts
                    mounts = [str(mount).strip(' ').strip('"').strip('\'') for mount in nameservice["mounts"]]
                else:
                    # only one mount point or comma separated list of mounts
                    mounts = [str(mount) for mount in re.split(r',|;', str(nameservice["mounts"]).strip(' ').strip('"').strip('\''))]
            else:
                # no mount point provided so mount to /
                mounts = ["/"]
            return {
                'urls': urls,
                'mounts': mounts,
            }

    def get_client(self):
        """Load HDFS client.

        Further calls to this method for the same alias will return the same client
        instance (in particular, any option changes to this alias will not be taken
        into account).

        """
        params = self.module.params
        options = {}

        try:
            #nameservices = json.loads(params.get('nameservices'))
            nameservices = ast.literal_eval(params.get('nameservices'))
        except:
            raise HdfsError('nameservices parameter "%s" does not have a valid format, it need to be json.', params.get('nameservices'))

        # nameservices could be parsed, check its format now
        if not isinstance(nameservices, list):
            # one nameservice defined
            options['nameservices'] = [self._parse_nameservice_parameter(nameservices)]
        else:
            # provided a list of namespaces
            options['nameservices'] = [self._parse_nameservice_parameter(nameservice) for nameservice in nameservices]

        options.update({
            'root': params.get('root', None),
            'proxy': params.get('proxy', None),
            'timeout': params.get('timeout', None),
            'verify': params.get('verify', False),
            'truststore': params.get('truststore', None),
        })
        authentication = params.get('authentication', 'none')

        if (authentication == 'token'):
            options.update({
                'auth_mechanism': 'TOKEN',
                'token': params.get('token'),
            })
        elif (authentication == 'kerberos'):
            options.update({
                'auth_mechanism': 'GSSAPI',
            })
        else:
            options.update({
                'auth_mechanism': 'NONE',
                'user': params.get('user', None),
            })

        return WebHDFSClient(**options)

    def get_authentication_type(self):
        return self.module.params.get('authentication')

    #################################################################################################################
    #                                     Common files functions
    #################################################################################################################

    def hdfs_set_attributes(self, path, owner=None, group=None, replication=None, quota=None, spaceQuota=None, permission=None):
        changed = False

        # performance improvement: get status and content only once
        ''' Find out current state '''
        status = self.hdfs_status(path, strict=False)
        content = self.hdfs_content(path, strict=False)
        aclStatus = self.client.getAclStatus(path, strict=False)

        curr_type = status['type']
        curr_space_quota = content['spaceQuota']
        curr_name_quota = content['quota']
        curr_replication = status['replication']
        curr_group = status['group']
        curr_owner = status['owner']

        # set modes and owners as needed
        if curr_owner != owner and owner is not None:
            self.hdfs_set_owner(path, owner)
            changed = True

        if curr_group != group and group is not None:
            changed = self.hdfs_set_group(path, group)
            changed = True

        changed |= self.hdfs_set_mode(path, permission)

        # only files can have a replication factor
        if curr_replication != replication and curr_type == 'FILE' and replication is not None:
            self.hdfs_set_replication(path, replication)
            changed = True

        # only dirs can have a name quota
        if curr_name_quota != quota and curr_type == 'DIRECTORY' and quota is not None:
            self.hdfs_set_namequota(path, quota)
            changed = True

        # only dirs can have a name quota
        if curr_space_quota != spaceQuota and curr_type == 'DIRECTORY' and spaceQuota is not None:
            self.hdfs_set_spacequota(path, spaceQuota)
            changed = True

        return changed

    def hdfs_set_attributes_recursive(self, path, owner=None, group=None, replication=None, quota=None, spaceQuota=None, permission=None):
        changed = False
        for root, dirs, files in self.client.walk(path, depth=0, status=False):
            for fsobj in dirs + files:
                # still works in hdfs :)
                path = os.path.join(root, fsobj)
                changed |= self.hdfs_set_attributes(path=path, owner=owner, group=group,
                                                    replication=replication, quota=quota,
                                                    spaceQuota=spaceQuota, permission=permission)
        return changed

    def hdfs_resolvepath(self, hdfs_path):
        return self.client.resolvepath(hdfs_path)

    def get_state(self, path):
        ''' Find out current state '''
        try:
            status = self.client.status(path, strict=False)
        except Exception as e:
            self.hdfs_fail_json(msg=str(e))

        if status is not None:
            if status['type'] == 'DIRECTORY':
                return 'directory'
            else: #FILE'
                return 'file'
        return 'absent'

    def hdfs_status(self, path, strict=False):
        ''' Find out current state '''
        try:
            status = self.client.status(path, strict=True)
        except HdfsError as e:
            if not strict:
                # seems there is a problem with strict, it ignores almost all errors.
                # need to skip only file not found
                if "File does not exist" in str(e):
                    status = None
                    pass
                else:
                    self.hdfs_fail_json(msg=str(e))
            else:
                self.hdfs_fail_json(msg=str(e))
        except Exception as e:
            self.hdfs_fail_json(msg=str(e))
        return status

    def hdfs_content(self, path, strict=False):
        ''' Find out current state '''
        try:
            content = self.client.content(path, strict=strict)
        except HdfsError as e:
            if not strict:
                # seems there is a problem with strict, it ignores almost all errors.
                # need to skip only file not found
                if "File does not exist" in str(e):
                    content = None
                    pass
                else:
                    self.hdfs_fail_json(msg=str(e))
            else:
                self.hdfs_fail_json(msg=str(e))
        except Exception as e:
            self.hdfs_fail_json(msg=str(e))
        return content

    def hdfs_checksum(self, path, strict=False):
        ''' Find out current state '''
        try:
            checksum = self.client.checksum(path)
        except HdfsError as e:
            if not strict:
                # seems there is a problem with strict, it ignores almost all errors.
                # need to skip only file not found
                if 'File %s not found.' % path in str(e):
                    checksum = None
                    pass
                else:
                    self.hdfs_fail_json(msg=str(e))
            else:
                self.hdfs_fail_json(msg=str(e))
        except Exception as e:
            self.hdfs_fail_json(msg=str(e))
        return checksum

    def hdfs_delete(self, path, recursive=True):
        try:
            # By default, this method will raise an HdfsError if trying to delete a non-empty directory.
            # returns True if the deletion was successful and False if no file or directory previously existed at hdfs_path
            result = self.client.delete(path, recursive=recursive)
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, delete failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, delete failed: %s" % e)
        return result

    def hdfs_makedirs(self, path, permission=None):
        try:
            self.client.makedirs(path, permission=permission)
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, mkdir failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, mkdir failed: %s" % e)
        return True

    def hdfs_set_times(self, path, access_time=None, modification_time=None):
        try:
            self.client.set_times(path, access_time=access_time, modification_time=modification_time)
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, updating times failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, updating times failed: %s" % e)
        return True

    def hdfs_touch(self, path, permission=None):
        try:
            self.client.write(path, data="")
            ## files are written asynchroniously need to force a wait ##
            content = self.client.read_file(path)
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, touch failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, touch failed: %s" % e)

    def hdfs_is_dir(self, path):
        status = self.hdfs_status(path, strict=False)
        if status is not None and status['type'] == 'DIRECTORY':
            return True
        else:
            return False

    def hdfs_exist(self, path):
        ''' Find out current state '''
        status = self.hdfs_status(path, strict=False)
        if status is not None:
            return True
        return False

    def hdfs_is_file(self, path):
        status = self.hdfs_status(path, strict=False)
        if status is not None and status['type'] == 'FILE':
            return True
        else:
            return False

    def hdfs_set_owner(self, path, owner):
        if owner is None:
            return False
        try:
            self.client.set_owner(path, owner=owner)
        except HdfsError as e:
            self.hdfs_fail_json(path=path, msg="Hdfs error, set owner failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, set owner failed: %s" % e)
        return True

    def hdfs_set_group(self, path, group):
        if group is None:
            return False
        try:
            self.client.set_owner(path, group=group)
        except HdfsError as e:
            self.hdfs_fail_json(path=path, msg="Hdfs error, set group failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, set group failed: %s" % e)
        return True

    def hdfs_set_replication(self, path, replication):
        if replication is None:
            return False
        try:
            self.client.set_replication(path, replication=replication)
        except HdfsError as e:
            self.hdfs_fail_json(path=path, msg="Hdfs error, set replication failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, set replication failed: %s" % e)
        return True

    #####################################################################################
    # Infortunately right now there is no way to Set Quotas in webHDFS
    # Check https://hadoop.apache.org/docs/r1.0.4/webhdfs.html for the full API specs
    # This is beeing adressed in https://issues.apache.org/jira/browse/HDFS-6192
    # Right now the only solution is to use shell to set Quotas until something better comes out.
    #####################################################################################

    def hdfs_set_namequota(self, path, quota):
        if quota is None:
            return False
        if quota == "-1":
            try:
                call("hdfs dfsadmin -clrQuota %s" % path, shell=True)
            except Exception as e:
                self.hdfs_fail_json(path=path, msg="clear name quota failed : %s" % e)
        else:
            try:
                # I don't know why this seems to work only this way
                call("hdfs dfsadmin -setQuota %s %s" % (quota, path), shell=True)
            except Exception as e:
                self.hdfs_fail_json(path=path, msg="set name quota failed : %s" % e)
        return True

    def hdfs_set_spacequota(self, path, quota):
        if quota is None:
            return False

        if quota == "-1":
            try:
                call("hdfs dfsadmin -clrSpaceQuota %s" % path, shell=True)
            except Exception as e:
                self.hdfs_fail_json(path=path, msg="set space quota failed : %s" % e)
        else:
            try:
                call("hdfs dfsadmin -setSpaceQuota %s %s" % (quota, path), shell=True)
            except Exception as e:
                self.hdfs_fail_json(path=path, msg="set space quota failed : %s" % e)
        return True

    #################################################################################################################
    #                                     Permissions functions
    #################################################################################################################

    def get_norm_permissions(self, path):
        status = self.hdfs_status(path, strict=False)
        aclStatus = self.client.getAclStatus(path, strict=False)

        permission = status['permission']
        stickybyte = aclStatus['stickyBit']

        if len(str(permission)) == 3:
            if stickybyte is True:
                permission = "1" + permission
            else:
                permission = "0" + permission

        return int(permission, 8)

    def _apply_operation_to_mode(self, user, operator, mode_to_apply, current_mode):
        if operator == '=':
            if user == 'u':
                mask = stat.S_IRWXU | stat.S_ISUID
            elif user == 'g':
                mask = stat.S_IRWXG | stat.S_ISGID
            elif user == 'o':
                mask = stat.S_IRWXO | stat.S_ISVTX

            # mask out u, g, or o permissions from current_mode and apply new permissions
            inverse_mask = mask ^ PERM_BITS
            new_mode = (current_mode & inverse_mask) | mode_to_apply
        elif operator == '+':
            new_mode = current_mode | mode_to_apply
        elif operator == '-':
            new_mode = current_mode - (current_mode & mode_to_apply)
        return new_mode

    def _get_octal_mode_from_symbolic_perms(self, path_stat, user, perms):
        prev_mode = stat.S_IMODE(path_stat.st_mode)

        is_directory = stat.S_ISDIR(path_stat.st_mode)
        has_x_permissions = (prev_mode & EXEC_PERM_BITS) > 0
        apply_X_permission = is_directory or has_x_permissions

        # Permission bits constants documented at:
        # http://docs.python.org/2/library/stat.html#stat.S_ISUID
        if apply_X_permission:
            X_perms = {
                'u': {'X': stat.S_IXUSR},
                'g': {'X': stat.S_IXGRP},
                'o': {'X': stat.S_IXOTH}
            }
        else:
            X_perms = {
                'u': {'X': 0},
                'g': {'X': 0},
                'o': {'X': 0}
            }

        user_perms_to_modes = {
            'u': {
                'r': stat.S_IRUSR,
                'w': stat.S_IWUSR,
                'x': stat.S_IXUSR,
                's': stat.S_ISUID,
                't': 0,
                'u': prev_mode & stat.S_IRWXU,
                'g': (prev_mode & stat.S_IRWXG) << 3,
                'o': (prev_mode & stat.S_IRWXO) << 6,
            },
            'g': {
                'r': stat.S_IRGRP,
                'w': stat.S_IWGRP,
                'x': stat.S_IXGRP,
                's': stat.S_ISGID,
                't': 0,
                'u': (prev_mode & stat.S_IRWXU) >> 3,
                'g': prev_mode & stat.S_IRWXG,
                'o': (prev_mode & stat.S_IRWXO) << 3,
            },
            'o': {
                'r': stat.S_IROTH,
                'w': stat.S_IWOTH,
                'x': stat.S_IXOTH,
                's': 0,
                't': stat.S_ISVTX,
                'u': (prev_mode & stat.S_IRWXU) >> 6,
                'g': (prev_mode & stat.S_IRWXG) >> 3,
                'o': prev_mode & stat.S_IRWXO,
            }
        }

        # Insert X_perms into user_perms_to_modes
        for key, value in X_perms.items():
            user_perms_to_modes[key].update(value)

        or_reduce = lambda mode, perm: mode | user_perms_to_modes[user][perm]
        return reduce(or_reduce, perms, 0)

    def _symbolic_mode_to_octal(self, path, symbolic_mode):
        new_mode = self.get_norm_permissions(path)
        mode_re = re.compile(r'^(?P<users>[ugoa]+)(?P<operator>[-+=])(?P<perms>[rwxXst-]*|[ugo])$')

        for mode in symbolic_mode.split(','):
            match = mode_re.match(mode)
            if match:
                users = match.group('users')
                operator = match.group('operator')
                perms = match.group('perms')

                if users == 'a':
                    users = 'ugo'

                for user in users:
                    mode_to_apply = self._get_octal_mode_from_symbolic_perms(path, user, perms)
                    new_mode = self._apply_operation_to_mode(user, operator, mode_to_apply, new_mode)
            else:
                raise ValueError("bad symbolic permission for mode: %s" % mode)
        return new_mode

    def hdfs_set_mode(self, path, mode):
        if mode is None:
            return False

        if not isinstance(mode, int):
            try:
                mode = int(mode, 8)
            except Exception:
                try:
                    mode = self._symbolic_mode_to_octal(path, mode)
                except Exception as e:
                    self.hdfs_fail_json(path=path,
                                        msg="mode must be in octal or symbolic form : %s " % mode,
                                        details=str(e))

                if mode != stat.S_IMODE(mode):
                    # prevent mode from having extra info orbeing invalid long number
                    self.hdfs_fail_json(path=path, msg="Invalid mode supplied, only permission info is allowed", details=mode)

        curr_mode = self.get_norm_permissions(path)

        if curr_mode != mode:
            try:
                # The hdfs setmode does not suport convertings ints to oct
                self.client.set_permission(path, int(oct(mode), 10))
            except HdfsError as e:
                self.hdfs_fail_json(path=path, msg="Hdfs error, set permissions failed: %s" % e)
            except Exception as e:
                self.hdfs_fail_json(path=path, msg="unknown error, set permissions failed: %s" % e)
            return True
        else:
            return False

    #################################################################################################################
    #                                         checksum functions
    #################################################################################################################

    def hdfs_digest_from_file(self, filename, algorithm):
        ''' Return hex digest of local file for a digest_method specified by name, or None if file is not present. '''

        status = self.hdfs_status(filename, strict=False)

        if status is None:
            return None
        if status['type'] == 'DIRECTORY':
            self.fail_json(msg="attempted to take checksum of directory: %s" % filename)

        # preserve old behaviour where the third parameter was a hash algorithm object
        if hasattr(algorithm, 'hexdigest'):
            digest_method = algorithm
        else:
            try:
                digest_method = AVAILABLE_HASH_ALGORITHMS[algorithm]()
            except KeyError:
                self.fail_json(msg="Could not hash file '%s' with algorithm '%s'. Available algorithms: %s" %
                                   (filename, algorithm, ', '.join(AVAILABLE_HASH_ALGORITHMS)))

        chunk_size = 64 * 1024

        for chunk in self.client.read_stream(filename, chunk_size=chunk_size):
            digest_method.update(chunk)

        return digest_method.hexdigest()

    def hdfs_md5(self, filename):
        if 'md5' not in AVAILABLE_HASH_ALGORITHMS:
            self.fail_json(msg="MD5 not available.  Possibly running in FIPS mode")
        return self.hdfs_digest_from_file(filename, 'md5')

    def hdfs_sha1(self, filename):
        ''' Return SHA1 hex digest of local file using digest_from_file(). '''
        return self.hdfs_digest_from_file(filename, 'sha1')

    def hdfs_sha256(self, filename):
        ''' Return SHA-256 hex digest of local file using digest_from_file(). '''
        return self.hdfs_digest_from_file(filename, 'sha256')

    #################################################################################################################
    #                                         Tocken functions
    #################################################################################################################

    def hdfs_get_token(self, renewer, kind=None, service=None):
        try:
            token = self.client.getDelegationToken(renewer=renewer, kind=kind, service=service)
        except HdfsError as e:
            self.hdfs_fail_json(msg="Hdfs error, create delegation token failed: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="Unknown error, create delegation token failed: %s" % e)
        return token['urlString']

    def hdfs_renew_token(self, tokenid, strict=True):
        try:
            expiration_date = self.client.renewDelegationToken(token=tokenid)
        except HdfsError as e:
            if e.message is None:
                if strict:
                    self.hdfs_fail_json(msg="Hdfs error, renew delegation token failed: token id %s is not a valid token." % tokenid)
                else:
                    return None
            else:
                self.hdfs_fail_json(msg="Hdfs error, renew delegation token failed: %s" % str(e))
        except Exception as e:
            self.hdfs_fail_json(msg="Unknown error, renew delegation token failed: %s" % e)
        return expiration_date

    def hdfs_cancel_token(self, tokenid, strict=True):
        try:
            self.client.cancelDelegationToken(token=tokenid)
        except HdfsError as e:
            if e.message is None:
                if strict:
                    self.hdfs_fail_json(msg="Hdfs error, cancel delegation token failed: token id %s is not a valid token." % tokenid)
                else:
                    return False
            else:
                self.hdfs_fail_json(msg="Hdfs error, cancel delegation token failed: %s" % str(e))
        except Exception as e:
            self.hdfs_fail_json(msg="Unknown error, cancel delegation token failed: %s" % e)
        return True

    #################################################################################################################
    #                                         SNAPSHOT functions
    #################################################################################################################

    def hdfs_create_snapshot(self, path, name):
        try:
            sspath = self.client.create_snapshot(hdfs_path=path, snapshotname=name)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not create snapshot on path %s : %s" % (path, e))
        return sspath

    def hdfs_delete_snapshot(self, path, name):
        try:
            self.client.delete_snapshot(hdfs_path=path, snapshotname=name)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not delete snapshot %s on path %s : %s" % (name, path, e))

    def hdfs_rename_snapshot(self, path, old_name, new_name):
        try:
            self.client.rename_snapshot(hdfs_path=path, oldsnapshotname=old_name, snapshotname=new_name)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not rename snapshot %s to %s on path %s : %s" % (old_name, new_name, path, e))

    def hdfs_list_snapshots(self, path):
        snapshots_path = self.hdfs_resolvepath(path) + "/.snapshot"
        if not self.hdfs_is_dir(snapshots_path):
            self.hdfs_fail_json(msg="error, hdfs path %s is not a valid snapshottable directory" % (path))
        try:
            res = self.client.list(hdfs_path=snapshots_path)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not list snapshots for path %s : %s" % (path, e))
        return res

    #################################################################################################################
    #                                         XATTRS functions
    #################################################################################################################

    def hdfs_getxattrs(self, path, key=None, strict=False):
        try:
            xattr = self.client.getxattrs(hdfs_path=path, key=key, strict=strict)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not fetch extended attribute on path %s : %s" % (path, e))
        return xattr

    def hdfs_listxattrs(self, path, strict=False):
        try:
            xattr = self.client.listxattrs(hdfs_path=path, strict=strict)
        except Exception as e:
            self.hdfs_fail_json(msg="error, could not fetch extended attribute keys for path %s : %s" % (path, e))
        return xattr

    def hdfs_setxattr(self, path, key, value, overwrite=True):
        changed = False

        current = self.hdfs_getxattrs(path=path, key=key)
        if current is None or key not in current or value != current[key]:
            try:
                xattr = self.client.setxattr(hdfs_path=path, key=key, value=value, overwrite=overwrite)
                changed = True
            except Exception as e:
                self.hdfs_fail_json(msg="error, could set extended attribute %s for path %s : %s" % (key, path, e))
        return changed

    def hdfs_rmxattr(self, path, key, strict=False):
        changed = False

        current = self.hdfs_getxattrs(path=path, key=key, strict=False)
        if current is not None and key in current:
            try:
                changed = self.client.removexattr(hdfs_path=path, key=key, strict=strict)
            except Exception as e:
                self.hdfs_fail_json(msg="error, could remove extended attribute %s for path %s : %s" % (key, path, e))
        return changed

    #################################################################################################################
    #                                         ACL functions
    #################################################################################################################

    def validate_acl_entries(self, entries):
        ''' check and normalize acl entries'''
        for entry in entries:
            p = re.compile("^(default:)?(user|group|mask|other):([A-Za-z_][A-Za-z0-9._-]*)?:([rwx-]{3})?$")
            m = p.match(entry)
            if not m:
                self.hdfs_fail_json(msg='Invalid acl entry %r.' % entry, changed=False)
        return True

    def compare_acl_entries(self, orig_entries, new_entries):
        equal = True
        for orig_ent in orig_entries:
            if orig_ent not in new_entries:
                return False
        # invert the loop
        for new_ent in new_entries:
            if new_ent not in orig_entries:
                return False
        return True

    def check_acl_entries_exist(self, orig_entries, new_entries):
        for new_ent in new_entries:
            if new_ent not in orig_entries:
                return False
        return True

    def hdfs_getacls(self, path, strict=False):
        entries = None
        try:
            raw_entries = self.client.getAclStatus(hdfs_path=path, strict=strict)
            entries = [entry for entry in raw_entries['entries']]
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, could not fetch file acls: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, could not fetch file acls: %s" % e)
        return entries

    def hdfs_remove_all_file_acl(self, path, strict=False):
        changed = False

        status = self.hdfs_status(path=path, strict=False)
        if status is None:
            return False

        try:
            orig_entries = self.hdfs_getacls(path=path, strict=strict)
            self.client.removeAcl(hdfs_path=path, strict=strict)
            self.client.removeDefaultAcl(hdfs_path=path, strict=strict)
            new_entries = self.hdfs_getacls(path=path, strict=strict)
            if not self.compare_acl_entries(orig_entries=orig_entries, new_entries=new_entries):
                changed = True
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, could not remove file acls: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, could not remove file acls: %s" % e)
        return changed

    def hdfs_remove_allacls(self, path, recursive=False, strict=False):
        # Fail if file does not exist
        status = self.hdfs_status(path=path, strict=strict)
        if status is None:
            return False

        changed = False
        changed |= self.hdfs_remove_all_file_acl(path=path, strict=False)
        if recursive:
            if status['type'] == 'DIRECTORY':
                for root, dirs, files in self.client.walk(path, depth=0, status=False):
                    for f in files + dirs:
                        fpath = os.path.join(root, f)
                        changed |= self.hdfs_remove_all_file_acl(path=fpath, strict=False)
        return changed

    def hdfs_remove_file_acl(self, path, entries, strict=False):
        changed = False

        status = self.hdfs_status(path=path, strict=False)
        if status is None:
            return False

        try:
            orig_entries = self.hdfs_getacls(path=path, strict=strict)
            raw_entries = ','.join(entries)
            self.client.removeAclEntries(hdfs_path=path, aclspec=raw_entries, strict=strict)
            new_entries = self.hdfs_getacls(path=path, strict=strict)
            if not self.compare_acl_entries(orig_entries=orig_entries, new_entries=new_entries):
                changed = True
        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, could not remove file acls: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, could not remove file acls: %s" % e)
        return changed

    def hdfs_remove_acls(self, path, entries, recursive=False, strict=False):
        # Validate and normalize acl entries
        self.validate_acl_entries(entries=entries)
        for entry in entries:
            entry_tab = entry.split(":")
            if entry_tab[0] != 'default' and entry_tab[1] == "":
                self.hdfs_fail_json(msg="Invalid ACLs entry %r the user, group, other and mask base entries are required" % entry, changed=False)
            if (entry_tab[0] != 'default' and entry_tab[2] != "") or (entry_tab[0] == 'default' and entry_tab[3] != ""):
                self.hdfs_fail_json(msg="Invalid ACLs entry %r the permission need to be null in delete." % entry, changed=False)

        # Fail if file does not exist
        status = self.hdfs_status(path=path, strict=strict)
        if status is None:
            return False

        changed = False

        changed |= self.hdfs_remove_file_acl(path=path, entries=entries, strict=False)
        if recursive:
            if status['type'] == 'DIRECTORY':
                for root, dirs, files in self.client.walk(path, depth=0, status=False):
                    for f in files + dirs:
                        fpath = os.path.join(root, f)
                        changed |= self.hdfs_remove_file_acl(path=fpath, entries=entries, strict=False)
        return changed

    def hdfs_add_file_acl(self, path, entries, strict=False):
        changed = False

        status = self.hdfs_status(path=path, strict=False)
        if status is None:
            return False
        elif status['type'] == 'FILE':
            proc_entries = []
            for entry in entries:
                entry_tab = entry.split(":")
                if entry_tab[0] != 'default':
                    proc_entries.append(entry)
            entries = proc_entries
        # if directory keep it as it is

        try:
            orig_entries = self.hdfs_getacls(path=path, strict=strict)

            raw_entries = ','.join(entries)
            self.client.modifyAclEntries(hdfs_path=path, aclspec=raw_entries)

            # It looks like the getacls does not print all acls, so we can really know if the acls
            # we are going to put really change something or not. so the only way is to always run
            # then perform the check, so that we know if something have changed or not.
            new_entries = self.hdfs_getacls(path=path, strict=strict)
            if not self.compare_acl_entries(orig_entries=orig_entries, new_entries=new_entries):
                changed = True

        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, could not add file acls: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, could not add file acls: %s" % e)
        return changed

    def hdfs_addacls(self, path, entries, recursive=False, strict=False):
        # Fail if file does not exist
        status = self.hdfs_status(path=path, strict=strict)
        if status is None:
            return False

        changed = False
        changed |= self.hdfs_add_file_acl(path=path, entries=entries, strict=False)
        if recursive:
            if status['type'] == 'DIRECTORY':
                for root, dirs, files in self.client.walk(path, depth=0, status=False):
                    for f in files + dirs:
                        fpath = os.path.join(root, f)
                        changed |= self.hdfs_add_file_acl(path=fpath, entries=entries, strict=False)
        return changed

    def hdfs_set_file_acl(self, path, entries, strict=False):
        changed = False

        status = self.hdfs_status(path=path, strict=False)
        if status is None:
            return False
        elif status['type'] == 'FILE':
            proc_entries = []
            for entry in entries:
                entry_tab = entry.split(":")
                if entry_tab[0] != 'default':
                    proc_entries.append(entry)
            entries = proc_entries
        # if directory keep it as it is

        try:
            orig_entries = self.hdfs_getacls(path=path, strict=strict)

            raw_entries = ','.join(entries)
            self.client.setAcl(hdfs_path=path, aclspec=raw_entries)

            new_entries = self.hdfs_getacls(path=path, strict=strict)
            if not self.compare_acl_entries(orig_entries=orig_entries, new_entries=new_entries):
                changed = True

        except HdfsError as e:
            self.hdfs_fail_json(msg="hdfs error, could not set file acls: %s" % e)
        except Exception as e:
            self.hdfs_fail_json(msg="unknown error, could not set file acls: %s" % e)
        return changed

    def hdfs_setacls(self, path, entries, recursive=False, strict=False):
        # check that entries for user, group, and others are provided
        u_valid = False
        g_valid = False
        o_valid = False
        for entry in entries:
            entry_tab = entry.split(":")
            if entry_tab[0] == 'user' and entry_tab[1] == "" and entry_tab[2] != "":
                u_valid = True
            if entry_tab[0] == 'group' and entry_tab[1] == "" and entry_tab[2] != "":
                g_valid = True
            if entry_tab[0] == 'other' and entry_tab[1] == "" and entry_tab[2] != "":
                o_valid = True
        if not g_valid or not u_valid or not o_valid:
            self.hdfs_fail_json(msg="Invalid ACLs the user, group and other entries are required")

        # Fail if file does not exist
        status = self.hdfs_status(path=path, strict=strict)
        if status is None:
            return False

        changed = False
        changed |= self.hdfs_set_file_acl(path=path, entries=entries, strict=False)
        if recursive:
            if status['type'] == 'DIRECTORY':
                for root, dirs, files in self.client.walk(path, depth=0, status=False):
                    for f in files + dirs:
                        fpath = os.path.join(root, f)
                        changed |= self.hdfs_set_file_acl(path=fpath, entries=entries, strict=False)
        return changed
