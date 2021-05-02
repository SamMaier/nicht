#!/usr/bin/python3
import random
from collections import deque

WINNING_SCORE = 10000

class Turn:
  def __init__(self):
    self.score = 0
    self.available_dice = 6

  def check_score(self, _dice_to_take):
    dice_to_take = sorted(_dice_to_take)
    assert len(dice_to_take) <= self.available_dice
    score = 0
    num_used_dice = 0
    if dice_to_take == [1,2,3,4,5,6]:
      score += 1500
      dice_to_take = []
      num_used_dice = 6
    for x in range (1,7):
      for num in reversed(range(3,7)):
        if dice_to_take.count(x) == num:
          for _ in range(num):
            dice_to_take.remove(x)
          score += (num - 2) * 100 * (x if x != 1 else (x * 10))
          num_used_dice += num
    for d in dice_to_take:
      if d == 1:
        score += 100
        num_used_dice += 1
      elif d == 5:
        score += 50
        num_used_dice += 1
    return (self.score + score, num_used_dice)

  def end_turn(self, dice):
    assert self.available_dice == len(dice)
    self.score = self.check_score(dice)[0]
    self.available_dice = -1

  def take_dice(self, dice):
    self.score, used_dice = self.check_score(dice)
    self.available_dice -= used_dice
    assert used_dice == len(dice)
    if self.available_dice == 0:
      self.available_dice = 6

  def roll_dice(self):
    result = []
    for i in range(self.available_dice):
      result.append(random.randint(1,6))
    if 1 in result or 5 in result: 
      return result
    for x in range(2,7):
      if result.count(x) >= 3:
        return result
    # Nicht!
    self.available_dice = -1
    self.score = 0
    return None


class Strategy:
  def __init__(self, fn):
    self.prediction_function = fn


  def make_decision(self, _dice, game, own_score, adj_score, max_score):
    def generate_all_picks(dice):
      def single_dice_gen(counts):
        if counts[0] < 3 and counts[0]:
          return [1]
        elif counts[4] < 3 and counts[4]:
          return [5]
        return None

        
      def double_dice_gen(counts):
        if counts[0] == 2:
          return [1,1]
        elif counts[0] == 1 and counts[4] and counts[4] < 3:
          return [1,5]
        elif counts[4] == 2:
          return [5,5]
        return None

      options = []
      counts = [dice.count(1), dice.count(2), dice.count(3), dice.count(4), dice.count(5), dice.count(6)]

      single = single_dice_gen(counts)
      if single:
        options.append(single)
      double = double_dice_gen(counts)
      if double:
        options.append(double)
       
      if 3 in counts:
        trip = [counts.index(3)+1]*3
        options.append(trip)
        if single:
          options.append(trip + single)
        if double:
          options.append(trip + double)

      if 4 in counts:
        quad = [counts.index(4)+1]*4
        options.append(quad)
        if single:
          options.append(quad + single)

      if 5 in counts:
        options.append([counts.index(5)+1]*5)

      return options


    def can_take_all_dice(dice):
      if dice == [1,2,3,4,5,6]:
        return True
      for x in [2,3,4,6]:
        if dice.count(x) == 1 or dice.count(x) == 2:
          return False
      return True


    dice = sorted(_dice)
    if can_take_all_dice(dice):
      return dice
    best_pick = None
    best_score, _ = game.check_score(dice)
    if best_score + own_score >= WINNING_SCORE:
      return generate_all_picks(dice)[-1]
    for pick in generate_all_picks(dice):
      score, num_used_dice = game.check_score(pick)
      available_dice = game.available_dice - num_used_dice
      prediction = self.prediction_function(available_dice, score, own_score, adj_score, max_score)
      if prediction > best_score:
        best_score = prediction
        best_pick = pick
        
    return best_pick


  def play_turn(self, own_score = 0, adjacent_score = 0, max_score = 0):
    game = Turn()
    while game.score + own_score < WINNING_SCORE:
      dice = game.roll_dice()
      if not dice:
        break
      dice_to_take = self.make_decision(dice, game, own_score, adjacent_score, max_score)
      if not dice_to_take:
        game.end_turn(dice)
        break
      else:
        game.take_dice(dice_to_take)
    return game.score


class Function:
  def __init__(self, m, b, own_score_c = 0, adj_score_c = 0, max_score_c = 0):
    self.m = m
    self.b = b
    self.own_score_c = own_score_c
    self.adj_score_c = adj_score_c
    self.max_score_c = max_score_c

  def call(self, x, own_score, adj_score, max_score):
    return (self.m*x) + (self.own_score_c*own_score) + (self.adj_score_c*adj_score) + (self.max_score_c*max_score) +self.b

  def mutate(self):
    m_m = random.uniform(-0.5,2)
    m_b = random.uniform(-0.5,2)
    m_o = random.uniform(-0.5,2)
    m_a = random.uniform(-0.5,2)
    m_mx = random.uniform(-0.5,2)
    return Function(self.m*m_m, self.b*m_b, self.own_score_c*m_o, self.adj_score_c*m_a, self.max_score_c*m_mx)

  def __str__(self):
    return "Function(" + str(self.m) + ", " + str(self.b) + ", " + str(self.own_score_c) +  ", " + str(self.adj_score_c) + ", " + str(self.max_score_c) + ")"
    
class Creature:
  def __init__(self, fns=None, zero_all = False):
    if fns is None:
      if zero_all:
        fns = [Function(random.uniform(-1.0,1.0), random.uniform(-200,1000)) for x in range(6)] 
      else:
        fns = [Function(random.uniform(-1.0,1.0), random.uniform(-200,1000), random.uniform(-1.0,1.0), random.uniform(-1.0,1.0), random.uniform(-1.0,1.0)) for x in range(6)] 
    assert len(fns) == 6
    self.fns = fns
    self.strat = Strategy(lambda d, s, o, a, m: fns[d-1].call(s, o, a, m))

  # Just to get non-competitve fitness
  def evaluate(self, n):
    val = 0
    for _ in range(n):
      val += self.strat.play_turn()
    return val

  def play_single_turn(self, own_score, adjacent_score, max_score):
    return self.strat.play_turn(own_score, adjacent_score, max_score)

  def gen_mutant(self):
    num_of_mutations = random.randint(1,5)
    fns = self.fns.copy()
    for _ in range(num_of_mutations):
      rand_loc = random.randint(0,5)
      fns[rand_loc] = fns[rand_loc].mutate()
      
    return Creature(fns)

  def __str__(self):
    return "Creature([" + ",\n".join([str(f) for f in self.fns]) + "])"
      
class Matchup:
  def __init__(self, creatures):
    self.creatures = creatures
    self.tally = [0]*len(creatures)

  def play_game(self, curr_turn):
    curr_turn -= 1 # Just setting up to increment right away
    scores = [0]*len(self.creatures)
    while scores[curr_turn] < WINNING_SCORE:
      curr_turn = (curr_turn + 1) % len(self.creatures)
      max_score = 0
      for i in range(len(scores)):
        if i == curr_turn:
          continue
        if scores[i] > max_score:
          max_score = scores[i]
      scores[curr_turn] += self.creatures[curr_turn].play_single_turn(scores[curr_turn], scores[(curr_turn + 1) % len(self.creatures)], max_score)
    return curr_turn
  
  def get_winner(self, n):
    for _ in range(n):
      for starter in range(len(self.creatures)):
        game_winner = self.play_game(starter)
        self.tally[game_winner] += 1
    return self.creatures[self.tally.index(max(self.tally))]

# 3 GREAT SOLO PLAYERs
#winner = Creature([Function(0.3576299561687098, 154.2237193766661),
#                   Function(0.17288173812000074, 158.557197887695),
#                   Function(0.5166028318225361, 201.1821159567643),
#                   Function(0.36904831949006134, 324.36493872116625),
#                   Function(0.9582939808572809, 339.67967962153176),
#                   Function(6.203658103193804, 3104.2754402961286)])
#runner_up = Creature([Function(0.3255622078722859, 282.3764025270552),
#                      Function(0.1444338457754891, 100.94515448510734),
#                      Function(0.6737078024802203, 102.4173438927874),
#                      Function(0.7078819299034407, 291.8847164506272),
#                      Function(0.42077984586108585, 455.61684598995805),
#                      Function(2.881268157958244, 1329.3238138727988)])
#random_guy = Creature([Function(-4.68340220354444, 1700.995221339466),
#                       Function(0.9368452001058065, -118.66996971082506),
#                       Function(0.7658604487203977, 102.4711566925939),
#                       Function(-0.14980383824231824, 374.32357762177423),
#                       Function(-1.1247622281824705, 498.73254507608965),
#                       Function(-0.4607148044356967, -165.70911870991122)])
creatures = deque()
for c in range(64 - len(creatures)):
  creatures.append(Creature())
for tourny in range(20):
  random.shuffle(creatures)
  while len(creatures) > 4:
    players = []
    for _ in range(4):
      players.append(creatures.popleft())
    creatures.append(Matchup(players).get_winner(50))
  
  finals_players = []
  for i in range(4):
    finals_players.append(creatures[i])
    for _ in range(10):
      creatures.append(creatures[i].gen_mutant())
  champ = Matchup(finals_players).get_winner(200)
  for _ in range(64-len(creatures)):
    creatures.append(champ.gen_mutant())
  print(champ)
  with open("h2hwinners.txt", "a") as f:
    f.write(str(champ))
    f.write("\n\n")
