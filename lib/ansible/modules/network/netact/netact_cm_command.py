#!/usr/bin/python
# Copyright: Nokia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name
# pylint: disable=wrong-import-position
# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements

"""
NetAct CM ansible command module
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: netact_cm_command

short_description: NetAct CM operation ansible module

version_added: "2.5"

description:
    netact_cm_command can be used to run various configuration management operations.
    This ansible module requires that target host have Nokia NetAct CM.
options:
    operation:
        description:
            operation
            Supported operations are upload, provision, import, export and Provision_Mass_Modification.
        required: true
    opsName:
        description:
            - user specified operation name
        required: false
    DN:
        description:
            - Specifies the scope of the operation (comma-separated Distinguished Names without spaces)
        required: false
    WS:
        description:
            Specifies the scope of the operation as defined in the working set
            (comma-separated working set names without spaces).
            At least one of the arguments DN or WS must be defined.
        required: false
    MR:
        description:
            Specifies the scope of the operation as defined in the maintenance region.
            MR id can be defined as a DN which contains MRC information (e.g. MRC-T1/MR-Test28).
            The comma-separated instance IDs (for example MRC-T1/MR-Test28) and/or maintenance region names
            without spaces). The value (string) of this argument is searched through MRs' instance
            Ids under specific MR collection. If there is no such value, then it is searched through
            MRs' names. Objects assigned to a given maintenance regions are added to the operation scope
        required: false
    planName:
        description:
            - Specifies a plan name.
        required: false
    type:
        description:
            - Specifies the type of the export operation (plan/actual/reference/template/siteTemplate)
        required: true
    fileFormat:
        description:
            - Indicates the CSV or RAML2 file format.
        required: false
    fileName:
        description:
            - Specifies a file name.
        required: false
    inputFile:
        description:
            Specifies the full file path for the import operation. 
            This parameter or the fileName parameter must be filled. 
            If both are present then the inputFile is used.
        required: false
    createBackupPlan:
        description:
            - Specifies if backup plan generation is enabled.
        required: false
    backupPlanName:
        description:
            - Specifies a backup plan name
        required: false
    extra_opts:
        description:
            Extra options to be set for operations
        required: true

author:
    - Harri Tuominen (@externalip)
'''

EXAMPLES = '''
# Pass in a message
- name: Upload
  netact_cm_command:
    operation: "Upload"
    opsname: 'Uploading_test'
    dn: "PLMN-PLMN/MRBTS-746"
    extra_opts: '-btsContentInUse true -bssHwContentInUse true'

- name: Provision
  netact_cm_command:
    operation: "Provision"
    opsname: 'Provision_test'
    dn: "PLMN-PLMN/MRBTS-746"    

- name: Export and fetching data from target
  netact_cm_command:
    operation: "Export"
    opsname: 'Export_test'
    planName: 'mySiteTemplate'
    type: 'actual'
    fileName: 'exportTest.xml'
- fetch:
    src: /var/opt/nokia/oss/global/racops/export/exportTest.xml
    dest: fetched
       
- name: Import
  netact_cm_command:
    operation: "Import"
    opsname: 'Import_test'
    
# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the netact_cm_command module generates
'''

from ansible.module_utils.basic import AnsibleModule

racclimx = '/opt/oss/bin/racclimx.sh'


def run_module():
    """
    Main module where option are handled and command is executed
    :return:
    """
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        operation=dict(type='str', required=True,
                       aliases=['op'],
                       choices=['Upload', 'Provision', 'Import',
                                'Export', 'Provision_Mass_Modification']),
        opsname=dict(type='str', required=False, aliases=['opsName']),
        dn=dict(type='str', required=False, aliases=['WS']),
        ws=dict(type='str', required=False, aliases=['DN']),
        mr=dict(type='str', required=False, aliases=['MR']),

        planname=dict(type='str', required=False, aliases=['planName']),
        typeoption=dict(type='str', required=False, aliases=['type'],
                        choices=['plan', 'actual', 'reference', 'template', 'siteTemplate']),
        fileformat=dict(type='str', required=False, choices=['CSV', 'RAML2'],
                        aliases=['fileFormat']),
        filename=dict(type='str', required=False, aliases=['fileName']),

        createBackupPlan=dict(type='str', required=False, choices=['true', 'false'],
                              aliases=['createBackupPlan']),
        backupPlanName=dict(type='str', required=False, aliases=['backupPlanName']),
        inputFile=dict(type='str', required=False),

        verbose=dict(type='str', required=False),
        extra_opts=dict(type='str', required=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    operation = module.params.get('operation')
    if not operation:
        module.fail_json(msg='Operation not defined', **result)

    opsname = module.params.get('opsname')
    dn = module.params.get('dn')
    ws = module.params.get('ws')
    mr = module.params.get('mr')

    planname = module.params.get('planname')
    typeoption = module.params.get('typeoption')
    fileformat = module.params.get('fileformat')
    filename = module.params.get('filename')

    createBackupPlan = module.params.get('createBackupPlan')
    backupPlanName = module.params.get('backupPlanName')
    inputfile = module.params.get('imputFile')

    extra_opts = module.params.get('extra_opts')
    verbose = module.params.get('verbose')

    # parameter checks

    command = [racclimx, '-op', operation]

    if opsname:
        command.append('-opsName')
        command.append(opsname)

    if dn:
        command.append('-DN')
        command.append(dn)

    if ws:
        command.append('-WS')
        command.append(dn)

    if mr:
        command.append('-MR')
        command.append(dn)

    if planname:
        command.append('-planName')
        command.append(planname)

    if typeoption:
        command.append('-type')
        command.append(typeoption)

    if fileformat:
        command.append('-fileFormat')
        command.append(fileformat)

    if filename:
        command.append('-fileName')
        command.append(filename)

    if createBackupPlan:
        command.append('-createBackupPlan')
        command.append(createBackupPlan)

    if backupPlanName:
        command.append('-backupPlanName')
        command.append(backupPlanName)

    if inputfile:
        command.append('-inputFile')
        command.append(inputfile)

    if extra_opts:
        command = command + extra_opts.split(" ")

    if verbose:
        if verbose == 'True':
            command.append("-v")

    rc, out, err = module.run_command(command, check_rc=True)
    if rc != 0:
        result['changed'] = False
        module.fail_json(msg=err)
    else:
        result['changed'] = True
        result['original_message'] = command
        result['message'] = out

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    """
    main
    :return:
    """
    run_module()


if __name__ == '__main__':
    main()
