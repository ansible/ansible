# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Payload
)

#AnsibleRequires -Wrapper module_wrapper

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting module_script_wrapper" "module_script_wrapper"

$script = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.module_entry))

# get the common module_wrapper code and invoke that to run the module
$entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.module_wrapper))
$entrypoint = [ScriptBlock]::Create($entrypoint)

&$entrypoint -Scripts $script -Environment $Payload.environment -ModuleName "script"

Write-AnsibleLog "INFO - ending module_script_wrapper" "module_script_wrapper"
