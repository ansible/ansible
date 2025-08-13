#!powershell

#AnsibleRequires -Wrapper

@{
    test = 'inline_signed_not_trusted'
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    whoami = [Environment]::UserName
    ünicode = $complex_args.input
} | ConvertTo-Json
