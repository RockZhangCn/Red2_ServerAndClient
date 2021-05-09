from CardPack import CardPack
from CardHand import CardHand
import json

class Player:
    def __init__(self):
        self.cardhand = CardHand.from_card_list([])
        self.bid = None
        self.playerid = None
        self.publichand = CardHand.from_card_list([])
        self.lord = None
        self.played = [[], [], []]
        self.curstage = None
        self.isHuman = False
        self.name = "玩家"
    def resume(self, object):
        start = 0
        first_request = object["requests"][0]
        self.cardhand.insert(first_request["own"])
        if "bid" in first_request:
            self.bid = max(first_request["bid"] + [0])
            self.curstage = "bid"
            start = 1
        for request in object["requests"][start:]:
            self.curstage = "play"
            if "publiccard" in request:
                self.publichand.insert(request["publiccard"])
                self.cardhand.insert(request["own"])
                self.lord = request["landlord"]
                self.playerid = request["pos"]
                self.bid = request["finalbid"]
            self.played[(self.playerid + 1) % 3].append(request["history"][0])
            self.played[(self.playerid + 2) % 3].append(request["history"][1])
        for response in object["responses"][start:]:
            self.played[self.playerid].append(response["response"])
    def action(self, object):
        print(object)
        self.resume(json.loads(object))
        response = self.customize_action()
        return json.dumps({"response": response})
    def customize_action(self):
        pass
