#!powershell

# Copyright: (c) 2019, RusoSova
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.2

$ErrorActionPreference = "Stop"

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

#Function to create a CIM object
Function GetCimsObject {
    param(
        [Parameter(Position=0)][string]$class #Class to query
    )
    try {
        $cimObj=Get-CimInstance -class $class
    } catch {
        $module.FailJson("There was an error retrieving Windows description $($_.Exception.Message)")
    }
    return $cimObj;
}

#Function to change CIM's object property. In this case used to change computer description
Function SetWinDescription {
    param(
        [Parameter(Position=0)]$object, #CIMs Object to apply the change too
        [Parameter(Position=0)]$property, #CIMs property to change
        [Parameter(Position=2)][string]$value #New value for the property
    )
    try {
        Set-CimInstance -InputObject $object -Property @{$property="$value"}
    } catch {
        $module.FailJson("There was an error changing Windows description $($_.Exception.Message)")
    }
}

#Function to update registry, in order to change license Owner and Organization
Function WinOwnership {
    param(
        [Parameter(Position=0)][ValidateSet("RegisteredOrganization","RegisteredOwner")][string]$type, #Organization or user
        [Parameter(Position=1)][ValidateSet("set","get")][string]$action, #Get Information or set information
        [Parameter(Position=2)][String]$value #Value to set
    )
	if ($action -eq "get") {
        try {
            $regObj=Get-ItemProperty -Path $regPath
        } catch {
            $module.FailJson("There was an error fetching registry $($_.Exception.Message)")
        }
		return $regObj.$type
    }
    #Upate Owner or Organization
    if ($action -eq "set") {
        try {
            Set-ItemProperty -Path $regPath -Name $type -Value $value
        } catch {
            $module.FailJson("There was an error updating $type $($_.Exception.Message)")
        }
    }
}

#Change description
if ($description -or $description -eq "") {
    $descriptionObject=GetCimsObject -class "Win32_OperatingSystem"
    if ($description -cne $descriptionObject.description) {
        if (-not $module.CheckMode) {
            SetWinDescription -object $descriptionObject -property "Description" -value $description
        }
        $module.Result.changed = $true
    }
}

#Change owner
if ($owner -or $owner -eq "") {
    $curentOwner=WinOwnership -type "RegisteredOwner"  -action "get"
    if ($curentOwner -cne $owner) {
        if (-not $module.CheckMode) {
            WinOwnership -type "RegisteredOwner"  -action "set" -value $owner
        }
        $module.Result.changed = $true
    }
}

#Change organization
if ($organization -or $organization -eq "") {
    $curentOrganization=WinOwnership -type "RegisteredOrganization"  -action "get"
    if ($curentOrganization -cne $organization) {
        if (-not $module.CheckMode) {
            WinOwnership -type "RegisteredOrganization"  -action "set" -value $organization
        }
        $module.Result.changed = $true
    }
}
$module.ExitJson()
