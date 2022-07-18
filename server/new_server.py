#!/usr/bin/env python

import asyncio
import json
import os
import sys

import websockets

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from common.message import Message
from log.log import logger
from server.room import RoomImpl


# GameEngine(login & session_restore) || SingleRoom
class GameServer(object):
    VALID_USERS = ("nian", "wei", "long", "gao")

    def __init__(self, address, port):
        self.__room_id_index = 0
        self.__room_list = []
        self.create_new_room()  # First room for use.
        self.__server_address = address
        self.__server_port = port

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

            if True or player_name in GameServer.VALID_USERS:
                for room in self.__room_list:
                    if room.is_user_online(player_name):
                        return False, "Repeat Login."

                # user is OffLine.
                room_id = self.get_room_id_by_player_name(player_name)
                # logger.debug("User [ " + player_name + " ] logined assigned room " + str(room_id))
                if room_id == -1:
                    room_id = self.assign_room_id(player_name)
                    logger.info("User [ " + player_name + " ] new login assigned room " + str(room_id))
                    # new login ,assign fixed room and position.
                    return await self.__room_list[room_id].assign_new_player(player_name, websocket)
                else:
                    # network restore,
                    logger.info("User [ " + player_name + " ] restore session assigned room " + str(room_id))
                    return await self.__room_list[room_id].update_user_websocket(player_name, websocket)
            else:
                return False, "Server: invalid user!"
        except websockets.exceptions.ConnectionClosedError:
            logger.error("Server check_permit exception websockets.exceptions.ConnectionClosedError")
            return False, "Server check_permit exception websockets.exceptions.ConnectionClosedError"
        except websockets.exceptions.ConnectionClosedOK:
            logger.error("check_permit exception websockets.exceptions.ConnectionClosedOK")
            return False, "Server check_permit exception websockets.exceptions.ConnectionClosedOK"
        except Exception as e:
            logger.error("check_permit exception " + str(e))
            return False, "Server check_permit exception " + str(e)

    # 服务器端主逻辑
    # websocket和path是该函数被回调时自动传过来的，不需要自己传
    async def main_logic(self, websocket, path):
        logger.info("received a new websocket {}".format(hash(websocket)))
        # 在这个过程中已经建立好了后续的通信，这里可以继续接收其他的新接入用户
        result, message = await self.check_permit(websocket)
        if result:
            # new serverplayer.
            pass
        else:
            msg = {
                "action": "network_issue",
                "position": -1,
                "pokers": [],
                "status": -1,
                "message": message
            }
            await websocket.send(json.dumps(msg))

    def run(self):
        # 把ip换成自己本地的ip
        start_server = websockets.serve(self.main_logic, self.__server_address, self.__server_port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    ipaddress = "0.0.0.0"
    port = 5678
    logger.info("New Server is running address {} port {}....".format(ipaddress, port))
    game_server = GameServer(address=ipaddress, port=5678)
    game_server.run()
