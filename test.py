from cpu import *
import time

def pause():
	raw_input('[paused]')

c = cpu('./roms/INVADERS')
while 1:
	c.gfx_dump()
	c.context_dump()
	c.run(2)
	pause()	
	
