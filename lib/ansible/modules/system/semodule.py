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
from ansible.module_utils._text import to_bytes, to_text
import os

# check each portion of policy version
def check_verison(version, cur_version):
    version_list = version.split('.')
    cur_version_list = cur_version.split('.')
    for num in version_list:
        loc = version_list.index(num)
        if version_list[loc] < cur_version_list[loc]:
            return True, 'older'
        elif version_list[loc] > cur_version_list[loc]:
            return True, 'newer'
    return False, 'same'

def get_semodule_info(module):
    rc, stdout, stderr = module.run_command(['semodule', '-l'])
    if rc != 0:
        module.fail_json(msg='semodule command failed')
    return stdout

def module_exist(module, name, semodule_info):
    if name in semodule_info:
        return True
    return False

#selinux module info
def module_info(module, name, semodule_info):
    cur_pol = {}
    semodule_list = semodule_info.split('\n')
    for line in semodule_list:
        if name in line:
            cur_pol['name'] ,cur_pol['version'] = line.split('\t')
    return cur_pol

def check_mode_exit(module, changed, policy_name, policy_version):
    if module.check_mode:
        module.exit_json(changed=changed, name=policy_name, version=policy_version)

def ensure(module, te_file, policy_def):
    changed = False
    semodule_info = get_semodule_info()
    if module_exist(policy_def['name'], semodule_info):
        if module.params['state'] == 'absent':
            check_mode_exit(module, True, policy_def['name'], '')
            remove_module(module, policy_def)
            changed = True
        cur_pol = module_info(policy_def['name'], semodule_info)
        ver_result = check_verison(policy_def['version'].split('.'), cur_pol['version'].split('.'))
        if ver_result[0]:
            if module.params['state'] == 'latest':
                check_mode_exit(module, True, policy_def['name'], policy_def['version'])
                apply_te_file(module, policy_def)
                changed = True
    else:
        check_mode_exit(module, policy_def['name'], policy_def['version'])
        apply_te_file(module, policy_def)
        changed = True
    end_pol = module_info(policy_def['name'], get_semodule_info())
    module.exit_json(changed=changed, name=end_pol['name'], version=end_pol['version'])

def check_run_fail(run, module):
    if run[0] != 0:
        module.fail_json(msg=run[2])

def remove_module(module, policy_def):
    semodule_out = module.run_command(['semodule','-r',policy_def['name']])
    check_run_fail(semodule_out, module)
    
def apply_te_file(module, policy_def):
    chk_module_out = module.run_command(['checkmodule','-M','-m', module.tmpdir+'/'+policy_def['name']+'.te', '-o', module.tmpdir+'/'+policy_def['name']+'.mod'])
    check_run_fail(chk_module_out, module)
    semod_package_out = module.run_command(['semodule_package','-o',module.tmpdir+'/'+policy_def['name']+'.pp','-m' ,module.tmpdir+'/'+policy_def['name']+'.mod'])
    check_run_fail(semod_package_out, module)
    semodule_out = module.run_command(['semodule', '-i',module.tmpdir+'/'+policy_def['name']+'.pp'])
    check_run_fail(semodule_out, module)

def copy_te_file(module, mod_name, te_module):
    try:
        with open(module.tmpdir+'/'+mod_name, 'w') as te_file:
            te_file.write(te_module)
    except IOError:
        module.fail_json(msg='Could not write te_file to host')

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
            type_enforcement_file=dict(type='path', required=True, aliases=['te_file']),
            state=dict(type='str', default='present', choices=['present', 'latest', 'absent'])
            ),
        supports_check_mode=True
    )
    check_requirements(module)
    te_module = to_text(module.params['type_enforcement_file'])
    # module mysemanage 1.0;
    intro_line = te_module.split('\n')[0].strip(';').split(' ')
    policy_def = {}
    policy_def['name'] = intro_line[1]
    policy_def['version'] = intro_line[2]
    ensure(module, te_file, policy_def)

if __name__ == '__main__':
    main()