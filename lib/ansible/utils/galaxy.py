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


def scm_archive_resource(src, scm='git', name=None, version='HEAD', keep_scm_meta=False):

    def run_scm_cmd(cmd, tempdir):
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

    if scm not in ['hg', 'git']:
        raise AnsibleError("- scm %s is not currently supported" % scm)

    try:
        scm_path = get_bin_path(scm)
    except (ValueError, OSError, IOError):
        raise AnsibleError("could not find/use %s, it is required to continue with installing %s" % (scm, src))

    tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    clone_cmd = [scm_path, 'clone']

    # Add specific options for ignoring certificates if requested
    ignore_certs = context.CLIARGS['ignore_certs'] or C.GALAXY_IGNORE_CERTS

    if ignore_certs:
        if scm == 'git':
            clone_cmd.extend(['-c', 'http.sslVerify=false'])
        elif scm == 'hg':
            clone_cmd.append('--insecure')

    clone_cmd.extend([src, name])

    run_scm_cmd(clone_cmd, tempdir)

    if scm == 'git' and version:
        checkout_cmd = [scm_path, 'checkout', to_text(version)]
        run_scm_cmd(checkout_cmd, os.path.join(tempdir, name))

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar', dir=C.DEFAULT_LOCAL_TMP)
    archive_cmd = None
    if keep_scm_meta:
        display.vvv('tarring %s from %s to %s' % (name, tempdir, temp_file.name))
        with tarfile.open(temp_file.name, "w") as tar:
            tar.add(os.path.join(tempdir, name), arcname=name)
    elif scm == 'hg':
        archive_cmd = [scm_path, 'archive', '--prefix', "%s/" % name]
        if version:
            archive_cmd.extend(['-r', version])
        archive_cmd.append(temp_file.name)
    elif scm == 'git':
        archive_cmd = [scm_path, 'archive', '--prefix=%s/' % name, '--output=%s' % temp_file.name]
        if version:
            archive_cmd.append(version)
        else:
            archive_cmd.append('HEAD')

    if archive_cmd is not None:
        display.vvv('archiving %s' % archive_cmd)
        run_scm_cmd(archive_cmd, os.path.join(tempdir, name))

    return temp_file.name
