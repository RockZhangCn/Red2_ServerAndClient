class CardPack:
    cardname = [i + j for i in ["♥️", "♦️", "♠️", "♣️"] for j in ["3","4","5","6","7","8","9","10","J","Q","K","A","2"]] + ["小王", "大王"]

    def __init__(self, cards):
        # cards is a list of 54 boolean elements
        self.cards = cards
        self.type_str, self.type_num, self.rank, self.length, self.arg = self.check_type()

    def from_card_list(card_list):
        tmp = [False] * 54
        for n in card_list:
            tmp[n] = True
        return CardPack(tmp)

    def to_card_list(self):
        cardlist = sorted([card for card, exist in enumerate(self.cards) if exist], key = lambda x: (-max(x - 51, 0), -(x % 13), x // 13))
        return cardlist

    def check_type(self):
        count = [sum(self.cards[i * 4: i * 4 + 4]) for i in range(13)] + [1 if c else 0 for c in self.cards[-2:]]
        maxcount, mincount = max(count), min(filter(lambda x: x > 0, count))
        card_by_count = [sorted([i for i, a in enumerate(count) if a == n]) for n in range(1, 5)]
        is_cont = lambda ordered_list: ordered_list == list(range(min(ordered_list), max(ordered_list) + 1))
        if sum(self.cards) == 1:
            return "单张", 2, card_by_count[0][0], None, None
        if sum(self.cards) == 2:
            if maxcount == 2:
                return "对子", 3, card_by_count[1][0], None, None
            if card_by_count[0] == [13, 14]:
                return "火箭", 30030, 15, None, None
        if maxcount == 1:
            tmp = card_by_count[0]
            if is_cont(tmp) and max(tmp) < 12 and len(tmp) >= 5:
                return "单顺", 5, min(tmp), len(tmp), None
        if maxcount == 2 and mincount == 2:
            tmp = card_by_count[1]
            if is_cont(tmp) and max(tmp) < 12 and len(tmp) >= 3:
                return "双顺", 7, min(tmp), len(tmp), None
        if sum(self.cards) == 4 and mincount == 4:
            return "炸弹", 30030, card_by_count[3][0], None, None
        if maxcount == 3:
            tmp = card_by_count[2]
            if is_cont(tmp) and (len(tmp) == 1 or max(tmp) < 12):
                l = len(tmp)
                if mincount == 3:
                    return "三张", 11, min(tmp), l, 0
                if mincount == 1 and len(card_by_count[1]) == 0:
                    if len(card_by_count[0]) == l:
                        return "三带一张", 11, min(tmp), l, 1
                if mincount == 2:
                    if len(card_by_count[1]) == l:
                        return "三带一对", 11, min(tmp), l, 2
        if maxcount == 4:
            tmp = card_by_count[3]
            if is_cont(tmp) and (len(tmp) == 1 or max(tmp) < 12):
                l = len(tmp)
                if mincount == 1 and len(card_by_count[1]) == 0 and len(card_by_count[2]) == 0:
                    if len(card_by_count[0]) == 2 * l:
                        return "四带二张", 13, min(tmp), l, 1
                if mincount == 2 and len(card_by_count[2]) == 0:
                    if len(card_by_count[1]) == 2 * l:
                        return "四带二对", 13, min(tmp), l, 2
        return "非法", 1, None, None, None

    def can_beat(self, other):
        if self.type_num == 1 or other.type_num == 1:
            return False
        if self.type_num == other.type_num:
            if self.arg is None or self.arg == other.arg:
                if self.length is None or self.length == other.length:
                    if self.rank > other.rank:
                        return True
        if self.type_num != other.type_num and self.type_num % other.type_num == 0:
            return True
        return False

    def __repr__(self):
        cardlist = self.to_card_list()
        string = str([self.cardname[card] for card in cardlist]) + "\n" + \
                 f"牌型：{self.type_str} \n大小：{self.rank}\n长度：{self.length}\n带张：{self.arg}\n"
        return string









