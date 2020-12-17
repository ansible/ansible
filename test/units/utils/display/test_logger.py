# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import logging
import sys


def test_logger():
    '''
    Avoid CVE-2019-14846 as 3rd party libs will disclose secrets when
    logging is set to DEBUG
    '''

    # clear loaded modules to have unadultered test.
    for loaded in list(sys.modules.keys()):
        if 'ansible' in loaded:
            del sys.modules[loaded]

    # force logger to exist via config
    from ansible import constants as C
    C.DEFAULT_LOG_PATH = '/dev/null'

    # initialize logger
    from ansible.utils.display import logger

    assert logger.root.level != logging.DEBUG
