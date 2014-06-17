#!powershell
# WANT_JSON

If ($args.Length -gt 0)
{
   $params = Get-Content $args[0] | ConvertFrom-Json;
}

$data = 'pong';
If (($params | Get-Member | Select-Object -ExpandProperty Name) -contains 'data')
{
   $data = $params.data;
}

$result = '{}' | ConvertFrom-Json;
$result | Add-Member -MemberType NoteProperty -Name ping -Value $data;
echo $result | ConvertTo-Json;
