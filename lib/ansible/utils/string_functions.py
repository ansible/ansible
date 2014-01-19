def isprintable(instring):
    #http://stackoverflow.com/a/3637294
    import string
    printset = set(string.printable)
    isprintable = set(instring).issubset(printset)
    return isprintable

