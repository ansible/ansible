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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging
import logging.handlers
import re

# from ansible.utils.unicode import to_bytes
from ansible.plugins.callback import CallbackBase


# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.

DEBUG_LOG_FORMAT = "%(asctime)s [%(name)s %(levelname)s %(playbook)s] (%(process)d):%(funcName)s:%(lineno)d - %(message)s"
CONTEXT_DEBUG_LOG_FORMAT = "%(asctime)s [%(name)s %(levelname)s] [playbook=%(playbook)s:%(playbook_uuid)s play=%(play)s:%(play_uuid)s task=%(task)s:%(task_uuid)s] (%(process)d):%(funcName)s:%(lineno)d - %(message)s"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(process)d @%(filename)s:%(lineno)d - %(message)s"
MIN_LOG_FORMAT = "%(asctime)s %(funcName)s:%(lineno)d - %(message)s"


def sluggify(value):
    return '%s' % (re.sub(r'[^\w-]', '_', value).lower().lstrip('_'))


class CallbackModule(CallbackBase):
    """
    Logging callbacks using python stdlin logging
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    # CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = 'generic_stdlog'
    CALLBACK_NEEDS_WHITELIST = True

    log_level = logging.DEBUG
    #log_name = 'ansible_generic_stdlog'
    #log_format = CONTEXT_DEBUG_LOG_FORMAT
    log_format = LOG_FORMAT

    def __init__(self):
        super(CallbackModule, self).__init__()

        # TODO: replace with a stack
        self.host = None

        self.logger = logging.getLogger('ansible.plugins.callbacks.generic_stdlog')
        self.logger.setLevel(self.log_level)

        # Note: by default, ansible doesn't setup any log handlers, so this wont do
        # anything without doing that. To enable, something like this:
        self.setup_stream_handler()
        self.setup_file_handler()

    def setup_stream_handler(self):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt=self.log_format)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def setup_file_handler(self):
        file_handler = logging.FileHandler('/tmp/ansible_callback.log')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt=self.log_format)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    # Note: it would be useful to have a 'always called'
    # callback, and a 'only called if not handled' callback
    def _v2_on_generic(self, *args, **kwargs):
        method_name = kwargs.pop('_callback_method_name', None)
        if method_name:
            self.logger.debug('_v2_on_generic being called to handle request for %s', method_name)

        for arg in args:
            self.logger.debug(arg)

        for k, v in kwargs.items():
            self.logger.debug('kw_k=%s', k)
            self.logger.debug('kw_v=%s', v)

    # this setup will call v2_on_missing for unknown callbacks and always call v2_on_all
    #v2_on_any = _v2_on_generic
    v2_on_all = _v2_on_generic
    v2_on_missing = _v2_on_generic
