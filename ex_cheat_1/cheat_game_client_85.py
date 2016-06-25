#!/usr/bin/python
import random
from math import exp
from collections import defaultdict

from cheat_game_server import Game
from cheat_game_server import Player, Human
from cheat_game_server import Claim, Take_Card, Cheat, Call_Cheat
from cheat_game_server import Rank, Suit, Card
from cheat_game_server import ActionEnum

class Agent(Player):
    def __init__(self, name):
        super(Agent, self).__init__(name)

    def make_claim(self, cards, claim):
        print 'making claim: {0:1d} cards of rank {1}'.format(claim.count, str(claim.rank))
        super(Agent, self).make_claim(cards, claim)

    def make_honest_claim(self, claim):
        super(Agent, self).make_honest_claim(claim)

    def take_card_from_deck(self, silent=False):
        if not silent: print 'Taking Card from deck'
        super(Agent, self).take_card_from_deck()

    def call_cheat(self):
        print 'Calling "Cheat!"'
        super(Agent, self).call_cheat()

    def make_move(self):
        print
        print 'Player {0:1d} ({1:s}) turn'.format(self.id, self.name)
        print "================"+"="*len(self.name)
        honest_moves = self.possible_honest_moves()
        state = self.game.get_state()
        opponent_count = state[3 - self.id]
        deck_count = state['DECK']
        table_count = state['TABLE']
        last_action = state['LAST_ACTION']
        cards_revealed = state['CARDS_REVEALED']
        last_claim = self.game.last_claim()
        # if opponent placed his last cards on the table - call_cheat or lose
        action = self.agent_logic(deck_count, table_count, opponent_count,
                                  last_action, last_claim, honest_moves, cards_revealed)
        assert action in honest_moves or isinstance(action, Cheat), "action %s (%s) is not in honest moves %s" % (type(action).__name__, action, honest_moves) 
        if isinstance(action, Call_Cheat):
            self.call_cheat()
        elif isinstance(action, Claim):
            self.make_honest_claim(action)
        elif isinstance(action, Take_Card):
            self.take_card_from_deck()
        elif isinstance(action, Cheat):
            self.make_claim(action.cards, Claim(action.rank, action.count))


class Agent_85(Agent):
    def __init__(self, name):
        super(Agent_85, self).__init__(name)
        self.card_counter = CheatGameCardCounter()
        self.first_move = True


    def agent_logic(self, deck_count, table_count, opponent_count,
                    last_action, last_claim, honest_moves, cards_revealed):
        
        self.action_scores = {'Claim' : 0, 'Take_Card' : 0, 'Call_Cheat' : 0, 'Cheat' : 0}

        if self.first_move: # that's terrible...
            self.card_counter.deal(self.cards, self.game.initial_card, opponent_count, deck_count, table_count)
            self.first_move = False

        # update the card counting obj and get an estimation on oponnent's claim
        self.card_counter.move(self.cards, opponent_count, deck_count, table_count)
        if last_action == ActionEnum.MAKE_CLAIM:
            self.action_scores['Call_Cheat'] = 1 - self.card_counter.claim_prob(last_claim)

        # score honest moves
        for move in honest_moves:
            self.action_scores[type(move).__name__] += 1

        # change the score of cheat move, based on risk factors
        if table_count < len(self.cards) < opponent_count:
            self.action_scores['Cheat'] += 0.1*len(self.cards)
        if deck_count < len(self.cards):
            self.action_scores['Cheat'] -= 0.1*deck_count

        # choose the best score:
        action_str = max(self.action_scores, key=self.action_scores.get)
        # mix strategies with p < 0.1 (smaller beacuse it might change to the best one):
        rand = random.random()
        if rand < 0.1:
            valid_moves = filter(lambda x: self.action_scores[x] != 0, self.action_scores.keys())
            random.shuffle(valid_moves)
            action_str = valid_moves[0]

        # if the actio is Take_Card or Call_Cheat - return it from honest_moves
        if action_str in ['Take_Card', 'Call_Cheat']:
            for move in honest_moves:
                if type(move).__name__ == action_str:
                    return move
        # otherwise use specialized functions to find the best move and return 
        elif action_str == 'Claim':
            return self.get_best_claim(filter(lambda x: isinstance(x, Claim), honest_moves))
        else:
            return self.get_best_cheat(table_count)

    # choose rank based on distance to remaining agent's card
    def choose_best_direction(self, rank=None):
        top_rank = rank if rank is not None else self.table.top_rank()
        rank_above = Rank.above(top_rank)
        rank_below = Rank.below(top_rank)
        rank_above_score = rank_below_score = 0
        for card in self.cards:
            rank_above_score += card.rank.dist(rank_above)
            rank_below_score += card.rank.dist(rank_below)
        if rank_above_score < rank_below_score:
            return rank_above
        else:
            return rank_below
        
    def get_best_cheat(self, table_count):
        cheat_rank = self.choose_best_direction()
        cheat_count = 1
        # decaying function of number of cards on the table - cheat less when risk is large
        r = 0.5 * exp(-0.1 * table_count)
        while cheat_count < 4 and random.random() < r and len(self.cards) >= (cheat_count + 1):
            cheat_count += 1
        # select cards furthest from current claim rank
        dist = defaultdict(int)
        for ind, card in enumerate(self.cards):
            dist[card] = cheat_rank.dist(card.rank)
        claim_cards = sorted(dist, key=dist.get)[:cheat_count]
        return Cheat(claim_cards, cheat_rank, cheat_count)

    def get_best_claim(self, honest_moves):
        # if you have both ranks - choose the better direction (just like in cheating)
        if len(set(map(lambda x: x.rank, honest_moves))) > 1:
            chosen_rank = self.choose_best_direction()
            honest_moves = filter(lambda x: x.rank == chosen_rank, honest_moves)
        # if more than one card of that rank - consider keeping some in case oponnent repeats the move
        honest_moves.sort(key=lambda x: x.count)
        if len(honest_moves) > 1 and len(self.cards) > 8:
            random.shuffle(honest_moves)
        return honest_moves[-1]
        
        
        
# This class will track the oponent's cards by assigning (and updating) probabilities
# to all cards in the deck. It will be used to estimate the validity of oponent's moves.
class CheatGameCardCounter(object):
    def __init__(self):
        self.unknown_prob = self.total_cards = 0
        self.my_knowns = list()
        self.it_knowns = list()
        self.pile_knowns = list() #the cards that I actually put into the pile.
    
    # should be called once the cards are dealt.
    def deal(self, my_cards, initial_card, hand_size, deck_size, pile_size):
        self.total_cards = deck_size + hand_size + pile_size + len(my_cards)
        self.pile_knowns.append(initial_card)   
        self.my_knowns.extend(my_cards)
        self.update_probs(hand_size, deck_size)

    # update all probabailities, according to the current state of the deck
    # should be called after every modification of the hands.
    def update_probs(self, hand_size, deck_size):
        unknowns = self.total_cards - len(self.pile_knowns) - len(self.it_knowns) - len(self.my_knowns)
        it_unknowns = hand_size - len(self.it_knowns)
        self.unknown_prob = 0 if unknowns == 0 else float(it_unknowns)/unknowns

    #return the probability of the oponent actually having the cards it claimed.
    def claim_prob(self, claim):
        my_known = len(filter(lambda card: card.rank == claim.rank, self.my_knowns+self.pile_knowns))
        it_known = len(filter(lambda card: card.rank == claim.rank, self.it_knowns))
        if claim.count > (4 - my_known):
            return 0
        return pow(self.unknown_prob, max(claim.count - it_known, 0))

    def move(self, my_cards, hand_size, deck_size, pile_size):
        if len(self.my_knowns) < len(my_cards):   # I took cards from either pile or the deck.
            self.my_knowns = my_cards
        elif pile_size == 0:                      # It took cards from the pile 
            self.it_knowns.extend(self.pile_knowns)
        else:
            # Ok, this is a little tricky: We get here when one of us added cards to the pile.
            # So we will add cards that were mine but no longer so, to the known cards of the pile.
            # This will not change anything if my_cards == self.my_knowns (i.e. I didn't add anything)
            self.pile_knowns.extend(set(self.my_knowns) - set(my_cards))
        self.update_probs(hand_size, deck_size)


if __name__ == "__main__":
    cheat = Game(Agent_85("Demo 1"), Human("me"))
    cheat.play()
