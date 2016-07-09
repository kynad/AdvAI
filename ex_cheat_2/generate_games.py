#!/usr/bin/python

import sys, threading, copy
from cheat_game_server import *
from cheat_game_client import *
from cheat_game_client_10 import Agent_10
from cheat_game_client_15 import Agent_15
from cheat_game_client_20 import Agent_20
from cheat_game_client_25 import Agent_25
from cheat_game_client_30 import Agent_30
from cheat_game_client_35 import Agent_35
from cheat_game_client_40 import Agent_40
from cheat_game_client_45 import Agent_45
from cheat_game_client_50 import Agent_50
from cheat_game_client_55 import Agent_55
from cheat_game_client_65 import Agent_65
from cheat_game_client_70 import Agent_70
from cheat_game_client_73 import Agent_73
from cheat_game_client_80 import Agent_80
from cheat_game_client_85 import Agent_85
from cheat_game_client_90 import Agent_90

## redirect print to /dev/null
devnull = open("/dev/null",'w')
stdout = sys.stdout
sys.stdout = devnull

#agents_ids = [10,15,20,25,30,35,40,45,50,55,65,70,73,80,85,90]
agents_ids = [10,15,20,25,30,35,40,50,55,65,70,73,80,85,90]

agents = dict()
agents[10] = Agent_10("agent_10")
agents[15] = Agent_15("agent_15")
agents[20] = Agent_20("agent_20")
agents[25] = Agent_25("agent_25")
agents[30] = Agent_30("agent_30")
agents[35] = Agent_35("agent_35")
agents[40] = Agent_40("agent_40")
agents[50] = Agent_50("agent_50")
agents[55] = Agent_55("agent_55")
agents[65] = Agent_65("agent_65")
agents[70] = Agent_70("agent_70")
agents[73] = Agent_73("agent_73")
agents[80] = Agent_80("agent_80")
agents[85] = Agent_85("agent_85")
agents[90] = Agent_90("agent_90")

num_of_games = int(sys.argv[1])
begin_counter = 0
if len(sys.argv) > 2:
    begin_counter = sys.argv[2]

class GamesGenerator(threading.Thread):
    def __init__(self, id_1, id_2):
        threading.Thread.__init__(self)
        self.id_1 = id_1
        self.id_2 = id_2
        self.agent_1 = copy.deepcopy(agents[id_1])
        self.agent_2 = copy.deepcopy(agents[id_2])
        self.num_games = num_games
    def __del__(self):
        del(self.agent_1)
        del(self.agent_2)
    def run(self):
        for i in xrange(begin_counter, begin_counter+num_of_games):
            game = Game(self.agent_1, self.agent_2)
            game.play()
            game.save_state_to_file("games/%s_vs_%s_%d" % (self.id_1, self.id_2, i))        
            del(game)

my_threads = []

for agent_id_1 in agents_ids:
    for agent_id_2 in agents_ids:
        for i in xrange(begin_counter, begin_counter+num_of_games):
            game = Game(agents[agent_id_1], agents[agent_id_2])
            game.play()
            game.save_state_to_file("games/%d_vs_%d_%d" % (agent_id_1, agent_id_2, i))        
            del(game)

# restore stdout
sys.stdout = stdout
devnull.close()

