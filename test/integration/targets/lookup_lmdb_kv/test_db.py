from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import lmdb
map_size = 1024 * 100
env = lmdb.open('./jp.mdb', map_size=map_size)
with env.begin(write=True) as txn:
    txn.put('fr'.encode(), 'France'.encode())
    txn.put('nl'.encode(), 'Netherlands'.encode())
    txn.put('es'.encode(), 'Spain'.encode())
    txn.put('be'.encode(), 'Belgium'.encode())
    txn.put('lu'.encode(), 'Luxembourg'.encode())
