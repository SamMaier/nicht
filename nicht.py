#!/usr/bin/python3
import random

class Game:
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


  def make_decision(self, _dice, game):
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
    for pick in generate_all_picks(dice):
      score, num_used_dice = game.check_score(pick)
      available_dice = game.available_dice - num_used_dice
      prediction = self.prediction_function(available_dice, score)
      if prediction > best_score:
        best_score = prediction
        best_pick = pick
        
    return best_pick


  def play_game(self):
    game = Game()
    while True:
      dice = game.roll_dice()
      if not dice:
        break
      dice_to_take = self.make_decision(dice, game)
      if not dice_to_take:
        game.end_turn(dice)
        break
      else:
        game.take_dice(dice_to_take)
    assert game.available_dice == -1
    return game.score

def generic_function(d,
                     s,
                     fns):
  return fns[d-1].call(s)
  
class Function:
  def __init__(self, m, b):
    self.m = m
    self.b = b

  def call(self, x):
    return (self.m*x) + self.b

  def mutate(self):
    mutation_size_m = random.uniform(0.5,2)
    mutation_size_b = random.uniform(0.5,2)
    return Function(self.m*mutation_size_m, self.b*mutation_size_b)

  def __str__(self):
    return "Function(" + str(self.m) + ", " + str(self.b) + ")"
    
class Creature:
  def __init__(self, fns):
    assert len(fns) == 6
    self.fns = fns
    self.strat = Strategy(lambda d, s: fns[d-1].call(s))

  def evaluate(self, n):
    val = 0
    for _ in range(n):
      val += self.strat.play_game()
    return val

  def gen_mutant(self):
    num_of_mutations = random.randint(1,5)
    fns = self.fns.copy()
    for _ in range(num_of_mutations):
      rand_loc = random.randint(0,5)
      fns[rand_loc] = fns[rand_loc].mutate()
      
    return Creature(fns)

  def __str__(self):
    return "Creature([" + ",\n".join([str(f) for f in self.fns]) + "])"
      

# Not totally correct, since probabilities at 4+ arent exclusive yet are being subtracted
risk_table = {1:2.0/3.0, 2:4.0/9.0, 3:8.0/27.0 - 4.0/216.0, 4: 16.0/81.0 - 4*0.0162, 5: 32.0/243.0 - 4*0.0355, 6: 64.0/729.0 - 4*0.0623}
dumb_creature = Creature([Function(1.0-risk_table[1], 100),
                          Function(1.0-risk_table[2], 200),
                          Function(1.0-risk_table[3], 300),
                          Function(1.0-risk_table[4], 400),
                          Function(1.0-risk_table[5], 500),
                          Function(1.0-risk_table[6], 600)])

winner = Creature([Function(0.3255622078722859, 282.3764025270552),
                  Function(0.1444338457754891, 100.94515448510734),
                  Function(0.6737078024802203, 102.4173438927874),
                  Function(0.7010228500069347, 334.21965970169293),
                  Function(0.42077984586108585, 455.61684598995805),
                  Function(2.881268157958244, 1329.3238138727988)])
#22000 so baseline gets ~1mil
NUM_EVALS = 22000
runner_up = dumb_creature
global_winner = winner
max_score = NUM_EVALS * 460 # 460 is a bad-ish average per turn
for gen in range(100):
  creatures = [global_winner, winner, global_winner.gen_mutant(), global_winner.gen_mutant(), winner.gen_mutant(), winner.gen_mutant(), runner_up.gen_mutant()]
  scores = [c.evaluate(NUM_EVALS) for c in creatures]
  print(scores)
  winning_score = scores[0]
  rup_score = 0
  for i in range(1, len(scores)):
    if scores[i] > winning_score:
      runner_up = winner
      rup_score = winning_score
      winner = creatures[i]
      winning_score = scores[i]
    elif scores[i] > rup_score:
      runner_up = creatures[i]
      rup_score = scores[i]

  if (winning_score > max_score):
    global_winner = winner
    max_score = winning_score
    print("New Record: "+ str(winning_score) + " from the " + str(scores.index(winning_score)))
    print(winner)

print(global_winner)
