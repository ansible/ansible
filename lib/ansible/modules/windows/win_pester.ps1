#!powershell

# Copyright: (c) 2017, Erwan Quelin (@equelin) <erwan.quelin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        output_file = @{ type = "str" }
        output_format = @{ type = "str"; default = "NunitXML" }
        path = @{ type = "str"; required = $true }
        tags = @{ type = "list"; elements = "str" }
        test_parameters = @{ type = "dict" }
        version = @{ type = "str"; aliases = @(,"minimum_version") }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$output_file = $module.Params.output_file
$output_format = $module.Params.output_format
$path = $module.Params.path
$tags = $module.Params.tags
$test_parameters = $module.Params.test_parameters
$version = $module.Params.version

Try {
    $version = [version]$version
}
Catch {
    $module.FailJson("Value '$version' for parameter 'minimum_version' is not a valid version format")
}

# Make sure path is a real path
Try {
    $path = $path.TrimEnd("\")
    $path = (Get-item -LiteralPath $path).FullName
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
$module.Result.pester_version = $Pester_version

# Test if the Pester module is available with a version greater or equal than the one specified in the $version parameter
If ((-not (Get-Module -Name $Pester -ErrorAction SilentlyContinue | Where-Object {$_.Version -ge $version})) -and ($version)) {
    $module.FailJson("$Pester version is not greater or equal to $version")
}

#Prepare Invoke-Pester parameters depending of the Pester's version.
#Invoke-Pester output deactivation behave differently depending on the Pester's version
If ($module.Result.pester_version -ge "4.0.0") {
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

if($tags.count){
    $Parameters.Tag = $tags
}

if($output_file){
    $Parameters.OutputFile   = $output_file
    $Parameters.OutputFormat = $output_format
}

# Run Pester tests
If (Test-Path -LiteralPath $path -PathType Leaf) {
    $test_parameters_check_mode_msg = ''
    if ($test_parameters.keys.count) {
        $Parameters.Script = @{Path = $Path ; Parameters = $test_parameters }
        $test_parameters_check_mode_msg = " with $($test_parameters.keys -join ',') parameters"
    }
    else {
        $Parameters.Script = $Path
    }

    if ($module.CheckMode) {
        $module.Result.output = "Run pester test in the file: $path$test_parameters_check_mode_msg"
    } else {
        $module.Result.output = Invoke-Pester @Parameters
    }
} else {
    $Parameters.Script = $path

    if ($module.CheckMode) {
        $module.Result.output = "Run Pester test(s): $path"
    } else {
        $module.Result.output = Invoke-Pester @Parameters
    }
}

$module.Result.changed = $true

$module.ExitJson()
