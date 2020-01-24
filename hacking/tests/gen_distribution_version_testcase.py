#!/usr/bin/env python

"""
This script generated test_cases for test_distribution_version.py.

To do so it outputs the relevant files from /etc/*release, the output of distro.linux_distribution()
and the current ansible_facts regarding the distribution version.

This assumes a working ansible version in the path.
"""


import os.path
import subprocess
import json
import sys

from ansible.module_utils import distro
from ansible.module_utils._text import to_text


filelist = [
    '/etc/oracle-release',
    '/etc/slackware-version',
    '/etc/redhat-release',
    '/etc/vmware-release',
    '/etc/openwrt_release',
    '/etc/system-release',
    '/etc/alpine-release',
    '/etc/release',
    '/etc/arch-release',
    '/etc/os-release',
    '/etc/SuSE-release',
    '/etc/gentoo-release',
    '/etc/os-release',
    '/etc/lsb-release',
    '/etc/altlinux-release',
    '/etc/os-release',
    '/etc/coreos/update.conf',
    '/usr/lib/os-release',
]

fcont = {}

for f in filelist:
    if os.path.exists(f):
        s = os.path.getsize(f)
        if s > 0 and s < 10000:
            with open(f) as fh:
                fcont[f] = fh.read()

dist = distro.linux_distribution(full_distribution_name=False)

facts = ['distribution', 'distribution_version', 'distribution_release', 'distribution_major_version', 'os_family']

try:
    b_ansible_out = subprocess.check_output(
        ['ansible', 'localhost', '-m', 'setup'])
except subprocess.CalledProcessError as e:
    print("ERROR: ansible run failed, output was: \n")
    print(e.output)
    sys.exit(e.returncode)

ansible_out = to_text(b_ansible_out)
parsed = json.loads(ansible_out[ansible_out.index('{'):])
ansible_facts = {}
for fact in facts:
    try:
        ansible_facts[fact] = parsed['ansible_facts']['ansible_' + fact]
    except Exception:
        ansible_facts[fact] = "N/A"

nicename = ansible_facts['distribution'] + ' ' + ansible_facts['distribution_version']

output = {
    'name': nicename,
    'distro': {
        'codename': distro.codename(),
        'id': distro.id(),
        'name': distro.name(),
        'version': distro.version(),
        'version_best': distro.version(best=True),
    },
    'input': fcont,
    'platform.dist': dist,
    'result': ansible_facts,
}

print(json.dumps(output, indent=4))
