from Player import Player

class Human(Player):
    def __init__(self):
        Player.__init__(self)
        self.isHuman = True