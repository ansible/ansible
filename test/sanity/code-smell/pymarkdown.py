"""Sanity test for Markdown files."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

import typing as t


def main() -> None:
    paths = sys.argv[1:] or sys.stdin.read().splitlines()

    self_dir = pathlib.Path(__file__).parent
    base_dir = self_dir.parent.parent.parent
    config_path = self_dir / 'pymarkdown.config.json'

    # This regex is intentionally a very loose check for potential frontmatter.
    # There's no good reason for a non-frontmatter containing file to match this pattern.
    frontmatter_pattern = re.compile(r'^\s*--')

    frontmatter_allowed_prefixes = [
        ".claude/",
        ".github/",
    ]

    frontmatter_paths = []
    other_paths = []
    results = []

    for path in paths:
        content = pathlib.Path(path).read_text()
        has_frontmatter = frontmatter_pattern.search(content)
        allow_frontmatter = any(path.startswith(prefix) for prefix in frontmatter_allowed_prefixes)

        # When potential frontmatter is detected, check it before running the document through pymarkdown.
        # This avoids treating frontmatter issues as Markdown issues, which would otherwise lead to confusing error messages.

        if allow_frontmatter:
            if has_frontmatter and (issues := check_frontmatter(path, content)):
                results.extend(issues)
            else:
                frontmatter_paths.append(path)
        else:
            if has_frontmatter:
                results.append(f'{path}:1:1: frontmatter-not-allowed: frontmatter is not allowed in this document')
            else:
                other_paths.append(path)

    results.extend(run_pymarkdown(frontmatter_paths, config_path, base_dir, enable_frontmatter=True))
    results.extend(run_pymarkdown(other_paths, config_path, base_dir, enable_frontmatter=False))

    if results:
        print('\n'.join(results))


def check_frontmatter(path: str, content: str) -> list[str]:
    """
    Check frontmatter formatting.
    Use only after detecting signs of frontmatter usage.
    This supplements the frontmatter support in pymarkdown, which is less aggressive about detecting potential frontmatter.
    """
    match = re.search(r"^(?P<content>---\n.*?)\n---\n", content, flags=re.DOTALL)

    if not match:
        return [f"{path}:1:1: malformed-frontmatter: document appears to start with malformed frontmatter"]

    yaml_content = match.group('content')

    try:
        yaml.load(yaml_content, Loader=SafeLoader)
    except yaml.MarkedYAMLError as ex:
        message = ' '.join(filter(None, (ex.context, ex.problem, ex.note))).strip()

        return [f"{path}:{ex.problem_mark.line}:{ex.problem_mark.column}: frontmatter-yaml: {message}"]
    except yaml.YAMLError as ex:
        return [f"{path}:1:1: frontmatter-yaml: {ex}"]

    return []


def run_pymarkdown(paths: list[str], config_path: pathlib.Path, base_dir: pathlib.Path, enable_frontmatter: bool) -> list[str]:
    """Run pymarkdown on the given paths and return a list of results."""

    if not paths:
        return []

    extensions: list[str] = []

    if enable_frontmatter:
        extensions.append('front-matter')

    cmd = [
        sys.executable,
        '-m',
        'pymarkdown',
        '--config',
        config_path,
        '--strict-config',
        '--enable-extensions',
        ','.join(extensions),
        'scan',
    ] + paths

    process = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        text=True,
    )

    if process.stderr:
        print(process.stderr.strip(), file=sys.stderr)
        sys.exit(1)

    if not (stdout := process.stdout.strip()):
        return []

    pattern = re.compile(r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[^:]*): (?P<message>.*) \((?P<aliases>.*)\)$')
    matches = parse_to_list_of_dict(pattern, stdout)

    for match in matches:
        match['path'] = str(pathlib.Path(match['path']).relative_to(base_dir))

    results = [f"{match['path']}:{match['line']}:{match['column']}: {match['aliases'].split(', ')[0]}: {match['message']}" for match in matches]

    return results


def parse_to_list_of_dict(pattern: re.Pattern, value: str) -> list[dict[str, t.Any]]:
    matched = []
    unmatched = []

    for line in value.splitlines():
        match = re.search(pattern, line)

        if match:
            matched.append(match.groupdict())
        else:
            unmatched.append(line)

    if unmatched:
        raise Exception(f'Pattern {pattern!r} did not match values:\n' + '\n'.join(unmatched))

    return matched


if __name__ == '__main__':
    main()
