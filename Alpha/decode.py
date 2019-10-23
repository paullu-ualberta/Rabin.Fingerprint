#
# decode.py - Uses chunks.data and a .encoded file to recreate original file
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

# hbdm_decodeV4.py
import sys

def read_encoded(inputFile):
    try:
        data = open(inputFile, 'rb').read()
    except:
        print( "File open/read failed: %s" % (inputFile) )
        sys.exit(-1)

    chunk_lst = []
    byteIndex = 0
    while byteIndex < len(data):
        chunk_lst.append(data[byteIndex : byteIndex + 23])
        byteIndex += 23
    return chunk_lst

def decode(inputFile, commonFile):
    chunk_lst = read_encoded(inputFile)
    byteIndex = 0
    try:
        fileBytes = open(commonFile, 'rb').read()
    except:
        print( "File open/read failed: %s" % (commonFile) )
        sys.exit(-1)

    chunk_dict = {}
    while byteIndex < len(fileBytes):
        theHash = fileBytes[byteIndex : byteIndex + 20]
        byteIndex += 20
        length = fileBytes[byteIndex : byteIndex + 3]
        byteIndex += 3
        chunk = bytearray(b'')
        while len(chunk) < int.from_bytes(length, 'big'):
            chunk.append(fileBytes[byteIndex])
            byteIndex += 1
        chunk_dict[theHash + length] = chunk

    return chunk_lst, chunk_dict

def decode_to_file(inputFile, outputFile, commonFile):
    chunk_lst, chunk_dict = decode(inputFile, commonFile)
    try:
        fileObject = open(outputFile, 'wb')
    except:
        print( "File open/write failed: %s" % (outputFile) )
        sys.exit(-1)


    for pair in chunk_lst:
        fileObject.write(chunk_dict[pair])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        filename = 'chunks.data'
    else:
        filename = sys.argv[2]
    decode_to_file(sys.argv[1] + ".encoded", sys.argv[1] + ".decoded", filename)
