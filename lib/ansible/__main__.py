# Copyright: (c) 2021, Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
from importlib.metadata import distribution


def main():
    dist = distribution('ansible-core')
    ep_map = {ep.name: ep for ep in dist.entry_points if ep.group == 'console_scripts'}

    parser = argparse.ArgumentParser(prog='python -m ansible', add_help=False)
    parser.add_argument('entry_point', choices=list(ep_map))
    args, extra = parser.parse_known_args()

    main = ep_map[args.entry_point].load()
    main([args.entry_point] + extra)


if __name__ == '__main__':
    main()
