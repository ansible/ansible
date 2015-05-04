def isprintable(instring):
    if isinstance(instring, str):
        #http://stackoverflow.com/a/3637294
        import string
        printset = set(string.printable)
        isprintable = set(instring).issubset(printset)
        return isprintable
    else:
        return True

def count_newlines_from_end(str):
    i = len(str)
    while i > 0:
        if str[i-1] != '\n':
            break
        i -= 1
    return len(str) - i

