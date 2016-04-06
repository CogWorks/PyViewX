from __future__ import division
from pyviewx.client import Dispatcher
from twisted.internet.task import LoopingCall
import pygame

def mean(l): return sum(l) / len(l)

class Validator(object):

    d = Dispatcher()

    def __init__(self, client, screen=None, worldsurf=None, escape=False, reactor=None, params=None, eye=0):
        if reactor is None:
            from twisted.internet import reactor

        self._init_params(params)
        self.eye = eye
        self.reactor = reactor
        self.escape = escape
        self.client = client
        self.client.addDispatcher(self.d)
        self._init_screen(screen)
        self.swidth, self.sheight = self.screen.get_size()
        self.center_x = int(self.swidth / 2)
        self.center_y = int(self.sheight / 2)
        if worldsurf:
            self.worldsurf = worldsurf
        else:
            self.worldsurf = self.screen.copy()
        self.worldsurf_rect = self.worldsurf.get_rect()


        pygame.mouse.set_visible(False)

        self.complete = False
        self.lc = None
        self._reset()
    def _init_params(self, params):
          self.size = 15
          self.width = 3
          self.frames = 60
          self.tolerance = 50
          self.frames_tolerance = 2
          self.hit_color = (0,115,10)
          self.timeout = 600
          self.miss_color = (255,255,255)
          self.bg_color = (0,0,0)
          if params:
               if 'miss_color' in params:
                    self.miss_color = params['miss_color']
               if 'bg_color' in params:
                    self.bg_color = params['bg_color']
               if 'size' in params:
                    self.size = params['size']
               if 'width' in params:
                    self.width = params['width']
               if 'frames' in params:
                    self.frames = params['frames']
               if 'tolerance' in params:
                    self.tolerance = params['tolerance']
               if 'frames_tolerance' in params:
                    self.frames_tolerance = params['frames_tolerance']
               if 'hit_color' in params:
                    self.hit_color = params['hit_color']
               if 'timeout' in params:
                    self.timeout = params['timeout']





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
        self.frames_count = 0
        self.frames_miss = 0
        self.validationResults = []
        self.gaze = []
        self.log = "INCOMPLETE"

        self.state = 0


    def _display(self):
        if self.exist == False:
              self.worldsurf.fill((0, 0, 0))
        else:
            r = pygame.Rect(0, 0, 0, 0)
            r.width = int((20 * self.swidth) / 100)
            r.height = int((30 * self.sheight) / 100)
            r.center = (self.center_x, self.center_y)
            pygame.draw.rect(self.worldsurf, self.bg_color, r, 0)
        if self.state < 2:
               fixcross_color = self.hit_color if self.frames_count > 0 and self.frames_miss == 0 else self.miss_color

               pygame.draw.line(self.worldsurf, fixcross_color, (self.center_x - self.size, self.center_y), (self.center_x + self.size, self.center_y), self.width)
               pygame.draw.line(self.worldsurf, fixcross_color, (self.center_x, self.center_y - self.size), (self.center_x, self.center_y + self.size), self.width)


        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        # pygame.display.flip()



    def _hit(self):
        if self.gaze:
            if self.check_hit(self.gaze):
                self.frames_count += 1
                self.frames_miss = 0
            else:
                self.frames_miss += 1
        if self.frames_miss >= self.frames_tolerance:
            self.frames_count = 0
            if self.frames_miss >= self.timeout:
                self.state = 1
                self.client.cancelCalibration()
                self.log = "TIMEOUT"
                self.complete = True
                self.lc.stop()
                return

        if self.frames_count >= self.frames:
            self.gameover_fixation = True
            self.state = 1
            self.client.acceptCalibrationPoint()
            self.log = "COMPLETE"




    def _update(self):
        self._display()
        self._hit()
        if self.state == 2:
            self.complete = True
            self.lc.stop()
            return



        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if self.escape and event.key == pygame.K_ESCAPE:
                    if self.lc:
                        self.log = "OVERRIDE"
                        self.lc.stop()
                        return
                if event.key == pygame.K_t:
                    self.client.acceptCalibrationPoint()
                    self.log = "OVERRIDE"
                    self.complete = True
                    self.lc.stop()
                    return


    def check_hit(self, gaze):
        return ((int(gaze[0])-self.center_x)**2 + (int(gaze[1])-self.center_y)**2) <= ((self.size+self.tolerance)**2)


    def start(self, stopCallback, *args, **kwargs):
#         self.client.setDataFormat('%TS %ET %SX %SY %DX %DY %EX %EY %EZ')
        if self.exist == False:
            self.client.startDataStreaming()
        else:
            self.client.cancelCalibration()
        self.client.validateCalibrationAccuracyExtended(self.center_x, self.center_y)
        self.lc = LoopingCall(self._update)
        dd = self.lc.start(1.0 / 30)
        if not stopCallback:
            stopCallback = self.stop
        dd.addCallback(stopCallback, self.validationResults, self.log, *args, **kwargs)


    def stop(self, lc):
        self.reactor.stop()
        pygame.quit()

    @d.listen('ET_SPL')
    def iViewXEvent(self, inResponse):
        self.ts = int(inResponse[0])
        self.gaze = map(float, [inResponse[2], inResponse[4]])
        self.eye_position = map(float, inResponse[10:])

    @d.listen('ET_VLX')
    def iViewXEvent(self, inResponse):
        if inResponse != []:
            self.state = 2
            # print inResponse
            self.validationResults.append(inResponse)
