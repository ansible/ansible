#!powershell
# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$src = '';
If ($params.src.GetType)
{
   $src = $params.src;
}
Else
{
   If ($params.path.GetType)
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
Set-Attr $result "content" $content;
Set-Attr $result "encoding" "base64";
echo $result | ConvertTo-Json;
