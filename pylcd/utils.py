# Copyright (C) 2013 Julian Metzler
# See the LICENSE file for the full license.

def bool_list_to_mask(list):
	mask = 0
	for i in range(len(list)):
		if bool(int(list[i])):
			mask += 2 ** i
	return mask

def nibble_to_mask(backend, nibble, data):
	l = [False] * 8
	l[backend.PIN_D4 - 1] = nibble[3]
	l[backend.PIN_D5 - 1] = nibble[2]
	l[backend.PIN_D6 - 1] = nibble[1]
	l[backend.PIN_D7 - 1] = nibble[0]
	if data:
		l[backend.PIN_RS - 1] = True
	mask = bool_list_to_mask(l)
	return mask

def value_to_byte(value):
	assert value >= 0
	assert value <= 255
	b = bin(value)[2:10]
	b = "0" * (8 - len(b)) + b
	bits = tuple([bit == "1" for bit in list(b)])
	return bits

def value_to_nibbles(value):
	byte = value_to_byte(value)
	return (byte[:4], byte[4:])

def byte_to_value(byte):
	b = "".join([str(int(item)) for item in byte])
	value = int(b, 2)
	return value