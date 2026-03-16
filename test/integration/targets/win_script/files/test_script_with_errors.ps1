# Test script to make sure we handle non-zero exit codes.

trap {
    Write-Error -ErrorRecord $_
    exit 1
}

throw "Oh noes I has an error"
