# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import os
import platform
import random
import shutil
import socket
import sys
import time

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleOptionsError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six.moves import shlex_quote
from ansible.plugins.loader import module_loader
from ansible.utils.cmd_functions import run_cmd
from ansible.utils.display import Display

display = Display()


class PullCLI(CLI):
    ''' Used to pull a remote copy of ansible on each managed node,
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

    @staticmethod
    def _get_inv_cli():
        inv_opts = ''
        if context.CLIARGS.get('inventory', False):
            for inv in context.CLIARGS['inventory']:
                if isinstance(inv, list):
                    inv_opts += " -i '%s' " % ','.join(inv)
                elif ',' in inv or os.path.exists(inv):
                    inv_opts += ' -i %s ' % inv

        return inv_opts

    def init_parser(self):
        ''' create an options parser for bin/ansible '''

        super(PullCLI, self).init_parser(
            usage='%prog -U <repository> [options] [<playbook.yml>]',
            desc="pulls playbooks from a VCS repo and executes them for the local host")

        # Do not add check_options as there's a conflict with --checkout/-C
        opt_help.add_connect_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_runtask_options(self.parser)
        opt_help.add_subset_options(self.parser)
        opt_help.add_inventory_options(self.parser)
        opt_help.add_module_options(self.parser)
        opt_help.add_runas_prompt_options(self.parser)

        self.parser.add_argument('args', help='Playbook(s)', metavar='playbook.yml', nargs='*')

        # options unique to pull
        self.parser.add_argument('--purge', default=False, action='store_true', help='purge checkout after playbook run')
        self.parser.add_argument('-o', '--only-if-changed', dest='ifchanged', default=False, action='store_true',
                                 help='only run the playbook if the repository has been updated')
        self.parser.add_argument('-s', '--sleep', dest='sleep', default=None,
                                 help='sleep for random interval (between 0 and n number of seconds) before starting. '
                                      'This is a useful way to disperse git requests')
        self.parser.add_argument('-f', '--force', dest='force', default=False, action='store_true',
                                 help='run the playbook even if the repository could not be updated')
        self.parser.add_argument('-d', '--directory', dest='dest', default=None, help='directory to checkout repository to')
        self.parser.add_argument('-U', '--url', dest='url', default=None, help='URL of the playbook repository')
        self.parser.add_argument('--full', dest='fullclone', action='store_true', help='Do a full clone, instead of a shallow one.')
        self.parser.add_argument('-C', '--checkout', dest='checkout',
                                 help='branch/tag/commit to checkout. Defaults to behavior of repository module.')
        self.parser.add_argument('--accept-host-key', default=False, dest='accept_host_key', action='store_true',
                                 help='adds the hostkey for the repo url if not already added')
        self.parser.add_argument('-m', '--module-name', dest='module_name', default=self.DEFAULT_REPO_TYPE,
                                 help='Repository module name, which ansible will use to check out the repo. Choices are %s. Default is %s.'
                                      % (self.REPO_CHOICES, self.DEFAULT_REPO_TYPE))
        self.parser.add_argument('--verify-commit', dest='verify', default=False, action='store_true',
                                 help='verify GPG signature of checked out commit, if it fails abort running the playbook. '
                                      'This needs the corresponding VCS module to support such an operation')
        self.parser.add_argument('--clean', dest='clean', default=False, action='store_true',
                                 help='modified files in the working repository will be discarded')
        self.parser.add_argument('--track-subs', dest='tracksubs', default=False, action='store_true',
                                 help='submodules will track the latest changes. This is equivalent to specifying the --remote flag to git submodule update')
        # add a subset of the check_opts flag group manually, as the full set's
        # shortcodes conflict with above --checkout/-C
        self.parser.add_argument("--check", default=False, dest='check', action='store_true',
                                 help="don't make any changes; instead, try to predict some of the changes that may occur")
        self.parser.add_argument("--diff", default=C.DIFF_ALWAYS, dest='diff', action='store_true',
                                 help="when changing (small) files and templates, show the differences in those files; works great with --check")

    def post_process_args(self, options):
        options = super(PullCLI, self).post_process_args(options)

        if not options.dest:
            hostname = socket.getfqdn()
            # use a hostname dependent directory, in case of $HOME on nfs
            options.dest = os.path.join('~/.ansible/pull', hostname)
        options.dest = os.path.expandvars(os.path.expanduser(options.dest))

        if os.path.exists(options.dest) and not os.path.isdir(options.dest):
            raise AnsibleOptionsError("%s is not a valid or accessible directory." % options.dest)

        if options.sleep:
            try:
                secs = random.randint(0, int(options.sleep))
                options.sleep = secs
            except ValueError:
                raise AnsibleOptionsError("%s is not a number." % options.sleep)

        if not options.url:
            raise AnsibleOptionsError("URL for repository not specified, use -h for help")

        if options.module_name not in self.SUPPORTED_REPO_MODULES:
            raise AnsibleOptionsError("Unsupported repo module %s, choices are %s" % (options.module_name, ','.join(self.SUPPORTED_REPO_MODULES)))

        display.verbosity = options.verbosity
        self.validate_conflicts(options)

        return options

    def run(self):
        ''' use Runner lib to do SSH things '''

        super(PullCLI, self).run()

        # log command line
        now = datetime.datetime.now()
        display.display(now.strftime("Starting Ansible Pull at %F %T"))
        display.display(' '.join(sys.argv))

        # Build Checkout command
        # Now construct the ansible command
        node = platform.node()
        host = socket.getfqdn()
        limit_opts = 'localhost,%s,127.0.0.1' % ','.join(set([host, node, host.split('.')[0], node.split('.')[0]]))
        base_opts = '-c local '
        if context.CLIARGS['verbosity'] > 0:
            base_opts += ' -%s' % ''.join(["v" for x in range(0, context.CLIARGS['verbosity'])])

        # Attempt to use the inventory passed in as an argument
        # It might not yet have been downloaded so use localhost as default
        inv_opts = self._get_inv_cli()
        if not inv_opts:
            inv_opts = " -i localhost, "
            # avoid interpreter discovery since we already know which interpreter to use on localhost
            inv_opts += '-e %s ' % shlex_quote('ansible_python_interpreter=%s' % sys.executable)

        # SCM specific options
        if context.CLIARGS['module_name'] == 'git':
            repo_opts = "name=%s dest=%s" % (context.CLIARGS['url'], context.CLIARGS['dest'])
            if context.CLIARGS['checkout']:
                repo_opts += ' version=%s' % context.CLIARGS['checkout']

            if context.CLIARGS['accept_host_key']:
                repo_opts += ' accept_hostkey=yes'

            if context.CLIARGS['private_key_file']:
                repo_opts += ' key_file=%s' % context.CLIARGS['private_key_file']

            if context.CLIARGS['verify']:
                repo_opts += ' verify_commit=yes'

            if context.CLIARGS['tracksubs']:
                repo_opts += ' track_submodules=yes'

            if not context.CLIARGS['fullclone']:
                repo_opts += ' depth=1'
        elif context.CLIARGS['module_name'] == 'subversion':
            repo_opts = "repo=%s dest=%s" % (context.CLIARGS['url'], context.CLIARGS['dest'])
            if context.CLIARGS['checkout']:
                repo_opts += ' revision=%s' % context.CLIARGS['checkout']
            if not context.CLIARGS['fullclone']:
                repo_opts += ' export=yes'
        elif context.CLIARGS['module_name'] == 'hg':
            repo_opts = "repo=%s dest=%s" % (context.CLIARGS['url'], context.CLIARGS['dest'])
            if context.CLIARGS['checkout']:
                repo_opts += ' revision=%s' % context.CLIARGS['checkout']
        elif context.CLIARGS['module_name'] == 'bzr':
            repo_opts = "name=%s dest=%s" % (context.CLIARGS['url'], context.CLIARGS['dest'])
            if context.CLIARGS['checkout']:
                repo_opts += ' version=%s' % context.CLIARGS['checkout']
        else:
            raise AnsibleOptionsError('Unsupported (%s) SCM module for pull, choices are: %s'
                                      % (context.CLIARGS['module_name'],
                                         ','.join(self.REPO_CHOICES)))

        # options common to all supported SCMS
        if context.CLIARGS['clean']:
            repo_opts += ' force=yes'

        path = module_loader.find_plugin(context.CLIARGS['module_name'])
        if path is None:
            raise AnsibleOptionsError(("module '%s' not found.\n" % context.CLIARGS['module_name']))

        bin_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        # hardcode local and inventory/host as this is just meant to fetch the repo
        cmd = '%s/ansible %s %s -m %s -a "%s" all -l "%s"' % (bin_path, inv_opts, base_opts,
                                                              context.CLIARGS['module_name'],
                                                              repo_opts, limit_opts)
        for ev in context.CLIARGS['extra_vars']:
            cmd += ' -e %s' % shlex_quote(ev)

        # Nap?
        if context.CLIARGS['sleep']:
            display.display("Sleeping for %d seconds..." % context.CLIARGS['sleep'])
            time.sleep(context.CLIARGS['sleep'])

        # RUN the Checkout command
        display.debug("running ansible with VCS module to checkout repo")
        display.vvvv('EXEC: %s' % cmd)
        rc, b_out, b_err = run_cmd(cmd, live=True)

        if rc != 0:
            if context.CLIARGS['force']:
                display.warning("Unable to update repository. Continuing with (forced) run of playbook.")
            else:
                return rc
        elif context.CLIARGS['ifchanged'] and b'"changed": true' not in b_out:
            display.display("Repository has not changed, quitting.")
            return 0

        playbook = self.select_playbook(context.CLIARGS['dest'])
        if playbook is None:
            raise AnsibleOptionsError("Could not find a playbook to run.")

        # Build playbook command
        cmd = '%s/ansible-playbook %s %s' % (bin_path, base_opts, playbook)
        if context.CLIARGS['vault_password_files']:
            for vault_password_file in context.CLIARGS['vault_password_files']:
                cmd += " --vault-password-file=%s" % vault_password_file
        if context.CLIARGS['vault_ids']:
            for vault_id in context.CLIARGS['vault_ids']:
                cmd += " --vault-id=%s" % vault_id

        for ev in context.CLIARGS['extra_vars']:
            cmd += ' -e %s' % shlex_quote(ev)
        if context.CLIARGS['become_ask_pass']:
            cmd += ' --ask-become-pass'
        if context.CLIARGS['skip_tags']:
            cmd += ' --skip-tags "%s"' % to_native(u','.join(context.CLIARGS['skip_tags']))
        if context.CLIARGS['tags']:
            cmd += ' -t "%s"' % to_native(u','.join(context.CLIARGS['tags']))
        if context.CLIARGS['subset']:
            cmd += ' -l "%s"' % context.CLIARGS['subset']
        else:
            cmd += ' -l "%s"' % limit_opts
        if context.CLIARGS['check']:
            cmd += ' -C'
        if context.CLIARGS['diff']:
            cmd += ' -D'

        os.chdir(context.CLIARGS['dest'])

        # redo inventory options as new files might exist now
        inv_opts = self._get_inv_cli()
        if inv_opts:
            cmd += inv_opts

        # RUN THE PLAYBOOK COMMAND
        display.debug("running ansible-playbook to do actual work")
        display.debug('EXEC: %s' % cmd)
        rc, b_out, b_err = run_cmd(cmd, live=True)

        if context.CLIARGS['purge']:
            os.chdir('/')
            try:
                shutil.rmtree(context.CLIARGS['dest'])
            except Exception as e:
                display.error(u"Failed to remove %s: %s" % (context.CLIARGS['dest'], to_text(e)))

        return rc

    @staticmethod
    def try_playbook(path):
        if not os.path.exists(path):
            return 1
        if not os.access(path, os.R_OK):
            return 2
        return 0

    @staticmethod
    def select_playbook(path):
        playbook = None
        errors = []
        if context.CLIARGS['args'] and context.CLIARGS['args'][0] is not None:
            playbooks = []
            for book in context.CLIARGS['args']:
                book_path = os.path.join(path, book)
                rc = PullCLI.try_playbook(book_path)
                if rc != 0:
                    errors.append("%s: %s" % (book_path, PullCLI.PLAYBOOK_ERRORS[rc]))
                    continue
                playbooks.append(book_path)
            if 0 < len(errors):
                display.warning("\n".join(errors))
            elif len(playbooks) == len(context.CLIARGS['args']):
                playbook = " ".join(playbooks)
            return playbook
        else:
            fqdn = socket.getfqdn()
            hostpb = os.path.join(path, fqdn + '.yml')
            shorthostpb = os.path.join(path, fqdn.split('.')[0] + '.yml')
            localpb = os.path.join(path, PullCLI.DEFAULT_PLAYBOOK)
            for pb in [hostpb, shorthostpb, localpb]:
                rc = PullCLI.try_playbook(pb)
                if rc == 0:
                    playbook = pb
                    break
                else:
                    errors.append("%s: %s" % (pb, PullCLI.PLAYBOOK_ERRORS[rc]))
            if playbook is None:
                display.warning("\n".join(errors))
            return playbook
