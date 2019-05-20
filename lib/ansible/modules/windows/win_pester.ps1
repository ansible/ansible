#!powershell

# Copyright: (c) 2017, Erwan Quelin (@equelin) <erwan.quelin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        path = @{ type = "str"; required = $true }
        version = @{ type = "str"; required = $false }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$version = $module.Params.version

$module.result.changed = $false

# Test if parameter $version is valid
Try {
    $version = [version]$version
}
Catch {
    $module.FailJson("Value '$version' for parameter 'version' is not a valid version format")
}

# Make sure path is a real path
Try {
    $path = $path.TrimEnd("\")
    $path = (Get-item -LiteralPath $path).FullName
    Test-Path $path
}
Catch {
    $module.FailJson("Cannot find file or directory: '$path' as it does not exist")
}

# Import Pester module if available
$Pester = 'Pester'

If (-not (Get-Module -Name $Pester -ErrorAction SilentlyContinue)) {
    If (Get-Module -Name $Pester -ListAvailable -ErrorAction SilentlyContinue) {
        Import-Module $Pester
    } else {
        $module.FailJson("Cannot find module: $Pester. Check if pester is installed, and if it is not, install using win_psmodule or win_chocolatey.")
    }
}

# Add actual pester's module version in the ansible's result variable
$Pester_version = (Get-Module -Name $Pester).Version.ToString()
$module.result.pester_version = $Pester_version

# Test if the Pester module is available with a version greater or equal than the one specified in the $version parameter
If ((-not (Get-Module -Name $Pester -ErrorAction SilentlyContinue | Where-Object {$_.Version -ge $version})) -and ($version)) {
    $module.FailJson("$Pester version is not greater or equal to $version")
}

#Prepare Invoke-Pester parameters depending of the Pester's version.
#Invoke-Pester output deactivation behave differently depending on the Pester's version
If ($module.result.pester_version -ge "4.0.0") {
    $Parameters = @{
        "show" = "none"
        "PassThru" = $True
    }
} else {
    $Parameters = @{
        "quiet" = $True
        "PassThru" = $True
    }
}

# Run Pester tests
if ($check_mode) {
    $module.result.output = "Run Pester test(s): $path"
} else {
    try {
        $module.result.output = Invoke-Pester $path @Parameters
    } catch {
        $module.FailJson($_.Exception)
    }
}

$module.result.changed = $true

$module.ExitJson()