#!powershell
# WANT_JSON

$params = New-Object psobject;
If ($args.Length -gt 0)
{
   $params = Get-Content $args[0] | ConvertFrom-Json;
}

$src = '';
If (($params | Get-Member | Select-Object -ExpandProperty Name) -contains 'src')
{
   $src = $params.src;
}
Else
{
   If (($params | Get-Member | Select-Object -ExpandProperty Name) -contains 'path')
   {
      $src = $params.path;
   }
}
If (-not $src)
{

}

$bytes = [System.IO.File]::ReadAllBytes($src);
$content = [System.Convert]::ToBase64String($bytes);

$result = New-Object psobject;
$result | Add-Member -MemberType NoteProperty -Name content -Value $content;
$result | Add-Member -MemberType NoteProperty -Name encoding -Value 'base64';
echo $result | ConvertTo-Json;
