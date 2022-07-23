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
    def card_compare(card1_name, card2_name):
        value1 = Card.adjust_value(card1_name)
        value2 = Card.adjust_value(card2_name)
        if value1 < value2:
            return -1
        elif value1 > value2:
            return 1
        else:
            return 0


class CardMode(object):
    MODE_SINGLE = 1  # "single"
    MODE_PAIR = 2  # "pair"
    MODE_THREE = 3  # "three"
    MODE_THREE_ONE = 4  # "three1"  8883
    MODE_THREE_TWE = 5  # "three2"   88833
    MODE_AIRPLANE_NONE = 6  # MODE_THREE + "s"  # 2*3  555666
    MODE_AIRPLANE_ONE = 7  # MODE_THREE_ONE + "s"  # 2*4  55576668
    MODE_AIRPLANE_TWE = 8  # MODE_THREE_TWE + "s"  # 2*5   5557766688
    MODE_SINGLE_LONG = 9  # "single_long"  # 6   345678
    MODE_PAIR_LONG = 10  # "pair_long"  # 6    334455

    MODE_BOMB = 11  # "bombs"  # 4   3333
    MODE_TWO_RED2 = 12  # "king2"  # 2   22
    MODE_INVALID = -1  # "invalid"

    @staticmethod
    def value(cards):
        cards.sort(reverse=True)

        value_set = set()
        for card in cards:
            value_set.add(Card.adjust_value(card))

        cnt = len(cards)
        value_set_len = len(value_set)
        if cnt == 1:
            return CardMode.MODE_SINGLE
        elif cnt == 2 and value_set_len == 1:
            if cards == [48, 48]:
                return CardMode.MODE_TWO_RED2
            else:
                return CardMode.MODE_PAIR

        elif cnt == 3 and value_set_len == 1:
            return CardMode.MODE_THREE

        elif cnt == 4:
            if value_set_len == 2:
                if cards[0]//4 == cards[1]//4 == cards[2]//4 or \
                        cards[3]//4 == cards[1]//4 == cards[2]//4:
                    return CardMode.MODE_THREE_ONE
                else:
                    return CardMode.MODE_INVALID

            elif value_set_len == 1:
                return CardMode.MODE_BOMB
            else:
                return CardMode.MODE_INVALID

        elif cnt == 5:
            if value_set_len == 2:
                if (cards[0]//4 == cards[1]//4 == cards[2]//4 and cards[3]//4 == cards[4]//4) or \
                        (cards[3]//4 == cards[4]//4 == cards[2]//4 and cards[0]//4 == cards[1]//4) :
                    return CardMode.MODE_THREE_TWE
                else:
                    return CardMode.MODE_INVALID
            elif value_set_len == 1:
                return CardMode.MODE_BOMB
            else:
                return CardMode.MODE_INVALID

        elif cnt >= 6:# 部分不太准确。
            if value_set_len == cnt:
                return CardMode.MODE_SINGLE_LONG
            if value_set_len == cnt // 2:
                # TODO more detail
                return CardMode.MODE_PAIR_LONG
            if value_set_len == cnt // 3:
                return CardMode.MODE_AIRPLANE_NONE
            if value_set_len == 1:
                return CardMode.MODE_BOMB
            if cnt % 5 == 0 and cnt // 5 <= value_set_len <= (cnt // 5) * 2:
                return CardMode.MODE_AIRPLANE_TWE
            if cnt % 4 == 0 and cnt // 4 <= value_set_len <= (cnt // 4) * 2:
                return CardMode.MODE_AIRPLANE_ONE

            return CardMode.MODE_INVALID
        else:
            return CardMode.MODE_INVALID


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
