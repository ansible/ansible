import sys
import os.path
import ansible.utils


class VarsModule(object):
    def __init__(self, inventory):
        self.inventory = inventory

    def run(self, host, vault_password=None):
        groups = sorted(self.inventory.groups_for_host(host.name), key=lambda g: g.depth)
        groups.append(host)

        playbook_basedir = self.inventory.playbook_basedir()
        playbook_basedir = os.path.abspath(playbook_basedir) if playbook_basedir is not None else None
        inventory_basedir = self.inventory.basedir()
        result = {}
        for basedir in filter(None, {playbook_basedir, inventory_basedir}):
            module_path = os.path.join(basedir, 'python_vars')
            sys.path.insert(0, module_path)
            for group in groups:
                if not os.path.exists(os.path.join(module_path, '%s.py' % group.name)):
                    continue
                vars = __import__(group.name).run(host)
                result = ansible.utils.combine_vars(result, vars)
            del sys.path[0]

        return result
