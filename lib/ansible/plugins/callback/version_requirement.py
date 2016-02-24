#!/usr/bin/python

import sys
from ansible import __version__

if __version__ < '2.0':
    from ansible.callbacks import display as pre2_display

    def display(*args, **kwargs):
        pre2_display(*args, **kwargs)
else:
    from ansible.utils.display import Display

    def display(*args, **kwargs):
        display_instance = Display()
        display_instance.display(*args, **kwargs)


def version_requirement(version):
    return version >= '2.0'


DESCRIPTION = "Supported versions: 2.0 or newer"


class CallbackModule(object):
    """
    Plugin stop execution of playbook
    if ansible version is outdated (< 2.0)

    """

    def _check_version(self):
        if not version_requirement(__version__):
            display(
                'FATAL: Current ansible version is not supported. %s' % DESCRIPTION,
                color='red')
            sys.exit(1)

    def playbook_on_start(self):
        self._check_version()

    def v2_playbook_on_start(self):
        self._check_version()
