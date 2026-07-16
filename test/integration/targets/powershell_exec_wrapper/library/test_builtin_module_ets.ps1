#!powershell

using namespace Ansible.Basic

#AnsibleRequires -CSharpUtil Ansible.Basic

$module = [AnsibleModule]::Create($args, @{ options = @{} })

# InitialSessionState.CreateDefault() (not CreateDefault2()) imports
# Microsoft.PowerShell.Security as a snapin module but snapins do not have
# ETS type definitions. The hosting pipeline needs to be created with
# InitialSessionState.CreateDefault2() which does not load anything by default
# and any subsequent imports will import the module and full ETS definitions
# like normal.
Import-Module -Name Microsoft.PowerShell.Security

$typeData = Get-TypeData -TypeName System.Security.AccessControl.ObjectSecurity
$module.Result.count = $typeData.Members.Count

$module.ExitJson()
