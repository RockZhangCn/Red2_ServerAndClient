import asyncio
import json

import websockets

from common.message import Message
from log.log import logger
from server.room import RoomImpl


# GameEngine(login & session_restore) || SingleRoom
class GameServer(object):
    VALID_USERS = ("nian", "wei", "long", "gao")

    def __init__(self):
        self.__room_id_index = 0
        self.__room_list = []
        self.create_new_room()  # First room for use.

    def create_new_room(self):
        new_room = RoomImpl(self.__room_id_index)
        self.__room_id_index += 1
        self.__room_list.append(new_room)
        return new_room.room_id()

    def get_room_id_by_player_name(self, name):
        for room in self.__room_list:
            if room.is_user_logined(name):
                return room.room_id()

        return -1

    def assign_room_id(self, name):
        for room in self.__room_list:
            if not room.is_room_full():
                return room.room_id()

        # create a new room.
        return self.create_new_room()

    # login & assign room.
    async def check_permit(self, websocket):
        try:
            recv_str = await websocket.recv()
            logger.info(str(hash(websocket)) + " Received new user message ----> " + recv_str)
            message = Message.from_string(recv_str)
            player_name = message.get_player_name()

            if player_name in GameServer.VALID_USERS:
                room_id = self.get_room_id_by_player_name(player_name)
                # logger.debug("User [ " + player_name + " ] logined assigned room " + str(room_id))
                if room_id == -1:
                    room_id = self.assign_room_id(player_name)
                    logger.debug("User [ " + player_name + " ] new login assigned room " + str(room_id))
                    # new login ,assign fixed room and position.
                    return await self.__room_list[room_id].assign_new_player(player_name, websocket)
                else:
                    # network restore,
                    logger.info("User [ " + player_name + " ] restore session assigned room " + str(room_id))
                    return await self.__room_list[room_id].update_user_websocket(player_name, websocket)
            else:
                msg = {
                    "action": "network_issue",
                    "position": -1,
                    "pokers": "",
                    "pokernum": 0,
                    "status": -1,
                    "message": "Invalid user " + player_name
                }

                await websocket.send(json.dumps(msg))
                return False
        except websockets.exceptions.ConnectionClosedError:
            logger.error("check_permit exception websockets.exceptions.ConnectionClosedError")
            return False
        except websockets.exceptions.ConnectionClosedOK:
            logger.error("check_permit exception websockets.exceptions.ConnectionClosedOK")
            return False

    # 服务器端主逻辑
    # websocket和path是该函数被回调时自动传过来的，不需要自己传
    async def main_logic(self, websocket, path):
        logger.info("received a new websocket {}".format(hash(websocket)))
        if await self.check_permit(websocket):
            # new serverplayer.
            pass
        else:
            msg = {
                "action": "network_issue",
                "position": -1,
                "pokers": "",
                "pokernum": 0,
                "status": -1,
                "message": "Server main_logic check_permit failed"
            }
            await websocket.send(json.dumps(msg))

    def run(self):
        # 把ip换成自己本地的ip
        start_server = websockets.serve(self.main_logic, '127.0.0.1', 5678)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    logger.info("New Server is running....")
    game_server = GameServer()
    game_server.run()
