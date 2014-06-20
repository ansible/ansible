#!/bin/bash
#===================================================================================================
#
#                bash_helper - Helper script for ansible modules written in bash
#
#---------------------------------------------------------------------------------------------------
#
#  This script helps bash ansible modules to:
#
#   - Validate and parse the module's arguments into bash environment variables.
#   - Capture stdout and stderr output and return it to ansible in JSON format.
#   - Intercept script errors and return failures automatically to ansible.
#   - Format and return results in JSON-compliant format.
#
#  USAGE
#
#       Include the following line at the beginning of your script (after the shebang):
#
#           #INSERT_BASH_HELPER --args "allowed_arguments" | --noparse --debug
#
#       where --args "allowed_arguments" specifies a space-delimited list of argument keywords that
#       are accepted by the module. Include the keyword '...' if positionnal arguments are also
#       accepted. The module's arguments are automatically stored in the correspondingly-named
#       environement variables (positionnals are stored in $1, $2, ...). In addition, ARGN, ARGV and
#       ARGS contain bash arrays of the parsed argument names, values and positionnal values. An
#       error is raised if any unsupported argument is passed to the module. If --args is omitted,
#       --args '' is assumed, that is the module will not accept any argument.  Use --noparse to
#       bypass the helper's argument parsing and receive all arguments in ansible's original
#       format. --debug is used only during development (see DEBUGGING below)..
#
#       EXAMPLE: #INSERT_BASH_HELPER --args "file contents owner group mode"
#
#             This will initialize the ansible module and parse the module arguments 'file=',
#             'contents=', 'owner=', 'group=' and 'mode=' into the corresponding bash environment
#             variables. If unknown name/value pairs are passed to the module, an error is returned
#             to ansible.
#
#  STDOUT/STDERR CAPTURE
#
#       All stdout/stderr written by the script is automatically captured by the helper and returned
#       to ansible in JSON format when the module ends.
#
#  ERROR TRAPPING
#
#       All script errors are automatically trapped by the use of a TRAR ERR and wll cause the bash
#       module to return immediately with an explanatory message if any command fails. To allow the
#       script to continue even if a command fails, enclose the command in an if statement, in a
#       pipe, test the command's results (see bash manpage under TRAP ERR to understand when errors
#       are trapped or not), or simply use the shortcut '||:' as follows:
#
#                        rm "file_may_not_exist" || :
#
#  RETURNING JSON RESPONSE
#
#       Call ansible_return with the following arguments to return values to ansible when the module
#       is done:
#
#        ansible_return [ name:rawvalue | name="value" | var ... ]
#
#       This will format the arguments into JSON-compliant format and return it to ansible along
#       with any stdout/stderr output already captured. Use the argument format 'name:rawvalue' to
#       return the specified JSON name and value pair exactly as is (for example, to return a
#       boolean), name="value" to return the specified bash value as a JSON-quoted string (use bash
#       quoting rules, the helper script will convert it to JSON as appropriate), or simply use the
#       'var' format to extract and return the value of an existing environment variable.
#
#       EXAMPLE:    string1="This string wll be returned to ansible"
#                   ansible_return failed:false msg="File altered" string1
#
#             will return the following to ansible:
#
#                  '{"failed": false, "msg": "File altered", "string1": "This
#                  string will be returned to ansible"}'
#
#  RETURNING COMPLEX JSON RESPONSES
#
#       To return more complex JSON responses, use the functions json_dict() to format a dictionary
#       (it has the same arguments as ansible_return) and json_array() to format an array. Include
#       the result of those functions in raw format to ansible_return. You may also embed arrays and
#       dicts recursively to create deep structures.
#
#       EXAMPLE:    myfacts="`json_dict factvar factvar2="value"`"
#                   myarray="`json_array a b c d e f`"
#                   ansible_return ansible_facts:"$myfacts" mylist:"$myarray"
#
#             will return the following to ansible:
#
#                      {"failed":false, "ansible_facts": {"factvar1": "", "factvar2": "value"}, 
#                       "mylist": ["a", "b", "c", "d", "e", "f"]}
#
#  IDEMPOTENCE
#
#       To make a bash module idempotent, add a #SUPPORTS_CHECK_MODE in the soure and a "CHECKMODE"
#       to the --args. CHECKMODE will contain 'True' when running in --check mode.
#
#  DEBUGGING YOUR MODULE
#
#       Use hacking/test-module from a git checkout to debug your module, making sure to specify the
#       bash interpreter:
#
#           hacking/test-module -m <module_path> -I bash=/bin/bash -a "args..."
#
#       To see all stdout/stderr messages on your terminal when debugging your module, add the
#       --debug option to #INCLUDE_BASH_HELPER. --debug has effect only when running under
#       hacking/test-module.
#
#       To trace your script's execution, add a 'set -x' command *after* (never before)
#       #INCLUDE_BASH_HELPER. Use --debug to see the output on the terminal.
#
#       EXAMPLE:
#
#           #INCLUDE_BASH_HELPER --options "myoptions..." --debug
#           set -x #Begin bash module trace
#
#---------------------------------------------------------------------------------------------------
#% 2013-10-02 Created. [Guy Sabourin]
#===================================================================================================

#--- json_escape_string() - Format a string value according to JSON syntax (no unicode for now) ---
function json_escape_string() {
    sed -E '$!N; s/(["\\\/])/\\\1/g; s/\'$'\b''/\\b/g; s/\n/\\n/g; s/\'$'\t''/\\t/g; s/\'$'\f''/\\f/g; s/\'$'\r''/\\r/g' <<<"$*" | tr -d '\n'
}

#--- json_unescape_string() - Convert a JSON string (without quotes) to native bash format ---
function json_unescape_string() {
    sed -E 's/\\"/"/g; s#\\/#/#g; s/\\b/'$'\b''/; s/\\n/\'$'\n''/g; s/\\t/\'$'\t''/g; s/\\f/\'$'\f''/g; s/\\r/\'$'\r''/g; s/\\\\/\\/g' <<<"$*"
}

#--- json_array() - Format a JSON array ---
function json_array() {
    local sep=''
    echo -n "["
    #--- Print each argument as a JSON element ---
    for value in "$@"; do
                #--- Quote value ---
                echo -n "$sep\"`json_escape_string "$value"`\""
        #--- Add a seperator for subsequent elements ---
        sep=', '
    done
    #--- Close JSON reponse ---
    echo "]"
}

#--- json_dict() - Format a JSON dictionary ---
function json_dict() {
    local var
    local sep=''
    echo -n "{"
    #--- Print each argument as a JSON element ---
    for var in "$@"; do
        #--- var=value : String value supplied inline, escape string for JSON  ---
        if [[ "$var" =~ ^([-_a-zA-Z0-9]*)=(.*)$ ]]; then
            echo -n "$sep\"${BASH_REMATCH[1]}\": \"`json_escape_string "${BASH_REMATCH[2]}"`\""
        #--- var:value : Raw JSON value supplied inline, don't escape ---
        elif [[ "$var" =~ ^([-_a-zA-Z0-9]*):(.*)$ ]]; then
            echo -n "$sep\"${BASH_REMATCH[1]}\": ${BASH_REMATCH[2]}"
        #--- var : String value is to be obtained from bash environment variables ---
        elif [[ "$var" =~ ^[a-zA-Z0-9_]*$ ]]; then
            echo -n "$sep\"$var\": \"`json_escape_string "${!var}"`\""
        #--- Otherwise, bad argument ---
        else
            ansible_return failed:true msg="Bad argument format supplied to ansible_return/json_dict: $var"
        fi
        #--- Add a seperator for subsequent elements ---
        sep=', '
    done
    #--- Close JSON reponse ---
    echo "}"
}

#--- ansible_return() - Format and return response to ansible ---
function ansible_return() {
    #--- Cancel exit trap ---
    trap - EXIT
    #--- Disable any debugging ---
    set +x
    #--- Close stdout/stderr capture ---
    local _extravars=''
    if [ -n "$ANSIBLE_ARGUMENTS_FILE" ]; then
        #--- Close logs and restore original stdout/stderr filedes ---
        exec 1>&'11'-
        exec 2>&'12'-
        #--- Get stdout and stderr contents ---
        local stdout="`cat "$ANSIBLE_STDOUT"`"
        local stderr="`cat "$ANSIBLE_STDERR"`"
        #--- Delete stdout and stderr temporary files ---
        rm "$ANSIBLE_STDOUT" "$ANSIBLE_STDERR"
        #--- Add stdout/stderr variables to JSON response if applicable ---
        [ -n "$stdout" ] && _extravars+=" stdout"
        [ -n "$stderr" ] && _extravars+=" stderr"
    fi
    #--- Return JSON response to ansible ---
    json_dict "$@" $_extravars
    exit 0
}

#------ Helper starts running here when inserted by ansible ------

#--- Preserve original stdout and stderr filedes ---
exec 11>&1
exec 12>&2

#--- Capture stdout/stderr output to temporary files ---
ANSIBLE_STDOUT=/tmp/ansible_module_$$.stdout
ANSIBLE_STDERR=/tmp/ansible_module_$$.stderr
exec 1>"$ANSIBLE_STDOUT"
exec 2>"$ANSIBLE_STDERR"

#--- Trap bash errors and uncontrolled exits ---
trap 'ansible_return failed:true rc:$? msg="module ${BASH_SOURCE[0]##*/} ended with errors, err=$?" command="$BASH_COMMAND" source="${BASH_SOURCE[0]}" lineno:$LINENO' ERR EXIT

#--- Get ansible module arguments ---
ANSIBLE_ARGUMENTS_FILE="$1"
_args="`cat "$1"`"
shift

#--- Parse helper arguments ---
_parse_args='Y'
_allowed_args=''
while [ $# -gt 0 ]; do
    case "$1" in
        --args) _allowed_args="$2"; shift; shift ;;
        --noparse) _parse_args=''; shift;;
        --debug) if [[ "${BASH_SOURCE[0]}" =~ "/.ansible_module_generated"$ ]]; then  #Only when under hacking
                    #--- Redirect all stdout/stderr to terminal ---
                    exec 1>&12
                    exec 2>&12
                    echo "This ansible bash module has --debug option: All stdout/stderr sent to terminal." >&2
                fi
                shift;;
        *) ansible_return failed:true msg="Invalid argument '$1' to bash_helper";;
    esac
done

#--- Parse ansible module arguments ---
ARGN=() #--- Names
ARGV=() #--- Values
ARGS=() #--- Positionnal arguments
if [ "$_parse_args" = 'Y' ]; then
    while [ -n "$_args" ]; do
        #--- Extract next argument, ignore leading and trailing spaces ---
        if [[ "$_args" =~ ^[' ']*([^ =]+)=(.*)[' ']*$ ]]; then
            #--- Keyword argument ---
            _var="${BASH_REMATCH[1]}"
            _args="${BASH_REMATCH[2]}"
        else
            #--- Positionnal argument ---
            _var=''
            [[ "$_args" =~ ^[' ']*(.*)$ ]]
            _args="${BASH_REMATCH[1]}"
        fi
        #--- Parse quoted argument ---
        if [ "${_args:0:1}" = '"' ]; then
            _value=''
            _args="${_args:1}"
            #--- Repeat parsing until closing quote ---
            while :; do
                #--- Get closing quote ---
                if [[ "$_args" =~ ^([^'"']*)'"'(.*)$ ]]; then
                    #--- Accumulate value ---
                    _value+="${BASH_REMATCH[1]}"
                    _args="${BASH_REMATCH[2]}"
                    #--- Stop parsing if quote is a real closure ---
                    [ "${_value:((-1))}" != '\' -o "${_value:((-2))}" == '\\' ] && break
                    #--- Otherwise, append quote as part of value and continue parsin ---
                    _value+='"'
                #--- No quote closure, this is bad ---
                else
                    echo "Module parameters parse failed for '$_var=' near '$_args'" >&2
                    exit 1
                fi
            done
        #--- Parse unquoted argument ---
        elif [[ "$_args" =~ ^([^ ]*)' '(.*)$ ]]; then
            _value="${BASH_REMATCH[1]}"
            _args="${BASH_REMATCH[2]}"
        #--- Otherwise, this is the last argument ---
        else
            _value="$_args"
            _args=''
        fi
        #--- Process positional argument ---
        if [ -z "$_var" ]; then
            #--- Allow only if caller supports positionnals ---
            if [[ ! " $_allowed_args " =~ ' ... ' ]]; then
                ansible_return failed:true msg="Positionnal arguments not supported by this module: '$_value'"
            fi
            #--- Accumulate positional argument in ARGS[] ---
            ARGS+=("$_value")
        #--- Process supported keyword argument ---
        elif [[ " $_allowed_args " =~ " $_var " ]]; then
            #--- Set corresponding environment variable ---
            declare "$_var"="`json_unescape_string "$_value"`"
            #--- Accumulate keyword argument in ARGN[] and ARGV[] ---
            ARGN+=("$_var")
            ARGV+=("$_value")
        #--- Otherwise, keyword argument not supported by module! ---
        else
            ansible_return failed:true msg="Unsupported argument '$_var='"
        fi
    done
    set -- "${ARGS[@]}"
else
    #--- Otherwise (--noparse), unshift ansible's original arguments ---
    set -- "$ANSIBLE_ARGUMENTS_FILE"
fi
