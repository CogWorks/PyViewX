from __future__ import division
from pyviewx.client import Dispatcher
from twisted.internet.task import LoopingCall
import pygame

def mean(l): return sum(l) / len(l)

class Validator(object):

	d = Dispatcher()

	def __init__(self, client, screen=None, escape=False, reactor=None, params=None, eye=0):
		if reactor is None:
			from twisted.internet import reactor
		self._init_params(params)
		self.eye = eye
		self.reactor = reactor
		self.escape = escape
		self.client = client
		self.client.addDispatcher(self.d)
		self._init_screen(screen)
		self.width, self.height = self.screen.get_size()
		self.center_x = int(self.width / 2)
		self.center_y = int(self.height / 2)
		self.worldsurf = self.screen.copy()
		self.worldsurf_rect = self.worldsurf.get_rect()


		pygame.mouse.set_visible(False)

		self.complete = False
		self.lc = None
		self._reset()
	def _init_params(self, params):
  		if params:
   			if 'gameover_fixcross_size' in params:
    				self.gameover_fixcross_size = params['gameover_fixcross_size']
   			if 'gameover_fixcross_width' in params:
    				self.gameover_fixcross_width = params['gameover_fixcross_width']
   			if 'gameover_fixcross_frames' in params:
    				self.gameover_fixcross_frames = params['gameover_fixcross_frames']
   			if 'gameover_fixcross_tolerance' in params:
    				self.gameover_fixcross_tolerance = params['gameover_fixcross_tolerance']  
   			if 'gameover_fixcross_frames_tolerance' in params:
    				self.gameover_fixcross_frames_tolerance = params['gameover_fixcross_frames_tolerance']
   			if 'gameover_fixcross_color' in params:
    				self.gameover_fixcross_color = params['gameover_fixcross_color'] 
   			if 'gameover_fixcross_timeout' in params:
    				self.gameover_fixcross_timeout = params['gameover_fixcross_timeout']         
	  	else:
    			self.gameover_fixcross_size = 15
    			self.gameover_fixcross_width = 3
    			self.gameover_fixcross_frames = 30
    			self.gameover_fixcross_tolerance = 50
    			self.gameover_fixcross_frames_tolerance = 2
    			self.gameover_fixcross_color = (0,115,10)
    			self.gameover_fixcross_timeout = 600 
	       
	
	
	def _init_screen(self, screen):
		if screen:
			self.screen = screen
			self.exist = True
		else:
			pygame.display.init()
			pygame.font.init()
			self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
			self.exist = False

	def _reset(self):
		self.gameover_fixcross_frames_count = 0
		self.gameover_fixcross_frames_miss = 0
		self.validationResults = []
		self.log = "INCOMPLETE"
		self.state = 0

# 	def _draw_text(self, text, font, color, loc):
# 		t = font.render(text, True, color)
# 		tr = t.get_rect()
# 		tr.center = loc
# 		self.worldsurf.blit(t, tr)

	def _display(self):
		if self.exist == True:
	  		self.worldsurf.fill((255, 255, 255))
		if self.state == 0:
   			fixcross_color = self.gameover_fixcross_color if self.gameover_fixcross_frames_count > 0 and self.gameover_fixcross_frames_miss == 0 else self.border_color

   			pygame.draw.line(self.worldsurf, fixcross_color, (self.center_x - self.gameover_fixcross_size, self.center_y), (self.center_x + self.gameover_fixcross_size, self.center_y), self.gameover_fixcross_width)
   			pygame.draw.line(self.worldsurf, fixcross_color, (self.center_x, self.center_y - self.gameover_fixcross_size), (self.center_x, self.center_y + self.gameover_fixcross_size), self.gameover_fixcross_width)
   

# 			if not self.currentPoint < 0:
# 				pygame.draw.circle(self.worldsurf, (255, 255, 0), self.calibrationPoints[self.currentPoint], 8)
# 				pygame.draw.circle(self.worldsurf, (0, 0, 0), self.calibrationPoints[self.currentPoint], 2)
		if self.state > 0:
			f = pygame.font.Font(None, 28)
   
			if not self.validationResults:
				self._draw_text('Calculating validation accuracy %s' , f, (255, 255, 255), (self.center_x, self.center_y))
			else:
				self._draw_text(' '.join(self.validationResults[0]), f, (255, 255, 255), (self.center_x, self.center_y))
				if len(self.validationResults) > 1:
					self._draw_text(' '.join(self.validationResults[1]), f, (255, 255, 255), (self.center_x, self.center_y + 30))
				self._draw_text("Press 'R' to revalidate, press 'Space Bar' to continue...", f, (255, 255, 255), (self.center_x, self.height - 60))
		self.screen.blit(self.worldsurf, self.worldsurf_rect)
		pygame.display.flip()



	def _hit(self):
		if check_hit(self.gaze):
			self.gameover_fixcross_frames_count += 1
			self.gameover_fixcross_frames_miss = 0
		else:
			self.gameover_fixcross_frames_miss += 1
		if self.gameover_fixcross_frames_miss >= self.gameover_fixcross_frames_tolerance:
			self.gameover_fixcross_frames_count = 0 
			if self.gameover_fixcross_frames_miss >= self.gameover_fixcross_timeout:
				self.state = 1
				self.client.cancelCalibration()
				self.log = "TIMEOUT"
		if self.gameover_fixcross_frames_count >= self.gameover_fixcross_frames:
			self.gameover_fixation = True
			self.state = 1
			self.client.acceptCalibrationPoint()
			self.log = "COMPLETE"
   

	def check_hit(self, gaze):
		((gaze[0]-self.center_x)**2 + (gaze[1]-self.center_y)**2) <= ((self.gameover_fixcross_size+self.gameover_fixcross_tolerance)**2
  
  
  
	def _update(self):
		self._hit()
		self._display()
  
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if self.escape and event.key == pygame.K_ESCAPE:
					if self.lc:
					 self.log = "OVERRIDE"
						self.lc.stop()
						return
# 				if self.state == 1:
# 					if event.key == pygame.K_SPACE:
# 						self.client.acceptCalibrationPoint()
# 				elif self.state == 2:
# 					if event.key == pygame.K_r:
# 						self._reset()
#       self.client.validateCalibrationAccuracyExtended(self.center_x, self.center_y)_
# # 						self.client.startCalibration(9, self.eye)
# 					elif event.key == pygame.K_SPACE:
# 						self.complete = True
# 						self.lc.stop()

	def start(self, stopCallback, wait=1, randomize=1, auto=0, speed=1, level=3, points=9, *args, **kwargs):
# 		self.client.setDataFormat('%TS %ET %SX %SY %DX %DY %EX %EY %EZ')
		if self.exist == False:
		 	self.client.startDataStreaming()
		
		self.client.validateCalibrationAccuracyExtended(self.center_x, self.center_y)
		self.lc = LoopingCall(self._update)
		dd = self.lc.start(1.0 / 30)
		if not stopCallback:
			stopCallback = self.stop
		dd.addCallback(stopCallback, self.log, self.validationResults, *args, **kwargs)

	def stop(self, lc):
		self.reactor.stop()
		pygame.quit()

	@d.listen('ET_SPL')
	def iViewXEvent(self, inResponse):
		self.ts = int(inResponse[0])
		self.gaze = int(inResponse[2:3])
		self.eye_position = map(float, inResponse[10:])

# 	@d.listen('ET_CAL')
# 	def iViewXEvent(self, inResponse):
# 		self.calibrationPoints = [None] * int(inResponse[0])
# 
# 	@d.listen('ET_CSZ')
# 	def iViewXEvent(self, inResponse):
# 		pass
# 
# 	@d.listen('ET_PNT')
# 	def iViewXEvent(self, inResponse):
# 		self.calibrationPoints[int(inResponse[0]) - 1] = (int(inResponse[1]), int(inResponse[2]))
# 
# 	@d.listen('ET_CHG')
# 	def iViewXEvent(self, inResponse):
# 		self.currentPoint = int(inResponse[0]) - 1

	@d.listen('ET_VLX')
	def iViewXEvent(self, inResponse):
		self.state = 2
		self.validationResults.append(inResponse)
# 
# 	@d.listen('ET_CSP')
# 	def iViewXEvent(self, inResponse):
# 		pass
# 
# 	@d.listen('ET_FIN')
# 	def iViewXEvent(self, inResponse):
# 		self.state = 1
# 		self.client.requestCalibrationResults()
# 		self.client.validateCalibrationAccuracy()
