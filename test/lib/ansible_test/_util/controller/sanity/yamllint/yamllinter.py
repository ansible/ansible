"""Wrapper around yamllint that supports YAML embedded in Ansible modules."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import typing as t

import yaml
from yaml.resolver import Resolver
from yaml.constructor import SafeConstructor
from yaml.error import MarkedYAMLError
from yaml.cyaml import CParser

from yamllint import linter
from yamllint.config import YamlLintConfig


def main():
    """Main program body."""
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    checker = YamlChecker()
    checker.check(paths)
    checker.report()


class TestConstructor(SafeConstructor):
    """Yaml Safe Constructor that knows about Ansible tags."""
    def construct_yaml_unsafe(self, node):
        """Construct an unsafe tag."""
        try:
            constructor = getattr(node, 'id', 'object')
            if constructor is not None:
                constructor = getattr(self, 'construct_%s' % constructor)
        except AttributeError:
            constructor = self.construct_object

        value = constructor(node)

        return value


TestConstructor.add_constructor(
    '!unsafe',
    TestConstructor.construct_yaml_unsafe)


TestConstructor.add_constructor(
    '!vault',
    TestConstructor.construct_yaml_str)


TestConstructor.add_constructor(
    '!vault-encrypted',
    TestConstructor.construct_yaml_str)


class TestLoader(CParser, TestConstructor, Resolver):
    """Custom YAML loader that recognizes custom Ansible tags."""
    def __init__(self, stream):
        CParser.__init__(self, stream)
        TestConstructor.__init__(self)
        Resolver.__init__(self)


class YamlChecker:
    """Wrapper around yamllint that supports YAML embedded in Ansible modules."""
    def __init__(self):
        self.messages = []

    def report(self):
        """Print yamllint report to stdout."""
        report = dict(
            messages=self.messages,
        )

        print(json.dumps(report, indent=4, sort_keys=True))

    def check(self, paths):  # type: (t.List[str]) -> None
        """Check the specified paths."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')

        yaml_conf = YamlLintConfig(file=os.path.join(config_path, 'default.yml'))
        module_conf = YamlLintConfig(file=os.path.join(config_path, 'modules.yml'))
        plugin_conf = YamlLintConfig(file=os.path.join(config_path, 'plugins.yml'))

        for path in paths:
            extension = os.path.splitext(path)[1]

            with open(path, encoding='utf-8') as file:
                contents = file.read()

            if extension in ('.yml', '.yaml'):
                self.check_yaml(yaml_conf, path, contents)
            elif extension == '.py':
                if path.startswith('lib/ansible/modules/') or path.startswith('plugins/modules/'):
                    conf = module_conf
                else:
                    conf = plugin_conf

                self.check_module(conf, path, contents)
            else:
                raise Exception('unsupported extension: %s' % extension)

    def check_yaml(self, conf, path, contents):  # type: (YamlLintConfig, str, str) -> None
        """Check the given YAML."""
        self.check_parsable(path, contents)
        self.messages += [self.result_to_message(r, path) for r in linter.run(contents, conf, path)]

    def check_module(self, conf, path, contents):  # type: (YamlLintConfig, str, str) -> None
        """Check the given module."""
        docs = self.get_module_docs(path, contents)

        for key, value in docs.items():
            yaml_data = value['yaml']
            lineno = value['lineno']
            fmt = value['fmt']

            if fmt != 'yaml':
                continue

            if yaml_data.startswith('\n'):
                yaml_data = yaml_data[1:]
                lineno += 1

            self.check_parsable(path, yaml_data, lineno)

            messages = list(linter.run(yaml_data, conf, path))

            self.messages += [self.result_to_message(r, path, lineno - 1, key) for r in messages]

    def check_parsable(self, path, contents, lineno=1):  # type: (str, str, int) -> None
        """Check the given contents to verify they can be parsed as YAML."""
        try:
            yaml.load(contents, Loader=TestLoader)
        except MarkedYAMLError as ex:
            self.messages += [{'code': 'unparsable-with-libyaml',
                               'message': '%s - %s' % (ex.args[0], ex.args[2]),
                               'path': path,
                               'line': ex.problem_mark.line + lineno,
                               'column': ex.problem_mark.column + 1,
                               'level': 'error',
                               }]

    @staticmethod
    def result_to_message(result, path, line_offset=0, prefix=''):  # type: (t.Any, str, int, str) -> t.Dict[str, t.Any]
        """Convert the given result to a dictionary and return it."""
        if prefix:
            prefix = '%s: ' % prefix

        return dict(
            code=result.rule or result.level,
            message=prefix + result.desc,
            path=path,
            line=result.line + line_offset,
            column=result.column,
            level=result.level,
        )

    def get_module_docs(self, path, contents):  # type: (str, str) -> t.Dict[str, t.Any]
        """Return the module documentation for the given module contents."""
        module_doc_types = [
            'DOCUMENTATION',
            'EXAMPLES',
            'RETURN',
        ]

        docs = {}

        fmt_re = re.compile(r'^# fmt:\s+(\S+)')

        def check_assignment(statement, doc_types=None):
            """Check the given statement for a documentation assignment."""
            for target in statement.targets:
                if not isinstance(target, ast.Name):
                    continue

                if doc_types and target.id not in doc_types:
                    continue

                fmt_match = fmt_re.match(statement.value.s.lstrip())
                fmt = 'yaml'
                if fmt_match:
                    fmt = fmt_match.group(1)

                docs[target.id] = dict(
                    yaml=statement.value.s,
                    lineno=statement.lineno,
                    end_lineno=statement.lineno + len(statement.value.s.splitlines()),
                    fmt=fmt.lower(),
                )

        module_ast = self.parse_module(path, contents)

        if not module_ast:
            return {}

        is_plugin = path.startswith('lib/ansible/modules/') or path.startswith('lib/ansible/plugins/') or path.startswith('plugins/')
        is_doc_fragment = path.startswith('lib/ansible/plugins/doc_fragments/') or path.startswith('plugins/doc_fragments/')

        if is_plugin and not is_doc_fragment:
            for body_statement in module_ast.body:
                if isinstance(body_statement, ast.Assign):
                    check_assignment(body_statement, module_doc_types)
        elif is_doc_fragment:
            for body_statement in module_ast.body:
                if isinstance(body_statement, ast.ClassDef):
                    for class_statement in body_statement.body:
                        if isinstance(class_statement, ast.Assign):
                            check_assignment(class_statement)
        else:
            raise Exception('unsupported path: %s' % path)

        return docs

    def parse_module(self, path, contents):  # type: (str, str) -> t.Optional[ast.Module]
        """Parse the given contents and return a module if successful, otherwise return None."""
        try:
            return ast.parse(contents)
        except SyntaxError as ex:
            self.messages.append(dict(
                code='python-syntax-error',
                message=str(ex),
                path=path,
                line=ex.lineno,
                column=ex.offset,
                level='error',
            ))
        except Exception as ex:  # pylint: disable=broad-except
            self.messages.append(dict(
                code='python-parse-error',
                message=str(ex),
                path=path,
                line=0,
                column=0,
                level='error',
            ))

        return None


if __name__ == '__main__':
    main()
