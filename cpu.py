from ctypes import *
from random import randint
from pygame import mixer
from pygame import key

def debug_print(s):
	print '[Debug]', s

def pause():
	raw_input('[paused]')

class cpu():
	#4K of ram
	memory = (c_ubyte * 4096)()

	"""
	0x000-0x1FF - Chip 8 interpreter (contains font set in emu)
	0x050-0x0A0 - Used for the built in 4x5 pixel font set (0-F)
	0x200-0xFFF - Program ROM and work RAM
	"""

	#memory for graphic
	#gfx = (c_ubyte * (64*32))() 
	gfx = (64*(c_ubyte * 32))()

	#the stack
	stack = (c_ushort*16)() 
	
	#register		
	idx = c_ushort() #index
	pc = c_ushort(512)
	sp = c_ushort() #stack pointer
	#general purpose registers
	v = (c_ubyte * 16)()

	#timers
	delay_timer = c_ubyte(0xff)
	sound_timer = c_ubyte(0xff)

	"""Finally, the Chip 8 has a HEX based keypad (0x0-0xF), you can use an array to store the current state of the key """
	keys = (c_ubyte*16)()

	""" scr is the pygame screen """
	def __init__(self, rom_file, scr): 
		debug_print('Loading %s' % rom_file)
		try:
			f = open(rom_file, 'rb')
		except:
			print 'Can not open rom file'
			return
		 
		self.scr = scr
		""" sound """
		mixer.init(44100, -16,2,2048)

		""" Load program into memory """
		i = 0
		t = f.read(1)
		while t:
			self.memory[i+512] = ord(t)
			t = f.read(1)
			i += 1

		font_set = (c_ubyte*80) (
			0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
			0x20, 0x60, 0x20, 0x20, 0x70, # 1
			0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
			0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
			0x90, 0x90, 0xF0, 0x10, 0x10, # 4
			0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
			0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
			0xF0, 0x10, 0x20, 0x40, 0x40, # 7
			0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
			0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
			0xF0, 0x90, 0xF0, 0x90, 0x90, # A
			0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
			0xF0, 0x80, 0x80, 0x80, 0xF0, # C
			0xE0, 0x90, 0x90, 0x90, 0xE0, # D
			0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
			0xF0, 0x80, 0xF0, 0x80, 0x80  # F
		)
		""" Load fonts into memory """
		for i in range(0, 80):
			self.memory[i] = font_set[i]

		return

	def op_0(self, args):
		if args[4] == 0xe0:
			self.scr.clrscr()
		elif args[4] == 0xee:
			self.sp.value -= 1
			self.pc.value = self.stack[self.sp.value]
		else:
			debug_print('op_0 invalid opcode')
			return 
		self.ni()

	def op_1(self, args):
		""" Jumps to address NNN """
		self.pc.value = args[5]

	def op_2(self, args):
		""" Calls subroutine at NNN """
		self.stack[self.sp.value] = self.pc.value
		self.sp.value += 1
		self.pc.value = args[5]

	def op_3(self, args):
		""" Skips the next instruction if VX equals NN """
		if self.v[args[2]] == args[4]:
			self.ni()
		self.ni()

	def op_4(self, args):
		""" Skips the next instruction if VX doesn't equal NN """
		if self.v[args[2]] != args[4]:
			self.ni()
		self.ni()

	def op_5(self, args):
		""" Skips the next instruction if VX equals VY """
		if self.v[args[2]] == self.v[args[1]]:
			self.ni()
		self.ni()

	def op_6(self, args):
		""" Sets VX to NN """
		self.v[args[2]] = args[4]
		self.ni()
				
	def op_7(self, args):
		""" Adds NN to VX """
		self.v[args[2]] += args[4]
		self.ni()

	def op_8(self, args):
		if args[0] == 0:
			""" Sets VX to the value of VY """
			self.v[args[2]] = self.v[args[1]]
		elif args[0] == 1:
			""" Sets VX to VX or VY """
			self.v[args[2]] |= self.v[args[1]]
		elif args[0] == 2:
			""" Sets VX to VX and VY """
			self.v[args[2]] &= self.v[args[1]]
		elif args[0] == 3:
			""" Sets VX to VX xor VY """
			self.v[args[2]] ^= self.v[args[1]]
		elif args[0] == 4:
			""" Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't """
			if self.v[args[1]] > (0xff - self.v[args[2]]):
				self.v[0xf] = 1
			else:
				self.v[0xf] = 0
			self.v[args[2]] += self.v[args[1]]
		elif args[0] == 5:
			""" VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't """
			if self.v[args[1]] > self.v[args[2]]:
				self.v[0xf] = 0
			else:
				self.v[0xf] = 1
			self.v[args[2]] -= self.v[args[1]]
		elif args[0] == 6:
			""" Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift """
			self.v[0xf] = (self.v[args[2]] & 1)
			self.v[args[2]] >>= 1
		elif args[0] == 7:
			""" Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't """
			if self.v[args[2]] > self.v[args[1]]:
				self.v[0xf] = 0
			else:
				self.v[0xf] = 1
			self.v[args[2]] = self.v[args[1]] - self.v[args[2]]
		elif args[0] == 0xe:
			""" Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift """
			self.v[0xf] = (self.v[args[2]] & 0x80)
			self.v[args[2]] <<= 1
		else:
			debug_print('op_8 invalid opcode')
			raw_input('')
			return
		
		self.ni()
			
	def op_9(self, args):
		""" Skips the next instruction if VX doesn't equal VY """
		if self.v[args[2]] != self.v[args[1]]:
			self.ni()
		self.ni()

	def op_a(self, args):
		""" Sets I to the address NNN """
		self.idx.value = args[5]		
		self.ni()

	def op_b(self, args):
		""" Jumps to the address NNN plus V0 """
		self.pc.value = args[3] + self.v[0]		

	def op_c(self, args):
		""" Sets VX to the result of a bitwise and operation on a random number and NN """
		self.v[args[2]] = (randint(0, 255) & args[4])
		self.ni()

	def op_d(self, args):
		"""
		Sprites stored in memory at location in index register (I), 8bits wide. Wraps around the screen. If when drawn, clears a pixel, 		register VF is set to 1 otherwise it is zero. All drawing is XOR drawing (i.e. it toggles the screen pixels). Sprites are drawn 		starting at position VX, VY. N is the number of 8bit rows that need to be drawn. If N is greater than 1, second line continues at 			position VX, VY+1, and so on. 
		"""
		x = self.v[args[2]]
		y = self.v[args[1]]
		height = args[0]
		pixel = c_ushort()

		self.v[0xf] = 0;
		for yline in range(height):
			pixel.value = self.memory[self.idx.value+yline]
			for xline in range(8):
				if (pixel.value & (0x80 >> xline)) != 0:
					if self.gfx[(x+xline)%64][(y+yline)%32] == 1:
						self.v[0xf] = 1
					self.gfx[(x+xline)%64][(y+yline)%32] ^= 1
		self.scr.refresh(self.gfx)
		self.ni()

	def op_e(self, args):
		""" Skips the next instruction if the key stored in VX is pressed """
		if args[4] == 0x9e:
			if self.keys[args[2]] == 1:
				self.ni()
		elif args[4] == 0xa1:
			if self.keys[args[2]] == 0:
				self.ni()
		else:
			debug_print('invalid opcode')
			return
		self.ni()

	def op_f(self, args):
		""" Sets VX to the value of the delay timer """
		""" A key press is awaited, and then stored in VX """
		""" Sets the delay timer to VX """
		""" Sets the sound timer to VX """
		""" Adds VX to I """
		""" Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font """
		""" Stores the Binary-coded decimal representation of VX, with the most significant of three digits at the address in I, the middle 			digit at I plus 1, and the least significant digit at I plus 2. (In other words, take the decimal representation of VX, place the 			hundreds digit in memory at location in I, the tens digit at location I+1, and the ones digit at location I+2.) """
		""" Stores V0 to VX in memory starting at address I """
		""" Fills V0 to VX with values from memory starting at address I """
		if args[4] == 0x07:
			self.v[args[2]] = self.delay_timer.value
		elif args[4] == 0x0a:
			debug_print('not implemented')
			self.ni()
		elif args[4] == 0x15:
			self.delay_timer.value = self.v[args[2]]
		elif args[4] == 0x18:
			self.sound_timer.value = self.v[args[2]]
		elif args[4] == 0x1e:
			if self.v[args[2]] > (0xfff-self.idx.value):
				self.v[0xf] = 1
			else:
				self.v[0xf] = 0
			self.idx.value += self.v[args[2]]
		elif args[4] == 0x29:
			self.idx.value = self.v[args[2]]*5
		elif args[4] == 0x33:
			self.memory[self.idx.value] = self.v[args[2]] / 100
			self.memory[self.idx.value+1] = (self.v[args[2]] / 10) % 10
			self.memory[self.idx.value+2] = (self.v[args[2]] / 100) % 10
		elif args[4] == 0x55:	
			for i in range(0, args[2] + 1):
				self.memory[self.idx.value+i] = self.v[i]
		elif args[4] == 0x65:
			for i in range(0, args[2] + 1):
				self.v[i] = self.memory[self.idx.value+i]
		self.ni()

	def op_parse(self, op): 
		fo = (op & 0xf000)
		t = (op & 0x0f00)
		s = (op & 0x00f0)
		f = (op & 0x000f)
		word = s|f
		tri_byte = t|s|f
		fo >>= 12
		t >>= 8
		s >>= 4
	
		return [f, s, t, fo, word, tri_byte]
	
	def ni(self):
		""" next instruction """
		self.pc.value += 2
		
	def fetch(self):
		return self.memory[self.pc.value] << 8 | self.memory[self.pc.value + 1]

	def context_dump(self):
		print '[opcode]', hex(self.fetch())
		print '[pc]:', self.pc.value
		print '[sp]:', self.sp.value
		print '[idx]:', self.idx.value
		print '##stack##'
		for i in range(16):
			print '[', self.stack[i], ']',
		print '' 
		print '##general purporse registers##'
		for i in range(16):
			print '[v]'+str(i)+':', self.v[i]

	def set_keys(self, k):
		for i in range(len(k)):
			self.keys[k[i]] = 1

	def clear_keys(self, k):
		for i in range(len(k)):
			self.keys[k[i]] = 0


	def gfx_dump(self):
		print self.gfx[:64*3]
		
	def keys_dump(self):
		print self.keys[:]

	def beep(self):
		mixer.music.load('./beep.mp3')
		mixer.music.play(0)

	def run(self, number_of_cycles = 1):
		op_dict = {
			0: self.op_0, 1: self.op_1, 2: self.op_2, 3: self.op_3,
			4: self.op_4, 5: self.op_5, 6: self.op_6, 7: self.op_7,
			8: self.op_8, 9: self.op_9 ,0xa: self.op_a, 0xb: self.op_b,
			0xc: self.op_c,0xd: self.op_d, 0xe: self.op_e, 0xf: self.op_f
		}

		for i in range(number_of_cycles):
			""" fetch opcode """
			op = self.fetch()

			""" decode """
			args = self.op_parse(op)
			
			""" execute """
			op_dict[args[3]](args)
		
			if self.delay_timer.value > 0:
				self.delay_timer.value -= 1

			if self.sound_timer.value == 1:
				self.beep()
			if self.sound_timer.value > 0:
				self.sound_timer.value -= 1
				
			
	
	

