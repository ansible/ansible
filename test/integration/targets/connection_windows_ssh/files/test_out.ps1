$c = [Char]::ConvertFromUtf32(0x1F3B5)

[Console]::Out.WriteLine("stdout $c")
[Console]::Error.WriteLine("stderr $c")
