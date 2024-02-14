# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

from __future__ import annotations

import asyncio
import os
import tempfile
from subprocess import Popen, PIPE
import tarfile

import ansible.constants as C
from ansible import context
from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.text.converters import to_text, to_native


display = Display()


def scm_archive_collection(src, name=None, version='HEAD'):
    return scm_archive_resource(src, scm='git', name=name, version=version, keep_scm_meta=False)


def _scm_archive_resource_scm_path(src, scm='git'):
    if scm not in ['hg', 'git']:
        raise AnsibleError("- scm %s is not currently supported" % scm)

    try:
        scm_path = get_bin_path(scm)
    except (ValueError, OSError, IOError):
        raise AnsibleError("could not find/use %s, it is required to continue with installing %s" % (scm, src))

    return scm_path


def _scm_archive_resource_clone_args(src, scm='git', name=None):
    clone_args = ['clone']

    # Add specific options for ignoring certificates if requested
    ignore_certs = context.CLIARGS['ignore_certs']

    if ignore_certs:
        if scm == 'git':
            clone_args.extend(['-c', 'http.sslVerify=false'])
        elif scm == 'hg':
            clone_args.append('--insecure')

    clone_args.extend([src, name])

    return clone_args


def _scm_archive_resource_checkout_args(scm='git', version='HEAD'):
    if scm == 'git' and version:
        checkout_args = ['checkout', to_text(version)]
    else:
        checkout_args = None

    return checkout_args


def _scm_archive_resource_archive_args(tempdir, temp_file, scm='git', name=None, version='HEAD', keep_scm_meta=False):
    archive_args = None
    if keep_scm_meta:
        display.vvv('tarring %s from %s to %s' % (name, tempdir, temp_file.name))
        with tarfile.open(temp_file.name, "w") as tar:
            tar.add(os.path.join(tempdir, name), arcname=name)
    elif scm == 'hg':
        archive_args = ['archive', '--prefix', "%s/" % name]
        if version:
            archive_args.extend(['-r', version])
        archive_args.append(temp_file.name)
    elif scm == 'git':
        archive_args = ['archive', '--prefix=%s/' % name, '--output=%s' % temp_file.name]
        if version:
            archive_args.append(version)
        else:
            archive_args.append('HEAD')

    return archive_args


def scm_archive_resource(src, scm='git', name=None, version='HEAD', keep_scm_meta=False):

    def run_scm_cmd(program, args, tempdir):
        cmd = [program] + args
        try:
            stdout = ''
            stderr = ''
            popen = Popen(cmd, cwd=tempdir, stdout=PIPE, stderr=PIPE)
            stdout, stderr = popen.communicate()
        except Exception as e:
            ran = " ".join(cmd)
            display.debug("ran %s:" % ran)
            raise AnsibleError("when executing %s: %s" % (ran, to_native(e)))
        if popen.returncode != 0:
            raise AnsibleError("- command %s failed in directory %s (rc=%s) - %s" % (' '.join(cmd), tempdir, popen.returncode, to_native(stderr)))

    scm_path = _scm_archive_resource_scm_path(src, scm)

    tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    clone_args = _scm_archive_resource_clone_args(src, scm, name)

    run_scm_cmd(scm_path, clone_args, tempdir)

    checkout_args = _scm_archive_resource_checkout_args(scm, version)
    if checkout_args is not None:
        run_scm_cmd(scm_path, checkout_args, os.path.join(tempdir, name))

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar', dir=C.DEFAULT_LOCAL_TMP)

    archive_args = _scm_archive_resource_archive_args(tempdir, temp_file, scm, name, version, keep_scm_meta)
    if archive_args is not None:
        display.vvv('archiving %s' % archive_args)
        run_scm_cmd(scm_path, archive_args, os.path.join(tempdir, name))

    return temp_file.name


async def scm_archive_resource_async(src, scm='git', name=None, version='HEAD', keep_scm_meta=False):

    async def run_scm_cmd_async(program, args, tempdir):
        try:
            stdout = ''
            stderr = ''
            original_cwd = os.getcwd()
            os.chdir(tempdir)
            subproces = await asyncio.create_subprocess_exec(program, *args, stdout=PIPE, stderr=PIPE)
            stdout, stderr = await subproces.communicate()
            os.chdir(original_cwd)
        except Exception as e:
            ran = " ".join([program] + args)
            display.debug("ran %s:" % ran)
            raise AnsibleError("when executing %s: %s" % (ran, to_native(e)))
        if subproces.returncode != 0:
            raise AnsibleError("- command %s failed in directory %s (rc=%s) - %s"
                               % (' '.join([program] + args), tempdir, subproces.returncode, to_native(stderr)))

    scm_path = _scm_archive_resource_scm_path(src, scm)

    tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    clone_args = _scm_archive_resource_clone_args(src, scm, name)

    await run_scm_cmd_async(scm_path, clone_args, tempdir)

    checkout_args = _scm_archive_resource_checkout_args(scm, version)
    if checkout_args is not None:
        await run_scm_cmd_async(scm_path, checkout_args, os.path.join(tempdir, name))

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar', dir=C.DEFAULT_LOCAL_TMP)

    archive_args = _scm_archive_resource_archive_args(tempdir, temp_file, scm, name, version, keep_scm_meta)
    if archive_args is not None:
        display.vvv('archiving %s' % archive_args)
        await run_scm_cmd_async(scm_path, archive_args, os.path.join(tempdir, name))

    return temp_file.name
