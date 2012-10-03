#!/usr/bin/env python
# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
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
#

import json
import os
import glob
import argparse
from jinja2 import Environment, FileSystemLoader


def main():
    p = argparse.ArgumentParser(description="Convert all ansible JSON documentation generate by module_formatter.py to a single file")

    p.add_argument("-d", "--docs-dir",
            action="store",
            dest="docs_dir",
            default="/tmp/ansible-modules-json/",
            help="Ansible version number")
    p.add_argument("-o", "--output-file",
            action="store",
            dest="output_file",
            default=None,
            help="Output file for aggregate content")
    p.add_argument("-T", "--template-dir",
            action="store",
            dest="template_dir",
            default="hacking/templates",
            help="directory containing Jinja2 templates")
    p.add_argument('-V', '--version', action='version', version='%(prog)s 1.0')

    args = p.parse_args()

    data = []

    for current_file in glob.glob(os.path.join(args.docs_dir, '*.json')):
        if not os.path.isdir(current_file):
            f = open(current_file)
            j = json.load(f)
            f.close()
            data.append(j)

    env = Environment(loader=FileSystemLoader(args.template_dir),
        variable_start_string="@{",
        variable_end_string="}@",
        trim_blocks=True,
        )

    template = env.get_template('js.j2')

    docs = {}
    docs['json'] = json.dumps(data, indent=2)

    text = template.render(docs)

    if args.output_file is not None:
        f = open(args.output_file, 'w')
        f.write(text)
        f.close()
    else:
        print text

if __name__ == '__main__':
    main()
