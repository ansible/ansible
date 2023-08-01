#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""Build documentation for ansible-core CLI programs."""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import inspect
import io
import itertools
import json
import pathlib
import sys
import typing as t
import warnings

import jinja2

if t.TYPE_CHECKING:
    from ansible.cli import CLI  # pragma: nocover

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR.parent.parent


def main() -> None:
    """Main program entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True, metavar='command')

    man_parser = subparsers.add_parser('man', description=build_man.__doc__, help=build_man.__doc__)
    man_parser.add_argument('--output-dir', required=True, type=pathlib.Path, metavar='DIR', help='output directory')
    man_parser.add_argument('--template-file', default=SCRIPT_DIR / 'man.j2', type=pathlib.Path, metavar='FILE', help='template file')
    man_parser.set_defaults(func=build_man)

    rst_parser = subparsers.add_parser('rst', description=build_rst.__doc__, help=build_rst.__doc__)
    rst_parser.add_argument('--output-dir', required=True, type=pathlib.Path, metavar='DIR', help='output directory')
    rst_parser.add_argument('--template-file', default=SCRIPT_DIR / 'rst.j2', type=pathlib.Path, metavar='FILE', help='template file')
    rst_parser.set_defaults(func=build_rst)

    json_parser = subparsers.add_parser('json', description=build_json.__doc__, help=build_json.__doc__)
    json_parser.add_argument('--output-file', required=True, type=pathlib.Path, metavar='FILE', help='output file')
    json_parser.set_defaults(func=build_json)

    try:
        # noinspection PyUnresolvedReferences
        import argcomplete
    except ImportError:
        pass
    else:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    kwargs = {name: getattr(args, name) for name in inspect.signature(args.func).parameters}

    sys.path.insert(0, str(SOURCE_DIR / 'lib'))

    args.func(**kwargs)


def build_man(output_dir: pathlib.Path, template_file: pathlib.Path) -> None:
    """Build man pages for ansible-core CLI programs."""
    if not template_file.resolve().is_relative_to(SCRIPT_DIR):
        warnings.warn("Custom templates are intended for debugging purposes only. The data model may change in future releases without notice.")

    import docutils.core
    import docutils.writers.manpage

    output_dir.mkdir(exist_ok=True, parents=True)

    for cli_name, source in generate_rst(template_file).items():
        with io.StringIO(source) as source_file:
            docutils.core.publish_file(
                source=source_file,
                destination_path=output_dir / f'{cli_name}.1',
                writer=docutils.writers.manpage.Writer(),
            )


def build_rst(output_dir: pathlib.Path, template_file: pathlib.Path) -> None:
    """Build RST documentation for ansible-core CLI programs."""
    if not template_file.resolve().is_relative_to(SCRIPT_DIR):
        warnings.warn("Custom templates are intended for debugging purposes only. The data model may change in future releases without notice.")

    output_dir.mkdir(exist_ok=True, parents=True)

    for cli_name, source in generate_rst(template_file).items():
        (output_dir / f'{cli_name}.rst').write_text(source)


def build_json(output_file: pathlib.Path) -> None:
    """Build JSON documentation for ansible-core CLI programs."""
    warnings.warn("JSON output is intended for debugging purposes only. The data model may change in future releases without notice.")

    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(json.dumps(collect_programs(), indent=4))


def generate_rst(template_file: pathlib.Path) -> dict[str, str]:
    """Generate RST pages using the provided template."""
    results: dict[str, str] = {}

    for cli_name, template_vars in collect_programs().items():
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_file.parent))
        template = env.get_template(template_file.name)
        results[cli_name] = template.render(template_vars)

    return results


def collect_programs() -> dict[str, dict[str, t.Any]]:
    """Return information about CLI programs."""
    programs: list[tuple[str, dict[str, t.Any]]] = []
    cli_bin_name_list: list[str] = []

    for source_file in (SOURCE_DIR / 'lib/ansible/cli').glob('*.py'):
        if source_file.name != '__init__.py':
            programs.append(generate_options_docs(source_file, cli_bin_name_list))

    return dict(programs)


def generate_options_docs(source_file: pathlib.Path, cli_bin_name_list: list[str]) -> tuple[str, dict[str, t.Any]]:
    """Generate doc structure from CLI module options."""
    import ansible.release

    if str(source_file).endswith('/lib/ansible/cli/adhoc.py'):
        cli_name = 'ansible'
        cli_class_name = 'AdHocCLI'
        cli_module_fqn = 'ansible.cli.adhoc'
    else:
        cli_module_name = source_file.with_suffix('').name
        cli_name = f'ansible-{cli_module_name}'
        cli_class_name = f'{cli_module_name.capitalize()}CLI'
        cli_module_fqn = f'ansible.cli.{cli_module_name}'

    cli_bin_name_list.append(cli_name)

    cli_module = importlib.import_module(cli_module_fqn)
    cli_class: type[CLI] = getattr(cli_module, cli_class_name)

    cli = cli_class([cli_name])
    cli.init_parser()

    parser: argparse.ArgumentParser = cli.parser
    long_desc = cli.__doc__
    arguments: dict[str, str] | None = getattr(cli, 'ARGUMENTS', None)

    action_docs = get_action_docs(parser)
    option_names: tuple[str, ...] = tuple(itertools.chain.from_iterable(opt.options for opt in action_docs))
    actions: dict[str, dict[str, t.Any]] = {}

    content_depth = populate_subparser_actions(parser, option_names, actions)

    docs = dict(
        version=ansible.release.__version__,
        source=str(source_file.relative_to(SOURCE_DIR)),
        cli_name=cli_name,
        usage=parser.format_usage(),
        short_desc=parser.description,
        long_desc=trim_docstring(long_desc),
        actions=actions,
        options=[item.__dict__ for item in action_docs],
        arguments=arguments,
        option_names=option_names,
        cli_bin_name_list=cli_bin_name_list,
        content_depth=content_depth,
        inventory='-i' in option_names,
        library='-M' in option_names,
    )

    return cli_name, docs


def populate_subparser_actions(parser: argparse.ArgumentParser, shared_option_names: tuple[str, ...], actions: dict[str, dict[str, t.Any]]) -> int:
    """Generate doc structure from CLI module subparser options."""
    try:
        # noinspection PyProtectedMember
        subparsers: dict[str, argparse.ArgumentParser] = parser._subparsers._group_actions[0].choices  # type: ignore
    except AttributeError:
        subparsers = {}

    depth = 0

    for subparser_action, subparser in subparsers.items():
        subparser_option_names: set[str] = set()
        subparser_action_docs: set[ActionDoc] = set()
        subparser_actions: dict[str, dict[str, t.Any]] = {}

        for action_doc in get_action_docs(subparser):
            for option_alias in action_doc.options:
                if option_alias in shared_option_names:
                    continue

                subparser_option_names.add(option_alias)
                subparser_action_docs.add(action_doc)

        depth = populate_subparser_actions(subparser, shared_option_names, subparser_actions)

        actions[subparser_action] = dict(
            option_names=list(subparser_option_names),
            options=[item.__dict__ for item in subparser_action_docs],
            actions=subparser_actions,
            name=subparser_action,
            desc=trim_docstring(subparser.get_default("func").__doc__),
        )

    return depth + 1


@dataclasses.dataclass(frozen=True)
class ActionDoc:
    """Documentation for an action."""
    desc: str | None
    options: tuple[str, ...]
    arg: str | None


def get_action_docs(parser: argparse.ArgumentParser) -> list[ActionDoc]:
    """Get action documentation from the given argument parser."""
    action_docs = []

    # noinspection PyProtectedMember
    for action in parser._actions:
        if action.help == argparse.SUPPRESS:
            continue

        # noinspection PyProtectedMember, PyUnresolvedReferences
        args = action.dest.upper() if isinstance(action, argparse._StoreAction) else None

        if args or action.option_strings:
            action_docs.append(ActionDoc(
                desc=action.help,
                options=tuple(action.option_strings),
                arg=args,
            ))

    return action_docs


def trim_docstring(docstring: str | None) -> str:
    """Trim and return the given docstring using the implementation from https://peps.python.org/pep-0257/#handling-docstring-indentation."""
    if not docstring:
        return ''  # pragma: nocover

    # Convert tabs to spaces (following the normal Python rules) and split into a list of lines
    lines = docstring.expandtabs().splitlines()

    # Determine minimum indentation (first line doesn't count)
    indent = sys.maxsize

    for line in lines[1:]:
        stripped = line.lstrip()

        if stripped:
            indent = min(indent, len(line) - len(stripped))

    # Remove indentation (first line is special)
    trimmed = [lines[0].strip()]

    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())

    # Strip off trailing and leading blank lines
    while trimmed and not trimmed[-1]:
        trimmed.pop()

    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    # Return a single string
    return '\n'.join(trimmed)


if __name__ == '__main__':
    main()
