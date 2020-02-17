#!powershell

# Copyright: (c) 2019, RusoSova
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.1

$spec = @{
    options = @{
        owner = @{ type="str" }
        organization = @{ type="str" }
        description = @{ type="str" }
    }
    required_one_of = @(
        ,@('owner', 'organization', 'description')
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$owner = $module.Params.owner
$organization = $module.Params.organization
$description = $module.Params.description
$regPath="HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\"

#Change description
if ($description -or $description -eq "") {
    $descriptionObject=Get-CimInstance -class "Win32_OperatingSystem"
    if ($description -cne $descriptionObject.description) {
        Set-CimInstance -InputObject $descriptionObject -Property @{"Description"="$description"} -WhatIf:$module.CheckMode
        $module.Result.changed = $true
    }
}

#Change owner
if ($owner -or $owner -eq "") {
    $curentOwner=(Get-ItemProperty -LiteralPath $regPath -Name RegisteredOwner).RegisteredOwner
    if ($curentOwner -cne $owner) {
        Set-ItemProperty -LiteralPath $regPath -Name "RegisteredOwner" -Value $owner -WhatIf:$module.CheckMode
        $module.Result.changed = $true
    }
}

#Change organization
if ($organization -or $organization -eq "") {
    $curentOrganization=(Get-ItemProperty -LiteralPath $regPath -Name RegisteredOrganization).RegisteredOrganization
    if ($curentOrganization -cne $organization) {
        Set-ItemProperty -LiteralPath $regPath -Name "RegisteredOrganization" -Value $organization -WhatIf:$module.CheckMode
        $module.Result.changed = $true
    }
}
$module.ExitJson()
