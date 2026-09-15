"""Writes unsolicited output directly to stdout, similar to plugins such as
kpatch-dnf, to verify that the ansible.builtin.dnf module does not fail to
parse the JSON response produced by the embedded DNF helper script when a
loaded DNF plugin also writes to stdout.
"""

import dnf


class AnsibleTestNoisyPlugin(dnf.Plugin):
    name = 'ansible_test_noisy'

    def sack(self):
        print('This is unsolicited stdout output from a test DNF plugin.')
