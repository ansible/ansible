$ErrorActionPreference = 'Stop'

$port = {{test_win_wait_for_port}}

$endpoint = New-Object -TypeName System.Net.IPEndPoint([System.Net.IPAddress]::Parse("0.0.0.0"), $port)
$listener = New-Object -TypeName System.Net.Sockets.TcpListener($endpoint)
$listener.Server.ReceiveTimeout = 3000
$listener.Start()

try {
    while ($true) {
        if (-not $listener.Pending()) {
            Start-Sleep -Seconds 1
        } else {
            $client = $listener.AcceptTcpClient()
            $client.Close()
            break
        }
    }
} finally {
    $listener.Stop()
}
