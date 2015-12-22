$ansible_home = Join-Path -Resolve $PSScriptRoot '..'

$prefix_path = [io.path]::combine($ansible_home, 'bin')
$prefix_pythonpath = [io.path]::combine($ansible_home, 'lib')
$prefix_manpath = [io.path]::combine($ansible_home, 'docs', 'man')

if (-Not [string]::IsNullOrEmpty($env:PATH)) { $prefix_path = ";$prefix_path" }
if (-Not [string]::IsNullOrEmpty($env:PYTHONPATH)) { $prefix_pythonpath = ";$prefix_pythonpath" }
if (-Not [string]::IsNullOrEmpty($env:MANPATH)) { $prefix_manpath = ";$prefix_manpath" }

$env:PATH += $prefix_path
$env:PYTHONPATH += $prefix_pythonpath
$env:MANPATH += $prefix_manpath

"PATH = $env:PATH"
"PYTHONPATH = $env:PYTHONPATH"
"MANPATH = $env:MANPATH"
