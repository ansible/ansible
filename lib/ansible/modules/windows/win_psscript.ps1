#!powershell

# Copyright: (c) 2020, Brian Scholer <@briantist>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module @{ ModuleName = 'PowerShellGet' ; ModuleVersion = '1.6.0' }

$spec = @{
    supports_check_mode = $true
    options = @{
        name = @{
            type = 'str'
            required = $true
        }
        repository = @{ type = 'str' }
        scope = @{
            type = 'str'
            choices = @('all_users', 'current_user')
            default = 'all_users'
        }
        state = @{
            type = 'str'
            choices = @('present', 'absent', 'latest')
            default = 'present'
        }
        required_version = @{ type = 'str' }
        minimum_version = @{ type = 'str' }
        maximum_version = @{ type = 'str' }
        source_username = @{ type = 'str' }
        source_password = @{
            type = 'str'
            no_log = $true
        }
        allow_prerelease = @{
            type = 'bool'
            default = $false
        }
    }

    mutually_exclusive = @(
       @('required_version', 'minimum_version'),
       @('required_version', 'maximum_version')
   )

   required_together = @(
       ,@('source_username', 'source_password')
   )
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$state = $module.Params.state
function Get-SplattableParameters {
    [CmdletBinding(DefaultParameterSetName='All')]
    [OutputType([hashtable])]
    param(
        [Parameter(Mandatory=$true)]
        [Ansible.Basic.AnsibleModule]
        $Module ,

        [Parameter(ParameterSetName='ForCommand')]
        [Alias('For')]
        [String]
        $ForCommand ,

        [Parameter(ParameterSetName='WithCommand', ValueFromPipeline=$true)]
        [Alias('Command')]
        [System.Management.Automation.CommandInfo]
        $WithCommand
    )

    Process {
        $ret = @{}

        $cmd = switch ($PSCmdlet.ParameterSetName) {
            'WithCommand' { $WithCommand }
            'ForCommand' { Get-Command -Name $ForCommand }
        }

        if ($cmd) {
            $commons = [System.Management.Automation.Cmdlet]::CommonParameters + [System.Management.Automation.Cmdlet]::CommonOptionalParameters
            $validParams = $cmd.Parameters.GetEnumerator() | ForEach-Object -Process {
                if ($commons -notcontains $_.Key) {
                    $_.Key
                }
            }
        }

        switch -Wildcard ($Module.Params.Keys) {
            '*' {
                $value = $Module.Params[$_]
                if ($null -eq $value) {
                    continue
                }

                $key = $_.Replace('_', '')
                if ($validParams -and $validParams -notcontains $key) {
                    continue
                }
            }

            'scope' { $value = $value.Replace('_', '') }
            'source_username' { continue } # handled in password block
            'source_password' {
                $key = 'Credential'
                $secure = ConvertTo-SecureString -String $value -AsPlainText -Force
                $value = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $Module.Params.source_username,$secure
            }
            '*_version' {
                if ($Module.Params.state -eq 'latest') {
                    $Module.FailJson("version options can't be used with 'state': 'latest'")
                }
            }
            'repository' {
                if ($Module.Params.state -eq 'absent') {
                    $Module.FailJson("'repository' is not valid with 'state': 'absent'")
                }
            }

            '*' { $ret[$key] = $value }
        }

        $ret
    }
}

$pGet,$pUninstall,$pFind,$pInstall = Get-Command -Name @(
     'Get-InstalledScript'
    ,'Uninstall-Script'
    ,'Find-Script'
    ,'Install-Script'
) | Get-SplattableParameters -Module $module

$existing = Get-InstalledScript @pGet -ErrorAction SilentlyContinue
$existing = if ($existing) {
    $existing | Group-Object -Property Name -AsHashTable -AsString
}
else {
    @{}
}

if ($state -eq 'absent') {
    if ($existing.Count) {
        try {
            $module.Result.changed = $true
            $existing.Values | Uninstall-Script -Force -WhatIf:$module.CheckMode -ErrorAction Stop
        } catch {
            $module.FailJson("Error uninstalling scripts.", $_)
        }
    }
}
else { # state is 'present' or 'latest'
    try {
        $remote = Find-Script @pFind -ErrorAction Stop
    } catch {
        $module.FailJson("Error searching for scripts.", $_)
    }

    try {
        $toInstall = $remote | Where-Object -FilterScript {
            $install = -not $existing.ContainsKey($_.Name) -or (
                $state -eq 'latest' -and
                ($_.Version -as [version]) -gt ($existing[$_.Name].Version -as [version])
            )
            $module.Result.changed = $module.Result.changed -or $install
            $install
        }

        if (($toInstall | Group-Object -Property Name -NoElement | Where-Object -Property Count -gt 1)) {
            $module.FailJson("Multiple scripts found. Please choose a specific repository.")
        }

        $toInstall | Install-Script -Scope:$pInstall.scope -Force -WhatIf:$module.CheckMode -ErrorAction Stop
    } catch {
        $module.FailJson("Error installing scripts.", $_)
    }
}

$module.ExitJson()
