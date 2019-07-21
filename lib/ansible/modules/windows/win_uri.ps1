#!powershell

# Copyright: (c) 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.CamelConversion
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.WebRequest

$spec = @{
    options = @{
       content_type = @{ type = "str" }
       body = @{ type = "raw" }
       dest = @{ type = "path" }
       creates = @{ type = "path" }
       removes = @{ type = "path" }
       return_content = @{ type = "bool"; default = $false }
       status_code = @{ type = "list"; elements = "int"; default = @(200) }
    }
    supports_check_mode = $true
}
$spec.options += $ansible_web_request_options
$spec.options.method.default = "GET"

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$url = $module.Params.url
$method = $module.Params.method.ToUpper()
$content_type = $module.Params.content_type
$body = $module.Params.body
$dest = $module.Params.dest
$creates = $module.Params.creates
$removes = $module.Params.removes
$return_content = $module.Params.return_content
$status_code = $module.Params.status_code

$JSON_CANDIDATES = @('text', 'json', 'javascript')

$module.Result.elapsed = 0
$module.Result.url = $url

if (-not ($method -cmatch '^[A-Z]+$')) {
    $module.FailJson("Parameter 'method' needs to be a single word in uppercase, like GET or POST.")
}

if ($creates -and (Test-AnsiblePath -Path $creates)) {
    $module.Result.skipped = $true
    $module.Result.msg = "The 'creates' file or directory ($creates) already exists."
    $module.ExitJson()
}

if ($removes -and -not (Test-AnsiblePath -Path $removes)) {
    $module.Result.skipped = $true
    $module.Result.msg = "The 'removes' file or directory ($removes) does not exist."
    $module.ExitJson()
}

$client = Get-AnsibleWebRequest -Module $module

if ($null -ne $content_type) {
    $client.ContentType = $content_type
}

$response_script = {
    param($Response, $Stream)

    ForEach ($prop in $Response.PSObject.Properties) {
        $result_key = Convert-StringToSnakeCase -string $prop.Name
        $prop_value = $prop.Value
        # convert and DateTime values to ISO 8601 standard
        if ($prop_value -is [System.DateTime]) {
            $prop_value = $prop_value.ToString("o", [System.Globalization.CultureInfo]::InvariantCulture)
        }
        $module.Result.$result_key = $prop_value
    }

    # manually get the headers as not all of them are in the response properties
    foreach ($header_key in $Response.Headers.GetEnumerator()) {
        $header_value = $Response.Headers[$header_key]
        $header_key = $header_key.Replace("-", "") # replace - with _ for snake conversion
        $header_key = Convert-StringToSnakeCase -string $header_key
        $module.Result.$header_key = $header_value
    }

    # we only care about the return body if we need to return the content or create a file
    if ($return_content -or $dest) {
        # copy to a MemoryStream so we can read it multiple times
        $memory_st = New-Object -TypeName System.IO.MemoryStream
        try {
            $Stream.CopyTo($memory_st)

            if ($return_content) {
                $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
                $content_bytes = $memory_st.ToArray()
                $module.Result.content = [System.Text.Encoding]::UTF8.GetString($content_bytes)
                if ($module.Result.ContainsKey("content_type") -and $module.Result.content_type -Match ($JSON_CANDIDATES -join '|')) {
                    try {
                        $module.Result.json = ([Ansible.Basic.AnsibleModule]::FromJson($module.Result.content))
                    } catch [System.ArgumentException] {
                        # Simply continue, since 'text' might be anything
                    }
                }
            }

            if ($dest) {
                $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
                $changed = $true

                if (Test-AnsiblePath -Path $dest) {
                    $actual_checksum = Get-FileChecksum -path $dest -algorithm "sha1"

                    $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider
                    $content_checksum = [System.BitConverter]::ToString($sp.ComputeHash($memory_st)).Replace("-", "").ToLower()

                    if ($actual_checksum -eq $content_checksum) {
                        $changed = $false
                    }
                }

                $module.Result.changed = $changed
                if ($changed -and (-not $module.CheckMode)) {
                    $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
                    $file_stream = [System.IO.File]::Create($dest)
                    try {
                        $memory_st.CopyTo($file_stream)
                    } finally {
                        $file_stream.Flush()
                        $file_stream.Close()
                    }
                }
            }
        } finally {
            $memory_st.Close()
        }
    }

    if ($status_code -notcontains $Response.StatusCode) {
        $module.FailJson("Status code of request '$([int]$Response.StatusCode)' is not in list of valid status codes $status_code : $($Response.StatusCode)'.")
    }
}

$body_st = $null
if ($null -ne $body) {
    if ($body -is [System.Collections.IDictionary] -or $body -is [System.Collections.IList]) {
        $body_string = ConvertTo-Json -InputObject $body -Compress
    } elseif ($body -isnot [String]) {
        $body_string = $body.ToString()
    } else {
        $body_string = $body
    }
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($body_string)

    $body_st = New-Object -TypeName System.IO.MemoryStream -ArgumentList @(,$buffer)
}

try {
    Invoke-WithWebRequest -Module $module -Request $client -Script $response_script -Body $body_st -IgnoreBadResponse
} catch {
    $module.FailJson("Unhandled exception occurred when sending web request. Exception: $($_.Exception.Message)", $_)
} finally {
    if ($null -ne $body_st) {
        $body_st.Dispose()
    }
}

$module.ExitJson()
