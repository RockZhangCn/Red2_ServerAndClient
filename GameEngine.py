from CardHand import CardHand
from CardPack import CardPack
import random
import json

class GameEngine:
    def __init__(self):
        self.players = [None, None, None]
        self.cumscores = [0, 0, 0]
        self.lastscores = [0, 0, 0]
        self.newgame()
    def newgame(self):
        allcards = list(range(54))
        random.shuffle(allcards)
        self.cardhands = [CardHand.from_card_list(allcards[:17]),
                          CardHand.from_card_list(allcards[17:34]),
                          CardHand.from_card_list(allcards[34:51])]
        self.public = CardHand.from_card_list(allcards[51:])
        self.curplayer = 0
        self.largestplayer = -1
        self.lord = None
        self.base = None
        self.multiplier = 1
        self.stage = "叫牌阶段"
        self.arg = 0
        self.curround = 0
        self.spring = True
        self.antispring = True
        self.messages = [{"requests": [], "responses": []},
                         {"requests": [], "responses": []},
                         {"requests": [], "responses": []}]
        self.round = [[], [], []]
        self.bids = []

    def registerPlayer(self, id_player, player):
        self.players[id_player] = player
    def step(self, res = None):
        print(self.stage)
        if self.stage == "叫牌阶段":
            self.messages[self.curplayer]["requests"].append({
                "own": self.cardhands[self.curplayer].to_card_list(),
                "bid": self.bids
            })
            request = json.dumps(self.messages[self.curplayer])
            if res is None:
                response = json.loads(self.players[self.curplayer].action(request))
            else:
                response = {"response": res}
            self.messages[self.curplayer]["responses"].append(response)
            new_bid = int(response["response"])
            self.bids.append(new_bid)
            if new_bid != 0:
                self.base = new_bid
                self.largestplayer = self.curplayer
            self.arg += 1
            if self.base == 3:
                self.stage = "出牌阶段"
                self.lord = self.largestplayer
            elif self.arg == 3:
                self.stage = "出牌阶段"
                if self.largestplayer == -1:
                    self.base = 1
                    self.lord = (self.curplayer + 1) % 3
                else:
                    self.lord = self.largestplayerplayer
            if self.lord is not None:
                self.cardhands[self.lord].insert(self.public)
                self.curplayer = self.lord
                self.arg = 0
            else:
                self.curplayer += 1
        elif self.stage == "出牌阶段":
            print("Cur hand: ", self.cardhands[self.curplayer])
            print("Cur Lord: ", self.lord)
            if self.curplayer != self.lord:
                self.spring = False
            if self.curplayer == self.lord and self.curround != 0:
                self.antispring = False
            if self.curround == 0:
                self.messages[self.curplayer]["requests"].append({
                    "history": [self.round[(self.curplayer + 1) % 3], self.round[(self.curplayer + 2) % 3]],
                    "publiccard": self.public.to_card_list(),
                    "own": self.cardhands[self.curplayer].to_card_list(),
                    "landlord": self.lord,
                    "pos": self.curplayer,
                    "finalbid": self.base
                })
            else:
                self.messages[self.curplayer]["requests"].append({
                    "history": [self.round[(self.curplayer + 1) % 3], self.round[(self.curplayer + 2) % 3]]
                })
            request = json.dumps(self.messages[self.curplayer])
            if res is None:
                response = json.loads(self.players[self.curplayer].action(request))
            else:
                response = {"response": res}
            self.messages[self.curplayer]["responses"].append(response)
            played = response["response"]
            self.round[self.curplayer] = played
            if len(played) > 0:
                self.largestplayer = self.curplayer
                self.cardhands[self.curplayer].remove(played)
                print(played)
                print(CardPack.from_card_list(played).type_str)
                print("len", len(self.cardhands[self.curplayer]))
                if CardPack.from_card_list(played).type_str in ["炸弹", "火箭"]:
                    self.multiplier *= 2
                if len(self.cardhands[self.curplayer]) == 0:
                    print("Here")
                    self.stage = "计分阶段"
                    self.arg = self.curplayer == self.lord
                    if self.spring:
                        self.multiplier *= 2
                    if self.antispring:
                        self.multiplier *= 2
                    self.step()
            self.curplayer = (self.curplayer + 1) % 3
            if self.curplayer == self.lord:
                self.curround += 1
        else:
            for i in range(3):
                base_score = self.base * self.multiplier
                if i == self.lord:
                    self.lastscores[i] = base_score * (2 if self.arg else -2)
                    self.cumscores[i] += base_score * (2 if self.arg else -2)
                else:
                    self.lastscores[i] = base_score * (-1 if self.arg else 1)
                    self.cumscores[i] += base_score * (-1 if self.arg else 1)
    def __repr__(self):
        print(self.cardhands[0])
        print(self.cardhands[1])
        print(self.cardhands[2])
        print(CardHand.from_card_list(self.public))
        print(self.curplayer)
        print(self.round[0], self.round[1], self.round[2])
        return ""
    def getPlayerHand(self, player_id):
        return self.cardhands[player_id].to_card_list()
    def getPublicHand(self):
        return self.public.to_card_list()
    def getLord(self):
        return self.lord
    def getScores(self):
        return self.cumscores




