# plugins/no_hosts_matched_fail.py

from ansible.errors import AnsibleError


class CallbackModule(object):
    def playbook_on_start(self):
        print('|---> plugin activated: %s' % __file__)

    def playbook_on_no_hosts_matched(self):
        raise AnsibleError("FATAL: no hosts matched or all hosts have already failed -- aborting\n")
