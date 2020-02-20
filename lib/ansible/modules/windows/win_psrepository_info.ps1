#!powershell

# Copyright: (c) 2020, Brian Scholer <@briantist>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.CamelConversion
#Requires -Module PowerShellGet

$spec = @{
    options = @{
        name = @{ type = 'str' ; default = '*' }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

function Convert-ObjectToSnakeCase {
    <#
        .SYNOPSIS
        Converts an object with CamelCase properties to a dictionary with snake_case keys.
        Works in the spirit of and depends on the existing CamelConversion module util.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true,ValueFromPipeline=$true)]
        [OutputType([System.Collections.Specialized.OrderedDictionary])]
        [Object]
        $InputObject ,

        [Parameter()]
        [Switch]
        $NoRecurse ,

        [Parameter()]
        [Switch]
        $OmitNull
    )

    Process {
        $result = [Ordered]@{}
        foreach ($property in $InputObject.PSObject.Properties) {
            $value = $property.Value
            if (-not $NoRecurse -and $value -is [System.Collections.IDictionary]) {
                $value = Convert-DictToSnakeCase -dict $value
            }
            elseif (-not $NoRecurse -and ($value -is [Array] -or $value -is [System.Collections.ArrayList])) {
                $value = Convert-ListToSnakeCase -list $value
            }
            elseif ($null -eq $value) {
                if ($OmitNull) {
                    continue
                }
            }
            elseif (-not $NoRecurse -and $value -isnot [System.ValueType] -and $value -isnot [string]) {
                $value = Convert-ObjectToSnakeCase -InputObject $value
            }

            $name = Convert-StringToSnakeCase -string $property.Name
            $result[$name] = $value
        }
        $result
    }
}

$module.Result.repositories = @(Get-PSRepository -Name $module.Params.name | Convert-ObjectToSnakeCase)

$module.ExitJson()
