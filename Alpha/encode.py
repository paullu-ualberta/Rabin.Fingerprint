#
# encode.py - Reads a file and encodes using Rabin fingerprinting for chunking
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

# Based on hbdm_encodeV5.py
from chunk_file import chunk
import sys
import os
import time

def get_chunk_info(commonFile):
    byteIndex = 0
    try:
        fileBytes = open(commonFile, 'rb').read()
    except:
        print( "File open/read failed: %s.  Starting de novo." % (commonFile) )
        fileBytes = []

    chunk_dict = {}
    counter = 0
    while byteIndex < len(fileBytes):
        hashVal = fileBytes[byteIndex : byteIndex + 20]
        byteIndex += 20
        length = fileBytes[byteIndex : byteIndex + 3]
        byteIndex += 3
        theChunk = bytearray(b'')
        while len(theChunk) < int.from_bytes(length, 'big'):
            theChunk.append(fileBytes[byteIndex])
            byteIndex += 1
        pair = hashVal + length
        chunk_dict[pair] = theChunk
        counter += 1
    if counter > 2 ** 24:
        raise("TOO MANY CHUNKS CANNOT REPRESENT IN 3 BYTES")
    return chunk_dict

def encode(inputFile, outputFile, commonFile):
    common_chunk_dict = get_chunk_info(commonFile)
    org_chunk_dict, org_chunk_lst = chunk(inputFile)
    print("Number of unique chunks:", len(org_chunk_dict))
    print("Total number of chunks:", len(org_chunk_lst))
    try:
        encodedFile = open(outputFile, 'wb')
    except:
        print( "File open/write failed: %s" % (outputFile) )
        sys.exit(-1)

    try:
        all_chunks_file = open(commonFile, 'ab+')
    except:
        print( "File open/append failed: %s" % (commonFile) )
        sys.exit(-1)

    counter = len(common_chunk_dict)

    for pair in org_chunk_lst:
        bytePair = pair[0] + pair[1].to_bytes(3, 'big')
        encodedFile.write(bytePair)
        if bytePair not in common_chunk_dict:
            all_chunks_file.write(bytePair + org_chunk_dict[pair])
            common_chunk_dict[bytePair] = org_chunk_dict[pair]
            counter += 1
    if counter > 2 ** 24:
        raise("TOO MANY CHUNKS CANNOT REPRESENT IN 3 BYTES")

def update_db(commonFile, org_chunk_dict_lst, org_chunk_lst_lst):
    common_chunk_dict = get_chunk_info(commonFile)
    try:
        all_chunks_file = open(commonFile, 'ab+')
    except:
        print( "File open/append failed: %s" % (commonFile) )
        sys.exit(-1)


    for i in range(len(org_chunk_lst_lst)):
        org_chunk_lst = org_chunk_lst_lst[i]
        org_chunk_dict = org_chunk_dict_lst[i]
        for pair in org_chunk_lst:
            bytePair = pair[0] + pair[1].to_bytes(3, 'big')
            if bytePair not in common_chunk_dict:
                all_chunks_file.write(bytePair + org_chunk_dict[pair])
                common_chunk_dict[bytePair] = org_chunk_dict[pair]

if __name__ == "__main__":
    if len(sys.argv) > 4:
        maskSize = int(sys.argv[4])
    else:
        maskSize = 6
    input = sys.argv[1]
    if os.path.isdir(input):
        for fileName in os.listdir(input):
            print(fileName)
            if "encoded" not in fileName and "decoded" not in fileName and "desktop.ini" not in fileName:
                encode(os.getcwd() + "\\" + input + "\\" + fileName, os.getcwd() + "\\" + input + "\\" + fileName +  ".encoded", sys.argv[2], maskSize)
    else:
        if len(sys.argv) < 3:
            filename = 'chunks.data'
        else:
            filename = sys.argv[2]
        encode(input, input + ".encoded", filename)
