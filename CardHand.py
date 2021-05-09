from CardPack import CardPack

class CardHand(CardPack):
    def __init__(self, cards):
        self.cards = cards

    def __len__(self):
        return sum(self.cards)

    def from_card_list(card_list):
        tmp = [False] * 54
        for n in card_list:
            tmp[n] = True
        return CardHand(tmp)

    def to_card_list(self):
        cardlist = sorted([card for card, exist in enumerate(self.cards) if exist], key = lambda x: (-max(x - 51, 0), -(x // 4), x % 4))
        return cardlist

    def __contains__(self, other):
        if isinstance(other, CardPack):
            for i in range(54):
                if other.cards[i] and not self.cards[i]:
                    return False
            return True
        elif isinstance(other, list):
            for l in other:
                if not self.cards[l]:
                    return False
            return True
        return False

    def remove(self, other):
        if isinstance(other, CardPack):
            for i in range(54):
                self.cards[i] = self.cards[i] and (not other.cards[i])
        else:
            for l in other:
                self.cards[l] = False

    def insert(self, other):
        if isinstance(other, CardPack):
            for i in range(54):
                self.cards[i] = self.cards[i] or other.cards[i]
        else:
            for l in other:
                self.cards[l] = True

    def __repr__(self):
        cardlist = self.to_card_list()
        string = str([self.cardname[card] for card in cardlist])
        return string