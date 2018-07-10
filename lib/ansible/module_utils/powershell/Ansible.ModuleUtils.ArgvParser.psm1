# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# The rules used in these functions are derived from the below
# https://docs.microsoft.com/en-us/cpp/cpp/parsing-cpp-command-line-arguments
# https://blogs.msdn.microsoft.com/twistylittlepassagesallalike/2011/04/23/everyone-quotes-command-line-arguments-the-wrong-way/

Function Escape-Argument($argument, $force_quote=$false) {
    # this converts a single argument to an escaped version, use Join-Arguments
    # instead of this function as this only escapes a single string.

    # check if argument contains a space, \n, \t, \v or "
    if ($force_quote -eq $false -and $argument.Length -gt 0 -and $argument -notmatch "[ \n\t\v`"]") {
        # argument does not need escaping (and we don't want to force it),
        # return as is
        return $argument
    } else {
        # we need to quote the arg so start with "
        $new_argument = '"'

        for ($i = 0; $i -lt $argument.Length; $i++) {
            $num_backslashes = 0

            # get the number of \ from current char until end or not a \
            while ($i -ne ($argument.Length - 1) -and $argument[$i] -eq "\") {
                $num_backslashes++
                $i++
            }

            $current_char = $argument[$i]
            if ($i -eq ($argument.Length -1) -and $current_char -eq "\") {
                # We are at the end of the string so we need to add the same \
                # * 2 as the end char would be a "
                $new_argument += ("\" * ($num_backslashes + 1) * 2)
            } elseif ($current_char -eq '"') {
                # we have a inline ", we need to add the existing \ but * by 2
                # plus another 1
                $new_argument += ("\" * (($num_backslashes * 2) + 1))
                $new_argument += $current_char
            } else {
                # normal character so no need to escape the \ we have counted
                $new_argument += ("\" * $num_backslashes)
                $new_argument += $current_char
            }
        }

        # we need to close the special arg with a "
        $new_argument += '"'
        return $new_argument
    }
}

Function Argv-ToString($arguments, $force_quote=$false) {
    # Takes in a list of un escaped arguments and convert it to a single string
    # that can be used when starting a new process. It will escape the
    # characters as necessary in the list.
    # While there is a CommandLineToArgvW function there is a no
    # ArgvToCommandLineW that we can call to convert a list to an escaped
    # string.
    # You can also pass in force_quote so that each argument is quoted even
    # when not necessary, by default only arguments with certain characters are
    # quoted.
    # TODO: add in another switch which will escape the args for cmd.exe

    $escaped_arguments = @()
    foreach ($argument in $arguments) {
        $escaped_argument = Escape-Argument -argument $argument -force_quote $force_quote
        $escaped_arguments += $escaped_argument
    }

    return ($escaped_arguments -join ' ')
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *
