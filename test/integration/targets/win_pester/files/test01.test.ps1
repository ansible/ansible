Describe -Name 'Test01' {
    It -name 'First Test' {
        {Get-Service} | Should Not Throw
    }
}