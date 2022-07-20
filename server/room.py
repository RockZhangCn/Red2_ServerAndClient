import json
import random
from abc import abstractmethod, ABCMeta

import websockets

from common.card import Card, CardMode
from common.message import ServerMessage
from common.player import ServerPlayer
from common.player_status import PlayerStatus
from log.log import logger


class AbstractGameRoom(metaclass=ABCMeta):
    @abstractmethod
    def users(self):
        pass

    @abstractmethod
    def room_id(self):
        pass

    @abstractmethod
    def assign_new_player(self, name, ws):
        pass

    @abstractmethod
    def broadcast_message(self, message):
        pass

    @abstractmethod
    def assign_initial_pokers(self):
        pass

    @abstractmethod
    def clear_user(self, ws, reason):
        pass


class RoomImpl(AbstractGameRoom):
    def __init__(self, id):
        self.__game_started = False
        self.__center_pokers_owner_pos = -1
        self.__room_id = id
        self.__room_players = [None, None, None, None]
        self.__center_pokers = []  # string list, 0*3
        self.__current_order_pos = random.randint(0, 10000) % 4
        self.__center_mode = CardMode.MODE_INVALID
        logger.info("Room handout order get current order pos " + str(self.__current_order_pos))
        self.__last_restore_broadcast_message = None

    def reset_room_data(self):
        self.__game_started = False
        self.__center_pokers_owner_pos = -1
        self.__room_players = [None, None, None, None]
        self.__center_pokers = []
        logger.info("Room id {} is reset game data".format(self.__room_id))

    def set_center_pokers(self, cards, owner_pos):
        logger.info("Server set center user pos [ {} ] issued pokers {}".format(owner_pos, cards))
        self.__center_pokers = cards
        self.__center_pokers_owner_pos = owner_pos
        self.__center_mode = CardMode.value(cards)

    def room_id(self):
        return self.__room_id

    def move_to_next_player(self):
        self.__current_order_pos = (self.__current_order_pos + 1) % 4
        if self.__room_players[self.__current_order_pos] is None:
            return
        if self.__room_players[self.__current_order_pos].get_player_status() == PlayerStatus.RunOut:
            self.move_to_next_player()
        logger.info("Server room move_to_next_player pos {}".format(self.__current_order_pos))

    def is_room_full(self):
        return self.get_user_count() == 4

    def users(self):
        return self.__room_players

    def is_user_online(self, player_name):
        for player in self.__room_players:
            if player is not None and player.get_player_name() == player_name:
                return player.get_player_status() != PlayerStatus.Offline

        return False

    def is_user_logined(self, player_name):
        for player in self.__room_players:
            if player is not None and player.get_player_name() == player_name:
                if player.get_player_status() != PlayerStatus.Offline:
                    logger.warning("User [{}] relogined due to incorrect status {}".format(player_name,
                                                                                           player.get_player_status()))
                else:
                    return True

        return False

    def assign_initial_pokers(self):
        all_cards = Card.all_cards
        random.shuffle(all_cards)
        logger.info("We begin to dispatcher_pokers start ")
        assert (self.get_user_count() == 4)
        for pos, player in enumerate(self.users()):
            if player is None:
                logger.error("assign_initial_pokers get None Player in list")
                continue
            # range step 4.
            player_cards = [all_cards[x + pos] for x in range(0, len(all_cards), 4)]
            player_cards.sort(reverse=True)
            logger.info("Player [ {} ] at pos {} dispatched cards {}".format(player.get_player_name(),
                                                                             pos, player_cards))
            player.set_player_owned_pokers(player_cards)
            player.set_has_red2(player_cards.count(48) > 0)

    async def broadcast_message(self, message):
        for player in self.users():
            if player is None or (player.get_player_status() == PlayerStatus.Offline):
                continue
            await player.send_msg(message)

    def get_user_status_from_restore_message(self, name):
        if self.__last_restore_broadcast_message:
            for player in self.__last_restore_broadcast_message["status_all"]:
                if player["player_name"] == name:
                    return PlayerStatus(player["status"])

        return PlayerStatus.Handout

    # offline restore to online.
    async def update_user_websocket(self, name, ws):
        logger.warning("We update_user_websocket name [" + name + "]")
        find_player = None
        for player in self.users():
            if player is None:
                continue
            if player.get_player_name() == name and player.get_player_status() == PlayerStatus.Offline:
                player.set_websocket(ws)
                status = self.get_user_status_from_restore_message(name)
                player.set_player_status(status)
                find_player = player
                break

        if find_player is None:
            logger.error("update_user_websocket get None player")
            return False, "Server:user has logged in, don't login twice."
        # build seated message.
        find_player.set_notify_message("重新上线了")
        self.__last_restore_broadcast_message['recover_pos'] = find_player.get_player_pos()
        # send restore message.
        logger.info("User {} restore online to broadcast".format(find_player.get_player_name()))
        await self.broadcast_restore_message()
        # player setup heartbeat and send/recv.
        await find_player.setup_message_loop()
        return True, "Success relogin."

    def update_active_user_pos(self, pos):
        self.__current_order_pos = pos

    async def broadcast_user_status(self, reply_player_pos):
        started_user_count = 0
        for pos, new_player in enumerate(self.__room_players):
            if new_player is None:
                continue
            if new_player.get_player_status() == PlayerStatus.Started:
                started_user_count += 1

        if started_user_count == 4:
            self.assign_initial_pokers()
            self.__game_started = True

        # build status message.
        user_status_info = []
        for pos, new_player in enumerate(self.__room_players):
            if new_player is None:
                continue
            # 切换到出牌状态 。
            if started_user_count == 4:
                new_player.set_player_status(PlayerStatus.SingleOne)

            if new_player.get_player_status() == PlayerStatus.RunOut and len(new_player.get_owned_pokers()) == 0:
                new_player.set_player_status(PlayerStatus.RunOut)
                new_player.set_notify_message("出完了")

            status_msg = ServerMessage(new_player)
            status_msg.build_resp_status_message()
            user_status_info.append(status_msg.to_dict())

        # Not start ,there is no order.
        actual_order_pos = -1
        if self.__game_started:
            actual_order_pos = self.__current_order_pos

        game_status_data = {"action": "status_broadcast",
                            "notify_pos": reply_player_pos,  # 回用户复用户的ui消息
                            "active_pos": actual_order_pos,  # current player handout. or do decision.
                            "center_poker_issuer": self.__center_pokers_owner_pos,  # center pokers handed by who ?
                            "center_pokers": self.__center_pokers,
                            "center_mode": self.__center_mode,
                            "recover_pos": -1,
                            "status_all": user_status_info}
        self.__last_restore_broadcast_message = game_status_data
        s = json.dumps(game_status_data)
        logger.info("Server broad_cast_user_status {} users ---> {}".format(self.get_user_count(), s))
        await self.broadcast_message(s)

    async def broadcast_restore_message(self):
        if self.__last_restore_broadcast_message:
            s = json.dumps(self.__last_restore_broadcast_message)
            logger.info("Server broad_cast_user_status {} users ---> {}".format(self.get_user_count(), s))
            await self.broadcast_message(s)

    async def assign_new_player(self, name, ws):
        new_player = ServerPlayer(name, pos=-1, ws=ws)
        if self.get_user_count() > 3:
            return False, "Server:Single room is full, can't seat new user"

        new_player.set_room(self)
        pos = -1
        for idx, player in enumerate(self.__room_players):
            if player is None:
                self.__room_players[idx] = new_player
                pos = idx
                break

        new_player.set_player_pos(pos)
        new_player.set_notify_message("Seat pos {}".format(pos))

        # build status message.
        await self.broadcast_user_status(pos)
        await new_player.setup_message_loop()

        return True, "Success"

    async def clear_user(self, pos, reason):

        for user in self.__room_players:
            if user is None:
                continue

            # find the user.
            if user.get_player_pos() == pos:
                # The game is in progress, exit will be marked as offline.
                if user.get_player_status() in (
                        PlayerStatus.SingleOne, PlayerStatus.Share2, PlayerStatus.Handout) and \
                        self.__game_started:
                    user.set_player_status(PlayerStatus.Offline)
                    user.set_notify_message("断线了")
                    logger.info("We set user [{}] in Offline status ".format(user.get_player_name()))
                    await self.broadcast_user_status(-1)
                else:
                    clear_user = user
                    logger.debug("clear_user pos {} there are {} players for reason {}".format(pos, self.get_user_count(), reason))
                    clear_user.set_player_status(PlayerStatus.Unlogin)
                    user.set_notify_message("退出房间了")
                    clear_name = clear_user.get_player_name()
                    self.__room_players[pos] = None
                    await self.broadcast_user_status(-1)
                    logger.info("we clear user [ {} ] left {} users".format(clear_name, self.get_user_count()))

                    # last user, release room.
                    if self.get_user_count() == 0:
                        self.reset_room_data()

                return

    def get_user_count(self):
        count = 0
        for user in self.__room_players:
            if user is None:
                continue
            count += 1
        return count