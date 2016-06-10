from pygame import *

class screen():
	""" back ground and sprite color """
	black = (0, 0, 0)
	white = (255, 255, 255)
	
	def __init__(self, caption = 'CHIP-8 EMULATOR', scale = 10):
		self.caption = caption
		self.scale = scale
		self.size = width, height = 64*scale, 32*scale

		self.scr = display.set_mode(self.size)
		display.set_caption(caption)

	def draw(self, x, y, c):
		draw.rect(self.scr, c, [x*self.scale, y*self.scale, self.scale, self.scale])

	def clrscr(self):
		self.scr.fill(self.black)
		
	def refresh(self, gfx):
		for x in range(64):
			for y in range(32):
				if gfx[x][y] == 1:
					self.draw(x, y, self.white)
				else:
					self.draw(x, y, self.black)
		display.flip()



		
