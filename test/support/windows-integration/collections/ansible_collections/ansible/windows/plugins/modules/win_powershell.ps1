#!powershell

# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -PowerShell Ansible.ModuleUtils.AddType
#AnsibleRequires -CSharpUtil Ansible.Basic

#AnsibleRequires -PowerShell ..module_utils.Process

using namespace System.IO
using namespace System.Management.Automation.Language
using namespace System.Management.Automation.Security

$spec = @{
    options = @{
        arguments = @{ type = 'list'; elements = 'str' }
        chdir = @{ type = 'str' }
        creates = @{ type = 'str' }
        depth = @{ type = 'int'; default = 2 }
        error_action = @{ type = 'str'; choices = 'silently_continue', 'continue', 'stop'; default = 'continue' }
        executable = @{ type = 'str' }
        parameters = @{ type = 'dict' }
        path = @{ type = 'str' }
        sensitive_parameters = @{
            type = 'list'
            elements = 'dict'
            options = @{
                name = @{ type = 'str'; required = $true }
                username = @{ type = 'str' }
                password = @{ type = 'str'; no_log = $true }
                value = @{ type = 'str'; no_log = $true }
            }
            mutually_exclusive = @(
                , @('value', 'username')
                , @('value', 'password')
            )
            required_one_of = @(, @('username', 'value'))
            required_together = @(, @('username', 'password'))
        }
        remote_src = @{ type = 'bool'; default = $false }
        removes = @{ type = 'str' }
        script = @{ type = 'str' }
    }
    required_one_of = @(
        , @('path', 'script')
    )
    mutually_exclusive = @(
        , @('path', 'script')
    )
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$module.Result.result = @{}
$module.Result.host_out = ''
$module.Result.host_err = ''
$module.Result.output = @()
$module.Result.error = @()
$module.Result.warning = @()
$module.Result.verbose = @()
$module.Result.debug = @()
$module.Result.information = @()

$stdPinvoke = @'
using System;
using System.Runtime.InteropServices;

namespace Ansible.Windows.WinPowerShell
{
    public class NativeMethods
    {
        [DllImport("Kernel32.dll", SetLastError = true)]
        public static extern bool AllocConsole();

        [DllImport("Kernel32.dll", SetLastError = true)]
        public static extern IntPtr GetConsoleWindow();

        [DllImport("Kernel32.dll")]
        public static extern IntPtr GetStdHandle(
            int nStdHandle);

        [DllImport("Kernel32.dll", SetLastError = true)]
        public static extern bool FreeConsole();

        [DllImport("Kernel32.dll")]
        public static extern bool SetStdHandle(
            int nStdHandle,
            IntPtr hHandle);
    }
}
'@

Add-CSharpType -AnsibleModule $module -References $stdPinvoke, @'
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Management.Automation;
using System.Management.Automation.Host;
using System.Security;

namespace Ansible.Windows.WinPowerShell
{
    public class Host : PSHost
    {
        private readonly PSHost PSHost;
        private readonly HostUI HostUI;

        public Host(PSHost host, StreamWriter stdout, StreamWriter stderr)
        {
            PSHost = host;
            HostUI = new HostUI(stdout, stderr);
        }

        public override CultureInfo CurrentCulture { get { return PSHost.CurrentCulture; } }

        public override CultureInfo CurrentUICulture { get {  return PSHost.CurrentUICulture; } }

        public override Guid InstanceId { get {  return PSHost.InstanceId; } }

        public override string Name { get { return PSHost.Name; } }

        public override PSHostUserInterface UI { get {  return HostUI; } }

        public override Version Version { get {  return PSHost.Version; } }

        public override void EnterNestedPrompt()
        {
            PSHost.EnterNestedPrompt();
        }

        public override void ExitNestedPrompt()
        {
            PSHost.ExitNestedPrompt();
        }

        public override void NotifyBeginApplication()
        {
            PSHost.NotifyBeginApplication();
        }

        public override void NotifyEndApplication()
        {
            PSHost.NotifyEndApplication();
        }

        public override void SetShouldExit(int exitCode)
        {
            PSHost.SetShouldExit(exitCode);
        }
    }

    public class HostUI : PSHostUserInterface
    {
        private StreamWriter _stdout;
        private StreamWriter _stderr;

        public HostUI(StreamWriter stdout, StreamWriter stderr)
        {
            _stdout = stdout;
            _stderr = stderr;
        }

        public override PSHostRawUserInterface RawUI { get { return null; } }

        public override Dictionary<string, PSObject> Prompt(string caption, string message, Collection<FieldDescription> descriptions)
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override int PromptForChoice(string caption, string message, Collection<ChoiceDescription> choices, int defaultChoice)
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override PSCredential PromptForCredential(string caption, string message, string userName, string targetName,
            PSCredentialTypes allowedCredentialTypes, PSCredentialUIOptions options)
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override PSCredential PromptForCredential(string caption, string message, string userName, string targetName)
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override string ReadLine()
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override SecureString ReadLineAsSecureString()
        {
            throw new MethodInvocationException("PowerShell is in NonInteractive mode. Read and Prompt functionality is not available.");
        }

        public override void Write(ConsoleColor foregroundColor, ConsoleColor backgroundColor, string value)
        {
            _stdout.Write(value);
        }

        public override void Write(string value)
        {
            _stdout.Write(value);
        }

        public override void WriteDebugLine(string message)
        {
            _stdout.WriteLine(String.Format("DEBUG: {0}", message));
        }

        public override void WriteErrorLine(string value)
        {
            _stderr.WriteLine(value);
        }

        public override void WriteLine(string value)
        {
            _stdout.WriteLine(value);
        }

        public override void WriteProgress(long sourceId, ProgressRecord record) {}

        public override void WriteVerboseLine(string message)
        {
            _stdout.WriteLine(String.Format("VERBOSE: {0}", message));
        }

        public override void WriteWarningLine(string message)
        {
            _stdout.WriteLine(String.Format("WARNING: {0}", message));
        }
    }
}
'@

Function Get-StdHandle {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet('Stdout', 'Stderr')]
        [string]
        $Stream
    )

    $id, $dotnet = switch ($Stream) {
        Stdout { -11, [Console]::Out }
        Stderr { -12, [Console]::Error }
    }
    $handle = [Ansible.Windows.WinPowerShell.NativeMethods]::GetStdHandle($id)

    [PSCustomObject]@{
        Stream = $Stream
        NET = $dotnet
        Raw = $handle
    }
}

Function Set-StdHandle {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [ValidateSet('Stdout', 'Stderr')]
        [string]
        $Stream,

        [IO.TextWriter]
        $NET,

        [IntPtr]
        $Raw
    )

    $id, $meth = switch ($Stream) {
        Stdout { -11; [Console]::SetOut($NET) }
        Stderr { -12; [Console]::SetError($NET) }
    }

    # .NET does not actually affect the std handle on the process, we need to call SetStdHandle so any child processes
    # spawned with Start-Process -NoNewWindow will use our custom pipe.
    [void][Ansible.Windows.WinPowerShell.NativeMethods]::SetStdHandle($id, $Raw)
}

Function Convert-OutputObject {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [AllowNull()]
        [object]
        $InputObject,

        [Parameter(Mandatory = $true)]
        [int]
        $Depth
    )

    begin {
        $childDepth = $Depth - 1

        $isType = {
            [CmdletBinding()]
            param (
                [Object]
                $InputObject,

                [Type]
                $Type
            )

            if ($InputObject -is $Type) {
                return $true
            }

            $psTypes = @($InputObject.PSTypeNames | ForEach-Object -Process {
                    $_ -replace '^Deserialized.'
                })

            $Type.FullName -in $psTypes
        }
    }

    process {
        if ($null -eq $InputObject) {
            $null
        }
        elseif ((&$isType -InputObject $InputObject -Type ([Enum])) -and $Depth -ge 0) {
            # ToString() gives the human readable value but I thought it better to give some more context behind
            # these types.
            @{
                Type = ($InputObject.PSTypeNames[0] -replace '^Deserialized.')
                String = $InputObject.ToString()
                Value = [int]$InputObject
            }
        }
        elseif ($InputObject -is [DateTime]) {
            # The offset is based on the Kind value
            # Unspecified leaves it off
            # UTC set it to Z
            # Local sets it to the local timezone
            $InputObject.ToString('o')
        }
        elseif (&$isType -InputObject $InputObject -Type ([DateTimeOffset])) {
            # If this is a deserialized object (from an executable) we need recreate a live DateTimeOffset
            if ($InputObject -isnot [DateTimeOffset]) {
                $InputObject = New-Object -TypeName DateTimeOffset $InputObject.DateTime, $InputObject.Offset
            }
            $InputObject.ToString('o')
        }
        elseif (&$isType -InputObject $InputObject -Type ([Type])) {
            if ($Depth -lt 0) {
                $InputObject.FullName
            }
            else {
                # This type is very complex with circular properties, only return somewhat useful properties.
                # BaseType might be a string (serialized output), try and convert it back to a Type if possible.
                $baseType = $InputObject.BaseType -as [Type]
                if ($baseType) {
                    $baseType = Convert-OutputObject -InputObject $baseType -Depth $childDepth
                }

                @{
                    Name = $InputObject.Name
                    FullName = $InputObject.FullName
                    AssemblyQualifiedName = $InputObject.AssemblyQualifiedName
                    BaseType = $baseType
                }
            }
        }
        elseif ($InputObject -is [string]) {
            # Get the BaseObject to strip out any ETS properties
            $InputObject.PSObject.BaseObject
        }
        elseif (&$isType -InputObject $InputObject -Type ([switch])) {
            $InputObject.IsPresent
        }
        # Have a defensive check to see if GetType() exists as a method on the object.
        # https://github.com/ansible-collections/ansible.windows/issues/708
        # We use ForEach-Object to defensively get the Methods as it fails on a WMI
        # based object
        # https://github.com/ansible-collections/ansible.windows/issues/767
        elseif ('GetType' -in ($InputObject.PSObject | ForEach-Object Methods | ForEach-Object Name) -and $InputObject.GetType().IsValueType) {
            # We want to display just this value and not any properties it has (if any).
            $InputObject.PSObject.BaseObject
        }
        elseif ($Depth -lt 0) {
            # This must occur after the above to ensure ints and other ValueTypes are preserved as is.
            [string]$InputObject
        }
        elseif ($InputObject -is [Collections.IList]) {
            , @(foreach ($obj in $InputObject) {
                    Convert-OutputObject -InputObject $obj -Depth $childDepth
                })
        }
        elseif ($InputObject -is [Collections.IDictionary]) {
            $newObj = @{}

            # Replicate ConvertTo-Json, props are replaced by keys if they share the same name. We only want ETS
            # properties as well.
            foreach ($prop in $InputObject.PSObject.Properties) {
                if ($prop.MemberType -notin @('AliasProperty', 'ScriptProperty', 'NoteProperty')) {
                    continue
                }
                $newObj[$prop.Name] = Convert-OutputObject -InputObject $prop.Value -Depth $childDepth
            }
            foreach ($kvp in $InputObject.GetEnumerator()) {
                $newObj[$kvp.Key] = Convert-OutputObject -InputObject $kvp.Value -Depth $childDepth
            }
            $newObj
        }
        else {
            $newObj = @{}
            foreach ($prop in $InputObject.PSObject.Properties) {
                $newObj[$prop.Name] = Convert-OutputObject -InputObject $prop.Value -Depth $childDepth
            }
            $newObj
        }
    }
}

Function Format-Exception {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [AllowNull()]
        $Exception
    )

    if (-not $Exception) {
        return $null
    }
    elseif ($Exception -is [Management.Automation.RemoteException]) {
        # When using a separate process the exceptions are a RemoteException, we want to get the info on the actual
        # exception.
        return Format-Exception -Exception $Exception.SerializedRemoteException
    }

    $type = if ($Exception -is [Exception]) {
        $Exception.GetType().FullName
    }
    else {
        # This is a RemoteException, we want to report the original non-serialized type.
        $Exception.PSTypeNames[0] -replace '^Deserialized.'
    }

    @{
        message = $Exception.Message
        type = $type
        help_link = $Exception.HelpLink
        source = $Exception.Source
        hresult = $Exception.HResult
        inner_exception = Format-Exception -Exception $Exception.InnerException
    }
}

Function Test-AnsiblePath {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSCustomUseLiteralPath', '',
        Justification = 'We want to support wildcard matching')]
    param (
        [Parameter(Mandatory = $true)]
        [String]
        $Path
    )

    # Certain system files fail on Test-Path due to it being locked, we can still get the attributes though.
    try {
        [void][System.IO.File]::GetAttributes($Path)
        return $true
    }
    catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        return $false
    }
    catch {
        # When testing a path like Cert:\LocalMachine\My, System.IO.File will
        # not work, we just revert back to using Test-Path for this
        return Test-Path -Path $Path
    }
}

Function New-AnonymousPipe {
    [CmdletBinding()]
    param ()

    $utf8NoBom = New-Object -TypeName Text.UTF8Encoding -ArgumentList $false

    $server = New-Object -TypeName IO.Pipes.AnonymousPipeServerStream -ArgumentList 'In', 'Inheritable'
    $client = New-Object -TypeName IO.Pipes.AnonymousPipeClientStream -ArgumentList 'Out', $server.ClientSafePipeHandle
    $clientWriter = New-Object -TypeName IO.StreamWriter -ArgumentList $client, $utf8NoBom
    $clientWriter.AutoFlush = $true  # Ensures the data stays in sync when dealing with subprocesses.

    # Create the background task that will constantly read from the pipe and append to our StringBuilder until the pipe
    # is closed. It also closes the pipe once finished so we don't have to. Without this the pipe buffer can become
    # full and hang the script.
    $sb = New-Object -TypeName Text.StringBuilder
    $ps = [PowerShell]::Create()

    [void]$ps.AddScript(@'
[CmdletBinding()]
param (
    [Text.StringBuilder]
    $StringBuilder,

    [IO.Pipes.AnonymousPipeServerStream]
    $Server,

    [Text.Encoding]
    $Encoding
)

$sr = New-Object -TypeName IO.StreamReader -ArgumentList $Server, $Encoding
try {
    $buffer = New-Object -TypeName char[] -ArgumentList $Server.InBufferSize
    while ($read = $sr.Read($buffer, 0, $buffer.Length)) {
        [void]$StringBuilder.Append($buffer, 0, $read)
    }
}
finally {
    $sr.Dispose()
}
'@).AddParameters(@{
            StringBuilder = $sb
            Server = $server
            Encoding = $utf8NoBom
        })
    $task = $ps.BeginInvoke()

    [PSCustomObject]@{
        PowerShell = $ps
        Task = $task
        Output = $sb
        Client = $clientWriter
        ClientString = $server.GetClientHandleAsString()
    }
}

$creates = $module.Params.creates
if ($creates -and (Test-AnsiblePath -Path $creates)) {
    $module.Result.msg = "skipped, since $creates exists"
    $module.ExitJson()
}

$removes = $module.Params.removes
if ($removes -and -not (Test-AnsiblePath -Path $removes)) {
    $module.Result.msg = "skipped, since $removes does not exist"
    $module.ExitJson()
}

$errors = @()
$scriptAst = if ($module.Params.script) {
    [Parser]::ParseInput($module.Params.script, [ref]$null, [ref]$errors)
}
else {
    if (-not (Test-Path -LiteralPath $module.Params.path)) {
        $module.FailJson("Could not find or access '$($module.Params.path)' on Windows host")
    }

    [Parser]::ParseFile($module.Params.path, [ref]$null, [ref]$errors)
}
if ($errors) {
    # Trying to parse pwsh 7 code may fail if using new syntax not available in
    # WinPS. Need to fallback to a more rudimentary scanner.
    # https://github.com/ansible-collections/ansible.windows/issues/452
    $scriptAst = $null
}

$supportsShouldProcess = $false
if ($scriptAst -and $scriptAst -is [Management.Automation.Language.ScriptBlockAst] -and $scriptAst.ParamBlock.Attributes) {
    $supportsShouldProcess = [bool]($scriptAst.ParamBlock.Attributes |
            Where-Object { $_.TypeName.Name -eq 'CmdletBinding' } |
            Select-Object -First 1 |
            ForEach-Object -Process {
                $_.NamedArguments | Where-Object {
                    $_.ArgumentName -eq 'SupportsShouldProcess' -and ($_.ExpressionOmitted -or $_.Argument.ToString() -eq '$true')
                }
            })
}
elseif (-not $scriptAst) {
    $scriptContent = if ($module.Params.script) {
        $module.Params.script
    }
    else {
        Get-Content -LiteralPath $module.Params.path -Raw
    }
    $supportsShouldProcess = $scriptContent -match '\[CmdletBinding\((?:[\w=\$]+,\s*)?SupportsShouldProcess(?:=\$true)?(?:,\s*[\w=\$]+)?\)\]'
}

if ($module.CheckMode -and -not $supportsShouldProcess) {
    $module.Result.changed = $true
    $module.Result.msg = "skipped, running in check mode"
    $module.ExitJson()
}

$isWDACEnabled = [SystemPolicy]::GetSystemLockdownPolicy() -ne 'None'

$runspace = $null
$processId = $null
$newStdout = New-AnonymousPipe
$newStderr = New-AnonymousPipe
$freeConsole = $false
$tempScript = $null

try {
    $oldStdout = Get-StdHandle -Stream Stdout
    $oldStderr = Get-StdHandle -Stream Stderr

    if ($module.Params.executable) {
        if ($PSVersionTable.PSVersion -lt [version]'5.0') {
            $module.FailJson("executable requires PowerShell 5.0 or newer")
        }

        # Neither Start-Process or Diagnostics.Process give us the ability to create a process with a new console and
        # the ability to inherit handles so we use own home grown CreateProcess wrapper.
        $applicationName = Resolve-ExecutablePath -FilePath $module.Params.executable
        $commandLine = ConvertTo-EscapedArgument -InputObject $module.Params.executable
        if ($module.Params.arguments) {
            $escapedArguments = @($module.Params.arguments | ConvertTo-EscapedArgument)
            $commandLine += " $($escapedArguments -join ' ')"
        }

        # While we could attach the stdout/stderr pipes here we would capture the startup info and prompt that
        # powershell will output. Instead we set the console as part of the pipeline we run.
        $si = [Ansible.Windows.Process.StartupInfo]@{
            WindowStyle = 'Hidden'  # Useful when debugging locally, doesn't really matter in normal Ansible.
        }
        $pi = [Ansible.Windows.Process.ProcessUtil]::NativeCreateProcess(
            $applicationName,
            $commandLIne,
            $null,
            $null,
            $true, # Required so the child process can inherit our anon pipes.
            'CreateNewConsole', # Ensures we don't mess with the current console output.
            $null,
            $null,
            $si
        )
        $processId = $pi.ProcessId
        $pi.Dispose()
    }

    # Using a custom host allows us to capture any host UI calls through our own output.
    $runspaceHost = New-Object -TypeName Ansible.Windows.WinPowerShell.Host -ArgumentList $Host, $newStdout.Client, $newStderr.Client
    if ($processId) {
        $connInfo = [System.Management.Automation.Runspaces.NamedPipeConnectionInfo]$processId

        # In case a user specified an executable that does not support the PSHost named pipe that PowerShell uses we
        # specify a timeout so the module does not hang.
        $connInfo.OpenTimeout = 60000
        $runspace = [RunspaceFactory]::CreateRunspace($runspaceHost, $connInfo)
    }
    else {
        $runspace = [RunspaceFactory]::CreateRunspace($runspaceHost)
    }

    $runspace.Open()

    $ps = [PowerShell]::Create()
    $ps.Runspace = $runspace

    $ps.Runspace.SessionStateProxy.SetVariable('Ansible', [PSCustomObject]@{
            PSTypeName = 'Ansible.Windows.WinPowerShell.Module'
            CheckMode = $module.CheckMode
            Verbosity = $module.Verbosity
            Result = @{}
            Diff = @{}
            Changed = $true
            Failed = $false
            Tmpdir = $module.Tmpdir
        })

    $eap = switch ($module.Params.error_action) {
        'stop' { 'Stop' }
        'continue' { 'Continue' }
        'silently_continue' { 'SilentlyContinue' }
    }
    $ps.Runspace.SessionStateProxy.SetVariable('ErrorActionPreference', [Management.Automation.ActionPreference]$eap)

    if ($processId) {
        # If we are running in a new process we need to set the various console encoding values to UTF-8 to ensure a
        # consistent encoding experience when PowerShell is running native commands and getting the output back. We
        # also need to redirect the stdout/stderr pipes to our anonymous pipe so we can capture any native console
        # output from .NET or calling a native application with 'Start-Process -NoNewWindow'.

        if (-not $isWDACEnabled) {
            [void]$ps.AddScript(@'
[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [String]
    $StdoutHandle,

    [Parameter(Mandatory=$true)]
    [String]
    $StderrHandle,

    [Parameter(Mandatory=$true)]
    [String]
    $SetStdPInvoke,

    [Parameter(Mandatory=$true)]
    [String]
    $SetScriptBlock,

    [Parameter(Mandatory=$true)]
    [String]
    $AddTypeCode,

    [Parameter(Mandatory=$true)]
    [String]
    $Tmpdir
)

# Using Add-Type here leaves an empty folder for some reason, our code does not and also allows us to control the
# temp directory used.
&([ScriptBlock]::Create($AddTypeCode)) -References $SetStdPInvoke -TempPath $Tmpdir

$setHandle = [ScriptBlock]::Create($SetScriptBlock)
$utf8NoBom = New-Object -TypeName Text.UTF8Encoding -ArgumentList $false

# Make sure our console encoding values are all set to UTF-8 for a consistent experience.
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = $utf8NoBom

# Set the stdout/stderr for both .NET and natively to our anonymous pipe.
@{Name = 'Stdout'; Handle = $StdoutHandle}, @{Name = 'Stderr'; Handle = $StderrHandle} | ForEach-Object -Process {
    $pipe = New-Object -TypeName IO.Pipes.AnonymousPipeClientStream -ArgumentList 'Out', $_.Handle
    $writer = New-Object -TypeName IO.StreamWriter -ArgumentList $pipe, $utf8NoBom
    $writer.AutoFlush = $true  # Ensures we data in the correct order.

    &$setHandle -Stream $_.Name -NET $writer -Raw $pipe.SafePipeHandle.DangerousGetHandle()
}
'@, $true).AddParameters(@{
                    StdoutHandle = $newStdout.ClientString
                    StderrHandle = $newStderr.ClientString
                    SetStdPInvoke = $stdPinvoke
                    SetScriptBlock = ${function:Set-StdHandle}
                    AddTypeCode = ${function:Add-CSharpType}
                    TmpDir = $module.Tmpdir
                }).AddStatement()
        }
    }
    else {
        # The psrp connection plugin doesn't have a console so we need to create one ourselves.
        if ([Ansible.Windows.WinPowerShell.NativeMethods]::GetConsoleWindow() -eq [IntPtr]::Zero) {
            $freeConsole = [Ansible.Windows.WinPowerShell.NativeMethods]::AllocConsole()
        }

        # Else we are running in the same process, we need to redirect the console and .NET output pipes to our
        # anonymous pipe. We shouldn't have to set the encoding, the module wrapper already does this.
        Set-StdHandle -Stream Stdout -NET $newStdout.Client -Raw $newStdout.Client.BaseStream.SafePipeHandle.DangerousGetHandle()
        Set-StdHandle -Stream Stderr -NET $newStderr.Client -Raw $newStderr.Client.BaseStream.SafePipeHandle.DangerousGetHandle()

        $utf8NoBom = New-Object -TypeName Text.UTF8Encoding -ArgumentList $false
        $OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = $utf8NoBom
    }

    if ($module.Params.chdir) {
        [void]$ps.AddCommand('Set-Location').AddParameter('LiteralPath', $module.Params.chdir).AddStatement()
    }

    if ($isWDACEnabled) {
        # Using an external process will already be in CLM so this is a safety
        # check to ensure it doesn't fail when in CLM already.
        $null = $ps.AddScript({
                if ($ExecutionContext.SessionState.LanguageMode -ne 'ConstrainedLanguage') {
                    $ExecutionContext.SessionState.LanguageMode = 'ConstrainedLanguage'
                }
            }).AddStatement()

        # If WDAC is applied we need to run the script from a temporary location
        # so that PowerShell can perform its normal trust operations. We need
        # to start from CLM or else we won't be able to run untrusted scripts
        # in CLM.
        if ($module.Params.script) {
            $tempScript = Join-Path $module.TmpDir "ansible.windows.win_powershell-$([Guid]::NewGuid()).ps1"
            [File]::WriteAllText($tempScript, $module.Params.script)
            $null = $ps.AddCommand($tempScript)
        }
        else {
            $null = $ps.AddCommand($module.Params.path)
        }
    }
    elseif ($module.Params.script) {
        $null = $ps.AddScript($module.Params.script)
    }
    else {
        # To ensure encoding is consistent with pwsh.exe and when running with WDAC,
        # we force WinPS to use UTF-8 in case the file does not have a BOM.
        # We do it in the pipeline as this could be running on a target executable.
        $null = $ps.AddScript(@'
if ($PSVersionTable.PSVersion -lt '6.0') {
    $clrFacade = [PSObject].Assembly.GetType('System.Management.Automation.ClrFacade')
    $defaultEncodingField = $clrFacade.GetField(
        '_defaultEncoding',
        [System.Reflection.BindingFlags]'NonPublic, Static')
    $defaultEncodingField.SetValue($null, [System.Text.UTF8Encoding]::new($false))
}
'@).AddStatement()

        $null = $ps.AddCommand($module.Params.path)
    }

    # We copy the existing parameter dictionary and add/modify the Confirm/WhatIf parameters if the script supports
    # processing. We do a copy to avoid modifying the original Params dictionary just for safety.
    $parameters = @{}
    if ($module.Params.parameters) {
        foreach ($kvp in $module.Params.parameters.GetEnumerator()) {
            $parameters[$kvp.Key] = $kvp.Value
        }
    }
    if ($module.Params.sensitive_parameters) {
        foreach ($paramDetails in $module.Params.sensitive_parameters) {
            $value = if ($paramDetails.username) {
                $credPass = if ($paramDetails.password) {
                    $paramDetails.password | ConvertTo-SecureString -AsPlainText -Force
                }
                else {
                    New-Object -TypeName System.Security.SecureString
                }
                New-Object System.Management.Automation.PSCredential ($paramDetails.username, $credPass)
            }
            elseif ($paramDetails.value) {
                $paramDetails.value | ConvertTo-SecureString -AsPlainText -Force
            }
            else {
                New-Object -TypeName System.Security.SecureString
            }

            $parameters[$paramDetails.name] = $value
        }
    }
    if ($supportsShouldProcess) {
        # We do this last to ensure we take precedence over any user inputted settings.
        $parameters.Confirm = $false  # Ensure we don't block on any confirmation prompts
        $parameters.WhatIf = $module.CheckMode
    }

    if ($parameters) {
        [void]$ps.AddParameters($parameters)
    }

    $psOutput = [Collections.Generic.List[Object]]@()
    try {
        $ps.Invoke(@(), $psOutput)
    }
    catch [Management.Automation.RuntimeException] {
        # $ErrorActionPrefrence = 'Stop' and an error was raised
        # OR
        # General exception was raised in the script like 'throw "error"'.
        # We treat these as failures in the script and return them back to the user.
        $module.Result.failed = $true
        $ps.Streams.Error.Add($_.Exception.ErrorRecord)
    }

    # Get the internal Ansible variable that can contain code specific information.
    # We use a new pipeline as $runspace.SessionStateProxy.GetVariable() will
    # truncate the values if they exceed the default serialization depth.
    # https://github.com/ansible-collections/ansible.windows/issues/642
    $resultPipeline = [PowerShell]::Create()
    $resultPipeline.Runspace = $runspace
    $result = $resultPipeline.AddScript('$Ansible').Invoke()[0]
}
finally {
    if (-not $processId) {
        $oldStdout, $oldStderr | ForEach-Object -Process {
            Set-StdHandle -Stream $_.Stream -NET $_.NET -Raw $_.Raw
        }
    }

    if ($runspace) {
        $runspace.Dispose()
    }
    if ($processId) {
        Stop-Process -Id $processId -Force
    }

    $newStdout, $newStderr | ForEach-Object -Process {
        $_.Client.Dispose()
        [void]$_.PowerShell.EndInvoke($_.Task)
    }

    if ($freeConsole) {
        [void][Ansible.Windows.WinPowerShell.NativeMethods]::FreeConsole()
    }

    if ($tempScript -and (Test-Path -LiteralPath $tempScript)) {
        Remove-Item -LiteralPath $tempScript -Force
    }
}

$module.Result.host_out = $newStdout.Output.ToString()
$module.Result.host_err = $newStderr.Output.ToString()
$module.Result.result = Convert-OutputObject -InputObject $result.Result -Depth $module.Params.depth
$module.Result.changed = $result.Changed
$module.Result.failed = $module.Result.failed -or $result.Failed

# If the diff was somehow changed to something else we cannot set it to the
# module output diff so check if it's still a dict.
if ($result.Diff -is [System.Collections.IDictionary]) {
    foreach ($kvp in $result.Diff.GetEnumerator()) {
        $module.Diff[$kvp.Key] = Convert-OutputObject -InputObject $kvp.Value -Depth $module.Params.depth
    }
}

# We process the output outselves to flatten anything beyond the depth and deal with certain problematic types with
# json serialization.
$module.Result.output = Convert-OutputObject -InputObject $psOutput -Depth $module.Params.depth

$module.Result.error = @($ps.Streams.Error | ForEach-Object -Process {
        $err = @{
            output = ($_ | Out-String)
            error_details = $null
            exception = Format-Exception -Exception $_.Exception
            target_object = Convert-OutputObject -InputObject $_.TargetObject -Depth $module.Params.depth
            category_info = @{
                category = [string]$_.CategoryInfo.Category
                category_id = [int]$_.CategoryInfo.Category
                activity = $_.CategoryInfo.Activity
                reason = $_.CategoryInfo.Reason
                target_name = $_.CategoryInfo.TargetName
                target_type = $_.CategoryInfo.TargetType
            }
            fully_qualified_error_id = $_.FullyQualifiedErrorId
            script_stack_trace = $_.ScriptStackTrace
            pipeline_iteration_info = $_.PipelineIterationInfo
        }
        if ($_.ErrorDetails) {
            $err.error_details = @{
                message = $_.ErrorDetails.Message
                recommended_action = $_.ErrorDetails.RecommendedAction
            }
        }

        $err
    })

'debug', 'verbose', 'warning' | ForEach-Object -Process {
    $module.Result.$_ = @($ps.Streams.$_ | Select-Object -ExpandProperty Message)
}

# Use Select-Object as Information may not be present on earlier pwsh version (<v5).
$module.Result.information = @($ps.Streams |
        Select-Object -ExpandProperty Information -ErrorAction SilentlyContinue |
        ForEach-Object -Process {
            @{
                message_data = Convert-OutputObject -InputObject $_.MessageData -Depth $module.Params.depth
                source = $_.Source
                time_generated = $_.TimeGenerated.ToUniversalTime().ToString('o')
                tags = @($_.Tags)
            }
        }
)

$module.ExitJson()
