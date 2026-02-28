"""Helpers for PowerShell's CLIXML data"""

from __future__ import annotations

import base64
import re
import xml.etree.ElementTree as ET


# This is weird, we are matching on byte sequences that match the utf-16-be
# matches for '_x(a-fA-F0-9){4}_'. The \x00 and {4} will match the hex sequence
# when it is encoded as utf-16-be byte sequence.
_STRING_DESERIAL_FIND = re.compile(rb"\x00_\x00x((?:\x00[a-fA-F0-9]){4})\x00_")

# Finds _x in a case insensitive way, _x is the escape sequence for a CLIXML
# str so needs to be escaped first.
_STRING_SERIAL_ESCAPE_ESCAPE = re.compile("(?i)_(x)")

# Finds C0, C1, and surrogate pairs in a unicode string for us to encode
# according to the PSRP rules.
_STRING_SERIAL_ESCAPE = re.compile("[\u0000-\u001f\u007f-\u009f\ud800-\ud8ff\udc00-\udfff\U00010000-\U0010ffff]")


def replace_stderr_clixml(stderr: bytes) -> bytes:
    """Replace CLIXML with stderr data.

    Tries to replace an embedded CLIXML string with the actual stderr data. If
    it fails to parse the CLIXML data, it will return the original data. This
    will replace any line inside the stderr string that contains a valid CLIXML
    sequence.

    :param bytes stderr: The stderr to try and decode.
    :returns: The stderr with the decoded CLIXML data or the original data.
    """
    clixml_header = b"#< CLIXML"

    # Instead of checking both patterns we just see if the next char
    # is \r or \n to match both Windows and POSIX newline after the marker.
    clixml_idx = stderr.find(clixml_header)
    if clixml_idx == -1:
        return stderr

    newline_idx = clixml_idx + 9
    if len(stderr) < (newline_idx + 1) or stderr[newline_idx] not in (ord(b'\r'), ord(b'\n')):
        return stderr

    lines: list[bytes] = []
    is_clixml = False
    for line in stderr.splitlines(True):
        if is_clixml:
            is_clixml = False

            # If the line does not contain the closing CLIXML tag, we just
            # add the found header line and this line without trying to parse.
            end_idx = line.find(b"</Objs>")
            if end_idx == -1:
                lines.append(clixml_header)
                lines.append(line)
                continue

            clixml = line[: end_idx + 7]
            remaining = line[end_idx + 7 :]

            # While we expect the stderr to be UTF-8 encoded, we fallback to
            # the most common "ANSI" codepage used by Windows cp437 if it is
            # not valid UTF-8.
            try:
                clixml_text = clixml.decode("utf-8")
            except UnicodeDecodeError:
                clixml_text = clixml.decode("cp437")

            try:
                decoded_clixml = extract_clixml_strings(clixml_text, stream="Error")
                lines.append("".join(decoded_clixml).encode('utf-8', errors='surrogatepass'))
                if remaining:
                    lines.append(remaining)

            except Exception:
                # Any errors and we just add the original CLIXML header and
                # line back in.
                lines.append(clixml_header)
                lines.append(line)

        elif line.startswith(clixml_header):
            # The next line should contain the full CLIXML data.
            clixml_header = line  # Preserve original newlines value.
            is_clixml = True

        else:
            lines.append(line)

    # This should never happen but if there was a CLIXML header without a newline
    # following it, we need to add it back.
    if is_clixml:
        lines.append(clixml_header)

    return b"".join(lines)


def extract_clixml_strings(
    data: str,
    stream: str | None = None,
) -> list[str]:
    """
    Takes a string that contains a CLIXML <Objs> element and extracts any
    string elements within. This is a rudimentary extraction designed for
    stderr CLIXML and -EncodedArguments.

    :param data: The raw CLIXML string.
    :param stream: The optional string to extra the data for.
    :returns: A list of CLIXML strings encoded within the CLIXML string.
    """
    lines: list[str] = []

    # A serialized string will serialize control chars and surrogate pairs as
    # _xDDDD_ values where DDDD is the hex representation of a big endian
    # UTF-16 code unit. As a surrogate pair uses 2 UTF-16 code units, we need
    # to operate our text replacement on the utf-16-be byte encoding of the raw
    # text. This allows us to replace the _xDDDD_ values with the actual byte
    # values and then decode that back to a string from the utf-16-be bytes.
    def rplcr(matchobj: re.Match) -> bytes:
        match_hex = matchobj.group(1)
        hex_string = match_hex.decode("utf-16-be")
        return base64.b16decode(hex_string.upper())

    # There are some scenarios where the stderr contains a nested CLIXML element like
    # '<# CLIXML\r\n<# CLIXML\r\n<Objs>...</Objs><Objs>...</Objs>'.
    # Parse each individual <Objs> element and add the error strings to our stderr list.
    # https://github.com/ansible/ansible/issues/69550
    while data:
        start_idx = data.find("<Objs ")
        end_idx = data.find("</Objs>")
        if start_idx == -1 or end_idx == -1:
            break

        end_idx += 7
        current_element = data[start_idx:end_idx]
        data = data[end_idx:]

        clixml = ET.fromstring(current_element)
        namespace_match = re.match(r'{(.*)}', clixml.tag)
        namespace = f"{{{namespace_match.group(1)}}}" if namespace_match else ""

        entries = clixml.findall(".//%sS" % namespace)
        if not entries:
            continue

        # If this is a new CLIXML element, add a newline to separate the messages.
        if lines:
            lines.append("\r\n")

        for string_entry in entries:
            actual_stream = string_entry.attrib.get('S', None)
            if actual_stream != stream:
                continue

            b_line = (string_entry.text or "").encode("utf-16-be")
            b_escaped = re.sub(_STRING_DESERIAL_FIND, rplcr, b_line)

            lines.append(b_escaped.decode("utf-16-be", errors="surrogatepass"))

    return lines


def build_array_list_clixml(
    values: list[str],
) -> str:
    """Builds a CLIXML string representing a System.Collections.ArrayList of strings."""

    def rplcr(matchobj: object) -> str:
        surrogate_char = matchobj.group(0)
        byte_char = surrogate_char.encode("utf-16-be", errors="surrogatepass")
        hex_char = base64.b16encode(byte_char).decode()
        hex_split = [hex_char[i : i + 4] for i in range(0, len(hex_char), 4)]

        return "".join([f"_x{i}_" for i in hex_split])

    objs = ET.Element('Objs', xmlns="http://schemas.microsoft.com/powershell/2004/04", Version="1.1.0.1")
    obj = ET.SubElement(objs, 'Obj', RefId="0")

    tn = ET.SubElement(obj, 'TN', RefId="0")
    ET.SubElement(tn, 'T').text = "System.Collections.ArrayList"
    ET.SubElement(tn, 'T').text = "System.Object"

    lst = ET.SubElement(obj, 'LST')
    for v in values:
        # Before running the translation we need to make sure that '_x' is
        # escaped as '_x005F_x'. While MS-PSRP doesn't state this, the x is
        # case insensitive so we need to escape both '_x' and '_X'.
        v = re.sub(_STRING_SERIAL_ESCAPE_ESCAPE, r"_x005F_\1", v)

        # Escape any control or codepoints that are represented as a
        # surrogate pair in UTF-16.
        v = re.sub(_STRING_SERIAL_ESCAPE, rplcr, v)
        ET.SubElement(lst, 'S').text = v

    return ET.tostring(objs, encoding='unicode')
