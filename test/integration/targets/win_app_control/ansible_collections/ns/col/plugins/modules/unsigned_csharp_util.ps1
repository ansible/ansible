#!powershell

#AnsibleRequires -CSharpUtil ..module_utils.CSharpUnsigned

@{
    changed = $false
    language_mode = $ExecutionContext.SessionState.LanguageMode.ToString()
    res = [ansible_collections.ns.col.plugins.module_utils.CSharpUnsigned.TestClass]::TestMethod("value")
} | ConvertTo-Json
