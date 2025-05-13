# Test script to make sure the Ansible script module works when arguments are
# passed via splatting (http://technet.microsoft.com/en-us/magazine/gg675931.aspx)

Write-Host $args.This
Write-Host $args.That
Write-Host $args.Other
