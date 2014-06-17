#!powershell
# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$data = 'FIXME';

$result = New-Object psobject;
Set-Attr $result "fixme" $data;
echo $result | ConvertTo-Json;
