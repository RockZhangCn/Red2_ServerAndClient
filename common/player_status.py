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


class PlayerResult(IntEnum):
    Win = 0
    Lose = 1
    Peace = 2
    InProgress = 3


class GameResult(IntEnum):
    Red2Win = 0
    Peace = 1
    NonRed2Win = 2
    InProgress = 3


