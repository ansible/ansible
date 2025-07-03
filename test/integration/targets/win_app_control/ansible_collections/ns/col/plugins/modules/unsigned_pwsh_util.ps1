#!powershell

#AnsibleRequires -PowerShell ..module_utils.PwshUnsigned

@{
    changed = $false
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    res = Test-PwshUnsigned
} | ConvertTo-Json
