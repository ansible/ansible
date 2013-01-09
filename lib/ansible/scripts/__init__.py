def ansible():
    from ._ansible_ import entry_point
    return entry_point()


def ansible_playbook():
    from ._ansible_playbook_ import entry_point
    return entry_point()


def ansible_pull():
    from ._ansible_pull_ import entry_point
    return entry_point()


def ansible_doc():
    from ._ansible_doc_ import entry_point
    return entry_point()
