import asyncio
import json
import queue
import threading

import websockets

from common.message import ClientMessage
from common.player_status import PlayerStatus
from log.log import logger


class NetworkHandler(threading.Thread):
    def __init__(self, user_id, recv_queue):
        threading.Thread.__init__(self)
        self.__event_loop = None
        self.__client_player_name = user_id
        self.running = True
        self.recv_queue = recv_queue
        self.send_queue = queue.Queue()

    def destroy(self):
        self.running = False

    def enqueue_message(self, message):
        logger.debug("Client enqueue_message to send " + message)
        self.send_queue.put(message)

    async def auth_system(self, websocket):
        try:
            cm = ClientMessage(self.__client_player_name)
            cm.build_req_status_msg([], PlayerStatus.Logined)
            logger.info("Client login send string " + str(cm))
            await websocket.send(str(cm))
            response_str = await websocket.recv()
            logger.info("Client auth_system received string " + response_str)
            msg = json.loads(response_str)
            self.recv_queue.put(msg)

            if 'network_issue' == msg['action']:
                return False
            else:
                return True
        except websockets.exceptions.ConnectionClosedError:
            logger.info("Client auth_system websockets.exceptions.ConnectionClosedError")
            self.recv_queue.put({"action": "login", "extra_data": "connect to server failed"})
            return False

    async def dispatcher(self, ws):
        while self.running:
            message = await ws.recv()
            msg = json.loads(message)

            # ignore heartbeat message.
            if msg['action'] == "pong":
                logger.debug("Client [{}] received Server {} message".format(self.__client_player_name, message))
                continue
            logger.info("Client [{}]<----- received messsage:{}".format(self.__client_player_name, message))

            self.recv_queue.put(msg)

    async def send_request(self, ws):
        while self.running:
            send_data = None
            # logger.debug("client io in send request")
            try:
                if not self.send_queue.empty():
                    send_data = self.send_queue.get()
                    # logger.debug("client io in send request with send_data " + send_data)

                if send_data is not None:
                    logger.debug("Client [{}] will ----> send content:{}".format(self.__client_player_name, send_data))
                    await ws.send(send_data)
                else:
                    # logger.warning("client io in send request asyncio.sleep")
                    await asyncio.sleep(1)
            except Exception as e:
                logger.fatal("client player send_request exception : {}".format(str(e)))

    async def heartbeat(self, ws):
        while self.running:  # 不断验证信号量，若收到心跳包，则信号量应该被分发器更改为True，返回心跳包，并修改信号量为False
            self.enqueue_message('{"action":"ping"}')
            # logger.debug("Client enqueued heartbeat " + '''{"action":"ping"}''')
            await asyncio.sleep(5)

    async def main_logic(self):
        try:
            async with websockets.connect('ws://127.0.0.1:5678') as ws:
                auth_result = await self.auth_system(ws)
                logger.info("auth_system return {}".format(auth_result))
                if auth_result:
                    task1 = asyncio.create_task(self.dispatcher(ws))
                    task2 = asyncio.create_task(self.heartbeat(ws))
                    task3 = asyncio.create_task(self.send_request(ws))
                    await task1
                    await task2
                    await task3
        except Exception as e:
            logger.error("main_logic exception :" + str(e))
            msg = {
                "action": "network_issue",
                "position": -1,
                "pokers": "",
                "status": -1,
                "message": str(e)
            }

            self.recv_queue.put(msg)

    def run(self):
        self.__event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__event_loop)
        self.__event_loop.run_until_complete(self.main_logic())
        # self.__event_loop.run_forever()
