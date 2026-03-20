"""Helpers for PowerShell command line and scripting arguments."""

from __future__ import annotations

import base64
import re
import shlex

from . import _clixml

# There are 5 chars that need to be escaped in a single quote.
# https://github.com/PowerShell/PowerShell/blob/b7cb335f03fe2992d0cbd61699de9d9aafa1d7c1/src/System.Management.Automation/engine/parser/CharTraits.cs#L265-L272
_PWSH_SINGLE_QUOTES = re.compile("(['\u2018\u2019\u201a\u201b])")

# These chars are a known set of chars that are safe to use as a bare command.
_PWSH_BARE_CMD = re.compile(r'^[\w\-\\\.\[\]/_~!%^:]+$')


def _get_encoded_arguments(
    script: str,
    args: list[str] | None = None,
) -> list[str]:
    """Builds an -EncodedCommand cmdline argument

    Returns a list of arguments that can be used with PowerShell to invoke
    a script with optional arguments.

    :param script: The script to encode.
    :param args: The string arguments to encode.
    :returns: The encoded arguments string value as a base64 string.
    """
    encoded_cmd = base64.b64encode(script.encode('utf-16-le')).decode()
    pwsh_args = ['-EncodedCommand', encoded_cmd]
    if not args:
        return pwsh_args

    # -EncodedCommand does not accept normal positional parameters. Instead it
    # only supports extra args through an encoded CLIXML string.
    clixml = _clixml.build_array_list_clixml(args)
    encoded_args = base64.b64encode(clixml.encode('utf-16-le')).decode()
    pwsh_args.extend(['-EncodedArguments', encoded_args])

    return pwsh_args


def parse_encoded_cmdline(
    cmd: str,
) -> tuple[str, list[str]] | None:
    """Parses a PowerShell encoded command line string.

    Attempts to parse a command line string for the encoded command/arguments.
    Will return None if not present or if the command line is not a valid for
    PowerShell.

    :param cmd: The command line string to parse.
    :returns: A tuple of the decoded command and list of arguments or None if ill-formed.
    """
    cmd_split = shlex.split(cmd)

    try:
        enc_cmd_idx = cmd_split.index("-EncodedCommand")
    except ValueError:
        enc_cmd_idx = -1

    if enc_cmd_idx == -1 or len(cmd_split) <= enc_cmd_idx + 1:
        return None

    enc_cmd_raw = cmd_split[enc_cmd_idx + 1]
    enc_cmd = base64.b64decode(enc_cmd_raw).decode('utf-16-le')

    try:
        enc_arg_idx = cmd_split.index("-EncodedArguments")
    except ValueError:
        return enc_cmd, []

    if len(cmd_split) <= enc_arg_idx + 1:
        # Was ill-formed so assume it's not a valid encoded pwsh cmd.
        return None

    clixml_raw = cmd_split[enc_arg_idx + 1]
    clixml = base64.b64decode(clixml_raw).decode('utf-16-le')
    cmd_args = _clixml.extract_clixml_strings(clixml)

    return enc_cmd, cmd_args


def get_pwsh_encoded_cmdline(
    script: str,
    *,
    args: list[str] | None = None,
    pwsh_path: str = 'powershell',
    disable_input: bool = False,
    override_execution_policy: bool = False,
) -> list[str]:
    """Builds a PowerShell command line argument list.

    Builds the encoded command line arguments for running the provided script.

    :param script: The PowerShell script to encode.
    :param args: Optional positional arguments to the script.
    :param pwsh_path: The PowerShell executable path, defaults to powershell.
    :param disable_input: Tells PowerShell to not read input from stdin.
    :param override_execution_policy: Adds args to override the execution policy.
    :returns: The command line arguments as a list.
    """
    cmd_args = [pwsh_path, '-NoProfile', '-NonInteractive']
    if override_execution_policy:
        cmd_args.extend(['-ExecutionPolicy', 'Unrestricted'])

    if disable_input:
        cmd_args.extend(['-InputFormat', 'None'])

    encoded_args = _get_encoded_arguments(script, args)
    cmd_args.extend(encoded_args)

    return cmd_args


def build_pwsh_cmd_statement(
    command: str,
    args: list[str] | None = None,
) -> str:
    """Builds a PowerShell command statement.

    Builds a valid PowerShell command statement with optional arguments. This
    statement can be used in a PowerShell script to execute a command with the
    arguments provided.

    :param command: The PowerShell command to execute.
    :param args: The arguments to provide to the command.
    :returns: The PowerShell script as a string representing this command statement.
    """
    pwsh_cmd = quote_pwsh_argument(command)
    if pwsh_cmd != command:
        # If we quoted the cmd we need to add the call operator for pwsh
        # to treat it as a command.
        pwsh_cmd = f"& {pwsh_cmd}"

    if args:
        remaining_args = " ".join([quote_pwsh_argument(a) for a in args])
        pwsh_cmd += f" {remaining_args}"

    return pwsh_cmd


def quote_pwsh_argument(
    value: str,
    *,
    force_quote: bool = False,
) -> str:
    """Quotes a value for use as a PowerShell argument.

    This safely quotes the provided value for use in a PowerShell script. The
    value will either be a bare keyword or a quoted string that is safe to use
    in a PowerShell script.

    :param value: The value to quote.
    :param force_quote: Force the quotes even if the value doesn't need it.
    :returns: The value that is safe to use as a PowerShell argument.
    """
    if not force_quote and _PWSH_BARE_CMD.match(value):
        return value

    # Escaping a pwsh string for single quotes is to just double up on the
    # single quote values inside the string.
    return f"'{_PWSH_SINGLE_QUOTES.sub(r'\1\1', value)}'"
