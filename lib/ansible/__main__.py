# Copyright: (c) 2021, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import importlib
import os
import sys

from importlib.metadata import distribution


def _short_name(name):
    return name.removeprefix('ansible-').replace('ansible', 'adhoc')


def main():
    dist = distribution('ansible-core')
    ep_map = {_short_name(ep.name): ep for ep in dist.entry_points if ep.group == 'console_scripts'}

    parser = argparse.ArgumentParser(prog='python -m ansible', add_help=False)
    parser.add_argument('entry_point', choices=list(ep_map) + ['test'])
    args, extra = parser.parse_known_args()

    if args.entry_point == 'test':
        ansible_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_root = os.path.join(ansible_root, 'test', 'lib')

        if os.path.exists(os.path.join(source_root, 'ansible_test', '_internal', '__init__.py')):
            # running from source, use that version of ansible-test instead of any version that may already be installed
            sys.path.insert(0, source_root)

        module = importlib.import_module('ansible_test._util.target.cli.ansible_test_cli_stub')
        main = module.main
    else:
        main = ep_map[args.entry_point].load()

    main([args.entry_point] + extra)


if __name__ == '__main__':
    main()
