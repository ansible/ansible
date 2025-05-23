# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Become

using namespace System.Collections
using namespace System.Diagnostics
using namespace System.IO
using namespace System.Management.Automation
using namespace System.Management.Automation.Security
using namespace System.Net
using namespace System.Text

[CmdletBinding()]
param (
    [Parameter()]
    [AllowEmptyString()]
    [string]
    $BecomeUser,

    [Parameter()]
    [SecureString]
    $BecomePassword,

    [Parameter()]
    [string]
    $LogonType = 'Interactive',

    [Parameter()]
    [string]
    $LogonFlags = 'WithProfile'
)

Import-CSharpUtil -Name 'Ansible.AccessToken.cs', 'Ansible.Become.cs', 'Ansible.Process.cs'

# We need to set password to the value of NullString so a null password is
# preserved when crossing the .NET boundary. If we pass $null it will
# automatically be converted to "" and we need to keep the distinction for
# accounts that don't have a password and when someone wants to become without
# knowing the password.
$password = [NullString]::Value
if ($null -ne $BecomePassword) {
    $password = [NetworkCredential]::new("", $BecomePassword).Password
}

$executable = if ($PSVersionTable.PSVersion -lt '6.0') {
    'powershell.exe'
}
else {
    'pwsh.exe'
}
$executablePath = Join-Path -Path $PSHome -ChildPath $executable

$actionInfo = Get-AnsibleExecWrapper -EncodeInputOutput
$bootstrapManifest = ConvertTo-Json -InputObject @{
    n = "exec_wrapper-become-$([Guid]::NewGuid()).ps1"
    s = $actionInfo.ScriptInfo.Script
    p = $actionInfo.Parameters
} -Depth 99 -Compress

# NB: CreateProcessWithTokenW commandline maxes out at 1024 chars, must
# bootstrap via small wrapper to invoke the exec_wrapper. Strings are used to
# avoid sanity tests like aliases and spaces.
[string]$command = @'
$m=foreach($i in $input){
    if([string]::Equals($i,"`0`0`0`0")){break}
    $i
}
$m=$m|ConvertFrom-Json
$p=@{}
foreach($o in $m.p.PSObject.Properties){$p[$o.Name]=$o.Value}
'@

if ([SystemPolicy]::GetSystemLockdownPolicy() -eq 'Enforce') {
    # If we started in CLM we need to execute the script from a file so that
    # PowerShell validates our exec_wrapper is trusted and will run in FLM.
    $command += @'
$n=Join-Path $env:TEMP $m.n
$null=New-Item $n -Value $m.s -Type File -Force
try{$input|&$n @p}
finally{if(Test-Path -LiteralPath $n){Remove-Item -LiteralPath $n -Force}}
'@
}
else {
    # If we started in FLM we pass the script through stdin and execute in
    # memory.
    $command += @'
$c=[System.Management.Automation.Language.Parser]::ParseInput($m.s,$m.n,[ref]$null,[ref]$null).GetScriptBlock()
$input|&$c @p
'@
}

# Strip out any leading or trailing whitespace and remove empty lines.
$command = @(
    ($command -split "\r?\n") |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
) -join "`n"

$encCommand = [Convert]::ToBase64String([Encoding]::Unicode.GetBytes($command))
# Shortened version of '-NonInteractive -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encCommand'
$commandLine = "$executable -noni -nop -ex Bypass -e $encCommand"
$result = [Ansible.Become.BecomeUtil]::CreateProcessAsUser(
    $BecomeUser,
    $password,
    $LogonFlags,
    $LogonType,
    $executablePath,
    $commandLine,
    $env:SystemRoot,
    $null,
    "$bootstrapManifest`n`0`0`0`0`n$($actionInfo.InputData)")

$stdout = $result.StandardOut
try {
    $stdout = [Encoding]::UTF8.GetString([Convert]::FromBase64String($stdout))
}
catch [FormatException] {
    # output wasn't Base64, ignore as it may contain an error message we want to pass to Ansible
    $null = $_
}

$Host.UI.WriteLine($stdout)
Write-PowerShellClixmlStderr -Output $result.StandardError
$Host.SetShouldExit($result.ExitCode)
