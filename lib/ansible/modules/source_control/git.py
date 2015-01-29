#!/usr/bin/python
# -*- coding: utf-8 -*-

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

DOCUMENTATION = '''
---
module: git
author: Michael DeHaan
version_added: "0.0.1"
short_description: Deploy software (or files) from git checkouts
description:
    - Manage I(git) checkouts of repositories to deploy files or software.
options:
    repo:
        required: true
        aliases: [ name ]
        description:
            - git, SSH, or HTTP protocol address of the git repository.
    dest:
        required: true
        description:
            - Absolute path of where the repository should be checked out to.
              This parameter is required, unless C(clone) is set to C(no)
              This change was made in version 1.8.3. Prior to this version,
              the C(dest) parameter was always required.
    version:
        required: false
        default: "HEAD"
        description:
            - What version of the repository to check out.  This can be the
              full 40-character I(SHA-1) hash, the literal string C(HEAD), a
              branch name, or a tag name.
    accept_hostkey:
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        version_added: "1.5"
        description:
            - if C(yes), adds the hostkey for the repo url if not already 
              added. If ssh_args contains "-o StrictHostKeyChecking=no", 
              this parameter is ignored.
    ssh_opts:
        required: false
        default: None
        version_added: "1.5"
        description:
            - Creates a wrapper script and exports the path as GIT_SSH
              which git then automatically uses to override ssh arguments.
              An example value could be "-o StrictHostKeyChecking=no"
    key_file:
        required: false
        default: None
        version_added: "1.5"
        description:
            - Specify an optional private key file to use for the checkout.
    reference:
        required: false
        default: null
        version_added: "1.4"
        description:
            - Reference repository (see "git clone --reference ...")
    remote:
        required: false
        default: "origin"
        description:
            - Name of the remote.
    refspec:
        required: false
        default: null
        version_added: "1.9"
        description:
            - Add an additional refspec to be fetched.
              If version is set to a I(SHA-1) not reachable from any branch
              or tag, this option may be necessary to specify the ref containing
              the I(SHA-1).
              Uses the same syntax as the 'git fetch' command.
              An example value could be "refs/meta/config".
    force:
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        version_added: "0.7"
        description:
            - If C(yes), any modified files in the working
              repository will be discarded.  Prior to 0.7, this was always
              'yes' and could not be disabled.  Prior to 1.9, the default was
              `yes`
    depth:
        required: false
        default: null
        version_added: "1.2"
        description:
            - Create a shallow clone with a history truncated to the specified
              number or revisions. The minimum possible value is C(1), otherwise
              ignored.
    clone:
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        version_added: "1.9"
        description:
            - If C(no), do not clone the repository if it does not exist locally
    update:
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        version_added: "1.2"
        description:
            - If C(no), do not retrieve new revisions from the origin repository
    executable:
        required: false
        default: null
        version_added: "1.4"
        description:
            - Path to git executable to use. If not supplied,
              the normal mechanism for resolving binary paths will be used.
    bare:
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        version_added: "1.4"
        description:
            - if C(yes), repository will be created as a bare repo, otherwise
              it will be a standard repo with a workspace.

    recursive:
        required: false
        default: "yes"
        choices: [ "yes", "no" ]
        version_added: "1.6"
        description:
            - if C(no), repository will be cloned without the --recursive
              option, skipping sub-modules.

    track_submodules:
        required: false
        default: "no"
        choices: ["yes", "no"]
        version_added: "1.8"
        description:
            - if C(yes), submodules will track the latest commit on their
              master branch (or other branch specified in .gitmodules).  If
              C(no), submodules will be kept at the revision specified by the
              main project. This is equivalent to specifying the --remote flag
              to git submodule update.

notes:
    - "If the task seems to be hanging, first verify remote host is in C(known_hosts).
      SSH will prompt user to authorize the first contact with a remote host.  To avoid this prompt, 
      one solution is to add the remote host public key in C(/etc/ssh/ssh_known_hosts) before calling 
      the git module, with the following command: ssh-keyscan -H remote_host.com >> /etc/ssh/ssh_known_hosts."
'''

EXAMPLES = '''
# Example git checkout from Ansible Playbooks
- git: repo=git://foosball.example.org/path/to/repo.git
       dest=/srv/checkout
       version=release-0.22

# Example read-write git checkout from github
- git: repo=ssh://git@github.com/mylogin/hello.git dest=/home/mylogin/hello

# Example just ensuring the repo checkout exists
- git: repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout update=no

# Example just get information about the repository whether or not it has
# already been cloned locally.
- git: repo=git://foosball.example.org/path/to/repo.git dest=/srv/checkout clone=no update=no

# Example checkout a github repo and use refspec to fetch all pull requests
- git: repo=https://github.com/ansible/ansible-examples.git dest=/src/ansible-examples refspec=+refs/pull/*:refs/heads/*
'''

import re
import tempfile

def get_submodule_update_params(module, git_path, cwd):

    #or: git submodule [--quiet] update [--init] [-N|--no-fetch] 
    #[-f|--force] [--rebase] [--reference <repository>] [--merge] 
    #[--recursive] [--] [<path>...]

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
        update_line = update_line.replace('[','')
        update_line = update_line.replace(']','')
        update_line = update_line.replace('|',' ')
        parts = shlex.split(update_line)
        for part in parts:    
            if part.startswith('--'):
                part = part.replace('--', '')
                params.append(part)

    return params

def write_ssh_wrapper():
    module_dir = get_module_path()
    try:
        # make sure we have full permission to the module_dir, which
        # may not be the case if we're sudo'ing to a non-root user
        if os.access(module_dir, os.W_OK|os.R_OK|os.X_OK):
            fd, wrapper_path = tempfile.mkstemp(prefix=module_dir + '/')
        else:
            raise OSError
    except (IOError, OSError):
        fd, wrapper_path = tempfile.mkstemp()
    fh = os.fdopen(fd, 'w+b')
    template = """#!/bin/sh
if [ -z "$GIT_SSH_OPTS" ]; then
    BASEOPTS=""
else
    BASEOPTS=$GIT_SSH_OPTS
fi

if [ -z "$GIT_KEY" ]; then
    ssh $BASEOPTS "$@"
else
    ssh -i "$GIT_KEY" $BASEOPTS "$@"
fi
"""
    fh.write(template)
    fh.close()
    st = os.stat(wrapper_path)
    os.chmod(wrapper_path, st.st_mode | stat.S_IEXEC)
    return wrapper_path

def set_git_ssh(ssh_wrapper, key_file, ssh_opts):

    if os.environ.get("GIT_SSH"):
        del os.environ["GIT_SSH"]
    os.environ["GIT_SSH"] = ssh_wrapper

    if os.environ.get("GIT_KEY"):
        del os.environ["GIT_KEY"]

    if key_file:
        os.environ["GIT_KEY"] = key_file    

    if os.environ.get("GIT_SSH_OPTS"):
        del os.environ["GIT_SSH_OPTS"]

    if ssh_opts:
        os.environ["GIT_SSH_OPTS"] = ssh_opts

def get_version(module, git_path, dest, ref="HEAD"):
    ''' samples the version of the git repo '''

    cmd = "%s rev-parse %s" % (git_path, ref)
    rc, stdout, stderr = module.run_command(cmd, cwd=dest)
    sha = stdout.rstrip('\n')
    return sha

def get_submodule_versions(git_path, module, dest, version='HEAD'):
    cmd = [git_path, 'submodule', 'foreach', git_path, 'rev-parse', version]
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg='Unable to determine hashes of submodules')
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
          reference, refspec):
    ''' makes a new git repo if it does not already exist '''
    dest_dirname = os.path.dirname(dest)
    try:
        os.makedirs(dest_dirname)
    except:
        pass
    cmd = [ git_path, 'clone' ]
    if bare:
        cmd.append('--bare')
    else:
        cmd.extend([ '--origin', remote ])
        if is_remote_branch(git_path, module, dest, repo, version) \
        or is_remote_tag(git_path, module, dest, repo, version):
            cmd.extend([ '--branch', version ])
    if depth:
        cmd.extend([ '--depth', str(depth) ])
    if reference:
        cmd.extend([ '--reference', str(reference) ])
    cmd.extend([ repo, dest ])
    module.run_command(cmd, check_rc=True, cwd=dest_dirname)
    if bare:
        if remote != 'origin':
            module.run_command([git_path, 'remote', 'add', remote, repo], check_rc=True, cwd=dest)

    if refspec:
        module.run_command([git_path, 'fetch', remote, refspec], check_rc=True, cwd=dest)

def has_local_mods(module, git_path, dest, bare):
    if bare:
        return False

    cmd = "%s status -s" % (git_path)
    rc, stdout, stderr = module.run_command(cmd, cwd=dest)
    lines = stdout.splitlines()
    lines = filter(lambda c: not re.search('^\\?\\?.*$', c), lines)

    return len(lines) > 0

def reset(git_path, module, dest):
    '''
    Resets the index and working tree to HEAD.
    Discards any changes to tracked files in working
    tree since that commit.
    '''
    cmd = "%s reset --hard HEAD" % (git_path,)
    return module.run_command(cmd, check_rc=True, cwd=dest)

def get_remote_head(git_path, module, dest, version, remote, bare):
    cloning = False
    cwd = None
    tag = False
    if remote == module.params['repo']:
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
        module.fail_json(msg="Could not determine remote revision for %s" % version)

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
    if version in out:
        return True
    else:
        return False

def get_branches(git_path, module, dest):
    branches = []
    cmd = '%s branch -a' % (git_path,)
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Could not determine branch data - received %s" % out)
    for line in out.split('\n'):
        branches.append(line.strip())
    return branches

def get_tags(git_path, module, dest):
    tags = []
    cmd = '%s tag' % (git_path,)
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Could not determine tag data - received %s" % out)
    for line in out.split('\n'):
        tags.append(line.strip())
    return tags

def is_remote_branch(git_path, module, dest, remote, version):
    cmd = '%s ls-remote %s -h refs/heads/%s' % (git_path, remote, version)
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
    if version in out:
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
    for b in branches:
        if b.startswith('* ') and 'no branch' in b:
            return True
    return False

def get_head_branch(git_path, module, dest, remote, bare=False):
    '''
    Determine what branch HEAD is associated with.  This is partly
    taken from lib/ansible/utils/__init__.py.  It finds the correct
    path to .git/HEAD and reads from that file the branch that HEAD is
    associated with.  In the case of a detached HEAD, this will look
    up the branch in .git/refs/remotes/<remote>/HEAD.
    '''
    if bare:
        repo_path = dest
    else:
        repo_path = os.path.join(dest, '.git')
    # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
    if os.path.isfile(repo_path):
        try:
            gitdir = yaml.safe_load(open(repo_path)).get('gitdir')
            # There is a posibility the .git file to have an absolute path.
            if os.path.isabs(gitdir):
                repo_path = gitdir
            else:
                repo_path = os.path.join(repo_path.split('.git')[0], gitdir)
        except (IOError, AttributeError):
            return ''
    # Read .git/HEAD for the name of the branch.
    # If we're in a detached HEAD state, look up the branch associated with
    # the remote HEAD in .git/refs/remotes/<remote>/HEAD
    f = open(os.path.join(repo_path, "HEAD"))
    if is_not_a_branch(git_path, module, dest):
        f.close()
        f = open(os.path.join(repo_path, 'refs', 'remotes', remote, 'HEAD'))
    branch = f.readline().split('/')[-1].rstrip("\n")
    f.close()
    return branch

def fetch(git_path, module, repo, dest, version, remote, bare, refspec):
    ''' updates repo from remote sources '''
    commands = [("set a new url %s for %s" % (repo, remote), [git_path, 'remote', 'set-url', remote, repo])]

    fetch_str = 'download remote objects and refs'

    if bare:
        refspecs = ['+refs/heads/*:refs/heads/*', '+refs/tags/*:refs/tags/*']
        if refspec:
            refspecs.append(refspec)
        commands.append((fetch_str, [git_path, 'fetch', remote] + refspecs))
    else:
        # unlike in bare mode, there's no way to combine the
        # additional refspec with the default git fetch behavior,
        # so use two commands
        commands.append((fetch_str, [git_path, 'fetch', remote]))
        refspecs = ['+refs/tags/*:refs/tags/*']
        if refspec:
            refspecs.append(refspec)
        commands.append((fetch_str, [git_path, 'fetch', remote] + refspecs))

    for (label,command) in commands:
        (rc,out,err) = module.run_command(command, cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to %s: %s %s" % (label, out, err))

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

        # add the submodule repo's hostkey
        if line.strip().startswith('url'):
            repo = line.split('=', 1)[1].strip()
            if module.params['ssh_opts'] is not None:
                if not "-o StrictHostKeyChecking=no" in module.params['ssh_opts']:
                    add_git_host_key(module, repo, accept_hostkey=module.params['accept_hostkey'])
            else:
                add_git_host_key(module, repo, accept_hostkey=module.params['accept_hostkey'])

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
            ### FIXME: determine this from .gitmodules
            version = 'master'
            after = get_submodule_versions(git_path, module, dest, '%s/%s'
                    % (remote, version))
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

def submodule_update(git_path, module, dest, track_submodules):
    ''' init and update any submodules '''

    # get the valid submodule params
    params = get_submodule_update_params(module, git_path, dest)

    # skip submodule commands if .gitmodules is not present
    if not os.path.exists(os.path.join(dest, '.gitmodules')):
        return (0, '', '')
    cmd = [ git_path, 'submodule', 'sync' ]
    (rc, out, err) = module.run_command(cmd, check_rc=True, cwd=dest)
    if 'remote' in params and track_submodules:
        cmd = [ git_path, 'submodule', 'update', '--init', '--recursive' ,'--remote' ]
    else:
        cmd = [ git_path, 'submodule', 'update', '--init', '--recursive' ]
    (rc, out, err) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        module.fail_json(msg="Failed to init/update submodules: %s" % out + err)
    return (rc, out, err)


def switch_version(git_path, module, dest, remote, version):
    cmd = ''
    if version != 'HEAD':
        if is_remote_branch(git_path, module, dest, remote, version):
            if not is_local_branch(git_path, module, dest, version):
                cmd = "%s checkout --track -b %s %s/%s" % (git_path, version, remote, version)
            else:
                (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, version), cwd=dest)
                if rc != 0:
                    module.fail_json(msg="Failed to checkout branch %s" % version)
                cmd = "%s reset --hard %s/%s" % (git_path, remote, version)
        else:
            cmd = "%s checkout --force %s" % (git_path, version)
    else:
        branch = get_head_branch(git_path, module, dest, remote)
        (rc, out, err) = module.run_command("%s checkout --force %s" % (git_path, branch), cwd=dest)
        if rc != 0:
            module.fail_json(msg="Failed to checkout branch %s" % branch)
        cmd = "%s reset --hard %s" % (git_path, remote)
    (rc, out1, err1) = module.run_command(cmd, cwd=dest)
    if rc != 0:
        if version != 'HEAD':
            module.fail_json(msg="Failed to checkout %s" % (version))
        else:
            module.fail_json(msg="Failed to checkout branch %s" % (branch))
    return (rc, out1, err1)

# ===========================================

def main():
    module = AnsibleModule(
        argument_spec = dict(
            dest=dict(),
            repo=dict(required=True, aliases=['name']),
            version=dict(default='HEAD'),
            remote=dict(default='origin'),
            refspec=dict(default=None),
            reference=dict(default=None),
            force=dict(default='no', type='bool'),
            depth=dict(default=None, type='int'),
            clone=dict(default='yes', type='bool'),
            update=dict(default='yes', type='bool'),
            accept_hostkey=dict(default='no', type='bool'),
            key_file=dict(default=None, required=False),
            ssh_opts=dict(default=None, required=False),
            executable=dict(default=None),
            bare=dict(default='no', type='bool'),
            recursive=dict(default='yes', type='bool'),
            track_submodules=dict(default='no', type='bool'),
        ),
        supports_check_mode=True
    )

    dest      = module.params['dest']
    repo      = module.params['repo']
    version   = module.params['version']
    remote    = module.params['remote']
    refspec   = module.params['refspec']
    force     = module.params['force']
    depth     = module.params['depth']
    update    = module.params['update']
    allow_clone = module.params['clone']
    bare      = module.params['bare']
    reference = module.params['reference']
    git_path  = module.params['executable'] or module.get_bin_path('git', True)
    key_file  = module.params['key_file']
    ssh_opts  = module.params['ssh_opts']

    gitconfig = None
    if not dest and allow_clone:
        module.fail_json(msg="the destination directory must be specified unless clone=no")
    elif dest:
        dest = os.path.abspath(os.path.expanduser(dest))
        if bare:
            gitconfig = os.path.join(dest, 'config')
        else:
            gitconfig = os.path.join(dest, '.git', 'config')

    # make sure the key_file path is expanded for ~ and $HOME
    if key_file is not None:
        key_file = os.path.abspath(os.path.expanduser(key_file))

    # create a wrapper script and export
    # GIT_SSH=<path> as an environment variable
    # for git to use the wrapper script
    ssh_wrapper = None
    if key_file or ssh_opts:
        ssh_wrapper = write_ssh_wrapper()
        set_git_ssh(ssh_wrapper, key_file, ssh_opts)
        module.add_cleanup_file(path=ssh_wrapper)

    # add the git repo's hostkey 
    if module.params['ssh_opts'] is not None:
        if not "-o StrictHostKeyChecking=no" in module.params['ssh_opts']:
            add_git_host_key(module, repo, accept_hostkey=module.params['accept_hostkey'])
    else:
        add_git_host_key(module, repo, accept_hostkey=module.params['accept_hostkey'])

    recursive = module.params['recursive']
    track_submodules = module.params['track_submodules']

    rc, out, err, status = (0, None, None, None)

    before = None
    local_mods = False
    repo_updated = None
    if (dest and not os.path.exists(gitconfig)) or (not dest and not allow_clone):
        # if there is no git configuration, do a clone operation unless:
        # * the user requested no clone (they just want info)
        # * we're doing a check mode test
        # In those cases we do an ls-remote
        if module.check_mode or not allow_clone:
            remote_head = get_remote_head(git_path, module, dest, version, repo, bare)
            module.exit_json(changed=True, before=before, after=remote_head)
        # there's no git config, so clone
        clone(git_path, module, repo, dest, remote, depth, version, bare, reference, refspec)
        repo_updated = True
    elif not update:
        # Just return having found a repo already in the dest path
        # this does no checking that the repo is the actual repo
        # requested.
        before = get_version(module, git_path, dest)
        module.exit_json(changed=False, before=before, after=before)
    else:
        # else do a pull
        local_mods = has_local_mods(module, git_path, dest, bare)
        before = get_version(module, git_path, dest)
        if local_mods:
            # failure should happen regardless of check mode
            if not force:
                module.fail_json(msg="Local modifications exist in repository (force=no).")
            # if force and in non-check mode, do a reset
            if not module.check_mode:
                reset(git_path, module, dest)
        # exit if already at desired sha version
        remote_head = get_remote_head(git_path, module, dest, version, remote, bare)
        if before == remote_head:
            if local_mods:
                module.exit_json(changed=True, before=before, after=remote_head,
                    msg="Local modifications exist")
            elif is_remote_tag(git_path, module, dest, repo, version):
                # if the remote is a tag and we have the tag locally, exit early
                if version in get_tags(git_path, module, dest):
                    repo_updated = False
            else:
                repo_updated = False
        if repo_updated is None:
            if module.check_mode:
                module.exit_json(changed=True, before=before, after=remote_head)
            fetch(git_path, module, repo, dest, version, remote, bare, refspec)
            repo_updated = True

    # switch to version specified regardless of whether
    # we got new revisions from the repository
    if not bare:
        switch_version(git_path, module, dest, remote, version)

    # Deal with submodules
    submodules_updated = False
    if recursive and not bare:
        submodules_updated = submodules_fetch(git_path, module, remote, track_submodules, dest)

        if module.check_mode:
            if submodules_updated:
                module.exit_json(changed=True, before=before, after=remote_head, submodules_changed=True)
            else:
                module.exit_json(changed=False, before=before, after=remote_head)

        if submodules_updated:
            # Switch to version specified
            submodule_update(git_path, module, dest, track_submodules)

    # determine if we changed anything
    after = get_version(module, git_path, dest)

    changed = False
    if before != after or local_mods or submodules_updated:
        changed = True

    # cleanup the wrapper script
    if ssh_wrapper:
        try:
            os.remove(ssh_wrapper)
        except OSError:
            # No need to fail if the file already doesn't exist
            pass

    module.exit_json(changed=changed, before=before, after=after)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.known_hosts import *

main()
