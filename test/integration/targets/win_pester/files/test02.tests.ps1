Describe -Name 'Test02' {
    It -name 'Second Test' {
        { Get-Date } | Should Throw
    }
}