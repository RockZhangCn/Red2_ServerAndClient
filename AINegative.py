from Player import Player

class AINegative (Player):
    def __init__(self):
        Player.__init__(self)
        self.isHuman = False
        self.name = "托管"

    def customize_action(self):
        if self.curstage == "bid":
            return 0
        if self.played[(self.playerid + 1) % 3][-1] == [] and self.played[(self.playerid + 2) % 3][-1] == []:
            return [self.cardhand.to_card_list()[-1]]
        else:
            return []