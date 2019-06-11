#!/usr/bin/python

ANSIBLE_METADATA = {
    'metdata_version': 1.1,
    'status': ['preview'],
    'supported_by': 'community'
}

# TODO: write
DOCUMENTATION = '''

'''

EXAMPLES = '''
'''

RETURN = '''
'''

REQUIREMENTS = [
    'semodule', 
    'checkmodule',
    'semodule_package'
]

from ansible.module_utils.basic import AnsibleModule
import os


def get_semodule_info(module):
    rc, stdout, stderr = module.run_command(['semodule', '-l'])
    if rc != 0:
        module.fail_json(msg='semodule command failed')
    return stdout

#selinux module info
def module_info(name, semodule_info):
    cur_pol = {}
    semodule_list = semodule_info.split('\n')
    for line in semodule_list:
        if name in line:
            cur_pol['name'] ,cur_pol['version'] = line.split('\t')
    return cur_pol


def check_mode_exit(module, changed, policy_name, policy_version):
    if module.check_mode:
        module.exit_json(changed=changed, name=policy_name, version=policy_version)


def ensure(module, policy_def):
    changed = False
    apply_te_file(module, policy_def)
    end_pol = module_info(policy_def['name'], get_semodule_info(module))
    changed = True
    module.exit_json(changed=changed, name=end_pol['name'], version=end_pol['version'])

def check_run_fail(run, module):
    if run[0] != 0:
        module.fail_json(msg=run[2])

def apply_te_file(module, policy_def):
    chk_module_out = module.run_command(['checkmodule','-M','-m', module.params['src'], '-o', policy_def['name']+'.mod'])
    check_run_fail(chk_module_out, module)
    semod_package_out = module.run_command(['semodule_package','-o', policy_def['name']+'.pp','-m' , policy_def['name']+'.mod'])
    check_run_fail(semod_package_out, module)
    semodule_out = module.run_command(['semodule', '-i', policy_def['name']+'.pp'])
    check_run_fail(semodule_out, module)


def get_te_info(module):
    with open(module.params['src'], 'r') as te_file:
        return te_file.read().split('\n')[0].strip(';').split(' ')


def check_requirements(module):
    if os.getuid() != 0:
        module.fail_json(msg='This module can only be run elevated')
    for req in REQUIREMENTS:
        rc, stdout, stderr = module.run_command(['which', req])
        if rc != 0 :
            module.fail_json(msg='missing the {name} utility which is required to run this module'.format(name=req))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True),
            state=dict(type='str', default='present', choices=['present', 'latest', 'absent'])
        ),
        supports_check_mode=True
    )
    check_requirements(module)
    # module mysemanage 1.0;
    intro_line = get_te_info(module)
    #module.fail_json(msg=intro_line)
    policy_def = {}
    policy_def['name'] = intro_line[1]
    policy_def['version'] = intro_line[2]
    ensure(module, policy_def)

if __name__ == '__main__':
    main()