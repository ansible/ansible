param (
    [int]$port = 8000,
)

$listener = New-Object Net.HttpListener
$listener.Prefixes.Add("http://+:$port/")
$listener.Start()

try {
    while ($listener.IsListening) {
        # process received request
        $context = $listener.GetContext()
        $Request = $context.Request
        $Response = $context.Response
        #$Response.Headers.Add("Content-Type","text/plain")

        $received = '{0} {1}' -f $Request.httpmethod, $Request.url.localpath

        # is there HTML content for this URL?
        $html = $htmlcontents[$received]
        if ($html -eq $null) {
            $Response.statuscode = 404
            $html = 'Oops, the page is not available!'
        }

        # return the HTML to the caller
        $buffer = [Text.Encoding]::UTF8.GetBytes($html)
        $Response.ContentLength64 = $buffer.length
        $Response.OutputStream.Write($buffer, 0, $buffer.length)

        $Response.Close()
    }
} finally {
    $listener.Stop()
    $listener.Close()
}
