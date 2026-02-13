# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.Collections.Generic
using namespace System.Globalization
using namespace System.IO
using namespace System.IO.Pipes
using namespace System.Management.Automation
using namespace System.Net.Sockets
using namespace System.Reflection
using namespace System.Security.Principal
using namespace System.Text
using namespace System.Threading
using namespace System.Threading.Tasks

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]
    $Name,

    [Parameter(Mandatory)]
    [PowerShell]
    $Pipeline,

    [Parameter(Mandatory)]
    [string]
    $AccessToken,

    [Parameter()]
    [string]
    $DebugHost = 'localhost',

    [Parameter()]
    [int]
    $DebugPort = 5678,

    [Parameter()]
    [IDictionary[]]
    $PathMapping = @()
)

Function Wait-TaskWithTimeout {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory)]
        [string]
        $Name,

        [Parameter(Mandatory, ValueFromPipeline)]
        [Task]
        $Task,

        [Parameter()]
        [int]
        $Timeout = 10
    )

    process {
        $start = Get-Date
        while (-not $Task.AsyncWaitHandle.WaitOne(300)) {
            if (((Get-Date) - $start).TotalSeconds -gt $Timeout) {
                throw "Timeout waiting for $Name"
            }
        }
        $Task.GetAwaiter().GetResult()
    }
}

# There is no public API to wait for Debug-Runspace to have been run so we use
# an internal API to check when the cmdlet has registered to a known event.
# A PR to add this as a public API is which we can hopefully use for newer
# versions of pwsh.
# https://github.com/PowerShell/PowerShell/pull/25788
$debugRunspaceCmd = Get-Command -Name Debug-Runspace -Module Microsoft.PowerShell.Utility
$runspaceBase = [PSObject].Assembly.GetType(
    'System.Management.Automation.Runspaces.RunspaceBase')
$availabilityChangedField = $runspaceBase.GetField(
    'AvailabilityChanged',
    [BindingFlags]'NonPublic, Instance')
if (-not $availabilityChangedField) {
    throw 'Cannot setup debug environment, failed to get AvailabilityChanged event field'
}

$debugPayload = @{
    runspace_id = $Pipeline.Runspace.Id
    name = $Name
    path_mapping = $PathMapping
}
$debugPayloadJson = $debugPayload | ConvertTo-Json -Depth 2 -Compress

# PowerShell doesn't expose a way to connect to a process through a socket so
# we add a shim that connects to the current proc's named pipe and read/write
# to the socket instead.
$proc = Get-Process -Id $pid
$procTime = if ($PSVersionTable.PSVersion -lt '6.0' -or $IsWindows) {
    $proc.StartTime.ToFileTime().ToString([CultureInfo]::InvariantCulture)
}
else {
    $proc.StartTime.ToFileTime().ToString("X8").Substring(1, 8)
}
$pipeName = 'PSHost.{0}.{1}.DefaultAppDomain.{2}' -f (
    $procTime,
    $pid,
    $proc.ProcessName
)

$stream = $pipe = $null
$client = [TcpClient]::new()
try {
    # Async tasks are used to not block the PowerShell engine and allow the
    # caller to stop the pipeline if needed.
    # We ensure we can connect to the current process' named pipe
    # before connecting to the debug socket.
    $pipe = [NamedPipeClientStream]::new(
        ".",
        $pipeName,
        [PipeDirection]::InOut,
        [PipeOptions]::Asynchronous,
        [TokenImpersonationLevel]::Identification,
        [HandleInheritability]::None)
    $null = $pipe.ConnectAsync() | Wait-TaskWithTimeout -Name 'connection to pwsh named pipe'

    # Once we have the named pipe connected we can connect to the socket and
    # share the debug information so the client side knows what to attach to.
    $null = $client.ConnectAsync($DebugHost, $DebugPort) |
        Wait-TaskWithTimeout -Name 'connection to debug socket'

    $stream = $client.GetStream()

    # Verify with the client that we have the correct access token and send
    # through the debug parameters.
    $writer = [StreamWriter]::new($stream, [Encoding]::UTF8, $client.SendBufferSize, $true)
    $writer.AutoFlush = $true
    $null = $writer.WriteLineAsync($AccessToken) |
        Wait-TaskWithTimeout -Name 'writing access token'
    $null = $writer.WriteLineAsync($debugPayloadJson) |
        Wait-TaskWithTimeout -Name 'writing debug information'
    $writer.Dispose()

    # Start the communication with the socket <-> pipe and wait for the client
    # to issue the Debug-Runspace command.
    $cancelTokenSource = [CancellationTokenSource]::new()
    $readTask = $stream.CopyToAsync($pipe, $client.ReceiveBufferSize, $cancelTokenSource.Token)
    $writeTask = $pipe.CopyToAsync($stream, $client.SendBufferSize, $cancelTokenSource.Token)

    $start = Get-Date
    while ($true) {
        $subscribed = $availabilityChangedField.GetValue($Pipeline.Runspace) |
            Where-Object Target -is $debugRunspaceCmd.ImplementingType
        if ($subscribed) {
            break
        }

        if (((Get-Date) - $start).TotalSeconds -gt 10) {
            throw 'Timeout waiting for Debug-Runspace to be called'
        }
    }

    # Create an object that can be disposed by PowerShell to clean up the resources
    # when the debug session has ended.
    $wrapper = [PSCustomObject]@{
        PSTypeName = 'Ansible.DebugWrapper'
        Pipe = $pipe
        Socket = $client
        SocketStream = $stream
        ReadTask = $readTask
        WriteTask = $writeTask
        CancelTokenSource = $cancelTokenSource
    }
    $wrapper.PSObject.Methods.Add(
        [PSScriptMethod]::new('WaitForExit', {
                # The only way to stop the active Debug-Runspace command launched
                # by the VSCode client is to stop the pipeline that it is running
                # on. Unfortunately there is no public API to get the running
                # pipeline on a runspace so we use reflection.
                # https://github.com/PowerShell/PowerShell/issues/25779
                $getCurrentlyRunningPipelineMeth = [Runspace].GetMethod(
                    'GetCurrentlyRunningPipeline',
                    [BindingFlags]'NonPublic, Instance')

                if (-not $getCurrentlyRunningPipelineMeth) {
                    # If for the API changed in the future we can't safely shutdown
                    # the debug session. The Dispose later on will close things
                    # down just in an ungraceful manner.
                    return
                }

                foreach ($runspace in Get-Runspace) {
                    $pipeline = $getCurrentlyRunningPipelineMeth.Invoke($runspace, @())
                    if (
                        $pipeline -and
                        $pipeline.Commands.Count -gt 0 -and
                        $pipeline.Commands[0].CommandText -eq 'Debug-Runspace'
                    ) {
                        $pipeline.Stop()
                        break
                    }
                }

                $taskList = [List[Task]]@($this.ReadTask, $this.WriteTask)
                while ($taskList.Count) {
                    $task = [Task]::WhenAny($taskList)
                    while (-not $task.AsyncWaitHandle.WaitOne(300)) {}
                    $finishedTask = $task.GetAwaiter().GetResult()

                    if ($finishedTask -eq $this.ReadTask) {
                        # The socket was closed by the debug client, close the pipe
                        # to ensure the write task can finish.
                        $this.Pipe.Close()
                    }
                    else {
                        # The pipe was closed for unknown reasons, close the socket
                        # so the debug client and read task can finish.
                        $this.Socket.Close()
                    }

                    $null = $taskList.Remove($finishedTask)
                    $null = $finishedTask.GetAwaiter().GetResult()
                }
            })
    )
    $wrapper.PSObject.Methods.Add(
        [PSScriptMethod]::new('Dispose', {
                $this.CancelTokenSource.Cancel()

                $this.Pipe.Dispose()
                $this.SocketStream.Dispose()
                $this.Socket.Dispose()
                $this.CancelTokenSource.Dispose()
            })
    )

    $wrapper
}
catch {
    if ($pipe) { $pipe.Dispose() }
    if ($stream) { $stream.Dispose() }
    $client.Dispose()

    throw
}
