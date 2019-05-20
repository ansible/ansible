#!powershell

# Copyright: (c) 2017, Erwan Quelin (@equelin) <erwan.quelin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        path = @{ type = "str"; required = $true }
        version = @{ type = "str" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$path = $module.Params.path
$version = $module.Params.version

# Test if parameter $version is valid
If ($version) {
    Try {
        $version = [version]$version
    }
    Catch {
        $module.FailJson("Value '$version' for parameter 'version' is not a valid version format")
    }
}

# Import Pester module if available
$PesterModule = 'Pester'

If (-not (Get-Module -Name $PesterModule -ErrorAction SilentlyContinue)) {
    If (Get-Module -Name $PesterModule -ListAvailable -ErrorAction SilentlyContinue) {
        Import-Module $PesterModule
    } else {
        $module.FailJson("Cannot find module: $PesterModule. Check if pester is installed, and if it is not, install using win_psmodule or win_chocolatey.")
    }
}

# Add actual pester's module version in the ansible's result variable
$module.result.pester_version = $( (Get-Module -Name $PesterModule).Version.ToString() )

# Test if the Pester module is available with a version greater or equal than the one specified in the $version parameter
If (-not (Get-Module -Name $PesterModule -ErrorAction SilentlyContinue | Where-Object {$_.Version -ge $version}) ) {
    $module.FailJson("$PesterModule version is not greater or equal to $version")
}

# Testing if test file or directory exist
If (-not (Test-Path -LiteralPath $path)) {
    $module.FailJson("Cannot find file or directory: '$path' as it does not exist")
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
If ($check_mode) {
    If (Test-Path -LiteralPath $path -PathType Leaf) {
        $module.result.output = "Run pester test in the file: $path"
    } elseif (Test-Path -LiteralPath $path -PathType Container) {
        $module.result.output = "Run pester test(s) who are in the directory: $path"
    }
} else {
    try {
        $module.result.output = Invoke-Pester $path @Parameters
    } catch {
        $module.FailJson($_.Exception)
    }
}

$module.result.changed = $true

$module.ExitJson()
