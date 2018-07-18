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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

########################################################
import datetime
import os
import platform
import random
import shutil
import socket
import sys
import time

try:  # py3
    from io import StringIO
except ImportError:
    try:  # py2, C version
        from cStringIO import StringIO
    except ImportError:  # py2 pure python version
        from StringIO import StringIO

from ansible.cli import CLI
from ansible import constants as C
from ansible.errors import AnsibleOptionsError
from ansible.module_utils._text import to_native
from ansible.cli.adhoc import AdHocCLI
from ansible.cli.playbook import PlaybookCLI

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


########################################################

class PullCLI(CLI):
    ''' is used to up a remote copy of ansible on each managed node,
        each set to run via cron and update playbook source via a source repository.
        This inverts the default *push* architecture of ansible into a *pull* architecture,
        which has near-limitless scaling potential.

        The setup playbook can be tuned to change the cron frequency, logging locations, and parameters to ansible-pull.
        This is useful both for extreme scale-out as well as periodic remediation.
        Usage of the 'fetch' module to retrieve logs from ansible-pull runs would be an
        excellent way to gather and analyze remote logs from ansible-pull.
    '''

    DEFAULT_REPO_TYPE = 'git'
    DEFAULT_PLAYBOOK = 'local.yml'
    REPO_CHOICES = ('git', 'subversion', 'hg', 'bzr')
    PLAYBOOK_ERRORS = {
        1: 'File does not exist',
        2: 'File is not readable',
    }
    SUPPORTED_REPO_MODULES = ['git']
    ARGUMENTS = {'playbook.yml': 'The name of one the YAML format files to run as an Ansible playbook.'
                                 'This can be a relative path within the checkout. By default, Ansible will'
                                 "look for a playbook based on the host's fully-qualified domain name,"
                                 'on the host hostname and finally a playbook named *local.yml*.', }

    SKIP_INVENTORY_DEFAULTS = True

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage='%prog -U <repository> [options] [<playbook.yml>]',
            connect_opts=True,
            vault_opts=True,
            runtask_opts=True,
            subset_opts=True,
            check_opts=False,  # prevents conflict of --checkout/-C and --check/-C
            inventory_opts=True,
            module_opts=True,
            runas_prompt_opts=True,
            desc="pulls playbooks from a VCS repo and executes them for the local host",
        )

        # options unique to pull
        self.parser.add_option('--purge', default=False, action='store_true', help='purge checkout after playbook run')
        self.parser.add_option('-o', '--only-if-changed', dest='ifchanged', default=False, action='store_true',
                               help='only run the playbook if the repository has been updated')
        self.parser.add_option('-s', '--sleep', dest='sleep', default=None,
                               help='sleep for random interval (between 0 and n number of seconds) before starting. '
                                    'This is a useful way to disperse git requests')
        self.parser.add_option('-f', '--force', dest='force', default=False, action='store_true',
                               help='run the playbook even if the repository could not be updated')
        self.parser.add_option('-d', '--directory', dest='dest', default=None, help='directory to checkout repository to')
        self.parser.add_option('-U', '--url', dest='url', default=None, help='URL of the playbook repository')
        self.parser.add_option('--full', dest='fullclone', action='store_true', help='Do a full clone, instead of a shallow one.')
        self.parser.add_option('-C', '--checkout', dest='checkout',
                               help='branch/tag/commit to checkout. Defaults to behavior of repository module.')
        self.parser.add_option('--accept-host-key', default=False, dest='accept_host_key', action='store_true',
                               help='adds the hostkey for the repo url if not already added')
        self.parser.add_option('-m', '--module-name', dest='module_name', default=self.DEFAULT_REPO_TYPE,
                               help='Repository module name, which ansible will use to check out the repo. Choices are %s. Default is %s.'
                                    % (self.REPO_CHOICES, self.DEFAULT_REPO_TYPE))
        self.parser.add_option('--verify-commit', dest='verify', default=False, action='store_true',
                               help='verify GPG signature of checked out commit, if it fails abort running the playbook. '
                                    'This needs the corresponding VCS module to support such an operation')
        self.parser.add_option('--clean', dest='clean', default=False, action='store_true',
                               help='modified files in the working repository will be discarded')
        self.parser.add_option('--track-subs', dest='tracksubs', default=False, action='store_true',
                               help='submodules will track the latest changes. This is equivalent to specifying the --remote flag to git submodule update')
        # add a subset of the check_opts flag group manually, as the full set's
        # shortcodes conflict with above --checkout/-C
        self.parser.add_option("--check", default=False, dest='check', action='store_true',
                               help="don't make any changes; instead, try to predict some of the changes that may occur")
        self.parser.add_option("--diff", default=C.DIFF_ALWAYS, dest='diff', action='store_true',
                               help="when changing (small) files and templates, show the differences in those files; works great with --check")

        super(PullCLI, self).parse()

        if not self.options.dest:
            hostname = socket.getfqdn()
            # use a hostname dependent directory, in case of $HOME on nfs
            self.options.dest = os.path.join('~/.ansible/pull', hostname)
        self.options.dest = os.path.expandvars(os.path.expanduser(self.options.dest))

        if os.path.exists(self.options.dest) and not os.path.isdir(self.options.dest):
            raise AnsibleOptionsError("%s is not a valid or accessible directory." % self.options.dest)

        if self.options.sleep:
            try:
                secs = random.randint(0, int(self.options.sleep))
                self.options.sleep = secs
            except ValueError:
                raise AnsibleOptionsError("%s is not a number." % self.options.sleep)

        if not self.options.url:
            raise AnsibleOptionsError("URL for repository not specified, use -h for help")

        if self.options.module_name not in self.SUPPORTED_REPO_MODULES:
            raise AnsibleOptionsError("Unsupported repo module %s, choices are %s" % (self.options.module_name, ','.join(self.SUPPORTED_REPO_MODULES)))

        display.verbosity = self.options.verbosity
        self.validate_conflicts(vault_opts=True)

    def _fetch_repo(self):
        # setup module specific options from CLI
        if self.options.module_name == 'git':
            repo_opts = "name=%s dest=%s" % (self.options.url, self.options.dest)
            if self.options.checkout:
                repo_opts += ' version=%s' % self.options.checkout
            if self.options.accept_host_key:
                repo_opts += ' accept_hostkey=yes'
            if self.options.private_key_file:
                repo_opts += ' key_file=%s' % self.options.private_key_file
            if self.options.verify:
                repo_opts += ' verify_commit=yes'
            if self.options.tracksubs:
                repo_opts += ' track_submodules=yes'
            if not self.options.fullclone:
                repo_opts += ' depth=1'
        elif self.options.module_name == 'subversion':
            repo_opts = "repo=%s dest=%s" % (self.options.url, self.options.dest)
            if self.options.checkout:
                repo_opts += ' revision=%s' % self.options.checkout
            if not self.options.fullclone:
                repo_opts += ' export=yes'
        elif self.options.module_name == 'hg':
            repo_opts = "repo=%s dest=%s" % (self.options.url, self.options.dest)
            if self.options.checkout:
                repo_opts += ' revision=%s' % self.options.checkout
        elif self.options.module_name == 'bzr':
            repo_opts = "name=%s dest=%s" % (self.options.url, self.options.dest)
            if self.options.checkout:
                repo_opts += ' version=%s' % self.options.checkout
        else:
            raise AnsibleOptionsError('Unsupported (%s) SCM module for pull, choices are: %s' % (self.options.module_name, ','.join(self.REPO_CHOICES)))

        if self.options.clean:
            repo_opts += ' force=yes'

        # none takes place of $0
        adhoc_args = [None, '-i', 'localhost,', '-m', self.options.module_name, '-a', repo_opts, 'localhost', '-c', 'local']

        for ev in self.options.extra_vars:
            adhoc_args.extend(['-e', ev])

        if self.options.verbosity > 0:
            verbose = ''
            verbose += '-%s' % ''.join(["v" for x in range(0, self.options.verbosity)])
            adhoc_args.extend([verbose])

        adhoc = AdHocCLI(adhoc_args)
        adhoc.parse()

        # Nap?
        if self.options.sleep:
            display.display("Sleeping for %d seconds..." % self.options.sleep)
            time.sleep(self.options.sleep)

        display.debug("running ansible with VCS module to checkout repo")
        # redirect stds
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        mystdout = StringIO()
        mystderr = StringIO()

        # actually run command
        display.debug("running ansible with VCS module to checkout repo")
        rc = adhoc.run()

        display.debug(mystdout.getvalue())
        display.debug(mystderr.getvalue())

        # restore normalcy
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        if rc != 0:
            if self.options.force:
                display.warning("Unable to update repository. Continuing with (forced) run of playbook.")
            else:
                display.error("Unable to fetch repository. Quitting")
                sys.exit(0)
        elif self.options.ifchanged and '"changed": true' not in mystdout.getvalue():
            display.display("Repository has not changed, quitting.")
            sys.exit(0)
        else:
            display.display("Repository retrieved.")

    def try_playbook(self, path):
        if not os.path.exists(path):
            return 1
        if not os.access(path, os.R_OK):
            return 2
        return 0

    def select_playbook(self, path):
        playbook = None
        if self.args and self.args[0] is not None:
            playbook = os.path.join(path, self.args[0])
            rc = self.try_playbook(playbook)
            if rc != 0:
                display.warning("%s: %s" % (playbook, self.PLAYBOOK_ERRORS[rc]))
                return None
            return playbook
        else:
            fqdn = socket.getfqdn()
            hostpb = os.path.join(path, fqdn + '.yml')
            shorthostpb = os.path.join(path, fqdn.split('.')[0] + '.yml')
            localpb = os.path.join(path, self.DEFAULT_PLAYBOOK)
            errors = []
            for pb in [hostpb, shorthostpb, localpb]:
                rc = self.try_playbook(pb)
                if rc == 0:
                    playbook = pb
                    break
                else:
                    errors.append("%s: %s" % (pb, self.PLAYBOOK_ERRORS[rc]))
            if playbook is None:
                display.warning("\n".join(errors))
            return playbook

    def run(self):
        ''' fetch a repo and run included playbook for this host '''

        super(PullCLI, self).run()

        # log command line
        now = datetime.datetime.now()
        display.display(now.strftime("Starting Ansible Pull at %F %T"))
        display.display(' '.join(sys.argv))

        # run adhoc to retrieve the repo
        self._fetch_repo()

        # select playbook
        playbook = self.select_playbook(self.options.dest)
        if playbook is None:
            raise AnsibleOptionsError("Could not find a playbook to run.")

        # get playbook arguments
        playbook_args = [None, '-c', 'local', playbook]

        for ev in self.options.extra_vars:
            playbook_args.extend(['-e', ev])

        if self.options.verbosity > 0:
            verbose = ''
            verbose += '-%s' % ''.join(["v" for x in range(0, self.options.verbosity)])
            playbook_args.extend([verbose])
        if self.options.ask_sudo_pass or self.options.ask_su_pass or self.options.become_ask_pass:
            playbook_args.extend(['--ask-become-pass'])
        if self.options.vault_password_files:
            for vault_password_file in self.options.vault_password_files:
                playbook_args.extend(['--vault-password-file', vault_password_file])
        if self.options.skip_tags:
            playbook_args.extend(['--skip-tags', to_native(u','.join(self.options.skip_tags))])
        if self.options.tags:
            playbook_args.extend(['-t', to_native(u','.join(self.options.tags))])
        if self.options.subset:
            playbook_args.extend(['-l', self.options.subset])
        else:
            node = platform.node()
            host = socket.getfqdn()
            subset = "localhost,%s,127.0.0.1" % ','.join(set([host, node, host.split('.')[0], node.split('.')[0]]))
            playbook_args.extend(['-l', subset])
        if self.options.check:
            playbook_args.extend(['-C'])
        if self.options.diff:
            playbook_args.extend(['-D'])

        os.chdir(self.options.dest)

        # inventory options
        if getattr(self.options, 'inventory', []):
            inv_opts = ''
            for inv in self.options.inventory:
                if isinstance(inv, list):
                    inv_opts += "%s" % ','.join(inv)
                elif ',' in inv or os.path.exists(inv):
                    inv_opts += "%s" % inv
        else:
            inv_opts = ''

        playbook_args.extend(['-i', inv_opts])

        ansible_playbook = PlaybookCLI(playbook_args)
        ansible_playbook.parse()

        # RUN THE PLAYBOOK COMMAND
        display.debug("running ansible-playbook to do actual work")
        rc = ansible_playbook.run()

        if self.options.purge:
            os.chdir('/')
            try:
                shutil.rmtree(self.options.dest)
            except Exception as e:
                display.error("Failed to remove %s: %s" % (self.options.dest, to_native(e)))

        return rc
