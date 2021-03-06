""" name conflict """
import time as t
import sys
from cpu import *
from screen import *

""" rom file """
rom_path = './roms/'
if len(sys.argv) >= 2:
	rom_file = rom_path + sys.argv[1]
else:
	rom_file = rom_path + 'PUZZLE'


""" init screen """
scr = screen('[CHIP-8 EMULATOR] -- l0stb1t')

""" init cpu """
chip8_cpu =  cpu(rom_file, scr)

while 1:
	chip8_cpu.run(1)
	t.sleep(0.005)


