# 红2 （四人斗地主)
## 基本架构
Client[python tkinter]  < --- websocket ---> Server[python asyncio]\r\n
UI Thread and Com Thread                      SingleThread

## 玩法介绍
+ 一种类似四人斗地主的棋牌游戏，总计使用两副牌，去掉四个大小王，每人初始26张牌。
+ 有红桃2的为一组，没有的为一组，出牌规则与斗地主类似。
+ 可以一人抢王炸（两张红桃2）进行1v3模式，也可以普通的2v2模式。
