# coding: utf-8
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import argparse
import os.path
import pathlib
import sys

from jinja2 import Environment, FileSystemLoader

from ansible.module_utils._text import to_bytes

# Pylint doesn't understand Python3 namespace modules.
from ..change_detection import update_file_if_different  # pylint: disable=relative-beyond-top-level
from ..commands import Command  # pylint: disable=relative-beyond-top-level


DEFAULT_TEMPLATE_FILE = pathlib.Path(__file__).parents[4] / 'docs/templates/man.j2'


# from https://www.python.org/dev/peps/pep-0257/
def trim_docstring(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def get_options(optlist):
    ''' get actual options '''

    opts = []
    for opt in optlist:
        res = {
            'desc': opt.help,
            'options': opt.option_strings
        }
        if isinstance(opt, argparse._StoreAction):
            res['arg'] = opt.dest.upper()
        elif not res['options']:
            continue
        opts.append(res)

    return opts


def dedupe_groups(parser):
    action_groups = []
    for action_group in parser._action_groups:
        found = False
        for a in action_groups:
            if a._actions == action_group._actions:
                found = True
                break
        if not found:
            action_groups.append(action_group)
    return action_groups


def get_option_groups(option_parser):
    groups = []
    for action_group in dedupe_groups(option_parser)[1:]:
        group_info = {}
        group_info['desc'] = action_group.description
        group_info['options'] = action_group._actions
        group_info['group_obj'] = action_group
        groups.append(group_info)
    return groups


def opt_doc_list(parser):
    ''' iterate over options lists '''

    results = []
    for option_group in dedupe_groups(parser)[1:]:
        results.extend(get_options(option_group._actions))

    results.extend(get_options(parser._actions))

    return results


# def opts_docs(cli, name):
def opts_docs(cli_class_name, cli_module_name):
    ''' generate doc structure from options '''

    cli_name = 'ansible-%s' % cli_module_name
    if cli_module_name == 'adhoc':
        cli_name = 'ansible'

    # WIth no action/subcommand
    # shared opts set
    # instantiate each cli and ask its options
    cli_klass = getattr(__import__("ansible.cli.%s" % cli_module_name,
                                   fromlist=[cli_class_name]), cli_class_name)
    cli = cli_klass([cli_name])

    # parse the common options
    try:
        cli.init_parser()
    except Exception:
        pass

    # base/common cli info
    docs = {
        'cli': cli_module_name,
        'cli_name': cli_name,
        'usage': cli.parser.format_usage(),
        'short_desc': cli.parser.description,
        'long_desc': trim_docstring(cli.__doc__),
        'actions': {},
        'content_depth': 2,
    }
    option_info = {'option_names': [],
                   'options': [],
                   'groups': []}

    for extras in ('ARGUMENTS'):
        if hasattr(cli, extras):
            docs[extras.lower()] = getattr(cli, extras)

    common_opts = opt_doc_list(cli.parser)
    groups_info = get_option_groups(cli.parser)
    shared_opt_names = []
    for opt in common_opts:
        shared_opt_names.extend(opt.get('options', []))

    option_info['options'] = common_opts
    option_info['option_names'] = shared_opt_names

    option_info['groups'].extend(groups_info)

    docs.update(option_info)

    # now for each action/subcommand
    # force populate parser with per action options

    def get_actions(parser, docs):
        # use class attrs not the attrs on a instance (not that it matters here...)
        try:
            subparser = parser._subparsers._group_actions[0].choices
        except AttributeError:
            subparser = {}

        depth = 0

        for action, parser in subparser.items():
            action_info = {'option_names': [],
                           'options': [],
                           'actions': {}}
            # docs['actions'][action] = {}
            # docs['actions'][action]['name'] = action
            action_info['name'] = action
            action_info['desc'] = trim_docstring(getattr(cli, 'execute_%s' % action).__doc__)

            # docs['actions'][action]['desc'] = getattr(cli, 'execute_%s' % action).__doc__.strip()
            action_doc_list = opt_doc_list(parser)

            uncommon_options = []
            for action_doc in action_doc_list:
                # uncommon_options = []

                option_aliases = action_doc.get('options', [])
                for option_alias in option_aliases:

                    if option_alias in shared_opt_names:
                        continue

                    # TODO: use set
                    if option_alias not in action_info['option_names']:
                        action_info['option_names'].append(option_alias)

                    if action_doc in action_info['options']:
                        continue

                    uncommon_options.append(action_doc)

                action_info['options'] = uncommon_options

            depth = 1 + get_actions(parser, action_info)

            docs['actions'][action] = action_info

        return depth

    action_depth = get_actions(cli.parser, docs)
    docs['content_depth'] = action_depth + 1

    docs['options'] = opt_doc_list(cli.parser)
    return docs


class GenerateMan(Command):
    name = 'generate-man'

    @classmethod
    def init_parser(cls, add_parser):
        parser = add_parser(name=cls.name,
                            description='Generate cli documentation from cli docstrings')

        parser.add_argument("-t", "--template-file", action="store", dest="template_file",
                            default=DEFAULT_TEMPLATE_FILE, help="path to jinja2 template")
        parser.add_argument("-o", "--output-dir", action="store", dest="output_dir",
                            default='/tmp/', help="Output directory for rst files")
        parser.add_argument("-f", "--output-format", action="store", dest="output_format",
                            default='man',
                            help="Output format for docs (the default 'man' or 'rst')")
        parser.add_argument('cli_modules', help='CLI module name(s)', metavar='MODULE_NAME', nargs='*')

    @staticmethod
    def main(args):
        template_file = args.template_file
        template_path = os.path.expanduser(template_file)
        template_dir = os.path.abspath(os.path.dirname(template_path))
        template_basename = os.path.basename(template_file)

        output_dir = os.path.abspath(args.output_dir)
        output_format = args.output_format

        cli_modules = args.cli_modules

        # various cli parsing things checks sys.argv if the 'args' that are passed in are []
        # so just remove any args so the cli modules dont try to parse them resulting in warnings
        sys.argv = [sys.argv[0]]

        allvars = {}
        output = {}
        cli_list = []
        cli_bin_name_list = []

        # for binary in os.listdir('../../lib/ansible/cli'):
        for cli_module_name in cli_modules:
            binary = os.path.basename(os.path.expanduser(cli_module_name))

            if not binary.endswith('.py'):
                continue
            elif binary == '__init__.py':
                continue

            cli_name = os.path.splitext(binary)[0]

            if cli_name == 'adhoc':
                cli_class_name = 'AdHocCLI'
                # myclass = 'AdHocCLI'
                output[cli_name] = 'ansible.1.rst.in'
                cli_bin_name = 'ansible'
            else:
                # myclass = "%sCLI" % libname.capitalize()
                cli_class_name = "%sCLI" % cli_name.capitalize()
                output[cli_name] = 'ansible-%s.1.rst.in' % cli_name
                cli_bin_name = 'ansible-%s' % cli_name

            # FIXME:
            allvars[cli_name] = opts_docs(cli_class_name, cli_name)
            cli_bin_name_list.append(cli_bin_name)

        cli_list = allvars.keys()

        doc_name_formats = {'man': '%s.1.rst.in',
                            'rst': '%s.rst'}

        for cli_name in cli_list:

            # template it!
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_basename)

            # add rest to vars
            tvars = allvars[cli_name]
            tvars['cli_list'] = cli_list
            tvars['cli_bin_name_list'] = cli_bin_name_list
            tvars['cli'] = cli_name
            if '-i' in tvars['options']:
                print('uses inventory')

            manpage = template.render(tvars)
            filename = os.path.join(output_dir, doc_name_formats[output_format] % tvars['cli_name'])
            update_file_if_different(filename, to_bytes(manpage))
