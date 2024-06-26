#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.AddType

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
}

Function Assert-Equal($actual, $expected) {
    if ($actual -cne $expected) {
        $call_stack = (Get-PSCallStack)[1]
        $error_msg = -join @(
            "AssertionError:`r`nActual: `"$actual`" != Expected: `"$expected`"`r`nLine: "
            "$($call_stack.ScriptLineNumber), Method: $($call_stack.Position.Text)"
        )
        Fail-Json -obj $result -message $error_msg
    }
}

$code = @'
using System;

namespace Namespace1
{
    public class Class1
    {
        public static string GetString(bool error)
        {
            if (error)
                throw new Exception("error");
            return "Hello World";
        }
    }
}
'@
$res = Add-CSharpType -References $code
Assert-Equal -actual $res -expected $null

$actual = [Namespace1.Class1]::GetString($false)
Assert-Equal $actual -expected "Hello World"

try {
    [Namespace1.Class1]::GetString($true)
}
catch {
    Assert-Equal ($_.Exception.ToString().Contains("at Namespace1.Class1.GetString(Boolean error)`r`n")) -expected $true
}

$code_debug = @'
using System;

namespace Namespace2
{
    public class Class2
    {
        public static string GetString(bool error)
        {
            if (error)
                throw new Exception("error");
            return "Hello World";
        }
    }
}
'@
$res = Add-CSharpType -References $code_debug -IncludeDebugInfo
Assert-Equal -actual $res -expected $null

$actual = [Namespace2.Class2]::GetString($false)
Assert-Equal $actual -expected "Hello World"

try {
    [Namespace2.Class2]::GetString($true)
}
catch {
    $tmp_path = [System.IO.Path]::GetFullPath($env:TMP).ToLower()
    Assert-Equal ($_.Exception.ToString().ToLower().Contains("at namespace2.class2.getstring(boolean error) in $tmp_path")) -expected $true
    Assert-Equal ($_.Exception.ToString().Contains(".cs:line 10")) -expected $true
}

$code_tmp = @'
using System;

namespace Namespace3
{
    public class Class3
    {
        public static string GetString(bool error)
        {
            if (error)
                throw new Exception("error");
            return "Hello World";
        }
    }
}
'@
$tmp_path = $env:USERPROFILE
$res = Add-CSharpType -References $code_tmp -IncludeDebugInfo -TempPath $tmp_path -PassThru
Assert-Equal -actual $res.GetType().Name -expected "RuntimeAssembly"
Assert-Equal -actual $res.Location -expected ""
Assert-Equal -actual $res.GetTypes().Length -expected 1
Assert-Equal -actual $res.GetTypes()[0].Name -expected "Class3"

$actual = [Namespace3.Class3]::GetString($false)
Assert-Equal $actual -expected "Hello World"

try {
    [Namespace3.Class3]::GetString($true)
}
catch {
    $actual = $_.Exception.ToString().ToLower().Contains("at namespace3.class3.getstring(boolean error) in $($tmp_path.ToLower())")
    Assert-Equal $actual -expected $true
    Assert-Equal ($_.Exception.ToString().Contains(".cs:line 10")) -expected $true
}

$warning_code = @'
using System;

namespace Namespace4
{
    public class Class4
    {
        public static string GetString(bool test)
        {
            if (test)
            {
                string a = "";
            }

            return "Hello World";
        }
    }
}
'@
$failed = $false
try {
    Add-CSharpType -References $warning_code
}
catch {
    $failed = $true
    $actual = $_.Exception.Message.Contains("error CS0219: Warning as Error: The variable 'a' is assigned but its value is never used")
    Assert-Equal -actual $actual -expected $true
}
Assert-Equal -actual $failed -expected $true

Add-CSharpType -References $warning_code -IgnoreWarnings
$actual = [Namespace4.Class4]::GetString($true)
Assert-Equal -actual $actual -expected "Hello World"

$reference_1 = @'
using System;
using System.Web.Script.Serialization;

//AssemblyReference -Name System.Web.Extensions.dll

namespace Namespace5
{
    public class Class5
    {
        public static string GetString()
        {
            return "Hello World";
        }
    }
}
'@

$reference_2 = @'
using System;
using Namespace5;
using System.Management.Automation;
using System.Collections;
using System.Collections.Generic;

namespace Namespace6
{
    public class Class6
    {
        public static string GetString()
        {
            Hashtable hash = new Hashtable();
            hash["test"] = "abc";
            return Class5.GetString();
        }
    }
}
'@

Add-CSharpType -References $reference_1, $reference_2
$actual = [Namespace6.Class6]::GetString()
Assert-Equal -actual $actual -expected "Hello World"

$ignored_warning = @'
using System;

//NoWarn -Name CS0219

namespace Namespace7
{
    public class Class7
    {
        public static string GetString()
        {
            string a = "";
            return "abc";
        }
    }
}
'@
Add-CSharpType -References $ignored_warning
$actual = [Namespace7.Class7]::GetString()
Assert-Equal -actual $actual -expected "abc"

$defined_symbol = @'
using System;

namespace Namespace8
{
    public class Class8
    {
        public static string GetString()
        {
#if SYMBOL1
            string a = "symbol";
#else
            string a = "no symbol";
#endif
            return a;
        }
    }
}
'@
Add-CSharpType -References $defined_symbol -CompileSymbols "SYMBOL1"
$actual = [Namespace8.Class8]::GetString()
Assert-Equal -actual $actual -expected "symbol"

$type_accelerator = @'
using System;

//TypeAccelerator -Name AnsibleType -TypeName Class9

namespace Namespace9
{
    public class Class9
    {
        public static string GetString()
        {
            return "a";
        }
    }
}
'@
Add-CSharpType -Reference $type_accelerator
$actual = [AnsibleType]::GetString()
Assert-Equal -actual $actual -expected "a"

$missing_type_class = @'
using System;

//TypeAccelerator -Name AnsibleTypeMissing -TypeName MissingClass

namespace Namespace10
{
    public class Class10
    {
        public static string GetString()
        {
            return "b";
        }
    }
}
'@
$failed = $false
try {
    Add-CSharpType -Reference $missing_type_class
}
catch {
    $failed = $true
    Assert-Equal -actual $_.Exception.Message -expected "Failed to find compiled class 'MissingClass' for custom TypeAccelerator."
}
Assert-Equal -actual $failed -expected $true

$arch_class = @'
using System;

namespace Namespace11
{
    public class Class11
    {
        public static int GetIntPtrSize()
        {
#if X86
            return 4;
#elif AMD64
            return 8;
#else
            return 0;
#endif
        }
    }
}
'@
Add-CSharpType -Reference $arch_class
Assert-Equal -actual ([Namespace11.Class11]::GetIntPtrSize()) -expected ([System.IntPtr]::Size)

$lib_set = @'
using System;

namespace Namespace12
{
    public class Class12
    {
        public static string GetString()
        {
            return "b";
        }
    }
}
'@
$env:LIB = "C:\fake\folder\path"
try {
    Add-CSharpType -Reference $lib_set
}
finally {
    Remove-Item -LiteralPath env:\LIB
}
Assert-Equal -actual ([Namespace12.Class12]::GetString()) -expected "b"

$unsafe_code_fail = @'
using System;

namespace Namespace13
{
    public class Class13
    {

        public static int GetNumber()
        {
            int num = 2;
            int* numPtr = &num;

            DoubleNumber(numPtr);

            return num;
        }

        private unsafe static void DoubleNumber(int* num)
        {
            *num = *num * 3;
        }
    }
}
'@
$failed = $false
try {
    Add-CSharpType -Reference $unsafe_code_fail
}
catch {
    $failed = $true
    $actual = $_.Exception.Message.Contains("error CS0227: Unsafe code may only appear if compiling with /unsafe")
    Assert-Equal -actual $actual -expected $true
}
Assert-Equal -actual $failed -expected $true

$unsafe_code = @'
using System;

//AllowUnsafe

namespace Namespace13
{
    public class Class13
    {
        public static int GetNumber()
        {
            int num = 2;
            unsafe
            {
                int* numPtr = &num;

                DoubleNumber(numPtr);
            }

            return num;
        }

        private unsafe static void DoubleNumber(int* num)
        {
            *num = *num * 2;
        }
    }
}
'@
Add-CSharpType -Reference $unsafe_code
Assert-Equal -actual ([Namespace13.Class13]::GetNumber()) -expected 4

$result.res = "success"
Exit-Json -obj $result
