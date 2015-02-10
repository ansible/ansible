import os
import json

import logging
import logging.handlers


class CallbackModule(object):
    """
    logs ansible-playbook and ansible runs to a syslog server in json format
    make sure you have in ansible.cfg:
        callback_plugins   = <path_to_callback_plugins_folder>
    and put the plugin in <path_to_callback_plugins_folder>
    
    This plugin makes use of the following environment variables:
        SYSLOG_SERVER   (optional): defaults to localhost
        SYSLOG_PORT     (optional): defaults to 514
    """

    def __init__(self):
        self.logger =  logging.getLogger('ansible logger')
        self.logger.setLevel(logging.DEBUG)

        self.handler = logging.handlers.SysLogHandler(
            address = (os.getenv('SYSLOG_SERVER','locahost'),
                       os.getenv('SYSLOG_PORT',514)), 
            facility=logging.handlers.SysLogHandler.LOG_USER
        )
        self.logger.addHandler(handler)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.logger.info('RUNNER_ON_FAILED ' + host + ' ' + json.dumps(res, sort_keys=True))

    def runner_on_ok(self, host, res):
        self.logger.info('RUNNER_ON_OK ' + host + ' ' + json.dumps(res, sort_keys=True))

    def runner_on_skipped(self, host, item=None):
        self.logger.info('RUNNER_ON_SKIPPED ' + host + ' ...')

    def runner_on_unreachable(self, host, res):
        self.logger.info('RUNNER_UNREACHABLE ' + host + ' ' + json.dumps(res, sort_keys=True))

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res):
        pass

    def runner_on_async_ok(self, host, res):
        pass

    def runner_on_async_failed(self, host, res):
        self.logger.info('RUNNER_SYNC_FAILED ' + host + ' ' + json.dumps(res, sort_keys=True))

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        self.logger.info('PLAYBOOK_ON_IMPORTED ' + host + ' ' + json.dumps(res, sort_keys=True))

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.logger.info('PLAYBOOK_ON_NOTIMPORTED ' + host + ' ' + json.dumps(res, sort_keys=True))

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass
