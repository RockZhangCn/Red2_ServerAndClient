import json
import random
from abc import abstractmethod, ABCMeta

from common.card import Card, CardMode
from common.message import ServerMessage
from common.player import ServerPlayer
from common.player_status import PlayerStatus, GameResult
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
        self.__offline_player_pos = -1
        self.__runout_order = []
        self.__game_mode = -1  # 22/13

    def reset_room_data(self):
        self.__game_started = False
        self.__center_pokers_owner_pos = -1
        self.__room_players = [None, None, None, None]
        self.__center_pokers = []
        self.__runout_order = []
        self.__game_mode = -1  # 22/13

        logger.info("Room id {} is reset game data".format(self.__room_id))

    def clear_runout_order(self):
        self.__runout_order.clear()

    def set_center_pokers(self, cards, owner_pos):
        logger.info("Server set center user pos [ {} ] issued pokers {}".format(owner_pos, cards))
        self.__center_pokers = cards
        self.__center_pokers_owner_pos = owner_pos
        self.__center_mode = CardMode.value(cards)

    def judge_game_over(self, run_out_player_pos):
        self.__runout_order.append(run_out_player_pos)
        red2_score = 0
        non_red_score = 0
        if self.__game_mode == 22:
            for i in self.__runout_order:
                if self.__room_players[i].red2_count() > 0:
                    red2_score += (4 - i)
                else:
                    non_red_score += (4 - i)

            if red2_score == 5 and non_red_score == 5:
                return GameResult.Peace

            if red2_score > 4:
                logger.info("Red2 win")
                return GameResult.Red2Win

            if non_red_score > 4:
                logger.info("Non red2 win")
                return GameResult.NonRed2Win
            return GameResult.InProgress

        elif self.__game_mode == 13:
            if self.__room_players[run_out_player_pos].red2_count() > 0:
                logger.info("red2 win")
                return GameResult.Red2Win
            else:
                logger.info("Non red2 win")
                return GameResult.NonRed2Win

    def room_id(self):
        return self.__room_id

    def set_game_mode(self, mode):
        logger.info("We are in {} mode".format(mode))
        self.__game_mode = mode

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

    async def broadcast_message(self, message):
        for player in self.users():
            if player is None or (player.get_player_status() == PlayerStatus.Offline):
                continue
            await player.send_msg(message)

    # offline restore to online.
    async def update_user_websocket(self, name, ws):
        logger.warning("We update_user_websocket name [" + name + "]")
        find_player = None
        for player in self.users():
            if player is None:
                continue
            if player.get_player_name() == name and player.get_player_status() == PlayerStatus.Offline:
                player.set_websocket(ws)
                find_player = player
                break

        if find_player is None:
            logger.error("update_user_websocket get None player")
            return False, "Server:user has logged in, don't login twice."
        # build seated message.
        find_player.set_notify_message("重新上线了")
        find_player.restore_backup_status()
        # send restore message.
        logger.info("User {} restore online to broadcast".format(find_player.get_player_name()))
        await self.broadcast_user_status(find_player.get_player_pos())
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
                            "offline_pos": self.__offline_player_pos,
                            "status_all": user_status_info}

        s = json.dumps(game_status_data)
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
                    self.__offline_player_pos = pos
                    user.save_backup_status()
                    user.set_player_status(PlayerStatus.Offline)
                    user.set_notify_message("断线了")
                    logger.info("We set user [{}] in Offline status ".format(user.get_player_name()))
                    await self.broadcast_user_status(-1)
                    self.__offline_player_pos = -1
                elif user.get_player_status() != PlayerStatus.Offline:
                    clear_user = user
                    self.__offline_player_pos = pos
                    logger.debug(
                        "clear_user pos {} there are {} players for reason {}".format(pos, self.get_user_count(),
                                                                                      reason))
                    clear_user.set_player_status(PlayerStatus.Unlogin)
                    user.set_notify_message("退出房间了")
                    clear_name = clear_user.get_player_name()
                    self.__room_players[pos] = None
                    await self.broadcast_user_status(-1)
                    logger.info("we clear user [ {} ] left {} users".format(clear_name, self.get_user_count()))
                    self.__offline_player_pos = -1
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
