@{
    ModuleVersion = '{{item.version}}'
    GUID = '{{item.version|to_uuid}}'
    Author = 'Ansible'
    CompanyName = 'Ansible'
    Copyright = '(c) 2017'
    Description = 'Test DSC Resource for Ansible integration tests'
    PowerShellVersion = '5.0'
    CLRVersion = '4.0'
    FunctionsToExport = '*'
    CmdletsToExport = '*'
}
