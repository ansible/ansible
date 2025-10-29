# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import copy
import dataclasses
import inspect
import operator
import argparse
import os
import os.path
import sys
import time
import typing as t

import yaml

import ansible
from ansible import constants as C
from ansible._internal import _templating
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.yaml import HAS_LIBYAML, yaml_load
from ansible.release import __version__
from ansible.utils.path import unfrackpath

from ansible._internal._datatag._tags import TrustedAsTemplate, Origin


#
# Special purpose OptionParsers
#
class SortingHelpFormatter(argparse.HelpFormatter):
    def add_arguments(self, actions):
        actions = sorted(actions, key=operator.attrgetter('option_strings'))
        super(SortingHelpFormatter, self).add_arguments(actions)


@dataclasses.dataclass(frozen=True, kw_only=True)
class DeprecatedArgument:
    version: str
    """The Ansible version that will remove the deprecated argument."""

    option: str | None = None
    """The specific option string that is deprecated; None applies to all options for this argument."""

    alternatives: str | None = None
    """The options to use instead."""

    def is_deprecated(self, option: str) -> bool:
        """Return True if the given option is deprecated, otherwise False."""
        return self.option is None or option == self.option

    def check(self, option: str) -> None:
        """Display a deprecation warning if the given option is deprecated."""
        if not self.is_deprecated(option):
            return

        from ansible.utils.display import Display

        Display().deprecated(  # pylint: disable=ansible-invalid-deprecated-version
            msg=f'The {option!r} argument is deprecated.',
            version=self.version,
            help_text=f'Use {self.alternatives} instead.' if self.alternatives else None
        )


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        self.__actions: dict[str | None, type[argparse.Action]] = {}

        super().__init__(*args, **kwargs)

    def register(self, registry_name, value, object):
        """Track registration of actions so that they can be resolved later by name, without depending on the internals of ArgumentParser."""
        if registry_name == 'action':
            self.__actions[value] = object

        super().register(registry_name, value, object)

    def _patch_argument(self, args: tuple[str, ...], kwargs: dict[str, t.Any]) -> None:
        """
        Patch `kwargs` for an `add_argument` call using the given `args` and `kwargs`.
        This is used to apply tags to entire categories of CLI arguments.
        """
        name = args[0]
        action = kwargs.get('action')
        resolved_action = self.__actions.get(action, action)  # get the action by name, or use as-is (assume it's a subclass of argparse.Action)
        action_signature = inspect.signature(resolved_action.__init__)

        if action_signature.parameters.get('type'):
            arg_type = kwargs.get('type', str)

            if not callable(arg_type):
                raise ValueError(f'Argument {name!r} requires a callable for the {"type"!r} parameter, not {arg_type!r}.')

            wrapped_arg_type = _tagged_type_factory(name, arg_type)

            kwargs.update(type=wrapped_arg_type)

    def _patch_parser(self, parser):
        """Patch and return the given parser to intercept the `add_argument` method for further patching."""
        parser_add_argument = parser.add_argument

        def add_argument(*ag_args, **ag_kwargs):
            self._patch_argument(ag_args, ag_kwargs)

            parser_add_argument(*ag_args, **ag_kwargs)

        parser.add_argument = add_argument

        return parser

    def add_subparsers(self, *args, **kwargs):
        sub = super().add_subparsers(*args, **kwargs)
        sub_add_parser = sub.add_parser

        def add_parser(*sub_args, **sub_kwargs):
            return self._patch_parser(sub_add_parser(*sub_args, **sub_kwargs))

        sub.add_parser = add_parser

        return sub

    def add_argument_group(self, *args, **kwargs):
        return self._patch_parser(super().add_argument_group(*args, **kwargs))

    def add_mutually_exclusive_group(self, *args, **kwargs):
        return self._patch_parser(super().add_mutually_exclusive_group(*args, **kwargs))

    def add_argument(self, *args, **kwargs) -> argparse.Action:
        action = kwargs.get('action')
        help = kwargs.get('help')
        if help and action in {'append', 'append_const', 'count', 'extend', PrependListAction}:
            help = f'{help.rstrip(".")}. This argument may be specified multiple times.'
        kwargs['help'] = help

        self._patch_argument(args, kwargs)

        deprecated: DeprecatedArgument | None

        if deprecated := kwargs.pop('deprecated', None):
            action_type = self.__actions.get(action, action)

            class DeprecatedAction(action_type):  # type: ignore[misc, valid-type]
                """A wrapper around an action which handles deprecation warnings."""

                def __call__(self, parser, namespace, values, option_string=None) -> t.Any:
                    deprecated.check(option_string)

                    return super().__call__(parser, namespace, values, option_string)

            kwargs['action'] = DeprecatedAction

        return super().add_argument(*args, **kwargs)


class AnsibleVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ansible_version = to_native(version(getattr(parser, 'prog')))
        print(ansible_version)
        parser.exit()


class UnrecognizedArgument(argparse.Action):
    def __init__(self, option_strings, dest, const=True, default=None, required=False, help=None, metavar=None, nargs=0):
        super(UnrecognizedArgument, self).__init__(option_strings=option_strings, dest=dest, nargs=nargs, const=const,
                                                   default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.error('unrecognized arguments: %s' % option_string)


class PrependListAction(argparse.Action):
    """A near clone of ``argparse._AppendAction``, but designed to prepend list values
    instead of appending.
    """
    def __init__(self, option_strings, dest, nargs=None, const=None, default=None, type=None,
                 choices=None, required=False, help=None, metavar=None):
        if nargs == 0:
            raise ValueError('nargs for append actions must be > 0; if arg '
                             'strings are not supplying the value to append, '
                             'the append const action may be more appropriate')
        if const is not None and nargs != argparse.OPTIONAL:
            raise ValueError('nargs must be %r to supply const' % argparse.OPTIONAL)
        super(PrependListAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar
        )

    def __call__(self, parser, namespace, values, option_string=None):
        items = copy.copy(ensure_value(namespace, self.dest, []))
        items[0:0] = values
        setattr(namespace, self.dest, items)


def ensure_value(namespace, name, value):
    if getattr(namespace, name, None) is None:
        setattr(namespace, name, value)
    return getattr(namespace, name)


#
# Callbacks to validate and normalize Options
#
def unfrack_path(pathsep=False, follow=True):
    """Turn an Option's data into a single path in Ansible locations"""
    def inner(value):
        if pathsep:
            return [unfrackpath(x, follow=follow) for x in value.split(os.pathsep) if x]

        if value == '-':
            return value

        return unfrackpath(value, follow=follow)
    return inner


def maybe_unfrack_path(beacon):

    def inner(value):
        if value.startswith(beacon):
            return beacon + unfrackpath(value[1:])
        return value
    return inner


def _git_repo_info(repo_path):
    """ returns a string containing git branch, commit id and commit date """
    result = None
    if os.path.exists(repo_path):
        # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
        if os.path.isfile(repo_path):
            try:
                with open(repo_path) as f:
                    gitdir = yaml_load(f).get('gitdir')
                # There is a possibility the .git file to have an absolute path.
                if os.path.isabs(gitdir):
                    repo_path = gitdir
                else:
                    repo_path = os.path.join(repo_path[:-4], gitdir)
            except (OSError, AttributeError):
                return ''
        with open(os.path.join(repo_path, "HEAD")) as f:
            line = f.readline().rstrip("\n")
            if line.startswith("ref:"):
                branch_path = os.path.join(repo_path, line[5:])
            else:
                branch_path = None
        if branch_path and os.path.exists(branch_path):
            branch = '/'.join(line.split('/')[2:])
            with open(branch_path) as f:
                commit = f.readline()[:10]
        else:
            # detached HEAD
            commit = line[:10]
            branch = 'detached HEAD'
            branch_path = os.path.join(repo_path, "HEAD")

        date = time.localtime(os.stat(branch_path).st_mtime)
        if time.daylight == 0:
            offset = time.timezone
        else:
            offset = time.altzone
        result = "({0} {1}) last updated {2} (GMT {3:+04d})".format(branch, commit, time.strftime("%Y/%m/%d %H:%M:%S", date), int(offset / -36))
    else:
        result = ''
    return result


def _gitinfo():
    basedir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    repo_path = os.path.join(basedir, '.git')
    return _git_repo_info(repo_path)


def version(prog=None):
    """ return ansible version """
    if prog:
        result = ["{0} [core {1}]".format(prog, __version__)]
    else:
        result = [__version__]

    gitinfo = _gitinfo()
    if gitinfo:
        result[0] = "{0} {1}".format(result[0], gitinfo)
    result.append("  config file = %s" % C.CONFIG_FILE)
    if C.DEFAULT_MODULE_PATH is None:
        cpath = "Default w/o overrides"
    else:
        cpath = C.DEFAULT_MODULE_PATH

    if HAS_LIBYAML:
        libyaml_fragment = "with libyaml"

        # noinspection PyBroadException
        try:
            from yaml._yaml import get_version_string

            libyaml_fragment += f" v{get_version_string()}"
        except Exception:  # pylint: disable=broad-except
            libyaml_fragment += ", version unknown"
    else:
        libyaml_fragment = "without libyaml"

    result.append("  configured module search path = %s" % cpath)
    result.append("  ansible python module location = %s" % ':'.join(ansible.__path__))
    result.append("  ansible collection location = %s" % ':'.join(C.COLLECTIONS_PATHS))
    result.append("  executable location = %s" % sys.argv[0])
    result.append("  python version = %s (%s)" % (''.join(sys.version.splitlines()), to_native(sys.executable)))
    result.append(f"  jinja version = {_templating.jinja2_version}")
    result.append(f"  pyyaml version = {yaml.__version__} ({libyaml_fragment})")

    return "\n".join(result)


#
# Functions to add pre-canned options to an OptionParser
#

def create_base_parser(prog, desc=None, epilog=None):
    """
    Create an options parser for all ansible scripts
    """
    # base opts
    parser = ArgumentParser(
        prog=prog,
        formatter_class=SortingHelpFormatter,
        epilog=epilog,
        description=desc,
        conflict_handler='resolve',
    )
    version_help = "show program's version number, config file location, configured module search path," \
                   " module location, executable location and exit"

    parser.add_argument('--version', action=AnsibleVersion, nargs=0, help=version_help)
    add_verbosity_options(parser)
    return parser


def add_verbosity_options(parser):
    """Add options for verbosity"""
    parser.add_argument('-v', '--verbose', dest='verbosity', default=C.DEFAULT_VERBOSITY, action="count",
                        help="Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, "
                             "the builtin plugins currently evaluate up to -vvvvvv. A reasonable level to start is -vvv, "
                             "connection debugging might require -vvvv.")


def add_async_options(parser):
    """Add options for commands which can launch async tasks"""
    parser.add_argument('-P', '--poll', default=C.DEFAULT_POLL_INTERVAL, type=int, dest='poll_interval',
                        help="set the poll interval if using -B (default=%s)" % C.DEFAULT_POLL_INTERVAL)
    parser.add_argument('-B', '--background', dest='seconds', type=int, default=0,
                        help='run asynchronously, failing after X seconds (default=N/A)')


def add_basedir_options(parser):
    """Add options for commands which can set a playbook basedir"""
    parser.add_argument('--playbook-dir', default=C.PLAYBOOK_DIR, dest='basedir', action='store',
                        help="Since this tool does not use playbooks, use this as a substitute playbook directory. "
                             "This sets the relative path for many features including roles/ group_vars/ etc.",
                        type=unfrack_path())


def add_check_options(parser):
    """Add options for commands which can run with diagnostic information of tasks"""
    parser.add_argument("-C", "--check", default=False, dest='check', action='store_true',
                        help="don't make any changes; instead, try to predict some of the changes that may occur")
    parser.add_argument("-D", "--diff", default=C.DIFF_ALWAYS, dest='diff', action='store_true',
                        help="when changing (small) files and templates, show the differences in those"
                             " files; works great with --check")


def add_connect_options(parser):
    """Add options for commands which need to connection to other hosts"""
    connect_group = parser.add_argument_group("Connection Options", "control as whom and how to connect to hosts")

    connect_group.add_argument('--private-key', '--key-file', default=C.DEFAULT_PRIVATE_KEY_FILE, dest='private_key_file',
                               help='use this file to authenticate the connection', type=unfrack_path())
    connect_group.add_argument('-u', '--user', default=C.DEFAULT_REMOTE_USER, dest='remote_user',
                               help='connect as this user (default=%s)' % C.DEFAULT_REMOTE_USER)
    connect_group.add_argument('-c', '--connection', dest='connection', default=C.DEFAULT_TRANSPORT,
                               help="connection type to use (default=%s)" % C.DEFAULT_TRANSPORT)
    connect_group.add_argument('-T', '--timeout', default=None, type=int, dest='timeout',
                               help="override the connection timeout in seconds (default depends on connection)")

    # ssh only
    connect_group.add_argument('--ssh-common-args', default=None, dest='ssh_common_args',
                               help="specify common arguments to pass to sftp/scp/ssh (e.g. ProxyCommand)")
    connect_group.add_argument('--sftp-extra-args', default=None, dest='sftp_extra_args',
                               help="specify extra arguments to pass to sftp only (e.g. -f, -l)")
    connect_group.add_argument('--scp-extra-args', default=None, dest='scp_extra_args',
                               help="specify extra arguments to pass to scp only (e.g. -l)")
    connect_group.add_argument('--ssh-extra-args', default=None, dest='ssh_extra_args',
                               help="specify extra arguments to pass to ssh only (e.g. -R)")

    parser.add_argument_group(connect_group)

    connect_password_group = parser.add_mutually_exclusive_group()
    connect_password_group.add_argument('-k', '--ask-pass', default=C.DEFAULT_ASK_PASS, dest='ask_pass', action='store_true',
                                        help='ask for connection password')
    connect_password_group.add_argument('--connection-password-file', '--conn-pass-file', default=C.CONNECTION_PASSWORD_FILE, dest='connection_password_file',
                                        help="Connection password file", type=unfrack_path(), action='store')

    parser.add_argument_group(connect_password_group)


def add_fork_options(parser):
    """Add options for commands that can fork worker processes"""
    parser.add_argument('-f', '--forks', dest='forks', default=C.DEFAULT_FORKS, type=int,
                        help="specify number of parallel processes to use (default=%s)" % C.DEFAULT_FORKS)


def add_inventory_options(parser):
    """Add options for commands that utilize inventory"""
    parser.add_argument('-i', '--inventory', '--inventory-file', dest='inventory', action="append",
                        help="specify inventory host path or comma separated host list",
                        deprecated=DeprecatedArgument(version='2.23', option='--inventory-file', alternatives="-i or --inventory"))
    parser.add_argument('--list-hosts', dest='listhosts', action='store_true',
                        help='outputs a list of matching hosts; does not execute anything else')
    parser.add_argument('-l', '--limit', default=C.DEFAULT_SUBSET, dest='subset',
                        help='further limit selected hosts to an additional pattern')
    parser.add_argument('--flush-cache', dest='flush_cache', action='store_true',
                        help="clear the fact cache for every host in inventory")


def add_meta_options(parser):
    """Add options for commands which can launch meta tasks from the command line"""
    parser.add_argument('--force-handlers', default=C.DEFAULT_FORCE_HANDLERS, dest='force_handlers', action='store_true',
                        help="run handlers even if a task fails")


def add_module_options(parser):
    """Add options for commands that load modules"""
    module_path = C.config.get_configuration_definition('DEFAULT_MODULE_PATH').get('default', '')
    parser.add_argument('-M', '--module-path', dest='module_path', default=None,
                        help="prepend colon-separated path(s) to module library (default=%s)" % module_path,
                        type=unfrack_path(pathsep=True), action=PrependListAction)


def add_output_options(parser):
    """Add options for commands which can change their output"""
    parser.add_argument('-o', '--one-line', dest='one_line', action='store_true', help='condense output',
                        deprecated=DeprecatedArgument(version='2.23', alternatives='callback configuration to enable the oneline callback'))
    parser.add_argument('-t', '--tree', dest='tree', default=None, help='log output to this directory',
                        deprecated=DeprecatedArgument(version='2.23', alternatives='callback configuration to enable the tree callback'))


def add_runas_options(parser):
    """
    Add options for commands which can run tasks as another user

    Note that this includes the options from add_runas_prompt_options().  Only one of these
    functions should be used.
    """
    runas_group = parser.add_argument_group("Privilege Escalation Options", "control how and which user you become as on target hosts")

    # consolidated privilege escalation (become)
    runas_group.add_argument("-b", "--become", default=C.DEFAULT_BECOME, action="store_true", dest='become',
                             help="run operations with become (does not imply password prompting)")
    runas_group.add_argument('--become-method', dest='become_method', default=C.DEFAULT_BECOME_METHOD,
                             help='privilege escalation method to use (default=%s)' % C.DEFAULT_BECOME_METHOD +
                                  ', use `ansible-doc -t become -l` to list valid choices.')
    runas_group.add_argument('--become-user', default=None, dest='become_user', type=str,
                             help='run operations as this user (default=%s)' % C.DEFAULT_BECOME_USER)

    parser.add_argument_group(runas_group)

    add_runas_prompt_options(parser)


def add_runas_prompt_options(parser, runas_group=None):
    """
    Add options for commands which need to prompt for privilege escalation credentials

    Note that add_runas_options() includes these options already.  Only one of the two functions
    should be used.
    """
    if runas_group is not None:
        parser.add_argument_group(runas_group)

    runas_pass_group = parser.add_mutually_exclusive_group()

    runas_pass_group.add_argument('-K', '--ask-become-pass', dest='become_ask_pass', action='store_true',
                                  default=C.DEFAULT_BECOME_ASK_PASS,
                                  help='ask for privilege escalation password')
    runas_pass_group.add_argument('--become-password-file', '--become-pass-file', default=C.BECOME_PASSWORD_FILE, dest='become_password_file',
                                  help="Become password file", type=unfrack_path(), action='store')

    parser.add_argument_group(runas_pass_group)


def add_runtask_options(parser):
    """Add options for commands that run a task"""
    parser.add_argument('-e', '--extra-vars', dest="extra_vars", action="append", type=maybe_unfrack_path('@'),
                        help="set additional variables as key=value or YAML/JSON, if filename prepend with @", default=[])


def add_tasknoplay_options(parser):
    """Add options for commands that run a task w/o a defined play"""
    parser.add_argument('--task-timeout', type=int, dest="task_timeout", action="store", default=C.TASK_TIMEOUT,
                        help="set task timeout limit in seconds, must be positive integer.")


def add_subset_options(parser):
    """Add options for commands which can run a subset of tasks"""
    parser.add_argument('-t', '--tags', dest='tags', default=C.TAGS_RUN, action='append',
                        help="only run plays and tasks tagged with these values")
    parser.add_argument('--skip-tags', dest='skip_tags', default=C.TAGS_SKIP, action='append',
                        help="only run plays and tasks whose tags do not match these values")


def add_vault_options(parser):
    """Add options for loading vault files"""
    parser.add_argument('--vault-id', default=[], dest='vault_ids', action='append', type=str,
                        help='the vault identity to use')
    base_group = parser.add_mutually_exclusive_group()
    base_group.add_argument('-J', '--ask-vault-password', '--ask-vault-pass', default=C.DEFAULT_ASK_VAULT_PASS, dest='ask_vault_pass', action='store_true',
                            help='ask for vault password')
    base_group.add_argument('--vault-password-file', '--vault-pass-file', default=[], dest='vault_password_files',
                            help="vault password file", type=unfrack_path(follow=False), action='append')


def _tagged_type_factory(name: str, func: t.Callable[[str], object], /) -> t.Callable[[str], object]:
    """
    Return a callable that wraps the given function.
    The result of the wrapped function will be tagged with Origin.
    It will also be tagged with TrustedAsTemplate if it is equal to the original input string.
    """
    def tag_value(value: str) -> object:
        result = func(value)

        if result is value or func is str:
            # Values which are not mutated are automatically trusted for templating.
            # The `is` reference equality is critically important, as other types may only alter the tags, so object equality is
            # not sufficient to prevent them being tagged as trusted when they should not.
            # Explicitly include all usages using the `str` type factory since it strips tags.
            result = TrustedAsTemplate().tag(result)

        if not (origin := Origin.get_tag(value)):
            origin = Origin(description=f'<CLI option {name!r}>')

        return origin.tag(result)

    tag_value._name = name  # simplify debugging by attaching the argument name to the function

    return tag_value
