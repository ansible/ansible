"""Original manpage generator helpers."""

from __future__ import annotations

import typing as t
from argparse import _StoreAction
from functools import lru_cache
from importlib import import_module
from itertools import chain
from sys import maxsize as _sys_maxsize

from ._paths import PROJECT_BIN_DIR_PATH


# from https://www.python.org/dev/peps/pep-0257/
def trim_docstring(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = _sys_maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < _sys_maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def get_normalized_options_from_actions(optlist):
    """Retrieve actual options from list."""
    opts = []
    for opt in optlist:
        res = {
            'desc': opt.help,
            'options': opt.option_strings
        }
        if isinstance(opt, _StoreAction):
            res['arg'] = opt.dest.upper()
        elif not res['options']:
            continue
        opts.append(res)

    return opts


def extract_unique_action_groups(parser):
    """Get action groups out of the parser."""
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


def traverse_cli_options(parser):
    """Extract options list out of a CLI parser."""
    results = []
    for option_group in extract_unique_action_groups(parser)[1:]:
        results.extend(
            get_normalized_options_from_actions(option_group._actions),
        )

    results.extend(get_normalized_options_from_actions(parser._actions))

    return results


def traverse_cli_actions(
        cli, shared_opt_names, parser=None, initial_depth=1,
):
    """Extract actions out of a CLI parser recursively.

    :returns: A tuple of nesting depth and CLI actions.
    """
    actions = {}
    discovered_depth = 0
    if parser is None:
        parser = cli.parser
    try:
        subparser = parser._subparsers._group_actions[0].choices
    except AttributeError:
        subparser = {}

    for action, action_parser in subparser.items():
        option_names = []
        uncommon_options = []
        for action_doc in traverse_cli_options(action_parser):
            for option_alias in action_doc.get('options', []):
                if option_alias in shared_opt_names:
                    continue

                if option_alias not in option_names:
                    option_names.append(option_alias)

                if action_doc in uncommon_options:
                    continue

                uncommon_options.append(action_doc)

        nested_depth, nested_actions = traverse_cli_actions(
            cli,
            shared_opt_names,
            action_parser,
            initial_depth=initial_depth + 1,
        )
        discovered_depth = max(discovered_depth, nested_depth)
        actions[action] = {
            'option_names': option_names,
            'options': uncommon_options,
            'actions': nested_actions,
            'name': action,
            'desc': trim_docstring(getattr(
                cli, f'execute_{action}',
            ).__doc__),
        }

    return initial_depth + discovered_depth, actions


@lru_cache(maxsize=1)
def lookup_cli_bin_names():
    """List the installable CLI entrypoints."""
    return [
        bin_path.name for bin_path in PROJECT_BIN_DIR_PATH.iterdir()
        if bin_path.name.removeprefix('ansible-') not in {'connection', 'test'}
    ]


def generate_cli_jinja2_context(cli_bin_name):
    """Make Jinja2 context doc structure from CLI."""
    cli_bin_name_list = lookup_cli_bin_names()
    assert cli_bin_name in cli_bin_name_list

    if cli_bin_name == 'ansible':
        target_cli_module = 'adhoc'
        cli_class_name = 'AdHocCLI'
    else:
        target_cli_module = cli_bin_name.removeprefix('ansible-')
        cli_class_name = f'{target_cli_module.capitalize()}CLI'

    cli_class = getattr(
        import_module(
            f'ansible.cli.{target_cli_module}',
            package='ansible',
        ),
        cli_class_name,
    )
    cli = cli_class([cli_bin_name])
    cli.init_parser()

    cli_options = traverse_cli_options(cli.parser)
    shared_opt_names = set(chain.from_iterable(
        opt.get('options', []) for opt in cli_options
    ))

    return {
        'cli': target_cli_module,  # FIXME: sphinx-only
        'cli_name': cli_bin_name,
        'usage': cli.parser.format_usage(),
        'short_desc': cli.parser.description,
        'long_desc': trim_docstring(cli.__doc__),
        'options': cli_options,
        'arguments': getattr(cli, 'ARGUMENTS', None),
        'inventory': '-i' in shared_opt_names,
        'library': '-M' in shared_opt_names,
        'cli_bin_name_list': cli_bin_name_list,
        **dict(zip(
            (
                'content_depth',  # FIXME: sphinx-only
                'actions',
            ),
            traverse_cli_actions(cli, shared_opt_names, cli.parser),
        )),
    }
