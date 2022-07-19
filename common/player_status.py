from enum import unique, IntEnum


@unique
class PlayerStatus(IntEnum):
    Unlogin = -2
    Offline = -1
    Logined = 0
    Started = 1  # 全部Start后，仍然应该是start。
    SingleOne = 2  # 抢红2, 这个动作之后都是Handout
    NoTake = 3
    Share2 = 4
    NoShare = 5
    Handout = 6
    RunOut = 7
    GameOver = 8  # --> Started
