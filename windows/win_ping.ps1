#!powershell
# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$data = 'pong';
If ($params.data.GetType)
{
   $data = $params.data;
}

$result = New-Object psobject;
Set-Attr $result "ping" $data;
echo $result | ConvertTo-Json;
