$path = $args[0]
$attr = $args[1]
$item = Get-Item "$path"

$attributes = $item.Attributes -split ','
If ($attributes -notcontains $attr) {
    $attributes += $attr
}
$item.Attributes = $attributes -join ','
