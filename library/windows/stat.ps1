#!powershell
# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$path = '';
If ($params.path.GetType)
{
   $path = $params.path;
}

$get_md5 = $TRUE;
If ($params.get_md5.GetType)
{
   $get_md5 = $params.get_md5;
}

$stat = New-Object psobject;
If (Test-Path $path)
{
   Set-Attr $stat "exists" $TRUE;
   $info = Get-Item $path;
   If ($info.Directory) # Only files have the .Directory attribute.
   {
      Set-Attr $stat "isdir" $FALSE;
      Set-Attr $stat "size" $info.Length;
   }
   Else
   {
      Set-Attr $stat "isdir" $TRUE;
   }
}
Else
{
   Set-Attr $stat "exists" $FALSE;
}

If ($get_md5 -and $stat.exists -and -not $stat.isdir)
{
   $path_md5 = (Get-FileHash -Path $path -Algorithm MD5).Hash.ToLower();
   Set-Attr $stat "md5" $path_md5;
}

$result = New-Object psobject;
Set-Attr $result "stat" $stat;
Set-Attr $result "changed" $FALSE;
echo $result | ConvertTo-Json;
