#!powershell
# WANT_JSON

$params = New-Object psobject;
If ($args.Length -gt 0)
{
   $params = Get-Content $args[0] | ConvertFrom-Json;
}

$path = '';
If (($params | Get-Member | Select-Object -ExpandProperty Name) -contains 'path')
{
   $path = $params.path;
}

$get_md5 = $TRUE;
If (($params | Get-Member | Select-Object -ExpandProperty Name) -contains 'get_md5')
{
   $get_md5 = $params.get_md5;
}

$stat = New-Object psobject;
If (Test-Path $path)
{
   $stat | Add-Member -MemberType NoteProperty -Name exists -Value $TRUE;
   $info = Get-Item $path;
   If ($info.Directory) # Only files have the .Directory attribute.
   {
      $stat | Add-Member -MemberType NoteProperty -Name isdir -Value $FALSE;
      $stat | Add-Member -MemberType NoteProperty -Name size -Value $info.Length;
   }
   Else
   {
      $stat | Add-Member -MemberType NoteProperty -Name isdir -Value $TRUE;
   }
}
Else
{
   $stat | Add-Member -MemberType NoteProperty -Name exists -Value $FALSE;
}

If ($get_md5 -and $stat.exists -and -not $stat.isdir)
{
   $path_md5 = (Get-FileHash -Path $path -Algorithm MD5).Hash.ToLower();
   $stat | Add-Member -MemberType NoteProperty -Name md5 -Value $path_md5;
}

$result = New-Object psobject;
$result | Add-Member -MemberType NoteProperty -Name stat -Value $stat;
$result | Add-Member -MemberType NoteProperty -Name changed -Value $FALSE;
echo $result | ConvertTo-Json;
