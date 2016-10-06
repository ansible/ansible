#!/usr/bin/env python

"""
This script generated test_cases for test_distribution_version.py.

To do so it outputs the relevant files from /etc/*release, the output of platform.dist() and the current ansible_facts regarding the distribution version.

This assumes a working ansible version in the path.
"""

import platform
import os.path
import subprocess
import json

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
]

fcont = {}

for f in filelist:
    if os.path.exists(f):
        s = os.path.getsize(f)
        if s > 0 and s < 10000:
            with open(f) as fh:
                fcont[f] = fh.read()

dist = platform.dist()


facts = ['distribution', 'distribution_version', 'distribution_release', 'distribution_major_version']
ansible_out = subprocess.Popen(['ansible', 'localhost', '-m', 'setup'], stdout=subprocess.PIPE).communicate()[0]
parsed = json.loads(ansible_out[ansible_out.index('{'):])
ansible_facts = {}
for fact in facts:
    try:
        ansible_facts[fact] = parsed['ansible_facts']['ansible_'+fact]
    except:
        ansible_facts[fact] = "N/A"

nicename = ansible_facts['distribution'] + ' ' + ansible_facts['distribution_version']

output = {
    'name': nicename,
    'input': fcont,
    'platform.dist': dist,
    'result': ansible_facts,
}

print(json.dumps(output, indent=4))

