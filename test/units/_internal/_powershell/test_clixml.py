from __future__ import annotations

import pytest

from ansible._internal._powershell import _clixml


CLIXML_WITH_ERROR = b'#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">' \
    b'<S S="Error">My error</S></Objs>'


def test_replace_stderr_clixml_by_itself():
    data = CLIXML_WITH_ERROR
    expected = b"My error"
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_with_pre_and_post_lines():
    data = b"pre\r\n" + CLIXML_WITH_ERROR + b"\r\npost"
    expected = b"pre\r\nMy error\r\npost"
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_with_remaining_data_on_line():
    data = b"pre\r\n" + CLIXML_WITH_ERROR + b"inline\r\npost"
    expected = b"pre\r\nMy errorinline\r\npost"
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_with_non_utf8_data():
    # \x82 in cp437 is é but is an invalid UTF-8 sequence
    data = CLIXML_WITH_ERROR.replace(b"error", b"\x82rror")
    expected = "My érror".encode("utf-8")
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_across_liens():
    data = b"#< CLIXML\r\n<Objs Version=\"foo\">\r\n</Objs>"
    expected = data
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_replace_stderr_clixml_with_invalid_clixml_data(newline):
    data = f"#< CLIXML{newline}<Objs Version=\"foo\"><</Objs>".encode()
    expected = data
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_with_no_clixml():
    data = b"foo"
    expected = data
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_replace_stderr_clixml_with_header_but_no_data():
    data = b"foo\r\n#< CLIXML\r\n"
    expected = data
    actual = _clixml.replace_stderr_clixml(data)

    assert actual == expected


def test_extract_clixml_empty():
    empty = '#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"></Objs>'
    expected = []
    actual = _clixml.extract_clixml_strings(empty)
    assert actual == expected


def test_extract_clixml_with_progress():
    progress = '#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">' \
               '<Obj S="progress" RefId="0"><TN RefId="0"><T>System.Management.Automation.PSCustomObject</T><T>System.Object</T></TN><MS>' \
               '<I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil />' \
               '<PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj></Objs>'
    expected = []
    actual = _clixml.extract_clixml_strings(progress)
    assert actual == expected


def test_extract_clixml_error_single_stream():
    single_stream = '#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">' \
                    '<S S="Error">fake : The term \'fake\' is not recognized as the name of a cmdlet. Check _x000D__x000A_</S>' \
                    '<S S="Error">the spelling of the name, or if a path was included._x000D__x000A_</S>' \
                    '<S S="Error">At line:1 char:1_x000D__x000A_</S>' \
                    '<S S="Error">+ fake cmdlet_x000D__x000A_</S><S S="Error">+ ~~~~_x000D__x000A_</S>' \
                    '<S S="Error">    + CategoryInfo          : ObjectNotFound: (fake:String) [], CommandNotFoundException_x000D__x000A_</S>' \
                    '<S S="Error">    + FullyQualifiedErrorId : CommandNotFoundException_x000D__x000A_</S>' \
                    '<S S="Error"> _x000D__x000A_</S>' \
                    '</Objs>'
    expected = [
        "fake : The term 'fake' is not recognized as the name of a cmdlet. Check \r\n",
        "the spelling of the name, or if a path was included.\r\n",
        "At line:1 char:1\r\n",
        "+ fake cmdlet\r\n",
        "+ ~~~~\r\n",
        "    + CategoryInfo          : ObjectNotFound: (fake:String) [], CommandNotFoundException\r\n",
        "    + FullyQualifiedErrorId : CommandNotFoundException\r\n",
        " \r\n",
    ]
    actual = _clixml.extract_clixml_strings(single_stream, stream="Error")
    assert actual == expected


def test_extract_clixml_error_multiple_streams():
    multiple_stream = '#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">' \
                      '<S S="Error">fake : The term \'fake\' is not recognized as the name of a cmdlet. Check _x000D__x000A_</S>' \
                      '<S S="Error">the spelling of the name, or if a path was included._x000D__x000A_</S>' \
                      '<S S="Error">At line:1 char:1_x000D__x000A_</S>' \
                      '<S S="Error">+ fake cmdlet_x000D__x000A_</S><S S="Error">+ ~~~~_x000D__x000A_</S>' \
                      '<S S="Error">    + CategoryInfo          : ObjectNotFound: (fake:String) [], CommandNotFoundException_x000D__x000A_</S>' \
                      '<S S="Error">    + FullyQualifiedErrorId : CommandNotFoundException_x000D__x000A_</S><S S="Error"> _x000D__x000A_</S>' \
                      '<S S="Info">hi info</S>' \
                      '<S S="Info">other</S>' \
                      '</Objs>'
    expected = ["hi info", "other"]
    actual = _clixml.extract_clixml_strings(multiple_stream, stream="Info")
    assert actual == expected


def test_extract_clixml_error_multiple_elements():
    multiple_elements = '#< CLIXML\r\n#< CLIXML\r\n<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">' \
                        '<Obj S="progress" RefId="0"><TN RefId="0"><T>System.Management.Automation.PSCustomObject</T><T>System.Object</T></TN><MS>' \
                        '<I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil />' \
                        '<PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj>' \
                        '<S S="Error">Error 1</S></Objs>' \
                        '<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"><Obj S="progress" RefId="0">' \
                        '<TN RefId="0"><T>System.Management.Automation.PSCustomObject</T><T>System.Object</T></TN><MS>' \
                        '<I64 N="SourceId">1</I64><PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil />' \
                        '<PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj>' \
                        '<Obj S="progress" RefId="1"><TNRef RefId="0" /><MS><I64 N="SourceId">2</I64>' \
                        '<PR N="Record"><AV>Preparing modules for first use.</AV><AI>0</AI><Nil />' \
                        '<PI>-1</PI><PC>-1</PC><T>Completed</T><SR>-1</SR><SD> </SD></PR></MS></Obj>' \
                        '<S S="Error">Error 2</S></Objs>'
    expected = ["Error 1", "\r\n", "Error 2"]
    actual = _clixml.extract_clixml_strings(multiple_elements, stream="Error")
    assert actual == expected


@pytest.mark.parametrize('clixml, expected', [
    ('', ''),
    ('just newline _x000A_', 'just newline \n'),
    ('surrogate pair _xD83C__xDFB5_', 'surrogate pair 🎵'),
    ('null char _x0000_', 'null char \0'),
    ('normal char _x0061_', 'normal char a'),
    ('escaped literal _x005F_x005F_', 'escaped literal _x005F_'),
    ('underscope before escape _x005F__x000A_', 'underscope before escape _\n'),
    ('surrogate high _xD83C_', 'surrogate high \uD83C'),
    ('surrogate low _xDFB5_', 'surrogate low \uDFB5'),
    ('lower case hex _x005f_', 'lower case hex _'),
    ('invalid hex _x005G_', 'invalid hex _x005G_'),
    # Tests regex actually matches UTF-16-BE hex chars (b"\x00" then hex char).
    ("_x\u6100\u6200\u6300\u6400_", "_x\u6100\u6200\u6300\u6400_"),
])
def test_extract_clixml_error_with_comlex_escaped_chars(clixml, expected):
    clixml_data = (
        '<# CLIXML\r\n'
        '<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">'
        f'<S S="Error">{clixml}</S>'
        '</Objs>'
    )
    # b_expected = expected.encode(errors="surrogatepass")

    actual = _clixml.extract_clixml_strings(clixml_data, stream="Error")
    assert actual == [expected]


def test_extract_clixml_string_encoded_arguments():
    # Generated from - change pwsh to an exe that prints back argv
    # pwsh {} -args 'simple', '_x005F_', ([char]::ConvertFromUtf32(0x1F3B5))
    encoded_clixml = (
        '<Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04">'
        '<Obj RefId="0">'
        '<TN RefId="0"><T>System.Collections.ArrayList</T><T>System.Object</T></TN>'
        '<LST>'
        '<S>simple</S>'
        '<S>_x005F_x005F_</S>'
        '<S>_xD83C__xDFB5_</S>'
        '</LST>'
        '</Obj>'
        '</Objs>'
    )
    expected = ['simple', '_x005F_', "\U0001F3B5"]

    actual = _clixml.extract_clixml_strings(encoded_clixml)
    assert actual == expected
