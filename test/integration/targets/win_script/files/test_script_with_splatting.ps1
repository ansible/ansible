# Test script to make sure the Ansible script module works when arguments are
# passed via splatting (http://technet.microsoft.com/en-us/magazine/gg675931.aspx)

Write-Output $args.This
Write-Output $args.That
Write-Output $args.Other
