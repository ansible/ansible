# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: git
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
version_added: "0.0.1"
short_description: Deploy software (or files) from git checkouts
description:
    - Manage I(git) checkouts of repositories to deploy files or software.
extends_documentation_fragment: action_common_attributes
options:
    repo:
        description:
            - git, SSH, or HTTP(S) protocol address of the git repository.
        type: str
        required: true
        aliases: [ name ]
    dest:
        description:
            - The path of where the repository should be checked out. This
              is equivalent to C(git clone [repo_url] [directory]). The repository
              named in O(repo) is not appended to this path and the destination directory must be empty. This
              parameter is required, unless O(clone) is set to V(false).
        type: path
        required: true
    version:
        description:
            - What version of the repository to check out. This can be
              the literal string V(HEAD), a branch name, a tag name.
              It can also be a I(SHA-1) hash, in which case O(refspec) needs
              to be specified if the given revision is not already available.
        type: str
        default: "HEAD"
    accept_hostkey:
        description:
            - Will ensure or not that C(-o StrictHostKeyChecking=no) is present as an ssh option.
            - Be aware that this disables a protection against MITM attacks.
            - Those using OpenSSH >= 7.5 might want to use O(accept_newhostkey) or set O(ssh_opts) to V(StrictHostKeyChecking=accept-new)
              instead, it does not remove the MITM issue but it does restrict it to the first attempt.
        type: bool
        default: 'no'
        version_added: "1.5"
    accept_newhostkey:
        description:
            - As of OpenSSH 7.5, C(-o StrictHostKeyChecking=accept-new) can be
              used which is safer and will only accepts host keys which are
              not present or are the same. If V(true), ensure that
              C(-o StrictHostKeyChecking=accept-new) is present as an ssh option.
        type: bool
        default: 'no'
        version_added: "2.12"
    ssh_opts:
        description:
            - Options git will pass to ssh when used as protocol, it works via C(git)'s
              E(GIT_SSH)/E(GIT_SSH_COMMAND) environment variables.
            - For older versions it appends E(GIT_SSH_OPTS) (specific to this module) to the
              variables above or via a wrapper script.
            - Other options can add to this list, like O(key_file) and O(accept_hostkey).
            - An example value could be C(-o StrictHostKeyChecking=no) (although this particular
              option is better set by O(accept_hostkey)).
            - The module ensures that C(BatchMode=yes) is always present to avoid prompts.
        type: str
        version_added: "1.5"

    key_file:
        description:
            - Specify an optional private key file path, on the target host, to use for the checkout.
            - This ensures C(IdentitiesOnly=yes) is present in O(ssh_opts).
        type: path
        version_added: "1.5"
    reference:
        description:
            - Reference repository (see C(git clone --reference ...)).
        type: str
        version_added: "1.4"
    remote:
        description:
            - Name of the remote.
        type: str
        default: "origin"
    refspec:
        description:
            - Add an additional refspec to be fetched.
              If version is set to a I(SHA-1) not reachable from any branch
              or tag, this option may be necessary to specify the ref containing
              the I(SHA-1).
              Uses the same syntax as the C(git fetch) command.
              An example value could be "refs/meta/config".
        type: str
        version_added: "1.9"
    force:
        description:
            - If V(true), any modified files in the working
              repository will be discarded.  Prior to 0.7, this was always
              V(true) and could not be disabled.  Prior to 1.9, the default was
              V(true).
        type: bool
        default: 'no'
        version_added: "0.7"
    depth:
        description:
            - Create a shallow clone with a history truncated to the specified
              number or revisions. The minimum possible value is V(1), otherwise
              ignored. Needs I(git>=1.9.1) to work correctly.
        type: int
        version_added: "1.2"
    clone:
        description:
            - If V(false), do not clone the repository even if it does not exist locally.
        type: bool
        default: 'yes'
        version_added: "1.9"
    update:
        description:
            - If V(false), do not retrieve new revisions from the origin repository.
            - Operations like archive will work on the existing (old) repository and might
              not respond to changes to the options version or remote.
        type: bool
        default: 'yes'
        version_added: "1.2"
    executable:
        description:
            - Path to git executable to use. If not supplied,
              the normal mechanism for resolving binary paths will be used.
        type: path
        version_added: "1.4"
    bare:
        description:
            - If V(true), repository will be created as a bare repo, otherwise
              it will be a standard repo with a workspace.
        type: bool
        default: 'no'
        version_added: "1.4"
    umask:
        description:
            - The umask to set before doing any checkouts, or any other
              repository maintenance.
        type: raw
        version_added: "2.2"

    recursive:
        description:
            - If V(false), repository will be cloned without the C(--recursive)
              option, skipping sub-modules.
        type: bool
        default: 'yes'
        version_added: "1.6"

    single_branch:
        description:
            - Clone only the history leading to the tip of the specified revision.
        type: bool
        default: 'no'
        version_added: '2.11'

    track_submodules:
        description:
            - If V(true), submodules will track the latest commit on their
              master branch (or other branch specified in C(.gitmodules)).  If
              V(false), submodules will be kept at the revision specified by the
              main project. This is equivalent to specifying the C(--remote) flag
              to git submodule update.
        type: bool
        default: 'no'
        version_added: "1.8"

    verify_commit:
        description:
            - If V(true), when cloning or checking out a O(version) verify the
              signature of a GPG signed commit. This requires git version>=2.1.0
              to be installed. The commit MUST be signed and the public key MUST
              be present in the GPG keyring.
        type: bool
        default: 'no'
        version_added: "2.0"

    archive:
        description:
            - Specify archive file path with extension. If specified, creates an
              archive file of the specified format containing the tree structure
              for the source tree.
              Allowed archive formats ["zip", "tar.gz", "tar", "tgz"].
            - This will clone and perform git archive from local directory as not
              all git servers support git archive.
        type: path
        version_added: "2.4"

    archive_prefix:
        description:
            - Specify a prefix to add to each file path in archive. Requires O(archive) to be specified.
        version_added: "2.10"
        type: str

    separate_git_dir:
        description:
            - The path to place the cloned repository. If specified, Git repository
              can be separated from working tree.
        type: path
        version_added: "2.7"

    gpg_allowlist:
        description:
           - A list of trusted GPG fingerprints to compare to the fingerprint of the
             GPG-signed commit.
           - Only used when O(verify_commit=yes).
           - Use of this feature requires Git 2.6+ due to its reliance on git's C(--raw) flag to C(verify-commit) and C(verify-tag).
           - Alias O(gpg_allowlist) is added in version 2.17.
           - Alias O(gpg_whitelist) is deprecated and will be removed in version 2.21.
        type: list
        elements: str
        default: []
        aliases: [ gpg_whitelist ]
        version_added: "2.9"

requirements:
    - git>=1.7.1 (the command line tool)
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        platforms: posix
notes:
    - "If the task seems to be hanging, first verify remote host is in C(known_hosts).
      SSH will prompt user to authorize the first contact with a remote host.  To avoid this prompt,
      one solution is to use the option accept_hostkey. Another solution is to
      add the remote host public key in C(/etc/ssh/ssh_known_hosts) before calling
      the git module, with the following command: C(ssh-keyscan -H remote_host.com >> /etc/ssh/ssh_known_hosts)."
"""

EXAMPLES = """
- name: Git checkout
  ansible.builtin.git:
    repo: 'https://github.com/ansible/ansible.git'
    dest: /tmp/checkout
    version: release-0.22

- name: Read-write git checkout from github
  ansible.builtin.git:
    repo: git@github.com:ansible/ansible.git
    dest: /tmp/checkout

- name: Just ensuring the repo checkout exists
  ansible.builtin.git:
    repo: 'https://github.com/ansible/ansible.git'
    dest: /tmp/checkout
    update: no

- name: Just get information about the repository whether or not it has already been cloned locally
  ansible.builtin.git:
    repo: git@github.com:ansible/ansible.git
    dest: /tmp/checkout
    clone: no
    update: no

- name: Checkout a github repo and use refspec to fetch all pull requests
  ansible.builtin.git:
    repo: 'https://github.com/ansible/ansible.git'
    dest: /tmp/checkout
    refspec: '+refs/pull/*:refs/heads/*'

- name: Create git archive from repo
  ansible.builtin.git:
    repo: git@github.com:ansible/ansible.git
    dest: /tmp/checkout
    archive: /tmp/ansible.zip

- name: Clone a repo with separate git directory
  ansible.builtin.git:
    repo: 'https://github.com/ansible/ansible.git'
    dest: /tmp/checkout
    separate_git_dir: /tmp/repo

- name: Example clone of a single branch
  ansible.builtin.git:
    repo: git@github.com:ansible/ansible.git
    dest: /tmp/checkout
    single_branch: yes
    version: master

- name: Avoid hanging when http(s) password is missing
  ansible.builtin.git:
    repo: 'https://github.com/ansible/ansible.git'
    dest: /tmp/checkout
  environment:
    GIT_TERMINAL_PROMPT: 0 # reports "terminal prompts disabled" on missing password
    # or GIT_ASKPASS: /bin/true # for git before version 2.3.0, reports "Authentication failed" on missing password
"""

RETURN = """
after:
    description: Last commit revision of the repository retrieved during the update.
    returned: success
    type: str
    sample: 4c020102a9cd6fe908c9a4a326a38f972f63a903
before:
    description: Commit revision before the repository was updated, "null" for new repository.
    returned: success
    type: str
    sample: 67c04ebe40a003bda0efb34eacfb93b0cafdf628
remote_url_changed:
    description: Contains True or False whether or not the remote URL was changed.
    returned: success
    type: bool
    sample: True
warnings:
    description: List of warnings if requested features were not available due to a too old git version.
    returned: error
    type: str
    sample: git version is too old to fully support the depth argument. Falling back to full checkouts.
git_dir_now:
    description: Contains the new path of .git directory if it is changed.
    returned: success
    type: str
    sample: /path/to/new/git/dir
git_dir_before:
    description: Contains the original path of .git directory if it is changed.
    returned: success
    type: str
    sample: /path/to/old/git/dir
"""

import filecmp
import os
import re
import shlex
import stat
import sys
import shutil
import tempfile
from ansible.module_utils.compat.version import LooseVersion

from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.six import b, string_types


def relocate_repo(module, result, repo_dir, old_repo_dir, worktree_dir):
    if os.path.exists(repo_dir):
        module.fail_json(msg='Separate-git-dir path %s already exists.' % repo_dir)
    if worktree_dir:
        dot_git_file_path = os.path.join(worktree_dir, '.git')
        try:
            shutil.move(old_repo_dir, repo_dir)
            with open(dot_git_file_path, 'w') as dot_git_file:
                dot_git_file.write('gitdir: %s' % repo_dir)
            result['git_dir_before'] = old_repo_dir
            result['git_dir_now'] = repo_dir
        except (IOError, OSError) as err:
            # if we already moved the .git dir, roll it back
            if os.path.exists(repo_dir):
                shutil.move(repo_dir, old_repo_dir)
            module.fail_json(msg=u'Unable to move git dir. %s' % to_text(err))


def head_splitter(headfile, remote, module=None, fail_on_error=False):
    """Extract the head reference"""
    # https://github.com/ansible/ansible-modules-core/pull/907

    res = None
    if os.path.exists(headfile):
        rawdata = None
        try:
            with open(headfile, 'r') as f:
                rawdata = f.readline()
        except Exception:
            if fail_on_error and module:
                module.fail_json(msg="Unable to read %s" % headfile)
        if rawdata:
            try:
                rawdata = rawdata.replace('refs/remotes/%s' % remote, '', 1)
                refparts = rawdata.split(' ')
                newref = refparts[-1]
                nrefparts = newref.split('/', 2)
                res = nrefparts[-1].rstrip('\n')
            except Exception:
                if fail_on_error and module:
                    module.fail_json(msg="Unable to split head from '%s'" % rawdata)
    return res


def unfrackgitpath(path):
    if path is None:
        return None

    # copied from ansible.utils.path
    return os.path.normpath(os.path.realpath(os.path.expanduser(os.path.expandvars(path))))


def get_submodule_update_params(module, git_path, cwd):
    # or: git submodule [--quiet] update [--init] [-N|--no-fetch]
    # [-f|--force] [--rebase] [--reference <repository>] [--merge]
    # [--recursive] [--] [<path>...]

    params = []

    # run a bad submodule command to get valid params
    cmd = "%s submodule update --help" % (git_path)
    rc, stdout, stderr = module.run_command(cmd, cwd=cwd)
    lines = stderr.split('\n')
    update_line = None
    for line in lines:
        if 'git submodule [--quiet] update ' in line:
            update_line = line
    if update_line:
        update_line = update_line.replace('[', '')
        update_line = update_line.replace(']', '')
        update_line = update_line.replace('|', ' ')
        parts = shlex.split(update_line)
        for part in parts:
            if part.startswith('--'):
                part = part.replace('--', '')
                params.append(part)

    return params


def write_ssh_wrapper(module):
    """
        This writes an shell wrapper for ssh options to be used with git
        this is only relevant for older versions of gitthat cannot
        handle the options themselves. Returns path to the script
    """
    try:
        # make sure we have full permission to the module_dir, which
        # may not be the case if we're sudo'ing to a non-root user
        if os.access(module.tmpdir, os.W_OK | os.R_OK | os.X_OK):
            fd, wrapper_path = tempfile.mkstemp(prefix=module.tmpdir + '/')
        else:
            raise OSError
    except (IOError, OSError):
        fd, wrapper_path = tempfile.mkstemp()

    # use existing git_ssh/ssh_command, fallback to 'ssh'
    template = b("""#!/bin/sh
%s $GIT_SSH_OPTS "$@"
""" % os.environ.get('GIT_SSH', os.environ.get('GIT_SSH_COMMAND', 'ssh')))

    # write it
    with os.fdopen(fd, 'w+b') as fh:
        fh.write(template)

    # set execute
    st = os.stat(wrapper_path)
    os.chmod(wrapper_path, st.st_mode | stat.S_IEXEC)

    module.debug('Wrote temp git ssh wrapper (%s): %s' % (wrapper_path, template))

    # ensure we cleanup after ourselves
    module.add_cleanup_file(path=wrapper_path)

    return wrapper_path


def set_git_ssh_env(key_file, ssh_opts, git_version, module):
    """
        use environment variables to configure git's ssh execution,
        which varies by version but this function should handle all.
    """

    # initialise to existing ssh opts and/or append user provided
    if ssh_opts is None:
        ssh_opts = os.environ.get('GIT_SSH_OPTS', '')
    else:
        ssh_opts = os.environ.get('GIT_SSH_OPTS', '') + ' ' + ssh_opts

    # hostkey acceptance
    accept_key = "StrictHostKeyChecking=no"
    if module.params['accept_hostkey'] and accept_key not in ssh_opts:
        ssh_opts += " -o %s" % accept_key

    # avoid prompts
    force_batch = 'BatchMode=yes'
    if force_batch not in ssh_opts:
        ssh_opts += ' -o %s' % (force_batch)

    # deal with key file
    if key_file:
        key_opt = '-i %s' % key_file
        if key_opt not in ssh_opts:
            ssh_opts += '  %s' % key_opt

        ikey = 'IdentitiesOnly=yes'
        if ikey not in ssh_opts:
            ssh_opts += ' -o %s' % ikey

    # older than 2.3 does not know how to use git_ssh_command,
    # so we force it into get_ssh var
    # https://github.com/gitster/git/commit/09d60d785c68c8fa65094ecbe46fbc2a38d0fc1f
    if git_version is not None and git_version < LooseVersion('2.3.0'):
        # for use in wrapper
        os.environ["GIT_SSH_OPTS"] = ssh_opts

        # these versions don't support GIT_SSH_OPTS so have to write wrapper
        wrapper = write_ssh_wrapper(module)

        # force use of git_ssh_opts via wrapper, git_ssh cannot not handle arguments
        os.environ['GIT_SSH'] = wrapper
    else:
        # we construct full finalized command string here
        full_cmd = os.environ.get('GIT_SSH', os.environ.get('GIT_SSH_COMMAND', 'ssh'))
        if ssh_opts:
            full_cmd += ' ' + ssh_opts
        # git_ssh_command can handle arguments to ssh
        os.environ["GIT_SSH_COMMAND"] = full_cmd


def get_version(module, git_path, dest, ref="HEAD"):
    """ samples the version of the git repo """

    cmd = "%s rev-parse %s" % (git_path, ref)
    rc, stdout, stderr = module.run_command(cmd, cwd=dest)
    sha = to_native(stdout).rstrip('\n')
    return sha


def ssh_supports_acceptnewhostkey(module):
    try:
        ssh_path = get_bin_path('ssh')
    except ValueError as err:
        module.fail_json(
            msg='Remote host is missing ssh command, so you cannot '
            'use acceptnewhostkey option.', details=to_text(err))
    supports_acceptnewhostkey = True
    cmd = [ssh_path, '-o', 'StrictHostKeyChecking=accept-new', '-V']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        supports_acceptnewhostkey = False
    return supports_acceptnewhostkey


def get_submodule_versions(git_path, module, dest, version='HEAD'):
    cmd = [git_path, 'submodule', 'foreach', git_path, 'rev-parse', version]
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(
            msg='Unable to determine hashes of submodules',
            stdout=out,
            stderr=err,
            rc=rc)
    submodules = {}
    subm_name = None
    for line in out.splitlines():
        if line.startswith("Entering '"):
            subm_name = line[10:-1]
        elif len(line.strip()) == 40:
            if subm_name is None:
                module.fail_json()
            submodules[subm_name] = line.strip()
            subm_name = None
        else:
            module.fail_json(msg='Unable to parse submodule hash line: %s' % line.strip())
    if subm_name is not None:
        module.fail_json(msg='Unable to find hash for submodule: %s' % subm_name)

    return submodules


def clone(git_path, module, repo, dest, remote, depth, version, bare,
          reference, refspec, git_version_used, verify_commit, separate_git_dir, result, gpg_allowlist, single_branch):
    """ makes a new git repo if it does not already exist """
    dest_dirname = os.path.dirname(dest)
    try:
        os.makedirs(dest_dirname)
    except Exception:
        pass
    cmd = [git_path, 'clone']

    if bare:
        cmd.append('--bare')
    else:
        cmd.extend(['--origin', remote])

    is_branch_or_tag = is_remote_branch(git_path, module, dest, repo, version) or is_remote_tag(git_path, module, dest, repo, version)
    if depth:
        if version == 'HEAD' or refspec:
            cmd.extend(['--depth', str(depth)])
        elif is_branch_or_tag:
            cmd.extend(['--depth', str(depth)])
            cmd.extend(['--branch', version])
        else:
            # only use depth if the remote object is branch or tag (i.e. fetchable)
            module.warn("Ignoring depth argument. "
                        "Shallow clones are only available for "
                        "HEAD, branches, tags or in combination with refspec.")
    if reference:
        cmd.extend(['--reference', str(reference)])

    if single_branch:
        if git_version_used is None:
            module.fail_json(msg='Cannot find git executable at %s' % git_path)

        if git_version_used < LooseVersion('1.7.10'):
            module.warn("git version '%s' is too old to use 'single-branch'. Ignoring." % git_version_used)
        else:
            cmd.append("--single-branch")

            if is_branch_or_tag:
                cmd.extend(['--branch', version])

    needs_separate_git_dir_fallback = False
    if separate_git_dir:
        if git_version_used is None:
            module.fail_json(msg='Cannot find git executable at %s' % git_path)
        if git_version_used < LooseVersion('1.7.5'):
            # git before 1.7.5 doesn't have separate-git-dir argument, do fallback
            needs_separate_git_dir_fallback = True
        else:
            cmd.append('--separate-git-dir=%s' % separate_git_dir)

    cmd.extend([repo, dest])
    module.run_command(cmd, check_rc=True, cwd=dest_dirname)
    if needs_separate_git_dir_fallback:
        relocate_repo(module, result, separate_git_dir, os.path.join(dest, ".git"), dest)

    if bare and remote != 'origin':
        module.run_command([git_path, 'remote', 'add', remote, repo], check_rc=True, cwd=dest)

    if refspec:
        cmd = [git_path, 'fetch']
        if depth:
            cmd.extend(['--depth', str(depth)])
        cmd.extend([remote, refspec])
        module.run_command(cmd, check_rc=True, cwd=dest)

    if verify_commit:
        verify_commit_sign(git_path, module, dest, version, gpg_allowlist)


def has_local_mods(module, git_path, dest, bare):
    if bare:
        return False

    cmd = "%s status --porcelain" % (git_path)
    rc, stdout, stderr = module.run_command(cmd, cwd=dest)
    lines = stdout.splitlines()
    lines = list(filter(lambda c: not re.search('^\\?\\?.*$', c), lines))

    return len(lines) > 0


def reset(git_path, module, dest):
    """
    Resets the index and working tree to HEAD.
    Discards any changes to tracked files in working
    tree since that commit.
    """
    cmd = "%s reset --hard HEAD" % (git_path,)
    return module.run_command(cmd, check_rc=True, cwd=dest)


def get_diff(module, git_path, dest, repo, remote, depth, bare, before, after):
    """ Return the difference between 2 versions """
    if before is None:
        return {'prepared': '>> Newly checked out %s' % after}
    elif before != after:
        # Ensure we have the object we are referring to during git diff !
        git_version_used = git_version(git_path, module)
        fetch(git_path, module, repo, dest, after, remote, depth, bare, '', git_version_used)
        cmd = '%s diff %s %s' % (git_path, before, after)
        (rc, out, err) = module.run_command(cmd, cwd=dest)
        if rc == 0 and out:
            return {'prepared': out}
        elif rc == 0:
            return {'prepared': '>> No visual differences between %s and %s' % (before, after)}
        elif err:
            return {'prepared': '>> Failed to get proper diff between %s and %s:\n>> %s' % (before, after, err)}
        else:
            return {'prepared': '>> Failed to get proper diff between %s and %s' % (before, after)}
    return {}


def get_remote_head(git_path, module, dest, version, remote, bare):
    cloning = False
    cwd = None
    tag = False
    if remote == module.params['repo']:
        cloning = True
    elif remote == 'file://' + os.path.expanduser(module.params['repo']):
        cloning = True
    else:
        cwd = dest
    if version == 'HEAD':
        if cloning:
            # cloning the repo, just get the remote's HEAD version
            cmd = '%s ls-remote %s -h HEAD' % (git_path, remote)
        else:
            head_branch = get_head_branch(git_path, module, dest, remote, bare)
            cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, head_branch)
    elif is_remote_branch(git_path, module, dest, remote, version):
        cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, version)
    elif is_remote_tag(git_path, module, dest, remote, version):
        tag = True
        cmd = '%s ls-remote %s -t refs/tags/%s*' % (git_path, remote, version)
    else:
        # appears to be a sha1.  return as-is since it appears
        # cannot check for a specific sha1 on remote
        return version
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=cwd)
    if len(out) < 1:
        module.fail_json(msg="Could not determine remote revision for %s" % version, stdout=out, stderr=err, rc=rc)

    out = to_native(out)

    if tag:
        # Find the dereferenced tag if this is an annotated tag.
        for tag in out.split('\n'):
            if tag.endswith(version + '^{}'):
                out = tag
                break
            elif tag.endswith(version):
                out = tag

    rev = out.split()[0]
    return rev


def is_remote_tag(git_path, module, dest, remote, version):
    cmd = '%s ls-remote %s -t refs/tags/%s' % (git_path, remote, version)
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
    if to_native(version, errors='surrogate_or_strict') in out:
        return True
    else:
        return False


def get_branches(git_path, module, dest):
    branches = []
    cmd = '%s branch --no-color -a' % (git_path,)
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Could not determine branch data - received %s" % out, stdout=out, stderr=err)
    for line in out.split('\n'):
        if line.strip():
            branches.append(line.strip())
    return branches


def get_annotated_tags(git_path, module, dest):
    tags = []
    cmd = [git_path, 'for-each-ref', 'refs/tags/', '--format', '%(objecttype):%(refname:short)']
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Could not determine tag data - received %s" % out, stdout=out, stderr=err)
    for line in to_native(out).split('\n'):
        if line.strip():
            tagtype, tagname = line.strip().split(':')
            if tagtype == 'tag':
                tags.append(tagname)
    return tags


def is_remote_branch(git_path, module, dest, remote, version):
    cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, version)
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
    if to_native(version, errors='surrogate_or_strict') in out:
        return True
    else:
        return False


def is_local_branch(git_path, module, dest, branch):
    branches = get_branches(git_path, module, dest)
    lbranch = '%s' % branch
    if lbranch in branches:
        return True
    elif '* %s' % branch in branches:
        return True
    else:
        return False


def is_not_a_branch(git_path, module, dest):
    branches = get_branches(git_path, module, dest)
    for branch in branches:
        if branch.startswith('* ') and ('no branch' in branch or 'detached from' in branch or 'detached at' in branch):
            return True
    return False


def get_repo_path(dest, bare):
    if bare:
        repo_path = dest
    else:
        repo_path = os.path.join(dest, '.git')
    # Check if the .git is a file. If it is a file, it means that the repository is in external directory respective to the working copy (e.g. we are in a
    # submodule structure).
    if os.path.isfile(repo_path):
        with open(repo_path, 'r') as gitfile:
            data = gitfile.read()
        ref_prefix, gitdir = data.rstrip().split('gitdir: ', 1)
        if ref_prefix:
            raise ValueError('.git file has invalid git dir reference format')

        # There is a possibility the .git file to have an absolute path.
        if os.path.isabs(gitdir):
            repo_path = gitdir
        else:
            # Use original destination directory with data from .git file.
            repo_path = os.path.join(dest, gitdir)
        if not os.path.isdir(repo_path):
            raise ValueError('%s is not a directory' % repo_path)
    return repo_path


def get_head_branch(git_path, module, dest, remote, bare=False):
    """
    Determine what branch HEAD is associated with.  This is partly
    taken from lib/ansible/utils/__init__.py.  It finds the correct
    path to .git/HEAD and reads from that file the branch that HEAD is
    associated with.  In the case of a detached HEAD, this will look
    up the branch in .git/refs/remotes/<remote>/HEAD.
    """
    try:
        repo_path = get_repo_path(dest, bare)
    except (IOError, ValueError) as err:
        # No repo path found
        # ``.git`` file does not have a valid format for detached Git dir.
        module.fail_json(
            msg='Current repo does not have a valid reference to a '
            'separate Git dir or it refers to the invalid path',
            details=to_text(err),
        )
    # Read .git/HEAD for the name of the branch.
    # If we're in a detached HEAD state, look up the branch associated with
    # the remote HEAD in .git/refs/remotes/<remote>/HEAD
    headfile = os.path.join(repo_path, "HEAD")
    if is_not_a_branch(git_path, module, dest):
        headfile = os.path.join(repo_path, 'refs', 'remotes', remote, 'HEAD')
    branch = head_splitter(headfile, remote, module=module, fail_on_error=True)
    return branch


def get_remote_url(git_path, module, dest, remote):
    """Return URL of remote source for repo."""
    command = [git_path, 'ls-remote', '--get-url', remote]
    (rc, out, err) = module.run_command(command, cwd=dest)
    if rc != 0:
        # There was an issue getting remote URL, most likely
        # command is not available in this version of Git.
        return None
    return to_native(out).rstrip('\n')


def set_remote_url(git_path, module, repo, dest, remote):
    """ updates repo from remote sources """
    # Return if remote URL isn't changing.
    remote_url = get_remote_url(git_path, module, dest, remote)
    if remote_url == repo or unfrackgitpath(remote_url) == unfrackgitpath(repo):
        return False

    command = [git_path, 'remote', 'set-url', remote, repo]
    (rc, out, err) = module.run_command(command, cwd=dest)
    if rc != 0:
        label = "set a new url %s for %s" % (repo, remote)
        module.fail_json(msg="Failed to %s: %s %s" % (label, out, err))

    # Return False if remote_url is None to maintain previous behavior
    # for Git versions prior to 1.7.5 that lack required functionality.
    return remote_url is not None


def fetch(git_path, module, repo, dest, version, remote, depth, bare, refspec, git_version_used, force=False):
    """ updates repo from remote sources """
    set_remote_url(git_path, module, repo, dest, remote)
    commands = []

    fetch_str = 'download remote objects and refs'
    fetch_cmd = [git_path, 'fetch']

    refspecs = []
    if depth:
        # try to find the minimal set of refs we need to fetch to get a
        # successful checkout
        currenthead = get_head_branch(git_path, module, dest, remote)
        if refspec:
            refspecs.append(refspec)
        elif version == 'HEAD':
            refspecs.append(currenthead)
        elif is_remote_branch(git_path, module, dest, repo, version):
            if currenthead != version:
                # this workaround is only needed for older git versions
                # 1.8.3 is broken, 1.9.x works
                # ensure that remote branch is available as both local and remote ref
                refspecs.append('+refs/heads/%s:refs/heads/%s' % (version, version))
            refspecs.append('+refs/heads/%s:refs/remotes/%s/%s' % (version, remote, version))
        elif is_remote_tag(git_path, module, dest, repo, version):
            refspecs.append('+refs/tags/' + version + ':refs/tags/' + version)
        if not refspecs:
            # if refspecs is empty, i.e. version is neither heads nor tags
            # assume it is a version hash
            # fall back to a full clone, otherwise we might not be able to checkout
            # version
            fetch_cmd.extend(['--depth', str(depth)])

    if not depth or not refspecs:
        # don't try to be minimalistic but do a full clone
        # also do this if depth is given, but version is something that can't be fetched directly
        if bare:
            refspecs = ['+refs/heads/*:refs/heads/*', '+refs/tags/*:refs/tags/*']
        else:
            # ensure all tags are fetched
            if git_version_used is not None and git_version_used >= LooseVersion('1.9'):
                fetch_cmd.append('--tags')
            else:
                # old git versions have a bug in --tags that prevents updating existing tags
                commands.append((fetch_str, fetch_cmd + [remote]))
                refspecs = ['+refs/tags/*:refs/tags/*']
        if refspec:
            refspecs.append(refspec)

    if force:
        fetch_cmd.append('--force')

    fetch_cmd.extend([remote])

    commands.append((fetch_str, fetch_cmd + refspecs))

    for (label, command) in commands:
        (rc, out, err) = module.run_command(command, cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to %s: %s %s" % (label, out, err), cmd=command)


def submodules_fetch(git_path, module, remote, track_submodules, dest):
    changed = False

    if not os.path.exists(os.path.join(dest, '.gitmodules')):
        # no submodules
        return changed

    gitmodules_file = open(os.path.join(dest, '.gitmodules'), 'r')
    for line in gitmodules_file:
        # Check for new submodules
        if not changed and line.strip().startswith('path'):
            path = line.split('=', 1)[1].strip()
            # Check that dest/path/.git exists
            if not os.path.exists(os.path.join(dest, path, '.git')):
                changed = True

    # Check for updates to existing modules
    if not changed:
        # Fetch updates
        begin = get_submodule_versions(git_path, module, dest)
        cmd = [git_path, 'submodule', 'foreach', git_path, 'fetch']
        (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to fetch submodules: %s" % out + err)

        if track_submodules:
            # Compare against submodule HEAD
            # FIXME: determine this from .gitmodules
            version = 'master'
            after = get_submodule_versions(git_path, module, dest, '%s/%s' % (remote, version))
            if begin != after:
                changed = True
        else:
            # Compare against the superproject's expectation
            cmd = [git_path, 'submodule', 'status']
            (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
            if rc != 0:
                module.fail_json(msg='Failed to retrieve submodule status: %s' % out + err)
            for line in out.splitlines():
                if line[0] != ' ':
                    changed = True
                    break
    return changed


def submodule_update(git_path, module, dest, track_submodules, force=False):
    """ init and update any submodules """

    # get the valid submodule params
    params = get_submodule_update_params(module, git_path, dest)

    # skip submodule commands if .gitmodules is not present
    if not os.path.exists(os.path.join(dest, '.gitmodules')):
        return (0, '', '')
    cmd = [git_path, 'submodule', 'sync']
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
    if 'remote' in params and track_submodules:
        cmd = [git_path, 'submodule', 'update', '--init', '--recursive', '--remote']
    else:
        cmd = [git_path, 'submodule', 'update', '--init', '--recursive']
    if force:
        cmd.append('--force')
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Failed to init/update submodules: %s" % out + err)
    return (rc, out, err)


def set_remote_branch(git_path, module, dest, remote, version, depth):
    """set refs for the remote branch version

    This assumes the branch does not yet exist locally and is therefore also not checked out.
    Can't use git remote set-branches, as it is not available in git 1.7.1 (centos6)
    """

    branchref = "+refs/heads/%s:refs/heads/%s" % (version, version)
    branchref += ' +refs/heads/%s:refs/remotes/%s/%s' % (version, remote, version)
    cmd = "%s fetch --depth=%s %s %s" % (git_path, depth, remote, branchref)
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Failed to fetch branch from remote: %s" % version, stdout=out, stderr=err, rc=rc)


def switch_version(git_path, module, dest, remote, version, verify_commit, depth, gpg_allowlist):
    cmd = ''
    if version == 'HEAD':
        branch = get_head_branch(git_path, module, dest, remote)
        (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, branch), cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to checkout branch %s" % branch,
                             stdout=out, stderr=err, rc=rc)
        cmd = "%s reset --hard %s/%s --" % (git_path, remote, branch)
    else:
        # FIXME check for local_branch first, should have been fetched already
        if is_remote_branch(git_path, module, dest, remote, version):
            if depth and not is_local_branch(git_path, module, dest, version):
                # git clone --depth implies --single-branch, which makes
                # the checkout fail if the version changes
                # fetch the remote branch, to be able to check it out next
                set_remote_branch(git_path, module, dest, remote, version, depth)
            if not is_local_branch(git_path, module, dest, version):
                cmd = "%s checkout --track -b %s %s/%s" % (git_path, version, remote, version)
            else:
                (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, version), cwd=dest)
                if rc != 0:
                    module.fail_json(msg="Failed to checkout branch %s" % version, stdout=out, stderr=err, rc=rc)
                cmd = "%s reset --hard %s/%s" % (git_path, remote, version)
        else:
            cmd = "%s checkout --force %s" % (git_path, version)
    (rc, out1, err1) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        if version != 'HEAD':
            module.fail_json(msg="Failed to checkout %s" % (version),
                             stdout=out1, stderr=err1, rc=rc, cmd=cmd)
        else:
            module.fail_json(msg="Failed to checkout branch %s" % (branch),
                             stdout=out1, stderr=err1, rc=rc, cmd=cmd)

    if verify_commit:
        verify_commit_sign(git_path, module, dest, version, gpg_allowlist)

    return (rc, out1, err1)


def verify_commit_sign(git_path, module, dest, version, gpg_allowlist):
    if version in get_annotated_tags(git_path, module, dest):
        git_sub = "verify-tag"
    else:
        git_sub = "verify-commit"
    cmd = "%s %s %s" % (git_path, git_sub, version)
    if gpg_allowlist:
        cmd += " --raw"
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg='Failed to verify GPG signature of commit/tag "%s"' % version, stdout=out, stderr=err, rc=rc)
    if gpg_allowlist:
        fingerprint = get_gpg_fingerprint(err)
        if fingerprint not in gpg_allowlist:
            module.fail_json(msg='The gpg_allowlist does not include the public key "%s" for this commit' % fingerprint, stdout=out, stderr=err, rc=rc)
    return (rc, out, err)


def get_gpg_fingerprint(output):
    """Return a fingerprint of the primary key.

    Ref:
    https://git.gnupg.org/cgi-bin/gitweb.cgi?p=gnupg.git;a=blob;f=doc/DETAILS;hb=HEAD#l482
    """
    for line in output.splitlines():
        data = line.split()
        if data[1] != 'VALIDSIG':
            continue

        # if signed with a subkey, this contains the primary key fingerprint
        data_id = 11 if len(data) == 11 else 2
        return data[data_id]


def git_version(git_path, module):
    """return the installed version of git"""
    cmd = "%s --version" % git_path
    (rc, out, err) = module.run_command(cmd)
    if rc != 0:
        # one could fail_json here, but the version info is not that important,
        # so let's try to fail only on actual git commands
        return None
    rematch = re.search('git version (.*)$', to_native(out))
    if not rematch:
        return None
    return LooseVersion(rematch.groups()[0])


def git_archive(git_path, module, dest, archive, archive_fmt, archive_prefix, version):
    """ Create git archive in given source directory """
    cmd = [git_path, 'archive', '--format', archive_fmt, '--output', archive, version]
    if archive_prefix is not None:
        cmd.insert(-1, '--prefix')
        cmd.insert(-1, archive_prefix)
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Failed to perform archive operation",
                         details="Git archive command failed to create "
                                 "archive %s using %s directory."
                                 "Error: %s" % (archive, dest, err))
    return rc, out, err


def create_archive(git_path, module, dest, archive, archive_prefix, version, repo, result):
    """ Helper function for creating archive using git_archive """
    all_archive_fmt = {'.zip': 'zip', '.gz': 'tar.gz', '.tar': 'tar',
                       '.tgz': 'tgz'}
    dummy, archive_ext = os.path.splitext(archive)
    archive_fmt = all_archive_fmt.get(archive_ext, None)
    if archive_fmt is None:
        module.fail_json(msg="Unable to get file extension from "
                             "archive file name : %s" % archive,
                         details="Please specify archive as filename with "
                                 "extension. File extension can be one "
                                 "of ['tar', 'tar.gz', 'zip', 'tgz']")

    repo_name = repo.split("/")[-1].replace(".git", "")

    if os.path.exists(archive):
        # If git archive file exists, then compare it with new git archive file.
        # if match, do nothing
        # if does not match, then replace existing with temp archive file.
        tempdir = tempfile.mkdtemp()
        new_archive_dest = os.path.join(tempdir, repo_name)
        new_archive = new_archive_dest + '.' + archive_fmt
        git_archive(git_path, module, dest, new_archive, archive_fmt, archive_prefix, version)

        # filecmp is supposed to be efficient than md5sum checksum
        if filecmp.cmp(new_archive, archive):
            result.update(changed=False)
            # Cleanup before exiting
            try:
                shutil.rmtree(tempdir)
            except OSError:
                pass
        else:
            try:
                shutil.move(new_archive, archive)
                shutil.rmtree(tempdir)
                result.update(changed=True)
            except OSError as e:
                module.fail_json(msg="Failed to move %s to %s" %
                                     (new_archive, archive),
                                 details=u"Error occurred while moving : %s"
                                         % to_text(e))
    else:
        # Perform archive from local directory
        git_archive(git_path, module, dest, archive, archive_fmt, archive_prefix, version)
        result.update(changed=True)

# ===========================================


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='path'),
            repo=dict(required=True, aliases=['name']),
            version=dict(default='HEAD'),
            remote=dict(default='origin'),
            refspec=dict(default=None),
            reference=dict(default=None),
            force=dict(default='no', type='bool'),
            depth=dict(default=None, type='int'),
            clone=dict(default='yes', type='bool'),
            update=dict(default='yes', type='bool'),
            verify_commit=dict(default='no', type='bool'),
            gpg_allowlist=dict(
                default=[], type='list', aliases=['gpg_whitelist'], elements='str',
                deprecated_aliases=[
                    dict(
                        name='gpg_whitelist',
                        version='2.21',
                        collection_name='ansible.builtin',
                    )
                ],
            ),
            accept_hostkey=dict(default='no', type='bool'),
            accept_newhostkey=dict(default='no', type='bool'),
            key_file=dict(default=None, type='path', required=False),
            ssh_opts=dict(default=None, required=False),
            executable=dict(default=None, type='path'),
            bare=dict(default='no', type='bool'),
            recursive=dict(default='yes', type='bool'),
            single_branch=dict(default=False, type='bool'),
            track_submodules=dict(default='no', type='bool'),
            umask=dict(default=None, type='raw'),
            archive=dict(type='path'),
            archive_prefix=dict(),
            separate_git_dir=dict(type='path'),
        ),
        mutually_exclusive=[('separate_git_dir', 'bare'), ('accept_hostkey', 'accept_newhostkey')],
        required_by={'archive_prefix': ['archive']},
        supports_check_mode=True
    )

    dest = module.params['dest']
    repo = module.params['repo']
    version = module.params['version']
    remote = module.params['remote']
    refspec = module.params['refspec']
    force = module.params['force']
    depth = module.params['depth']
    update = module.params['update']
    allow_clone = module.params['clone']
    bare = module.params['bare']
    verify_commit = module.params['verify_commit']
    gpg_allowlist = module.params['gpg_allowlist']
    reference = module.params['reference']
    single_branch = module.params['single_branch']
    git_path = module.params['executable'] or module.get_bin_path('git', True)
    key_file = module.params['key_file']
    ssh_opts = module.params['ssh_opts']
    umask = module.params['umask']
    archive = module.params['archive']
    archive_prefix = module.params['archive_prefix']
    separate_git_dir = module.params['separate_git_dir']

    result = dict(changed=False, warnings=list())

    if module.params['accept_hostkey']:
        if ssh_opts is not None:
            if ("-o StrictHostKeyChecking=no" not in ssh_opts) and ("-o StrictHostKeyChecking=accept-new" not in ssh_opts):
                ssh_opts += " -o StrictHostKeyChecking=no"
        else:
            ssh_opts = "-o StrictHostKeyChecking=no"

    if module.params['accept_newhostkey']:
        if not ssh_supports_acceptnewhostkey(module):
            module.warn("Your ssh client does not support accept_newhostkey option, therefore it cannot be used.")
        else:
            if ssh_opts is not None:
                if ("-o StrictHostKeyChecking=no" not in ssh_opts) and ("-o StrictHostKeyChecking=accept-new" not in ssh_opts):
                    ssh_opts += " -o StrictHostKeyChecking=accept-new"
            else:
                ssh_opts = "-o StrictHostKeyChecking=accept-new"

    # evaluate and set the umask before doing anything else
    if umask is not None:
        if not isinstance(umask, string_types):
            module.fail_json(msg="umask must be defined as a quoted octal integer")
        try:
            umask = int(umask, 8)
        except Exception:
            module.fail_json(msg="umask must be an octal integer",
                             details=to_text(sys.exc_info()[1]))
        os.umask(umask)

    # Certain features such as depth require a file:/// protocol for path based urls
    # so force a protocol here ...
    if os.path.expanduser(repo).startswith('/'):
        repo = 'file://' + os.path.expanduser(repo)

    # We screenscrape a huge amount of git commands so use C locale anytime we
    # call run_command()
    locale = get_best_parsable_locale(module)
    module.run_command_environ_update = dict(LANG=locale, LC_ALL=locale, LC_MESSAGES=locale, LC_CTYPE=locale, LANGUAGE=locale)

    if separate_git_dir:
        separate_git_dir = os.path.realpath(separate_git_dir)

    gitconfig = None
    if not dest and allow_clone:
        module.fail_json(msg="the destination directory must be specified unless clone=no")
    elif dest:
        dest = os.path.abspath(dest)
        try:
            repo_path = get_repo_path(dest, bare)
            if separate_git_dir and os.path.exists(repo_path) and separate_git_dir != repo_path:
                result['changed'] = True
                if not module.check_mode:
                    relocate_repo(module, result, separate_git_dir, repo_path, dest)
                    repo_path = separate_git_dir
        except (IOError, ValueError) as err:
            # No repo path found
            # ``.git`` file does not have a valid format for detached Git dir.
            module.fail_json(
                msg='Current repo does not have a valid reference to a '
                'separate Git dir or it refers to the invalid path',
                details=to_text(err),
            )
        gitconfig = os.path.join(repo_path, 'config')

    # iface changes so need it to make decisions
    git_version_used = git_version(git_path, module)

    # GIT_SSH=<path> as an environment variable, might create sh wrapper script for older versions.
    set_git_ssh_env(key_file, ssh_opts, git_version_used, module)

    if depth is not None and git_version_used is not None and git_version_used < LooseVersion('1.9.1'):
        module.warn("git version is too old to fully support the depth argument. Falling back to full checkouts.")
        depth = None

    recursive = module.params['recursive']
    track_submodules = module.params['track_submodules']

    result.update(before=None)

    local_mods = False
    if (dest and not os.path.exists(gitconfig)) or (not dest and not allow_clone):
        # if there is no git configuration, do a clone operation unless:
        # * the user requested no clone (they just want info)
        # * we're doing a check mode test
        # In those cases we do an ls-remote
        if module.check_mode or not allow_clone:
            remote_head = get_remote_head(git_path, module, dest, version, repo, bare)
            result.update(changed=True, after=remote_head)
            if module._diff:
                diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'])
                if diff:
                    result['diff'] = diff
            module.exit_json(**result)
        # there's no git config, so clone
        clone(git_path, module, repo, dest, remote, depth, version, bare, reference,
              refspec, git_version_used, verify_commit, separate_git_dir, result, gpg_allowlist, single_branch)
    elif not update:
        # Just return having found a repo already in the dest path
        # this does no checking that the repo is the actual repo
        # requested.
        result['before'] = get_version(module, git_path, dest)
        result.update(after=result['before'])
        if archive:
            # Git archive is not supported by all git servers, so
            # we will first clone and perform git archive from local directory
            if module.check_mode:
                result.update(changed=True)
                module.exit_json(**result)

            create_archive(git_path, module, dest, archive, archive_prefix, version, repo, result)

        module.exit_json(**result)
    else:
        # else do a pull
        local_mods = has_local_mods(module, git_path, dest, bare)
        result['before'] = get_version(module, git_path, dest)
        if local_mods:
            # failure should happen regardless of check mode
            if not force:
                module.fail_json(msg="Local modifications exist in the destination: " + dest + " (force=no).", **result)
            # if force and in non-check mode, do a reset
            if not module.check_mode:
                reset(git_path, module, dest)
                result.update(changed=True, msg='Local modifications exist in the destination: ' + dest)

        # exit if already at desired sha version
        if module.check_mode:
            remote_url = get_remote_url(git_path, module, dest, remote)
            remote_url_changed = remote_url and remote_url != repo and unfrackgitpath(remote_url) != unfrackgitpath(repo)
        else:
            remote_url_changed = set_remote_url(git_path, module, repo, dest, remote)
        result.update(remote_url_changed=remote_url_changed)

        if module.check_mode:
            remote_head = get_remote_head(git_path, module, dest, version, remote, bare)
            result.update(changed=(result['before'] != remote_head or remote_url_changed), after=remote_head)
            # FIXME: This diff should fail since the new remote_head is not fetched yet?!
            if module._diff:
                diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'])
                if diff:
                    result['diff'] = diff
            module.exit_json(**result)
        else:
            fetch(git_path, module, repo, dest, version, remote, depth, bare, refspec, git_version_used, force=force)

        result['after'] = get_version(module, git_path, dest)

    # switch to version specified regardless of whether
    # we got new revisions from the repository
    if not bare:
        switch_version(git_path, module, dest, remote, version, verify_commit, depth, gpg_allowlist)

    # Deal with submodules
    submodules_updated = False
    if recursive and not bare:
        submodules_updated = submodules_fetch(git_path, module, remote, track_submodules, dest)
        if submodules_updated:
            result.update(submodules_changed=submodules_updated)

            if module.check_mode:
                result.update(changed=True, after=remote_head)
                module.exit_json(**result)

            # Switch to version specified
            submodule_update(git_path, module, dest, track_submodules, force=force)

    # determine if we changed anything
    result['after'] = get_version(module, git_path, dest)

    if result['before'] != result['after'] or local_mods or submodules_updated or remote_url_changed:
        result.update(changed=True)
        if module._diff:
            diff = get_diff(module, git_path, dest, repo, remote, depth, bare, result['before'], result['after'])
            if diff:
                result['diff'] = diff

    if archive:
        # Git archive is not supported by all git servers, so
        # we will first clone and perform git archive from local directory
        if module.check_mode:
            result.update(changed=True)
            module.exit_json(**result)

        create_archive(git_path, module, dest, archive, archive_prefix, version, repo, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
