# from client.client_io import send_msg_to_server

# client input name, seat.
# c->login(name)   --> seated pos --> draw seat profile
#  msg: { action : login, name : player_name }
#  resp: { position: 3//-1 (login failed) }

# c->prepare(name)  //received all prepare.
#                --> game start
#                --> dispatch pokers. (isFirst)
# msg : { action: prepare, name: player_name }
#  resp: { received_cards:["3", "8", "9"] , state: occupy ,isFirst: True}

# section 1 Occupy red 2
#  msg : { action : occupy/negative, name: player_name }
# client isFirst ?  occupy or negative
#                   s->next player
# resp : { received_cards:["3", "8", "9"], state: occupy ,isFirst: True}

# 服务器主动推送：
# resp : { received_cards:["3", "8", "9"], state: giveup}
# section 2 giveup red 2
# msg : { action:give2／negative, name:player_name }
#                  --> dispatch pokers and first player.
# resp : { received_cards:["3", "8", "9"], state: running , isFirst: True}


# secion 3 running
#               first player pending
# msg : {　action: handout, cards:["7","8","9"] , name:player_name }  winner set.
# resp : { state:running, success: true/false,  isFirst:false }  draw cards out.
# resp : { state:running, isFirst:true,  pos_cards: ["1"], pos : 0 }

import json

from log.log import logger


# this is a map internally.
class Message(object):
    def __init__(self, player_name):
        self.current_msg = {}
        self.set_player_name(player_name)

    @classmethod
    def from_string(cls, message_str):
        try:
            current_msg = json.loads(message_str)
            if current_msg['action'] == "ping":
                return cls("ping")

            msg_obj = cls(current_msg['player_name'])
            return msg_obj
        except Exception as e:
            logger.error("We meet an exception " + str(e))

    def set_attribute(self, name, value):
        self.current_msg[name] = value

    def set_player_name(self, name):
        self.current_msg['player_name'] = name

    def set_action(self, action):
        self.current_msg['action'] = action

    def set_extra_data(self, data):
        self.current_msg['extra_data'] = data

    def get_player_name(self):
        return self.current_msg['player_name']

    def get_action(self):
        return self.current_msg['action']

    def get_extra_data(self):
        return self.current_msg['extra_data']

    def __str__(self):
        return json.dumps(self.current_msg)


class ServerMessage(Message):
    def __init__(self, server_player):
        Message.__init__(self, server_player.get_player_name())
        self.__server_player = server_player

    def build_resp_status_message(self):
        self.current_msg["action"] = "resp_status"
        self.current_msg["position"] = self.__server_player.get_player_pos()
        self.current_msg["pokers"] = self.__server_player.get_owned_pokers()
        self.current_msg["status"] = self.__server_player.get_player_status().value
        self.current_msg['message'] = self.__server_player.get_notify_message()
        self.current_msg['result'] = self.__server_player.get_game_result().value

    def to_dict(self):
        return self.current_msg


class ClientMessage(Message):
    def __init__(self, player_name):
        Message.__init__(self, player_name)

    def build_req_status_msg(self, handout_pokers, status):
        self.current_msg["action"] = "status"
        self.current_msg["handout_pokers"] = handout_pokers
        self.current_msg["req_status"] = status
        return self

    def clear_current_msg(self):
        self.current_msg = {}

    def __str__(self):
        data = json.dumps(self.current_msg)
        return data

    def to_dict(self):
        return self.current_msg

    # def send(self):
    #     send_msg_to_server(str(self))


if __name__ == "__main__":
    client = ClientMessage("rock")
    client.build_login_msg()
    client.set_login_name()
    logger.info(str(client))

    ms = Message()
    ms.set_attribute("name", "zhang")
    ms.set_attribute("player_name", "zshou")

    messgage = Message.from_string(str(ms))
    logger.info("Revert name is " + messgage.get_player_name())
