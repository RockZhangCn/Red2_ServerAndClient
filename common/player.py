import asyncio
import copy
import json
import queue

import websockets

from client.client_io import NetworkHandler
from common.message import ClientMessage
from common.player_status import PlayerStatus
from log.log import logger


class Player(object):
    def __init__(self, name, pos, ws):
        self.__name = name
        self.__pos = pos
        self.__ws = ws
        self.__has_red2 = False
        self.__owned_pokers = []
        self.__status = PlayerStatus.Logined
        self.__pending_message = ""

    def get_player_name(self):
        return self.__name

    def set_notify_message(self, msg):
        self.__pending_message = msg

    def get_notify_message(self):
        return self.__pending_message

    def get_player_status(self):
        return self.__status

    def set_player_status(self, status):
        self.__status = status

    def set_player_name(self, name):
        self.__name = name

    def get_player_pos(self):
        return self.__pos

    def set_player_pos(self, pos):
        self.__pos = pos

    def set_websocket(self, ws):
        self.__ws = ws

    def get_websocket(self):
        return self.__ws

    def has_red2(self):
        return self.__has_red2

    def set_has_red2(self, has):
        self.__has_red2 = has

    def set_player_owned_pokers(self, card_list):
        self.__owned_pokers = card_list

        logger.info("set_player_owned_pokers : {} {}".format(len(card_list), card_list))

    def received_added_red2(self):
        self.__pending_message = "收到红2"
        self.__owned_pokers.append(48)
        self.__has_red2 = True
        self.__owned_pokers.sort(reverse=True)

    def handout_taken_red2(self):
        if self.__has_red2:
            while self.__owned_pokers.count(48) > 0:
                self.__owned_pokers.remove(48)

            self.__has_red2 = False
            self.__pending_message = "被抽走红2"

    def get_owned_pokers(self):
        return self.__owned_pokers

    async def send_message(self, message):
        await self.__ws.send(message)


class ClientPlayer(Player):
    def __init__(self, name, pos, ws):
        Player.__init__(self, name, pos, ws)
        self.__msg_client = ClientMessage(name)
        self.__recv_queue = queue.Queue()
        self.__network_handler = None

    def has_new_message(self):
        return not self.__recv_queue.empty()

    def recv_queue(self):
        return self.__recv_queue

    def destroy(self):
        # self.__network_handler.stop()
        self.__network_handler.destroy()
        self.__network_handler.join()

    def login(self, address):
        # self.bottom_user_name_widget.config(state='disabled')
        #  启动网络请求。
        self.__network_handler = NetworkHandler(self.get_player_name(), self.__recv_queue, address)
        self.__network_handler.start()

    def prepare_ready(self):
        self.__msg_client.build_req_status_msg([], PlayerStatus.Started)
        self.__network_handler.enqueue_message(str(self.__msg_client))

    def single_user(self):
        self.__msg_client.build_req_status_msg([], PlayerStatus.SingleOne)
        self.__network_handler.enqueue_message(str(self.__msg_client))

    def notake2(self):
        self.__msg_client.build_req_status_msg([], PlayerStatus.NoTake)
        self.__network_handler.enqueue_message(str(self.__msg_client))

    def stolean(self):
        self.__msg_client.build_req_status_msg([], PlayerStatus.NoShare)
        self.__network_handler.enqueue_message(str(self.__msg_client))

    def share_red2(self):
        self.__msg_client.build_req_status_msg([], PlayerStatus.Share2)
        self.__network_handler.enqueue_message(str(self.__msg_client))

    def hand_out(self, cards):
        if len(self.get_owned_pokers()) == len(cards) and len(cards) != 0:
            logger.info("Player [{}] has run out, final cards {}".format(self.get_player_name(), cards))
            self.__msg_client.build_req_status_msg(cards, PlayerStatus.RunOut)
        else:
            self.__msg_client.build_req_status_msg(cards, PlayerStatus.Handout)

        self.__network_handler.enqueue_message(str(self.__msg_client))

    def __str__(self):
        return self.__name + " seat in pos " + str(self.__pos) \
               + " has cards " + ' '.join(self.__owned_pokers)


# listen_server(authentication & ROOM -- users, rules.)  >>
# ServerPlayer(name, ws) (send_message, recv_message, heart_beat)
class ServerPlayer(Player):
    def __init__(self, name, pos, ws):
        super().__init__(name, pos, ws)
        self.__room = None
        self.__send_out_queue = queue.Queue()

    def set_room(self, room):
        self.__room = room

    async def setup_message_loop(self):
        logger.info("ServerPlayer [" + self.get_player_name() + "] setup message loop")
        task1 = asyncio.create_task(self.heartbeat())
        task2 = asyncio.create_task(self.recv_msg())
        # task3 = asyncio.create_task(self.send_msg())
        await task1
        await task2
        # await task3

    async def heartbeat(self):
        while True:
            try:
                await self.get_websocket().send('{"action":"pong"}')
                logger.debug('Server sent to user [' + self.get_player_name() + '] ---> {"action":"pong"}')
            except websockets.exceptions.ConnectionClosedError:
                await self.__room.clear_user(self.get_player_pos(), "hearbeat websockets.exceptions.ConnectionClosedError")
                break
            except websockets.exceptions.ConnectionClosedOK:
                await self.__room.clear_user(self.get_player_pos(), "hearbeat websockets.exceptions.ConnectionClosedOK")
                break
            except Exception as e:
                logger.fatal("heartbeat meet exception " + str(e))
                break
            await asyncio.sleep(5)

    async def send_msg(self, message):
        logger.info("Player [" + self.get_player_name() + "] send message ----> " + message)
        await self.get_websocket().send(message)

    def hand_out_cards(self, hand_out_cards):
        new_cards = []
        for card in self.get_owned_pokers():
            if card in hand_out_cards:
                hand_out_cards.remove(card)
            else:
                new_cards.append(card)
        self.set_player_owned_pokers(new_cards)

    async def recv_msg(self):
        while True:
            try:
                recv_text = await self.get_websocket().recv()
                msg = json.loads(recv_text)

                if msg["action"] == "ping":
                    logger.debug("Player [{}] received ping from client".format(self.get_player_name()))
                    continue

                logger.info("Server user [{}] received content <--- {}".format(self.get_player_name(), recv_text))

                if msg['action'] == "status":
                    self.set_player_status(PlayerStatus(msg['req_status']))

                logger.info("Server received User [{}] pos {} status {}".format(self.get_player_name(),
                                                                                self.get_player_pos(),
                                                                                self.get_player_status()))

                if self.get_player_status() == PlayerStatus.Logined.value:
                    self.set_notify_message("上线了")
                elif self.get_player_status() == PlayerStatus.Started.value:
                    self.set_notify_message("准备好了")
                # received take2 or no take.
                # 有人抢红2 。
                elif self.get_player_status() == PlayerStatus.SingleOne.value:
                    self.__room.update_active_user_pos(self.get_player_pos())
                    for pos, new_player in enumerate(self.__room.users()):
                        new_player.set_player_status(PlayerStatus.Handout)

                        # 移动牌。
                        if pos != self.get_player_pos():
                            new_player.handout_taken_red2()

                    while self.get_owned_pokers().count(48) < 2:
                        self.received_added_red2()
                        # 通知 所有 用户 有人打独。TODO
                    self.set_notify_message("在打独")
                    logger.info("After take2 we get pokers {}".format(self.get_owned_pokers()))
                # 不抢红2.
                elif self.get_player_status() == PlayerStatus.NoTake.value:
                    notake_count = 0
                    for pos, new_player in enumerate(self.__room.users()):
                        if new_player.get_player_status() == PlayerStatus.NoTake.value:
                            notake_count += 1

                    # always move to next user.
                    self.__room.move_to_next_player()
                    self.set_notify_message("不抢")
                    if notake_count == 4:
                        for pos, new_player in enumerate(self.__room.users()):
                            if new_player.get_owned_pokers().count(48) == 2:
                                new_player.set_player_status(PlayerStatus.Share2)
                            else:
                                new_player.set_player_status(PlayerStatus.Handout)
                elif self.get_player_status() == PlayerStatus.Share2.value:
                    # move 2, and set message.
                    self.hand_out_cards([48])
                    face_pos = (self.get_player_pos() + 2) % 4
                    self.__room.users()[face_pos].received_added_red2()
                    self.__room.users()[face_pos].set_notify_message("从对家接收一个红2")
                    self.set_player_status(PlayerStatus.Handout)
                    self.set_notify_message("让出一个红2给对家")
                elif self.get_player_status() == PlayerStatus.NoShare.value:
                    self.set_player_status(PlayerStatus.Handout)
                elif self.get_player_status() == PlayerStatus.Handout.value:
                    logger.info("We switched to Handout state")
                    hand_out_cards = msg["handout_pokers"]
                    issued_pokers = copy.deepcopy(hand_out_cards)
                    self.__room.move_to_next_player()
                    if len(hand_out_cards) > 0:
                        self.set_notify_message("出牌{}张".format(len(hand_out_cards)))
                        self.hand_out_cards(hand_out_cards)
                        self.__room.set_center_pokers(issued_pokers, self.get_player_pos())
                    else:
                        self.set_notify_message("过牌")
                elif self.get_player_status() == PlayerStatus.RunOut.value:
                    logger.info("We received user {} run out".format(self.get_player_name()))
                    # TODO should we move to next player ?
                    pass


                # room broad case all this user started.
                # broadcast user status.
                await self.__room.broadcast_user_status(self.get_player_pos())

                # check start the game.
            except websockets.exceptions.ConnectionClosedError:
                await self.__room.clear_user(self.get_player_pos(),
                                             "recv_msg websockets.exceptions.ConnectionClosedError")
                break
            except websockets.exceptions.ConnectionClosedOK:
                await self.__room.clear_user(self.get_player_pos(), "recv_msg websockets.exceptions.ConnectionClosedOK")
                break
            except Exception as e:
                logger.fatal("Server is meet exception " + str(e))
                break
