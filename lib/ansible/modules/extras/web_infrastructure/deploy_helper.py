#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Jasper N. Brouwer <jasper@nerdsweide.nl>
# (c) 2014, Ramon de la Fuente <ramon@delafuente.nl>
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
module: deploy_helper
version_added: "2.0"
author: "Ramon de la Fuente (@ramondelafuente)"
short_description: Manages some of the steps common in deploying projects.
description:
  - The Deploy Helper manages some of the steps common in deploying software.
    It creates a folder structure, manages a symlink for the current release
    and cleans up old releases.
  - "Running it with the C(state=query) or C(state=present) will return the C(deploy_helper) fact.
    C(project_path), whatever you set in the path parameter,
    C(current_path), the path to the symlink that points to the active release,
    C(releases_path), the path to the folder to keep releases in,
    C(shared_path), the path to the folder to keep shared resources in,
    C(unfinished_filename), the file to check for to recognize unfinished builds,
    C(previous_release), the release the 'current' symlink is pointing to,
    C(previous_release_path), the full path to the 'current' symlink target,
    C(new_release), either the 'release' parameter or a generated timestamp,
    C(new_release_path), the path to the new release folder (not created by the module)."

options:
  path:
    required: True
    aliases: ['dest']
    description:
      - the root path of the project. Alias I(dest).
        Returned in the C(deploy_helper.project_path) fact.

  state:
    required: False
    choices: [ present, finalize, absent, clean, query ]
    default: present
    description:
      - the state of the project.
        C(query) will only gather facts,
        C(present) will create the project I(root) folder, and in it the I(releases) and I(shared) folders,
        C(finalize) will remove the unfinished_filename file, create a symlink to the newly
          deployed release and optionally clean old releases,
        C(clean) will remove failed & old releases,
        C(absent) will remove the project folder (synonymous to the M(file) module with C(state=absent))

  release:
    required: False
    default: None
    description:
      - the release version that is being deployed. Defaults to a timestamp format %Y%m%d%H%M%S (i.e. '20141119223359').
        This parameter is optional during C(state=present), but needs to be set explicitly for C(state=finalize).
        You can use the generated fact C(release={{ deploy_helper.new_release }}).

  releases_path:
    required: False
    default: releases
    description:
      - the name of the folder that will hold the releases. This can be relative to C(path) or absolute.
        Returned in the C(deploy_helper.releases_path) fact.

  shared_path:
    required: False
    default: shared
    description:
      - the name of the folder that will hold the shared resources. This can be relative to C(path) or absolute.
        If this is set to an empty string, no shared folder will be created.
        Returned in the C(deploy_helper.shared_path) fact.

  current_path:
    required: False
    default: current
    description:
      - the name of the symlink that is created when the deploy is finalized. Used in C(finalize) and C(clean).
        Returned in the C(deploy_helper.current_path) fact.

  unfinished_filename:
    required: False
    default: DEPLOY_UNFINISHED
    description:
      - the name of the file that indicates a deploy has not finished. All folders in the releases_path that
        contain this file will be deleted on C(state=finalize) with clean=True, or C(state=clean). This file is
        automatically deleted from the I(new_release_path) during C(state=finalize).

  clean:
    required: False
    default: True
    description:
      - Whether to run the clean procedure in case of C(state=finalize).

  keep_releases:
    required: False
    default: 5
    description:
      - the number of old releases to keep when cleaning. Used in C(finalize) and C(clean). Any unfinished builds
        will be deleted first, so only correct releases will count. The current version will not count.

notes:
  - Facts are only returned for C(state=query) and C(state=present). If you use both, you should pass any overridden
    parameters to both calls, otherwise the second call will overwrite the facts of the first one.
  - When using C(state=clean), the releases are ordered by I(creation date). You should be able to switch to a
    new naming strategy without problems.
  - Because of the default behaviour of generating the I(new_release) fact, this module will not be idempotent
    unless you pass your own release name with C(release). Due to the nature of deploying software, this should not
    be much of a problem.
'''

EXAMPLES = '''

# General explanation, starting with an example folder structure for a project:

root:
    releases:
        - 20140415234508
        - 20140415235146
        - 20140416082818

    shared:
        - sessions
        - uploads

    current: -> releases/20140416082818


The 'releases' folder holds all the available releases. A release is a complete build of the application being
deployed. This can be a clone of a repository for example, or a sync of a local folder on your filesystem.
Having timestamped folders is one way of having distinct releases, but you could choose your own strategy like
git tags or commit hashes.

During a deploy, a new folder should be created in the releases folder and any build steps required should be
performed. Once the new build is ready, the deploy procedure is 'finalized' by replacing the 'current' symlink
with a link to this build.

The 'shared' folder holds any resource that is shared between releases. Examples of this are web-server
session files, or files uploaded by users of your application. It's quite common to have symlinks from a release
folder pointing to a shared/subfolder, and creating these links would be automated as part of the build steps.

The 'current' symlink points to one of the releases. Probably the latest one, unless a deploy is in progress.
The web-server's root for the project will go through this symlink, so the 'downtime' when switching to a new
release is reduced to the time it takes to switch the link.

To distinguish between successful builds and unfinished ones, a file can be placed in the folder of the release
that is currently in progress. The existence of this file will mark it as unfinished, and allow an automated
procedure to remove it during cleanup.


# Typical usage:
- name: Initialize the deploy root and gather facts
  deploy_helper: path=/path/to/root
- name: Clone the project to the new release folder
  git: repo=git://foosball.example.org/path/to/repo.git dest={{ deploy_helper.new_release_path }} version=v1.1.1
- name: Add an unfinished file, to allow cleanup on successful finalize
  file: path={{ deploy_helper.new_release_path }}/{{ deploy_helper.unfinished_filename }} state=touch
- name: Perform some build steps, like running your dependency manager for example
  composer: command=install working_dir={{ deploy_helper.new_release_path }}
- name: Create some folders in the shared folder
  file: path='{{ deploy_helper.shared_path }}/{{ item }}' state=directory
  with_items: ['sessions', 'uploads']
- name: Add symlinks from the new release to the shared folder
  file: path='{{ deploy_helper.new_release_path }}/{{ item.path }}'
        src='{{ deploy_helper.shared_path }}/{{ item.src }}'
        state=link
  with_items:
      - { path: "app/sessions", src: "sessions" }
      - { path: "web/uploads",  src: "uploads" }
- name: Finalize the deploy, removing the unfinished file and switching the symlink
  deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=finalize

# Retrieving facts before running a deploy
- name: Run 'state=query' to gather facts without changing anything
  deploy_helper: path=/path/to/root state=query
# Remember to set the 'release' parameter when you actually call 'state=present' later
- name: Initialize the deploy root
  deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=present

# all paths can be absolute or relative (to the 'path' parameter)
- deploy_helper: path=/path/to/root
                 releases_path=/var/www/project/releases
                 shared_path=/var/www/shared
                 current_path=/var/www/active

# Using your own naming strategy for releases (a version tag in this case):
- deploy_helper: path=/path/to/root release=v1.1.1 state=present
- deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=finalize

# Using a different unfinished_filename:
- deploy_helper: path=/path/to/root
                 unfinished_filename=README.md
                 release={{ deploy_helper.new_release }}
                 state=finalize

# Postponing the cleanup of older builds:
- deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=finalize clean=False
- deploy_helper: path=/path/to/root state=clean
# Or running the cleanup ahead of the new deploy
- deploy_helper: path=/path/to/root state=clean
- deploy_helper: path=/path/to/root state=present

# Keeping more old releases:
- deploy_helper: path=/path/to/root release={{ deploy_helper.new_release }} state=finalize keep_releases=10
# Or, if you use 'clean=false' on finalize:
- deploy_helper: path=/path/to/root state=clean keep_releases=10

# Removing the entire project root folder
- deploy_helper: path=/path/to/root state=absent

# Debugging the facts returned by the module
- deploy_helper: path=/path/to/root
- debug: var=deploy_helper

'''

class DeployHelper(object):

    def __init__(self, module):
        module.params['path'] = os.path.expanduser(module.params['path'])

        self.module    = module
        self.file_args = module.load_file_common_arguments(module.params)

        self.clean               = module.params['clean']
        self.current_path        = module.params['current_path']
        self.keep_releases       = module.params['keep_releases']
        self.path                = module.params['path']
        self.release             = module.params['release']
        self.releases_path       = module.params['releases_path']
        self.shared_path         = module.params['shared_path']
        self.state               = module.params['state']
        self.unfinished_filename = module.params['unfinished_filename']

    def gather_facts(self):
        current_path   = os.path.join(self.path, self.current_path)
        releases_path  = os.path.join(self.path, self.releases_path)
        if self.shared_path:
            shared_path    = os.path.join(self.path, self.shared_path)
        else:
            shared_path    = None

        previous_release, previous_release_path = self._get_last_release(current_path)

        if not self.release and (self.state == 'query' or self.state == 'present'):
            self.release = time.strftime("%Y%m%d%H%M%S")

        new_release_path = os.path.join(releases_path, self.release)

        return {
            'project_path':             self.path,
            'current_path':             current_path,
            'releases_path':            releases_path,
            'shared_path':              shared_path,
            'previous_release':         previous_release,
            'previous_release_path':    previous_release_path,
            'new_release':              self.release,
            'new_release_path':         new_release_path,
            'unfinished_filename':      self.unfinished_filename
        }

    def delete_path(self, path):
        if not os.path.lexists(path):
            return False

        if not os.path.isdir(path):
            self.module.fail_json(msg="%s exists but is not a directory" % path)

        if not self.module.check_mode:
            try:
                shutil.rmtree(path, ignore_errors=False)
            except Exception, e:
                self.module.fail_json(msg="rmtree failed: %s" % str(e))

        return True

    def create_path(self, path):
        changed = False

        if not os.path.lexists(path):
            changed = True
            if not self.module.check_mode:
                os.makedirs(path)

        elif not os.path.isdir(path):
            self.module.fail_json(msg="%s exists but is not a directory" % path)

        changed += self.module.set_directory_attributes_if_different(self._get_file_args(path), changed)

        return changed

    def check_link(self, path):
        if os.path.lexists(path):
            if not os.path.islink(path):
                self.module.fail_json(msg="%s exists but is not a symbolic link" % path)

    def create_link(self, source, link_name):
        changed = False

        if os.path.islink(link_name):
            norm_link = os.path.normpath(os.path.realpath(link_name))
            norm_source = os.path.normpath(os.path.realpath(source))
            if norm_link == norm_source:
                changed = False
            else:
                changed = True
                if not self.module.check_mode:
                    if not os.path.lexists(source):
                        self.module.fail_json(msg="the symlink target %s doesn't exists" % source)
                    tmp_link_name = link_name + '.' + self.unfinished_filename
                    if os.path.islink(tmp_link_name):
                        os.unlink(tmp_link_name)
                    os.symlink(source, tmp_link_name)
                    os.rename(tmp_link_name, link_name)
        else:
            changed = True
            if not self.module.check_mode:
                os.symlink(source, link_name)

        return changed

    def remove_unfinished_file(self, new_release_path):
        changed = False
        unfinished_file_path  = os.path.join(new_release_path, self.unfinished_filename)
        if os.path.lexists(unfinished_file_path):
            changed = True
            if not self.module.check_mode:
                os.remove(unfinished_file_path)

        return changed

    def remove_unfinished_builds(self, releases_path):
        changes = 0

        for release in os.listdir(releases_path):
            if os.path.isfile(os.path.join(releases_path, release, self.unfinished_filename)):
                if self.module.check_mode:
                    changes += 1
                else:
                    changes += self.delete_path(os.path.join(releases_path, release))

        return changes

    def remove_unfinished_link(self, path):
        changed = False

        tmp_link_name = os.path.join(path, self.release + '.' + self.unfinished_filename)
        if not self.module.check_mode and os.path.exists(tmp_link_name):
            changed = True
            os.remove(tmp_link_name)

        return changed

    def cleanup(self, releases_path, reserve_version):
        changes = 0

        if os.path.lexists(releases_path):
            releases = [ f for f in os.listdir(releases_path) if os.path.isdir(os.path.join(releases_path,f)) ]
            try:
                releases.remove(reserve_version)
            except ValueError:
                pass

            if not self.module.check_mode:
                releases.sort( key=lambda x: os.path.getctime(os.path.join(releases_path,x)), reverse=True)
                for release in releases[self.keep_releases:]:
                    changes += self.delete_path(os.path.join(releases_path, release))
            elif len(releases) > self.keep_releases:
                changes += (len(releases) - self.keep_releases)

        return changes

    def _get_file_args(self, path):
        file_args = self.file_args.copy()
        file_args['path'] = path
        return file_args

    def _get_last_release(self, current_path):
        previous_release = None
        previous_release_path = None

        if os.path.lexists(current_path):
            previous_release_path   = os.path.realpath(current_path)
            previous_release        = os.path.basename(previous_release_path)

        return previous_release, previous_release_path

def main():

    module = AnsibleModule(
        argument_spec = dict(
            path                = dict(aliases=['dest'], required=True, type='str'),
            release             = dict(required=False, type='str', default=None),
            releases_path       = dict(required=False, type='str', default='releases'),
            shared_path         = dict(required=False, type='str', default='shared'),
            current_path        = dict(required=False, type='str', default='current'),
            keep_releases       = dict(required=False, type='int', default=5),
            clean               = dict(required=False, type='bool', default=True),
            unfinished_filename = dict(required=False, type='str', default='DEPLOY_UNFINISHED'),
            state               = dict(required=False, choices=['present', 'absent', 'clean', 'finalize', 'query'], default='present')
        ),
        add_file_common_args = True,
        supports_check_mode  = True
    )

    deploy_helper = DeployHelper(module)
    facts  = deploy_helper.gather_facts()

    result = {
        'state': deploy_helper.state
    }

    changes = 0

    if deploy_helper.state == 'query':
        result['ansible_facts'] = { 'deploy_helper': facts }

    elif deploy_helper.state == 'present':
        deploy_helper.check_link(facts['current_path'])
        changes += deploy_helper.create_path(facts['project_path'])
        changes += deploy_helper.create_path(facts['releases_path'])
        if deploy_helper.shared_path:
            changes += deploy_helper.create_path(facts['shared_path'])

        result['ansible_facts'] = { 'deploy_helper': facts }

    elif deploy_helper.state == 'finalize':
        if not deploy_helper.release:
            module.fail_json(msg="'release' is a required parameter for state=finalize (try the 'deploy_helper.new_release' fact)")
        if deploy_helper.keep_releases <= 0:
            module.fail_json(msg="'keep_releases' should be at least 1")

        changes += deploy_helper.remove_unfinished_file(facts['new_release_path'])
        changes += deploy_helper.create_link(facts['new_release_path'], facts['current_path'])
        if deploy_helper.clean:
            changes += deploy_helper.remove_unfinished_link(facts['project_path'])
            changes += deploy_helper.remove_unfinished_builds(facts['releases_path'])
            changes += deploy_helper.cleanup(facts['releases_path'], facts['new_release'])

    elif deploy_helper.state == 'clean':
        changes += deploy_helper.remove_unfinished_link(facts['project_path'])
        changes += deploy_helper.remove_unfinished_builds(facts['releases_path'])
        changes += deploy_helper.cleanup(facts['releases_path'], facts['new_release'])

    elif deploy_helper.state == 'absent':
        # destroy the facts
        result['ansible_facts'] = { 'deploy_helper': [] }
        changes += deploy_helper.delete_path(facts['project_path'])

    if changes > 0:
        result['changed'] = True
    else:
        result['changed'] = False

    module.exit_json(**result)


# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
