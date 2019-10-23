#
# chunk_file.py - Uses Rabin fingerprinting to split a file (or stream
#	of bytes) into variable-length chunks
#
# Copyright (C) 2019 Paul Lu, Owen Randall, <paullu@cs.ualberta.ca>
#
# Originally implemented by Owen Randall.
#	Credits:  Owen Randall, Paul Lu
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Based on chunk_fileV3_1.py
from rabin_fingerprint import byteWindowFingerprinter3, irreducible_polynomial, print_bits
import sys
import hashlib
import time
import datetime

def chunk(fileName = None, windowSize = 3, fingerprintSize = 8, maskSize = 8, data = None,verbose=False):
    cutValue = 1
    mask = (2 ** maskSize) - 1
    fingerprinter = byteWindowFingerprinter3(irreducible_polynomial(fingerprintSize), windowSize)
    if fileName != None:
        try:
            data = open(fileName, 'rb').read()
        except:
            print( "File open/read failed: %s" % (fileName) )
            sys.exit(-1)
    chunk_dict = {}
    chunk_lst = []
    length = 0
    hasher = hashlib.sha1()
    chunk = bytearray(b'')

    lenInBytes = 0
    oneMB = 1024 * 1024
    tenMB = 10 * oneMB
    for byte in data:
        if verbose and ( ( lenInBytes % tenMB ) == 0 ):
            print( "%5d MB: %s" % (lenInBytes/oneMB, datetime.datetime.now()), flush=True )
        lenInBytes += 1

        length += 1
        fingerprint = fingerprinter.update(byte)
        hasher.update(byte.to_bytes(1, 'big'))
        chunk.append(byte)
        if fingerprint & mask == cutValue:
            hVal = hasher.digest()
            pair = (hVal, length)
            chunk_lst.append(pair)
            # print(len(chunk_lst))
            if pair not in chunk_dict:
                chunk_dict[pair] = chunk
            elif chunk_dict[pair] != chunk:
                raise("ERROR NON MATCHING CHUNK")
                print(pair)
                print(chunk_dict[pair])
                print(chunk)
            hasher = hashlib.sha1()
            length = 0
            chunk = bytearray(b'')

    hVal = hasher.digest()
    pair = (hVal, length)
    chunk_lst.append(pair)
    if pair not in chunk_dict:
        chunk_dict[pair] = chunk
    elif chunk_dict[pair] != chunk:
        raise("ERROR NON MATCHING CHUNK")
        print(pair)
        print(chunk_dict[pair])
        print(chunk)

    return chunk_dict, chunk_lst
