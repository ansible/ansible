#!powershell
# WANT_JSON

If ($args.Length -gt 0)
{
   $params = Get-Content $args[0] | ConvertFrom-Json;
}

$data = 'pong';
If ($params.data.GetType)
{
   $data = $params.data;
}

$result = New-Object psobject;
$result | Add-Member -MemberType NoteProperty -Name ping -Value $data;
echo $result | ConvertTo-Json;
