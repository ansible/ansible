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

short_description: Manage network configuration data in Nokia Core and Radio networks

version_added: "2.5"

description:
    netact_cm_command can be used to run various configuration management operations.
    This module requires that the target hosts have Nokia NetAct network management system installed.
    Module will access the Configurator command line interface in NetAct to upload network configuration to NetAct,
    run configuration export, plan import and configuration provision operations
    To set the scope of the operation, define Distinguished Name (DN) or Working Set (WS) or
    Maintenance Region (MR) as input
options:
    operation:
        description:
            Supported operations allow user to upload actual configuration from the network, to import and
            provision prepared plans, or export reference or actual configuration for planning purposes.
            Provision_Mass_Modification enables provisioning the same parameters to multiple network elements.
            This operation supports modifications only to one object class at a time. With this option
            NetAct Configurator creates and provisions a plan to the network with the given scope and options.
        required: true
        choices:
            - upload
            - provision
            - import
            - export
            - Provision_Mass_Modification
        aliases:
            - op
    opsName:
        description:
            - user specified operation name
        required: false
    DN:
        description:
            Sets the exact scope of the operation in form of a list of managed object
            Distinguished Names (DN) in the network.
            A single DN or a list of DNs can be given (comma separated list without spaces).
            Alternatively, if DN or a list of DNs is not given, working set (WS) or Maintenance Region (MR)
            must be provided as parameter to set the scope of operation.
        required: false

    WS:
        description:
            Sets the scope of the operation to use one or more pre-defined working sets (WS) in NetAct.
            A working set contains network elements selected by user according to defined criteria.
            A single WS name, or multiple WSs can be provided (comma-separated list without spaces).
            Alternatively, if a WS name or a list of WSs is not given, Distinguished Name (DN) or
            Maintenance Region(MR) must be provided as parameter to set the scope of operation.
        required: false
    MR:
        description:
            Sets the scope of the operation to network elements assigned to a Maintenance Region (MR)
            Value can be set as MR IDs including the Maintenance Region Collection (MRC)
            information (for example MRC-FIN1/MR-Hel).
            Multiple MRs can be given (comma-separated list without spaces)
            The value of this parameter is searched through MR IDs under given MRC. If there is no match,
            then it is searched from all MR names.
            Alternatively, if MR ID or a list or MR IDs is not given, Distinguished Name (DN) or Working Set (WS)
            must be provided as parameter to set the scope of operation.
        required: false
    planName:
        description:
            - Specifies a plan name.
        required: false
    typeOption:
        description:
             Specifies the type of the export operation.
        required: false
        choices:
          - plan
          - actual
          - reference
          - template
          - siteTemplate
        aliases:
            - type
    fileFormat:
        description:
            Indicates file format.
        required: false
        choices:
            - RAML2
            - CSV
            - XLSX
    fileName:
        description:
            - Specifies a file name. Valid for Import and Export operations.
        required: false
    inputFile:
        description:
            Specifies full path to plan file location for the import operation.
            This parameter (inputFile) or the fileName parameter must be filled. If both are present then
            the inputFile is used.
        required: false
    createBackupPlan:
        description:
            - Specifies if backup plan generation is enabled.
        required: false
        type: bool
    backupPlanName:
        description:
            - Specifies a backup plan name
        required: false
    verbose:
        description:
            NetAct Configurator will print more info
        required: false
    extra_opts:
        description:
            Extra options to be set for operations. Check Configuration Management > Configuration Management
            Operating Procedures > Command Line Operations in Nokia NetAct user documentation for further
            information for extra options.
        required: false
notes:
    - Check mode is not currently supported
author:
    - Harri Tuominen (@hatuomin)
'''

EXAMPLES = '''
# Pass in a message
- name: Upload
  netact_cm_command:
    operation: "Upload"
    opsname: 'Uploading_test'
    dn: "PLMN-PLMN/MRBTS-746"
    extra_opts: '-btsContentInUse true'

- name: Provision
  netact_cm_command:
    operation: "Provision"
    opsname: 'Provision_test'
    dn: "PLMN-PLMN/MRBTS-746"
    planName: 'mySiteTemplate'
    type: 'actual'
    createBackupPlan: true
    backupPlanName: 'myBackupPlanName'

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
    fileFormat: 'CSV'
    type: 'plan'
    fileName: 'myCSVFile'
    planName: 'myPlanName'
    extra_ops: 'enablePolicyPlans true'

# fail the module
- name: Test failure of the module
  netact_cm_command:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    returned: Command line
    type: str
    sample: '/opt/oss/bin/racclimx.sh -op Upload -opsName Uploading_testi -DN PLMN-PLMN/MRBTS-746'
message:
    description: The output message that the netact_cm_command module generates
    returned: Command output message
    type: str
changed:
    description: data changed
    returned: true if data is changed
    type: bool
'''

from ansible.module_utils.basic import AnsibleModule

racclimx = '/opt/oss/bin/racclimx.sh'


def main():
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
        opsName=dict(type='str', required=False),
        DN=dict(type='str', required=False),
        WS=dict(type='str', required=False),
        MR=dict(type='str', required=False),

        planName=dict(type='str', required=False),
        typeOption=dict(type='str', required=False, aliases=['type'],
                        choices=['plan', 'actual', 'reference', 'template', 'siteTemplate']),
        fileFormat=dict(type='str', required=False, choices=['CSV', 'RAML2', 'XLSX']),
        fileName=dict(type='str', required=False),
        createBackupPlan=dict(type='bool', required=False),
        backupPlanName=dict(type='str', required=False),
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
        cmd='',
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
        result['skipped'] = True
        result['msg'] = 'check mode not (yet) supported for this module'
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    operation = module.params.get('operation')
    if not operation:
        module.fail_json(msg='Operation not defined', **result)

    opsname = module.params.get('opsName')
    dn = module.params.get('DN')
    ws = module.params.get('WS')
    mr = module.params.get('MR')

    planname = module.params.get('planName')
    typeoption = module.params.get('typeOption')
    fileformat = module.params.get('fileFormat')
    filename = module.params.get('fileName')

    createBackupPlan = module.params.get('createBackupPlan')
    backupPlanName = module.params.get('backupPlanName')
    inputfile = module.params.get('inputFile')

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
        command.append(ws)

    if mr:
        command.append('-MR')
        command.append(mr)

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
        command.append('true')

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
        result['original_message'] = out
        result['cmd'] = command
        result['message'] = out

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


if __name__ == '__main__':
    main()
