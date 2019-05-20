Describe -Name 'Test01' {
    It -name 'First Test' {
        { Get-Date } | Should Not Throw
    }
}