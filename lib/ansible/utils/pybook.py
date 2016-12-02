#!/usr/bin/env python
# coding: utf-8

import yaml

block_stack = []

def append_impl(new_co, current_name, populate):
    if not block_stack:
        block_stack.append({} if current_name else [])
        
    
    current_object = block_stack[-1]
    is_seq = type(current_object) == list
    
    if is_seq:
        if populate:
            current_object.extend(new_co)
        else:
            current_object.append(new_co)
    else:
        if populate:
            current_object.update(new_co)
        else:
            current_object[current_name] = new_co

class Block:
    def __init__(self, is_sequence):
        self.is_sequence = is_sequence
        self.current_name = None
        
    def __enter__(self):
        new_co = [] if self.is_sequence else {}
        append_impl(new_co, self.current_name, False)
        
        block_stack.append(new_co)
        self.current_name = None

        return None
    
    def __exit__(self, type, value, traceback):
        if type:
            raise

        block_stack.pop()

        return True
    
    def __call__(self, name):
        self.current_name = name
        return self

mapping  = Block(False)
sequence = Block(True)

def append_by_args(args, is_yaml, populate=False):
    ln = len(args)
    if ln == 1:
        current_name, new_co = None, args[0]
    else:
        current_name, new_co = args
        
    if is_yaml:
        new_co = yaml.load(new_co)
    append_impl(new_co, current_name, populate)
    

def append(*args):
    append_by_args(args, False)

def append_yaml(*args):
    append_by_args(args, True)

def populate_yaml(*args):
    append_by_args(args, True, populate=True)

book_globals = {
    "mapping":  mapping,
    "sequence": sequence,
    "append":   append,
    "append_yaml":   append_yaml,
    "populate_yaml": populate_yaml
}

#__all__ = book_globals.keys()

def run_pybook_file(f):
    # :TRICKY: supposed to be empty
    assert not block_stack

    exec(f, book_globals)
    return block_stack.pop()

def run_pybook(fname):
    with open(fname) as f:
        return run_pybook_file(f)

def main():
    import sys
    fname = sys.argv[1]

    try:
        result = run_pybook(fname)
    except Exception, e:
        raise
    import pprint
    pprint.pprint(result)
    
if __name__ == '__main__':
    main()