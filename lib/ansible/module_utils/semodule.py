from ansible.errors import AnsibleError

def parse_pol_info(name, semodule_info):
        cur_pol = {}
        semodule_list = semodule_info.split('\n')
        for line in semodule_list:
            if name in line:
                cur_pol['name'] ,cur_pol['version'] = line.split('\t')
        return cur_pol

def read_te_file(file):
    try:
        with open(file, 'r') as te_file:
            return [ x.strip(';').split(' ') for x in te_file.read().split('\n') if 'module' in x ][0]
    except IndexError:
        AnsibleError('Module is missing module definition line')

def parse_module_info(module_info):
    policy_def = {}
    policy_def['name'] = module_info[1]
    policy_def['version'] = module_info[2]
    return policy_def