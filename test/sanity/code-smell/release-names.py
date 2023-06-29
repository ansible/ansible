# -*- coding: utf-8 -*-
# (c) 2019, Ansible Project
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
"""
Test that the release name is present in the list of used up release names
"""


from __future__ import annotations

import pathlib

from ansible.release import __codename__


def main():
    """Entrypoint to the script"""

    releases = pathlib.Path('.github/RELEASE_NAMES.txt').read_text().splitlines()

    # Why this format?  The file's sole purpose is to be read by a human when they need to know
    # which release names have already been used.  So:
    # 1) It's easier for a human to find the release names when there's one on each line
    # 2) It helps keep other people from using the file and then asking for new features in it
    for name in (r.split(maxsplit=1)[1] for r in releases):
        if __codename__ == name:
            break
    else:
        print(f'.github/RELEASE_NAMES.txt: Current codename {__codename__!r} not present in the file')


if __name__ == '__main__':
    main()
