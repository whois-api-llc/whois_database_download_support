#Utilities to be included into mysql loader scripts

#
# Prints the version number and exits.
#
function printVersionAndExit()
{
    echo "$MYNAME Version $VERSION"
    echo ""
    exit 0
}
#
#
# Prints all the arguments but only if the program is in the verbose mode.
#
function printVerbose()
{
    if [ "$VERBOSE" == "true" ]; then
        echo $* >&2
    fi
}

#
# Prints an error message to the standard error. The text will not mixed up with
# the data that is printed to the standard output.
#
function printError()
{
    echo "$*" >&2
}

function printMessage()
{
    echo -n "$*" >&2
}

function printMessageNl()
{
    echo "$*" >&2
}

function printDebug()
{
    if [ "$DEBUG" == "yes" ]; then
        echo "$*" >&2
    fi
}

