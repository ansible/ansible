# http://stackoverflow.com/questions/9948517/how-to-stop-a-powershell-script-on-the-first-error
#$ErrorActionPreference = "Stop";
# http://stackoverflow.com/questions/15777492/why-are-my-powershell-exit-codes-always-0

trap
{
    Write-Error -ErrorRecord $_
    exit 1;
}

throw "Oh noes I has an error"
