#!/usr/bin/env python

# A tool to check the order of precedence for ansible variables
# https://github.com/ansible/ansible/blob/devel/test/integration/test_var_precedence.yml

from __future__ import annotations

import json
import os
import sys
import shutil
import stat
import subprocess
import tempfile
import yaml
from optparse import OptionParser
from jinja2 import Environment

ENV = Environment()
TESTDIR = tempfile.mkdtemp()


def run_command(args, cwd=None):
    p = subprocess.Popen(
        args,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
        cwd=cwd,
    )
    (so, se) = p.communicate()
    return (p.returncode, so, se)


def clean_test_dir():
    if os.path.isdir(TESTDIR):
        shutil.rmtree(TESTDIR)
    os.makedirs(TESTDIR)


class Role(object):
    def __init__(self, name):
        self.name = name
        self.load = True
        self.dependencies = []
        self.defaults = False
        self.vars = False
        self.tasks = []
        self.params = dict()

    def write_role(self):

        fpath = os.path.join(TESTDIR, 'roles', self.name)
        if not os.path.isdir(fpath):
            os.makedirs(fpath)

        if self.defaults:
            # roles/x/defaults/main.yml
            fpath = os.path.join(TESTDIR, 'roles', self.name, 'defaults')
            if not os.path.isdir(fpath):
                os.makedirs(fpath)
            fname = os.path.join(fpath, 'main.yml')
            with open(fname, 'w') as f:
                f.write('findme: %s\n' % self.name)

        if self.vars:
            # roles/x/vars/main.yml
            fpath = os.path.join(TESTDIR, 'roles', self.name, 'vars')
            if not os.path.isdir(fpath):
                os.makedirs(fpath)
            fname = os.path.join(fpath, 'main.yml')
            with open(fname, 'w') as f:
                f.write('findme: %s\n' % self.name)

        if self.dependencies:
            fpath = os.path.join(TESTDIR, 'roles', self.name, 'meta')
            if not os.path.isdir(fpath):
                os.makedirs(fpath)
            fname = os.path.join(fpath, 'main.yml')
            with open(fname, 'w') as f:
                f.write('dependencies:\n')
                for dep in self.dependencies:
                    f.write('- { role: %s }\n' % dep)


class DynamicInventory(object):
    BASESCRIPT = '''#!/usr/bin/python
import json
data = """{{ data }}"""
data = json.loads(data)
print(json.dumps(data, indent=2, sort_keys=True))
'''

    BASEINV = {
        '_meta': {
            'hostvars': {
                'testhost': {}
            }
        }
    }

    def __init__(self, features):
        self.ENV = Environment()
        self.features = features
        self.fpath = None
        self.inventory = self.BASEINV.copy()
        self.build()

    def build(self):
        xhost = 'testhost'
        if 'script_host' in self.features:
            self.inventory['_meta']['hostvars'][xhost]['findme'] = 'script_host'
        else:
            self.inventory['_meta']['hostvars'][xhost] = {}

        if 'script_child' in self.features:
            self.inventory['child'] = {
                'hosts': [xhost],
                'vars': {'findme': 'script_child'}
            }

        if 'script_parent' in self.features:

            self.inventory['parent'] = {
                'vars': {'findme': 'script_parent'}
            }

            if 'script_child' in self.features:
                self.inventory['parent']['children'] = ['child']
            else:
                self.inventory['parent']['hosts'] = [xhost]

        if 'script_all' in self.features:
            self.inventory['all'] = {
                'hosts': [xhost],
                'vars': {
                    'findme': 'script_all'
                },
            }
        else:
            self.inventory['all'] = {
                'hosts': [xhost],
            }

    def write_script(self):
        fdir = os.path.join(TESTDIR, 'inventory')
        if not os.path.isdir(fdir):
            os.makedirs(fdir)
        fpath = os.path.join(fdir, 'hosts')
        # fpath = os.path.join(TESTDIR, 'inventory')
        self.fpath = fpath

        data = json.dumps(self.inventory)
        t = self.ENV.from_string(self.BASESCRIPT)
        fdata = t.render(data=data)
        with open(fpath, 'w') as f:
            f.write(fdata + '\n')
        st = os.stat(fpath)
        os.chmod(fpath, st.st_mode | stat.S_IEXEC)


class VarTestMaker(object):
    def __init__(self, features, dynamic_inventory=False):
        clean_test_dir()
        self.dynamic_inventory = dynamic_inventory
        self.di = None
        self.features = features[:]
        self.inventory = ''
        self.playvars = dict()
        self.varsfiles = []
        self.playbook = dict(hosts='testhost', gather_facts=False)
        self.tasks = []
        self.roles = []
        self.ansible_command = None
        self.stdout = None

    def write_playbook(self):
        fname = os.path.join(TESTDIR, 'site.yml')
        pb_copy = self.playbook.copy()

        if self.playvars:
            pb_copy['vars'] = self.playvars
        if self.varsfiles:
            pb_copy['vars_files'] = self.varsfiles
        if self.roles:
            pb_copy['roles'] = []
            for role in self.roles:
                role.write_role()
                role_def = dict(role=role.name)
                role_def.update(role.params)
                pb_copy['roles'].append(role_def)
        if self.tasks:
            pb_copy['tasks'] = self.tasks

        with open(fname, 'w') as f:
            pb_yaml = yaml.dump([pb_copy], f, default_flow_style=False, indent=2)

    def build(self):

        if self.dynamic_inventory:
            # python based inventory file
            self.di = DynamicInventory(self.features)
            self.di.write_script()
        else:
            # ini based inventory file
            if 'ini_host' in self.features:
                self.inventory += 'testhost findme=ini_host\n'
            else:
                self.inventory += 'testhost\n'
            self.inventory += '\n'

            if 'ini_child' in self.features:
                self.inventory += '[child]\n'
                self.inventory += 'testhost\n'
                self.inventory += '\n'
                self.inventory += '[child:vars]\n'
                self.inventory += 'findme=ini_child\n'
                self.inventory += '\n'

            if 'ini_parent' in self.features:
                if 'ini_child' in self.features:
                    self.inventory += '[parent:children]\n'
                    self.inventory += 'child\n'
                else:
                    self.inventory += '[parent]\n'
                    self.inventory += 'testhost\n'
                self.inventory += '\n'
                self.inventory += '[parent:vars]\n'
                self.inventory += 'findme=ini_parent\n'
                self.inventory += '\n'

            if 'ini_all' in self.features:
                self.inventory += '[all:vars]\n'
                self.inventory += 'findme=ini_all\n'
                self.inventory += '\n'

            # default to a single file called inventory
            invfile = os.path.join(TESTDIR, 'inventory', 'hosts')
            ipath = os.path.join(TESTDIR, 'inventory')
            if not os.path.isdir(ipath):
                os.makedirs(ipath)

            with open(invfile, 'w') as f:
                f.write(self.inventory)

        hpath = os.path.join(TESTDIR, 'inventory', 'host_vars')
        if not os.path.isdir(hpath):
            os.makedirs(hpath)
        gpath = os.path.join(TESTDIR, 'inventory', 'group_vars')
        if not os.path.isdir(gpath):
            os.makedirs(gpath)

        if 'ini_host_vars_file' in self.features:
            hfile = os.path.join(hpath, 'testhost')
            with open(hfile, 'w') as f:
                f.write('findme: ini_host_vars_file\n')

        if 'ini_group_vars_file_all' in self.features:
            hfile = os.path.join(gpath, 'all')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_all\n')

        if 'ini_group_vars_file_child' in self.features:
            hfile = os.path.join(gpath, 'child')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_child\n')

        if 'ini_group_vars_file_parent' in self.features:
            hfile = os.path.join(gpath, 'parent')
            with open(hfile, 'w') as f:
                f.write('findme: ini_group_vars_file_parent\n')

        if 'pb_host_vars_file' in self.features:
            os.makedirs(os.path.join(TESTDIR, 'host_vars'))
            fname = os.path.join(TESTDIR, 'host_vars', 'testhost')
            with open(fname, 'w') as f:
                f.write('findme: pb_host_vars_file\n')

        if 'pb_group_vars_file_parent' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'parent')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_parent\n')

        if 'pb_group_vars_file_child' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'child')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_child\n')

        if 'pb_group_vars_file_all' in self.features:
            if not os.path.isdir(os.path.join(TESTDIR, 'group_vars')):
                os.makedirs(os.path.join(TESTDIR, 'group_vars'))
            fname = os.path.join(TESTDIR, 'group_vars', 'all')
            with open(fname, 'w') as f:
                f.write('findme: pb_group_vars_file_all\n')

        if 'play_var' in self.features:
            self.playvars['findme'] = 'play_var'

        if 'set_fact' in self.features:
            self.tasks.append(dict(set_fact='findme="set_fact"'))

        if 'vars_file' in self.features:
            self.varsfiles.append('varsfile.yml')
            fname = os.path.join(TESTDIR, 'varsfile.yml')
            with open(fname, 'w') as f:
                f.write('findme: vars_file\n')

        if 'include_vars' in self.features:
            self.tasks.append(dict(include_vars='included_vars.yml'))
            fname = os.path.join(TESTDIR, 'included_vars.yml')
            with open(fname, 'w') as f:
                f.write('findme: include_vars\n')

        if 'role_var' in self.features:
            role = Role('role_var')
            role.vars = True
            role.load = True
            self.roles.append(role)

        if 'role_parent_default' in self.features:
            role = Role('role_default')
            role.load = False
            role.defaults = True
            self.roles.append(role)

            role = Role('role_parent_default')
            role.dependencies.append('role_default')
            role.defaults = True
            role.load = True
            if 'role_params' in self.features:
                role.params = dict(findme='role_params')
            self.roles.append(role)

        elif 'role_default' in self.features:
            role = Role('role_default')
            role.defaults = True
            role.load = True
            if 'role_params' in self.features:
                role.params = dict(findme='role_params')
            self.roles.append(role)

        debug_task = dict(debug='var=findme')
        test_task = {'assert': dict(that=['findme == "%s"' % self.features[0]])}
        if 'task_vars' in self.features:
            test_task['vars'] = dict(findme="task_vars")
        if 'registered_vars' in self.features:
            test_task['register'] = 'findme'

        if 'block_vars' in self.features:
            block_wrapper = [
                debug_task,
                {
                    'block': [test_task],
                    'vars': dict(findme="block_vars"),
                }
            ]
        else:
            block_wrapper = [debug_task, test_task]

        if 'include_params' in self.features:
            self.tasks.append(dict(name='including tasks', include_tasks='included_tasks.yml', vars=dict(findme='include_params')))
        else:
            self.tasks.append(dict(include_tasks='included_tasks.yml'))

        fname = os.path.join(TESTDIR, 'included_tasks.yml')
        with open(fname, 'w') as f:
            f.write(yaml.dump(block_wrapper))

        self.write_playbook()

    def run(self):
        """
        if self.dynamic_inventory:
            cmd = 'ansible-playbook -c local -i inventory/hosts site.yml'
        else:
            cmd = 'ansible-playbook -c local -i inventory site.yml'
        """
        cmd = 'ansible-playbook -c local -i inventory site.yml'
        if 'extra_vars' in self.features:
            cmd += ' --extra-vars="findme=extra_vars"'
        cmd = cmd + ' -vvvvv'
        self.ansible_command = cmd
        (rc, so, se) = run_command(cmd, cwd=TESTDIR)
        self.stdout = so

        if rc != 0:
            raise Exception("playbook failed (rc=%s), stdout: '%s' stderr: '%s'" % (rc, so, se))

    def show_tree(self):
        print('## TREE')
        cmd = 'tree %s' % TESTDIR
        (rc, so, se) = run_command(cmd)
        lines = so.split('\n')
        lines = lines[:-3]
        print('\n'.join(lines))

    def show_content(self):
        print('## CONTENT')
        cmd = 'find %s -type f | xargs tail -n +1' % TESTDIR
        (rc, so, se) = run_command(cmd)
        print(so)

    def show_stdout(self):
        print('## COMMAND')
        print(self.ansible_command)
        print('## STDOUT')
        print(self.stdout)


def main():
    features = [
        'extra_vars',
        'include_params',
        # 'role_params',  # FIXME: we don't yet validate tasks within a role
        'set_fact',
        # 'registered_vars',  # FIXME: hard to simulate
        'include_vars',
        # 'role_dep_params',
        'task_vars',
        'block_vars',
        'role_var',
        'vars_file',
        'play_var',
        # 'host_facts',  # FIXME: hard to simulate
        'pb_host_vars_file',
        'ini_host_vars_file',
        'ini_host',
        'pb_group_vars_file_child',
        # 'ini_group_vars_file_child', # FIXME: this contradicts documented precedence pb group vars files should override inventory ones
        'pb_group_vars_file_parent',
        'ini_group_vars_file_parent',
        'pb_group_vars_file_all',
        'ini_group_vars_file_all',
        'ini_child',
        'ini_parent',
        'ini_all',
        'role_parent_default',
        'role_default',
    ]

    parser = OptionParser()
    parser.add_option('-f', '--feature', action='append')
    parser.add_option('--use_dynamic_inventory', action='store_true')
    parser.add_option('--show_tree', action='store_true')
    parser.add_option('--show_content', action='store_true')
    parser.add_option('--show_stdout', action='store_true')
    parser.add_option('--copy_testcases_to_local_dir', action='store_true')
    (options, args) = parser.parse_args()

    if options.feature:
        for f in options.feature:
            if f not in features:
                print('%s is not a valid feature' % f)
                sys.exit(1)
        features = list(options.feature)

    fdesc = {
        'ini_host': 'host var inside the ini',
        'script_host': 'host var inside the script _meta',
        'ini_child': 'child group var inside the ini',
        'script_child': 'child group var inside the script',
        'ini_parent': 'parent group var inside the ini',
        'script_parent': 'parent group var inside the script',
        'ini_all': 'all group var inside the ini',
        'script_all': 'all group var inside the script',
        'ini_host_vars_file': 'var in inventory/host_vars/host',
        'ini_group_vars_file_parent': 'var in inventory/group_vars/parent',
        'ini_group_vars_file_child': 'var in inventory/group_vars/child',
        'ini_group_vars_file_all': 'var in inventory/group_vars/all',
        'pb_group_vars_file_parent': 'var in playbook/group_vars/parent',
        'pb_group_vars_file_child': 'var in playbook/group_vars/child',
        'pb_group_vars_file_all': 'var in playbook/group_vars/all',
        'pb_host_vars_file': 'var in playbook/host_vars/host',
        'play_var': 'var set in playbook header',
        'role_parent_default': 'var in roles/role_parent/defaults/main.yml',
        'role_default': 'var in roles/role/defaults/main.yml',
        'role_var': 'var in ???',
        'include_vars': 'var in included file',
        'set_fact': 'var made by set_fact',
        'vars_file': 'var in file added by vars_file',
        'block_vars': 'vars defined on the block',
        'task_vars': 'vars defined on the task',
        'extra_vars': 'var passed via the cli'
    }

    dinv = options.use_dynamic_inventory
    if dinv:
        # some features are specific to ini, so swap those
        for (idx, x) in enumerate(features):
            if x.startswith('ini_') and 'vars_file' not in x:
                features[idx] = x.replace('ini_', 'script_')

    dinv = options.use_dynamic_inventory

    index = 1
    while features:
        VTM = VarTestMaker(features, dynamic_inventory=dinv)
        VTM.build()

        if options.show_tree or options.show_content or options.show_stdout:
            print('')
        if options.show_tree:
            VTM.show_tree()
        if options.show_content:
            VTM.show_content()

        try:
            print("CHECKING: %s (%s)" % (features[0], fdesc.get(features[0], '')))
            res = VTM.run()
            if options.show_stdout:
                VTM.show_stdout()

            features.pop(0)

            if options.copy_testcases_to_local_dir:
                topdir = 'testcases'
                if index == 1 and os.path.isdir(topdir):
                    shutil.rmtree(topdir)
                if not os.path.isdir(topdir):
                    os.makedirs(topdir)
                thisindex = str(index)
                if len(thisindex) == 1:
                    thisindex = '0' + thisindex
                thisdir = os.path.join(topdir, '%s.%s' % (thisindex, res))
                shutil.copytree(TESTDIR, thisdir)

        except Exception as e:
            print("ERROR !!!")
            print(e)
            print('feature: %s failed' % features[0])
            sys.exit(1)
        finally:
            shutil.rmtree(TESTDIR)
            index += 1


if __name__ == "__main__":
    main()
