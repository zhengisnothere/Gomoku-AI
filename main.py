import random
import sys

import pygame

pygame.init()
board_w, board_h = 15, 15
cell_size = 30
screen_w, screen_h = board_w * cell_size, board_h * cell_size
screen = pygame.display.set_mode((screen_w, screen_h))
pygame.display.set_caption('Gomoku')
font = pygame.font.SysFont('Arial', 10)

class Checkerboard:
  def __init__(self, x, y, bw, bh, cell_size, p1_ai=False, p2_ai=False):
    self.x = x
    self.y = y
    self.bw = bw
    self.bh = bh
    self.cell_size = cell_size
    self.checkerboard = [0 for _ in range(bw * bh)]
    self.p1_weights = [0 for _ in range(bw * bh)]
    self.p2_weights = [0 for _ in range(bw * bh)]
    self.p1_ai = p1_ai
    self.p2_ai = p2_ai
    self.create_board()
    self.player_index = 1
    self.player_moving = True
    self.pressed = False
    self.last_pressed = False
    self.ai_think_time = 500

  def create_board(self):
    bw, bh = self.bw, self.bh
    cell_size = self.cell_size
    self.board = pygame.Surface((bw * cell_size, bh * cell_size))
    self.board.fill((255, 255, 255))
    for iy in range(bh):
      pygame.draw.line(self.board, (0, 0, 0), (0, iy * cell_size), (bw * cell_size, iy * cell_size))
    for ix in range(bw):
      pygame.draw.line(self.board, (0, 0, 0), (ix * cell_size, 0), (ix * cell_size, bh * cell_size))
    pygame.draw.circle(self.board, (255, 0, 0), (bw * cell_size / 2, bh * cell_size / 2), 2)

  def draw(self, screen):
    screen.blit(self.board, (self.x, self.y))
    self.draw_checkers(screen)

  def draw_checkers(self, screen):
    for iy in range(self.bh):
      for ix in range(self.bw):
        checker = self.checkerboard[iy * self.bw + ix]
        color = (0, 0, 0) if checker == 1 else (240, 240, 240)
        if checker != 0:
          x = self.x + ix * self.cell_size + self.cell_size / 2
          y = self.y + iy * self.cell_size + self.cell_size / 2
          pygame.draw.circle(screen, color, (x, y), self.cell_size / 2 - 2)
          pygame.draw.circle(screen, (0, 0, 0), (x, y), self.cell_size / 2 - 2, 1)
        else:
          weight1 = self.p1_weights[iy * self.bw + ix]
          weight2 = self.p2_weights[iy * self.bw + ix]
          w1t = font.render(str(weight1), True, (255, 0, 0))
          w2t = font.render(str(weight2), True, (0, 0, 255))
          x = self.x + ix * self.cell_size + self.cell_size / 2
          y = self.y + iy * self.cell_size + self.cell_size / 2
          screen.blit(w1t, (x - self.cell_size / 2 + 4, y - self.cell_size / 2))
          screen.blit(w2t, (x + self.cell_size / 2 - 10, y - self.cell_size / 2))

  def place_checker(self, x, y, checker):
    self.checkerboard[self.bh * y + x] = checker

  def ai_move(self, player_index):
    self.pressed = pygame.mouse.get_pressed()[0]
    if not self.pressed and self.last_pressed:
      self_weight = self.p1_weights if player_index == 1 else self.p2_weights
      opponent_weight = self.p2_weights if player_index == 1 else self.p1_weights
      attack = max(self_weight) >= max(opponent_weight)
      if attack:
        max_weights = [i for i, w in enumerate(self_weight) if w == max(self_weight)]
        max_weight_index = random.choice(max_weights)
      else:
        max_weights = [i for i, w in enumerate(opponent_weight) if w == max(opponent_weight)]
        max_weight_index = random.choice(max_weights)
      ix = max_weight_index % self.bw
      iy = max_weight_index // self.bw
      self.place_checker(ix, iy, player_index)
      self.player_moving = False
    self.last_pressed = self.pressed

  def human_move(self, player_index):
    self.pressed = pygame.mouse.get_pressed()[0]
    if not self.pressed and self.last_pressed:
      mx, my = pygame.mouse.get_pos()
      ix, iy = (mx - self.x) // self.cell_size, (my - self.y) // self.cell_size
      if 0 <= ix <= self.bw - 1 and 0 <= iy <= self.bh - 1 and self.checkerboard[self.bh * iy + ix] == 0:
        self.place_checker(ix, iy, player_index)
        self.player_moving = False
    self.last_pressed = self.pressed

  def calc_weight_one_dir(self, x, y, dx, dy, player_index):
    # 反方向连续子权重计算错误
    ix, iy = x, y
    weight = 0
    checker = player_index
    counter = 1
    while checker == player_index:
      ix += dx
      iy += dy
      if 0 <= ix < self.bw and 0 <= iy < self.bh:
        checker = self.checkerboard[self.bh * iy + ix]
      else:
        checker = 3 - player_index
      if checker == player_index:
        weight += counter
        counter += 1
      elif checker == 3 - player_index:
        weight -= 1
    return weight

  def update_weight(self, player_index):
    for y in range(self.bh):
      for x in range(self.bw):
        checker = self.checkerboard[self.bh * y + x]
        weight = 0
        if checker == 0:
          for iy in range(-1, 2):
            for ix in range(-1, 2):
              if 0 <= x + ix < self.bw and 0 <= y + iy < self.bh:
                checker = self.checkerboard[self.bh * (y + iy) + (x + ix)]
                if checker == player_index:
                  weight += self.calc_weight_one_dir(x, y, ix, iy, player_index)
                elif checker == 3 - player_index:
                  weight -= 1
        if player_index == 1:
          self.p1_weights[self.bh * y + x] = weight
        else:
          self.p2_weights[self.bh * y + x] = weight

  def update(self):
    if 0 in self.checkerboard:
      if self.player_index == 1:
        if self.p1_ai:
          self.ai_move(self.player_index)
        else:
          self.human_move(self.player_index)
      else:
        if self.p2_ai:
          self.ai_move(self.player_index)
        else:
          self.human_move(self.player_index)
      self.update_weight(1)
      self.update_weight(2)
      if not self.player_moving:
        self.player_index = 3 - self.player_index
        self.player_moving = True

checkerboard = Checkerboard(0, 0, board_w, board_h, cell_size, False, False)

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()
  screen.fill((0, 0, 0))

  checkerboard.update()
  checkerboard.draw(screen)

  pygame.display.update()
