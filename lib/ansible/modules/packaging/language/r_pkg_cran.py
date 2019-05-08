#!/usr/bin/python

# Copyright: (c) 2019, Daniel Chen <chendaniely@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: r_pkg_cran

short_description: Install R packages from CRAN

version_added: "2.4"

description:
    - "Install R packages from CRAN"

options:
    pkg_name:
        description:
            - Package name to install from CRAN
        required: true

extends_documentation_fragment:
    - azure

author:
    - Daniel Chen (@chendaniely)
'''

EXAMPLES = '''
# Install a single package
  - r_pkg_cran:
      name: 'gapminder'
      state: 'present'

# Install a multiple packages
  - r_pkg_cran:
      name: ['gapminder', 'AmesHousing']
      state: 'present'

# Remove a single package
  - r_pkg_cran:
      name: 'gapminder'
      state: 'absent'

# Remove multiple packages
  - r_pkg_cran:
      name: ['gapminder', 'AmesHousing']
      state: 'absent'
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils._text import to_native

def list_pkg(module):
    cmd = [module.rscript_bin_path, '-e', 'row.names(installed.packages())']
    rc, stdout, stderr = module.run_command(cmd)
    return stdout

def install_pkg(module, pkg_name):
    cmd = [module.rscript_bin_path, '-e', 'install.packages("{0}")'.format(pkg_name)]
    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        if stderr:
            module.fail_json(msg='{0}'.format(to_native(stderr)))

def remove_pkg(module, pkg_name):
    cmd = [module.rscript_bin_path, '-e', 'remove.packages("{0}")'.format(pkg_name)]
    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        module.fail_json(msg='{0}'.format(to_native(stderr)))

def require_pkg(module, pkg_name):
    """Require a package in R.
    In R, require will attempt to load and attach a package,
    If the package does not exist R will return FALSE.
    If the package does exist R will return TRUE.
    """
    cmd = [module.rscript_bin_path, '-e', 'require({0})'.format(pkg_name)]
    rc, stdout, stderr = module.run_command(cmd)
    module.fail_json(msg='{0}'.format(to_native(stderr)))

def main():
    module = AnsibleModule(
        argument_spec = {
            'name': {'type': 'list',
                     'required': True},
            'state': {'type': 'str',
                      'choices': ['absent', 'present'],
                      'default': 'present'}
            },
        supports_check_mode=True
    )

    result = {'changed': False}

    try:
        module.rscript_bin_path = get_bin_path('Rscript', required=True, opt_dirs=['/usr/bin'])
    except ValueError as e:
        module.fail_json(msg=to_native(e))

    packages = list_pkg(module)
    for pkg in module.params['name']:
        if module.params['state'] == 'present': # if you want to install the package
            if pkg not in packages:
                install_pkg(module, pkg)
                result['changed'] = True
        elif module.params['state'] == 'absent': # if you want to remove the package
            if pkg in packages:
                remove_pkg(module, pkg)
                result['changed'] = True
            else:
                require_pkg(module, pkg)
                            

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


if __name__ == '__main__':
    main()
