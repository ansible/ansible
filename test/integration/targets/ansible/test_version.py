#!/usr/bin/env python

import re
import subprocess


p = subprocess.Popen(['ansible', '--version'], stdout=subprocess.PIPE)
version_string = p.communicate()[0]
version_lines = version_string.splitlines()

assert len(version_lines) == 6, 'Incorrect number of lines in "ansible --version" output'
assert re.match(b'ansible [0-9.a-z]+$', version_lines[0]), 'Incorrect ansible version line in "ansible --version" output'
assert re.match(b'  config file = .*$', version_lines[1]), 'Incorrect config file line in "ansible --version" output'
assert re.match(b'  configured module search path = .*$', version_lines[2]), 'Incorrect module search path in "ansible --version" output'
assert re.match(b'  ansible python module location = .*$', version_lines[3]), 'Incorrect python module location in "ansible --version" output'
assert re.match(b'  executable location = .*$', version_lines[4]), 'Incorrect executable locaction in "ansible --version" output'
assert re.match(b'  python version = .*$', version_lines[5]), 'Incorrect python version in "ansible --version" output'
