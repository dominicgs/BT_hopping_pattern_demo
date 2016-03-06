#!/usr/bin/env python

# Copyright 2016 Mike Ryan

class Connection(object):
	def __init__(self, hop_increment, channel_map=0x1fffffffff):
		self.hop_increment = hop_increment

		self.used_channels = []
		self.remap_index = []
		for i in range(37):
			if channel_map & (1 << (36 - i)):
				self.used_channels.append(True)
				self.remap_index.append(i)
			else:
				self.used_channels.append(False)

	def _index_to_phys(self, index):
		if index < 11:
			return 2404 + index * 2
		else:
			return 2406 + index * 2

	# generate the complete hopping sequence
	def gen_hops(self):
		unmapped_channel = 0
		while True:
			if not self.used_channels[unmapped_channel]:
				unmapped_channel = self.remap_index[unmapped_channel % len(self.remap_index)]
			yield self._index_to_phys(unmapped_channel), True
			unmapped_channel = (unmapped_channel + self.hop_increment) % 37
