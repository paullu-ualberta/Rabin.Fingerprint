#
# rabin_fingerprint.py - Uses Rabin fingerprinting to split a file (or stream
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

import random
from collections import deque
import os
import json
# import pdb

class fingerprinter:
    def __init__(self, d_size):
        self.window = pow(2, d_size + 1) - 1
        self.remainder = 0
        self.mask = 1 << d_size
        self.irreducible = irreducible_polynomial(d_size)

    def update(self, b): #Updates the remainder when supplied the next bit in the sequence
        self.remainder <<= 1 #Left shift the remainder
        self.remainder |= b #Append the new bit
        self.remainder &= self.window #Prevent the remainder from growing larger than needed
        if self.remainder & self.mask > 0:
            self.remainder ^= self.irreducible
        return self.remainder

    def flush(self):
        self.remainder = 0

class windowFingerprinter:
    def __init__(self, degree, irreducible):
        self.remainder = 0
        self.irreducible = irreducible
        self.window = deque([0] * (degree + 1))
        self.mask = 1 << degree
        self.pop_polynomial = divide_polynomial(1 << (degree + 1), self.irreducible)

    def update(self, bit):
        self.remainder <<= 1
        self.remainder |= bit
        if self.remainder & self.mask > 0:
            self.remainder ^= self.irreducible
        if self.window.pop() == 1:
            self.remainder ^= self.pop_polynomial
        self.window.appendleft(bit)
        return self.remainder

    def flush(self):
        self.remainder =  0

class byteWindowFingerprinter:
    def __init__(self, degree, irreducible):
        self.remainder = 0
        self.irreducible = irreducible
        self.leading_window_bit = 0
        self.window = deque([0] * (degree // 8)) #Degree must be divisible by 8
        self.incoming_table = compute_incoming_table(self.irreducible, degree)
        self.outgoing_table = compute_outgoing_table(self.irreducible, degree)
        self.degree = degree

    def update(self, byte):
        outgoing_byte = self.window.pop()
        new_leading_bit = outgoing_byte & 1
        outgoing_byte >>= 1
        outgoing_byte |= self.leading_window_bit << 7
        self.leading_window_bit = new_leading_bit
        self.remainder = (self.remainder << 8) | byte
        self.remainder = self.remainder ^ self.incoming_table[self.remainder >> self.degree] ^ self.outgoing_table[outgoing_byte]
        self.window.appendleft(byte)
        return self.remainder

    def flush(self):
        self.remainder =  0
        self.window = deque([0] * (self.degree // 8))

def compute_incoming_table(irreducible, degree):
    table = [0] * 256
    for byte in range(256):
        poly_sum = byte << degree
        irreducible <<= 7
        mask = 1 << (degree + 7)
        for i in range(8):
            if mask & poly_sum > 0:
                poly_sum ^= irreducible
            mask >>= 1
            irreducible >>= 1
        table[byte] = poly_sum
    return table

def compute_outgoing_table(irreducible, degree):
    table = [0] * 256
    divs = [0] * 8
    for i in range(8):
        divs[i] = divide_polynomial(1 << (i + degree + 1), irreducible)
    for byte in range(256):
        poly_sum = 0
        bcopy = byte
        for i in range(8):
            if byte & 1 > 0:
                poly_sum ^=  divs[i]
            byte >>= 1
        table[bcopy] = poly_sum
    return table


class byteWindowFingerprinter3_1:
    def __init__(self, irreducible, window_size):
        self.window = deque([0] * window_size)
        self.outgoing_table = compute_outgoing_table3_1(irreducible, window_size)
        self.fingerprint = 0
        self.degree = irreducible.bit_length() - 1
        self.mask = 1 << self.degree
        self.irreducible = irreducible

    def update(self, byte):
        self.fingerprint <<= 1
        if self.fingerprint & self.mask > 0:
            self.fingerprint ^= self.irreducible
        self.fingerprint ^= byte ^ self.outgoing_table[self.window.pop()]
        self.window.appendleft(byte)
        return self.fingerprint

    def flush(self):
        self.fingerprint = 0
        self.window = deque([0] * len(self.window))

def compute_outgoing_table3_1(irreducible, window_size):
    table = []
    for byte in range(255):
        r = byte
        mask = 1 << (irreducible.bit_length() - 1)
        for i in range(window_size):
            r <<= 1
            if r & mask > 0:
                r ^= irreducible
        table.append(r)
    return table

class byteWindowFingerprinter3_2:
    def __init__(self, window_size):
        self.window = deque([0] * window_size)
        self.fingerprint = 0
        self.window_size = window_size

    def update(self, byte):
        self.fingerprint = (self.fingerprint << 1) ^ byte ^ (self.window.pop() << self.window_size)
        self.window.appendleft(byte)
        return self.fingerprint

    def flush(self):
        self.fingerprint = 0
        self.window = deque([0] * len(self.window))


class byteWindowFingerprinter3_3:
    def __init__(self, irreducible, window_size, step_size):
        self.window = deque([0] * window_size)
        self.step_size = step_size
        self.outgoing_table = compute_outgoing_table3_3(irreducible, window_size)
        self.incoming_table = compute_incoming_table3_3(irreducible, step_size)
        self.fingerprint = 0
        self.degree = irreducible.bit_length() - 1
        self.mask1 = ((2 ** step_size) - 1) << self.degree
        self.mask2 = (2 ** self.degree) - 1
        self.irreducible = irreducible

    def update(self, bytes):
        # print(self.window)
        for byte in bytes:
            self.fingerprint = (self.fingerprint << 1) ^ byte ^ self.outgoing_table[self.window.pop()]
        top_n_bits = (self.mask1 & self.fingerprint) >> self.degree
        self.fingerprint = self.fingerprint & self.mask2 ^ self.incoming_table[top_n_bits]
        self.window.extendleft(bytes)
        return self.fingerprint

    def flush(self):
        self.fingerprint = 0
        self.window = deque([0] * len(self.window))

def compute_incoming_table3_3(irreducible, step_size):
    table = [0]
    rshift = irreducible.bit_length() - 1
    mask1 = (1 << rshift) - 1
    for bits in range(1, 2 ** step_size):
        bits <<= rshift
        b_len = bits.bit_length() - irreducible.bit_length()
        irreducible2 = irreducible << b_len
        mask2 = 1 << (bits.bit_length() - 1)
        for i in range(b_len + 1):
            if mask2 & bits > 0:
                bits ^= irreducible2
            s = bits >> rshift
            if s < len(table):
                table.append(bits & mask1 ^ table[s])
                break
            mask2 >>= 1
            irreducible2 >>= 1

    return table

def compute_outgoing_table3_3(irreducible, window_size):
    table = []
    for byte in range(255):
        r = byte
        mask = 1 << (irreducible.bit_length() - 1)
        for i in range(window_size):
            r <<= 1
            if r & mask > 0:
                r ^= irreducible
        table.append(r)
    return table

class byteWindowFingerprinter3_4:
    def __init__(self, irreducible, window_size, step_size, cut_value, mask_size):
        self.window = deque([0] * window_size)
        self.step_size = step_size
        self.outgoing_table = compute_outgoing_table3_4(irreducible, window_size)
        self.incoming_table = compute_incoming_table3_4(irreducible, step_size)
        self.fingerprint = 0
        self.degree = irreducible.bit_length() - 1
        self.mask1 = ((2 ** step_size) - 1) << self.degree
        self.mask2 = (2 ** self.degree) - 1
        self.irreducible = irreducible
        self.cut_value = cut_value
        self.f_mask = (1 << mask_size) - 1

    def update(self, bytes):
        fingerprints = []
        for byte in bytes:
            self.fingerprint = (self.fingerprint << 1) ^ byte ^ self.outgoing_table[self.window.pop()]
            fingerprints.append(self.fingerprint & self.mask2)
        top_n_bits = (self.mask1 & self.fingerprint) >> self.degree
        incoming = self.incoming_table[top_n_bits]
        self.fingerprint ^= incoming[-1]
        self.window.extendleft(bytes)
        for i in range(self.step_size):
            print(fingerprints[i] ^ incoming[i])

    def flush(self):
        self.fingerprint = 0
        self.window = deque([0] * len(self.window))

def compute_incoming_table3_4(irreducible, step_size):
    table = []
    m0 = 1 << (step_size - 1)
    ir0 = irreducible >> (irreducible.bit_length() - step_size)
    bits0 = 0
    max = 1 << step_size
    while bits0 < max:
        incoming = []
        bits1 = bits0
        ir1 = ir0
        m1 = m0
        sum = 0
        counter = 0
        while counter < step_size:
            if bits1 & m1 > 0:
                sum ^= irreducible
                bits1 ^= ir1
            incoming.append(sum)
            sum <<= 1
            m1 >>= 1
            ir1 >>= 1
            counter += 1
        table.append(incoming)
        bits0 += 1
    return table

def compute_outgoing_table3_4(irreducible, window_size):
    table = []
    for byte in range(255):
        r = byte
        mask = 1 << (irreducible.bit_length() - 1)
        for i in range(window_size):
            r <<= 1
            if r & mask > 0:
                r ^= irreducible
        table.append(r)
    return table

class byteWindowFingerprinter3:
    def __init__(self, irreducible, window_size):
        self.window = deque([0] * window_size)
        self.incoming_table = compute_incoming_table3(irreducible)
        self.outgoing_table = compute_outgoing_table3(irreducible, window_size)
        self.fingerprint = 0
        self.degree = irreducible.bit_length() - 1
        self.rshift = self.degree - 8
        self.mask1 = ((2**8) - 1) << (self.degree - 8)
        self.mask2 = (2**self.degree) - 1

    def update(self, byte):
        top_byte = self.mask1 & self.fingerprint
        self.fingerprint = self.incoming_table[top_byte >> self.rshift] \
                            ^ self.outgoing_table[self.window.pop()] ^ \
                            ((self.fingerprint << 8) | byte) & self.mask2
        self.window.appendleft(byte)
        return self.fingerprint

    def flush(self):
        self.fingerprint = 0
        self.window = deque([0] * len(self.window))

def compute_incoming_table3(irreducible):
    table = [0] * 2**8
    for byte in range(2**8):
        table[byte] = divide_polynomial(byte << (irreducible.bit_length() - 1), irreducible)
    return table

def compute_outgoing_table3(irreducible, window_size):
    table = [0] * (2**8)
    for byte in range(2**8):
        r = byte
        for i in range(window_size):
            r = divide_polynomial(r << 8, irreducible)
        table[byte] = r
    return table


class byteWindowFingerprinter2:
    def __init__(self, degree, irreducible, step_size):
        self.remainder = 0
        self.step_size = step_size
        self.irreducible = irreducible
        self.window = deque([0] * (degree // 8)) #Degree must be divisible by 8
        self.leading_window_bit = 0
        self.incoming_table = compute_incoming_table2(self.irreducible, degree, step_size)
        self.outgoing_table = compute_outgoing_table2(self.irreducible, degree, step_size)
        self.degree = degree

    def update(self, byte):
        # pdb.set_trace()
        self.remainder <<= self.step_size
        self.remainder |= byte
        top_byte = self.remainder >> self.degree
        self.remainder ^= self.incoming_table[top_byte]
        outgoing_byte = self.window.pop()
        new_leading_bit = outgoing_byte & 1
        outgoing_byte >>= 1
        outgoing_byte |= self.leading_window_bit << 7
        self.remainder ^= self.outgoing_table[outgoing_byte]
        self.leading_window_bit = new_leading_bit
        self.window.appendleft(byte)
        return self.remainder

    def flush(self):
        self.remainder =  0



def compute_incoming_table2(irreducible, degree, step_size):
    table = [0] * (2 ** step_size)
    for step in range(2 ** step_size):
        poly_sum = step << degree
        irreducible <<= step_size - 1
        mask = 1 << (degree + step_size - 1)
        for i in range(step_size):
            if mask & poly_sum > 0:
                poly_sum ^= irreducible
            if i == step_size - 1:
                break
            mask >>= 1
            irreducible >>= 1
        table[step] = poly_sum
        # if poly_sum != divide_polynomial(step << degree, irreducible):
        #     raise(str(step))
    return table

def compute_outgoing_table2(irreducible, degree, step_size):
    # pdb.set_trace()
    table = [0] * (2 ** step_size)
    divs = [0] * step_size
    for i in range(step_size):
        divs[i] = divide_polynomial(1 << (i + degree + 1), irreducible)
    for step in range(2 ** step_size):
        poly_sum = 0
        step_copy = step
        for i in range(step_size):
            if step & 1 > 0:
                poly_sum ^=  divs[i]
            step >>= 1
        table[step_copy] = poly_sum
    return table


def irreducible_polynomial(d): #Return a random polynomial of degree. Degree must be > 1
    random.seed(d)
    p = 1 #Start with leading coefficient of 1 so the polynomial is of degree d
    odd = False #is there an odd number of non-zero coefficients? Must be odd to be irreducible.
                #Starts False as the constant coefficient is always set to 1 at the end
    for i in range(d - 1):
        p = p << 1
        if bool(random.getrandbits(1)): #Randomly set coefficients to 1
            p = p | 1
            odd = not odd
    p = p << 1
    p = p | 1 #Add the trailing coefficient of one. Must have this for irreducible polynomials
    if not odd: #Make sure there's an odd number of non-zero coefficients
        index = random.randint(1, d - 1) #Get a random non-leading and non-trailing coefficient
        mask = 1 << index
        if p & mask == 0: #Swap the coefficient value to make an odd number
            p = p | mask #The bit is 0, set to 1
        else:
            p = p ^ mask #The bit is 1, set to 0
    return p


def divide_polynomial(p1, p2): #return p1 - p2. Assuming p1 >= p2
    mask = 1
    org_p2 = p2
    while mask <= p2: #Align the mask to be one bit higher than the leading coefficient of p2
        mask = mask << 1
    while mask <= p1: #Push the mask and p2 left untill the mask is one bit higher than p1, making
                      #the leading coefficients of p1 and p2 line up
        mask = mask << 1
        p2 = p2 << 1
    mask = mask >> 1 #The mask is now inline with the leading coefficient of p1
    while p2 >= org_p2:
        if mask & p1 > 0: #If there is a coefficient in the place being currently looked at
            p1 = p1 ^ p2 #Subtract p2 from p1
        mask = mask >> 1 #Move the mask and p2 over
        p2 = p2 >> 1
    return p1 #Return the remainder

def print_bits(x, n=0):
    lst = []
    while x > 0:
        lst.insert(0, str(x & 1) + " ")
        x = x >> 1
    while n > len(lst):
        lst.insert(0, "0 ")
    print("".join(lst))

def print_bit_len(x):
    n = 0
    while x > 0:
        n += 1
        x >>= 1
    print(n)

def eval(p):
    sum = 0
    while p > 0:
        sum = (sum + (p & 1)) % 2
        p = p >> 1
        return sum

if __name__ == "__main__":
    data = []
    for i in range(5):
        data.append(random.randint(0, 255))

    for x in "strabcdef":
        data.append(ord(x))

    for i in range(5):
        data.append(random.randint(0, 255))

    fingerprinter = byteWindowFingerprinter3(irreducible_polynomial(16), 3)
    for byte in data:
        f = fingerprinter.update(byte)
        print(chr(byte), byte)
        # for b in fingerprinter.window:
        #     print("B", b)
        print(f)
        # print(f, chr(fingerprinter.window[0]), chr(fingerprinter.window[1]))
