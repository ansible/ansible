#!powershell

$res = @{
  changed = $false
  source = "user"
  msg = "hi from selfcontained.ps1"
}

ConvertTo-Json $res