import random

from log.log import logger


class Card(object):
    all_cards = [x for x in range(0, 52)] * 2
    cards_count = len(all_cards)

    @staticmethod
    def adjust_value(card):
        value = card // 4
        return value

    @staticmethod
    def card_to_picture_index(card):
        role = card.split("*")[0]
        value = card.split("*")[1]
        role = int(role)
        index = Card.cards_index.index(value)
        return index * 4 + role

    @staticmethod
    def cards_to_string(cards):
        return "|".join(cards)

    @staticmethod
    def card_compare(card1_name, card2_name):
        value1 = Card.adjust_value(card1_name)
        value2 = Card.adjust_value(card2_name)
        if value1 < value2:
            return -1
        elif value1 > value2:
            return 1
        else:
            return 0

    def __str__(self):
        return self.__name


class CardHand(object):
    MODE_SINGLE = "single"
    MODE_PAIR = "pair"
    MODE_THREE = "three"
    MODE_THREE_ONE = "three1"
    MODE_THREE_TWE = "three2"
    MODE_AIRPLANE_NONE = MODE_THREE + "s"  # 2*3
    MODE_AIRPLANE_ONE = MODE_THREE_ONE + "s"  # 2*4
    MODE_AIRPLANE_TWE = MODE_THREE_TWE + "s"  # 2*5
    MODE_SINGLE_LONG = "single_long"  # 6
    MODE_PAIR_LONG = "pair_long"  # 6

    MODE_BOMB = "bombs"  # 4
    MODE_TWO_RED2 = "twored2"  # 2
    MODE_INVALID = "invalid"

    def __init__(self, cards):
        self.cards_in_a_hand = cards
        self.cards_in_a_hand.sort(key=Card.adjust_value, reverse=True)

    def hand_mode(self):
        cnt = len(self.cards_in_a_hand)
        value_set = set()
        for cardname in self.cards_in_a_hand:
            value_set.add(Card.adjust_value(cardname))

        value_set_len = len(value_set)
        if cnt == 1:
            return CardHand.MODE_SINGLE
        if cnt == 2:
            if value_set_len == 1:
                if (Card.adjust_value(self.cards_in_a_hand[0]) == 15) and (self.cards_in_a_hand[0][0:2] == "♥️") and (
                        self.cards_in_a_hand[1][0:2] == "♥️"):
                    return CardHand.MODE_TWO_RED2
                else:
                    return CardHand.MODE_PAIR
            else:
                return CardHand.MODE_INVALID
        if cnt == 3:
            if value_set_len == 3:
                return CardHand.MODE_THREE
            else:
                return CardHand.MODE_INVALID

        if cnt == 4:
            if value_set_len == 2:
                return CardHand.MODE_THREE_ONE
            elif value_set_len == 1:
                return CardHand.MODE_BOMB
            else:
                return CardHand.MODE_INVALID

        if cnt == 5:
            if value_set_len == 2:
                return CardHand.MODE_THREE_TWE
            elif value_set_len == 1:
                return CardHand.MODE_BOMB
            else:
                return CardHand.MODE_INVALID

        if cnt >= 6:
            if value_set_len == cnt:
                return CardHand.MODE_SINGLE_LONG
            if value_set_len == cnt // 2:
                return CardHand.MODE_PAIR_LONG
            if value_set_len == cnt // 3:
                return CardHand.MODE_AIRPLANE_NONE
            if value_set_len == 1:
                return CardHand.MODE_BOMB
            if cnt % 5 == 0 and value_set_len == (cnt // 5) * 2:
                return CardHand.MODE_AIRPLANE_TWE
            if cnt % 4 == 0 and value_set_len <= (cnt // 4) * 2:
                return CardHand.MODE_AIRPLANE_ONE

            return CardHand.MODE_INVALID


if __name__ == '__main__':
    cards = [x for x in range(0, 52)] * 2
    logger.info("length {} cards {}".format(len(cards), cards))

    random.shuffle(cards)
    for pos, player in enumerate(["name", "shou", "zhang", "nie"]):
        # range step 4.
        player_cards = [cards[x + pos] for x in range(0, len(cards), 4)]
        player_cards.sort(reverse=True)
        logger.info("Player [ {} ] at pos {} dispatched cards {}".format(player,
                                                                         pos, player_cards))
