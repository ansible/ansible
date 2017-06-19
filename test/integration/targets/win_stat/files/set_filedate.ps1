$date = Get-Date -Year 2016 -Month 11 -Day 1 -Hour 7 -Minute 10 -Second 5 -Millisecond 0

$item = Get-Item -Path "$($args[0])"
$item.CreationTime = $date
$item.LastAccessTime = $date
$item.LastWriteTime = $date
