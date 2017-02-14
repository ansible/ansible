#!/usr/bin/python

from ansible.plugins.action import ActionBase
import os


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        if result.get('skipped'):
            return result

        cp_path = self._task.args.get('control_persist_path', None)
        if cp_path is None:
            ansible_user_dir = task_vars.get('ansible_user_dir')
            inventory_hostname = task_vars.get('inventory_hostname')
            ansible_user_id = task_vars.get('ansible_user_id')
            cp_path = "{}/.ansible/cp/ansible-ssh-{}-22-{}".format(ansible_user_dir, inventory_hostname, ansible_user_id)

        if os.path.isfile(cp_path):
            os.remove(cp_path)
            result.update(dict(changed=True))
        else:
            result.update(dict(changed=False))
        return result
