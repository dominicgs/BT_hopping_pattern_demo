#!/usr/bin/env python

# Copyright 2016 Dominic Spill, Michael Ossmann, Will Code

BT_NUM_CHANNELS = 79

class Piconet(object):
	def __init__(self, address):
		self.address = address
		self.sequence = []
		self.precalc()
		self.perm_table_init()
		#self.gen_hops()

	# do all the precalculation that can be done before knowing the address
	def precalc(self):
		# populate channel list
		# actual frequency is 2402 + channel[i] MHz
		self.channels = [
			(i * 2) % BT_NUM_CHANNELS
			for i in xrange(BT_NUM_CHANNELS)
		]
	
	
		# precalculate some of single_hop()/gen_hop()'s variables
		self.a1 = (self.address >> 23) & 0x1f
		self.b = (self.address >> 19) & 0x0f
		self.c1 = ((self.address >> 4) & 0x10) + \
			((self.address >> 3) & 0x08) + \
			((self.address >> 2) & 0x04) + \
			((self.address >> 1) & 0x02) + \
			(self.address & 0x01)
		self.d1 = (self.address >> 10) & 0x1ff
		self.e = ((self.address >> 7) & 0x40) + \
			((self.address >> 6) & 0x20) + \
			((self.address >> 5) & 0x10) + \
			((self.address >> 4) & 0x08) + \
			((self.address >> 3) & 0x04) + \
			((self.address >> 2) & 0x02) + \
			((self.address >> 1) & 0x01)
	
	# 5 bit permutation
	# assumes z is constrained to 5 bits, p_high to 5 bits, p_low to 9 bits
	def perm5(self, z, p_high, p_low):
		index1 = (0, 2, 1, 3, 0, 1, 0, 3, 1, 0, 2, 1, 0, 1)
		index2 = (1, 3, 2, 4, 4, 3, 2, 4, 4, 3, 4, 3, 3, 2)
	
		# bits of p_low and p_high are control signals
		p = [(p_low >> i) & 0x01 for i in xrange(9)]
		p.extend([(p_high >> i) & 0x01 for i in xrange(5)])
		
		# bit swapping will be easier with an array of bits
		z_bit = [(z >> i) & 0x01 for i in xrange(5)]
			
	
		# butterfly operations
		for i in xrange(13, 0, -1):
			# swap bits according to index arrays if control signal tells us to
			if (p[i]):
				tmp = z_bit[index1[i]]
				z_bit[index1[i]] = z_bit[index2[i]]
				z_bit[index2[i]] = tmp
	
		# reconstruct output from rearranged bits
		output = sum([z_bit[i] << i for i in xrange(5)])
		return output
	
	def perm_table_init(self):
		# populate perm_table for all possible inputs
		self.perm_table = [[[self.perm5(z, p_high, p_low) for p_low in xrange(0x200)]for p_high in xrange(0x20)] for z in xrange(0x20)]
	
	# drop-in replacement for perm5() using lookup table
	def fast_perm(self, z, p_high, p_low):
		return self.perm_table[z][p_high][p_low]

	# generate the complete hopping sequence
	def gen_hops(self):
		# a, b, c, d, e, f, x, y1, y2 are variable names used in section 2.6 of the spec
		# sequence index = clock >> 1
		f = base_f = 0
		for h in xrange(0x04):
			#clock bits
			for i in xrange(0x20):
				# clock bits 21-25
				a = self.a1 ^ i
				for j in xrange(0x20):
					# clock bits 16-20
					c = self.c1 ^ j
					c_flipped = c ^ 0x1f
					for k in xrange(0x200):
						# clock bits 7-15
						d = self.d1 ^ k
						for x in xrange(0x20):
							# clock bits 2-6
							perm_in = ((x + a) % 32) ^ self.b
							# y1 (clock bit 1) = 0, y2 = 0
							perm_out = self.fast_perm(perm_in, c, d)
							channel = self.channels[(perm_out + self.e + f) % BT_NUM_CHANNELS]
							#self.sequence.append(channel)
							yield channel
							
							# y1 (clock bit 1) = 1, y2 = 32
							perm_out = self.fast_perm(perm_in, c_flipped, d)
							channel = self.channels[(perm_out + self.e + f + 32) % BT_NUM_CHANNELS]
							#self.sequence.append(channel)
							yield channel
						base_f = base_f + 16
						f = base_f % BT_NUM_CHANNELS

if __name__ == '__main__':
	import sys
	if len(sys.argv) < 2:
		print "Using default address of 00:00:65:87:CB:A9"
		address = 0x6587cba9
	else:
		address = int(sys.argv[1].replace(':',''), 16)
	pn = Piconet(address)
	for x, channel in enumerate(pn.gen_hops()):
		print "%02d" % channel
		if x > 20:
			sys.exit()