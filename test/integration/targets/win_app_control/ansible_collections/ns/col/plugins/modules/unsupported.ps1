#!powershell

#AnsibleRequires -Wrapper

@{
    test = 'unsupported'
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    whoami = [Environment]::UserName
} | ConvertTo-Json
