#!/usr/bin/env python

import os
import sys
import tkinter as tk  # 使用Tkinter前需要先导入
import tkinter.messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from PIL import Image, ImageTk
from PIL.ImageTk import PhotoImage

from common.player import ClientPlayer
from common.player_status import PlayerStatus
from log.log import logger


class UserUIPanel(object):
    def __init__(self, name_widget, message_widget, show_timer, show_pokers):
        self.name_widget = name_widget
        self.message_widget = message_widget
        self.timer_func = show_timer
        self.poker_func = show_pokers

    def __set_name(self, value):
        self.name_widget.set(value)

    name = property(fset=__set_name)

    def __set_message(self, value):
        self.message_widget.set(value)

    message = property(fset=__set_message)

    def __show_timer(self, show):
        if show:
            self.timer_func()

    timer = property(fset=__show_timer)

    def __show_pokers(self, cards):
        self.poker_func(cards)

    pokers = property(fset=__show_pokers)


class Application(object):
    def __init__(self, window):
        self.__window = window
        self.width = window.winfo_screenwidth()
        self.__window.protocol("WM_DELETE_WINDOW", self.close_all)

        self.__center_pokers_list = []
        self.__selected_poker_list = list()
        self.__owned_poker_list = []
        self.bottom_canvas_draw_next_pos = 0
        self.we_seat_pos = -1
        self.player = None

        self.__user_ui_panel = [None, None, None, None]

        self.timer_show = ImageTk.PhotoImage(
            Image.open(SCRIPT_DIR + f"/image/timer.png").resize((80, 105), Image.ANTIALIAS))

        # background pokers.
        self.image_background = ImageTk.PhotoImage(
            Image.open(SCRIPT_DIR + f"/image/green_back.png").resize((120, 180), Image.ANTIALIAS))

        # poker index.
        self.images = []
        for i in range(54):
            self.images.append(
                ImageTk.PhotoImage(
                    Image.open(SCRIPT_DIR + f"/image/{i}.png").resize((120, 180),
                                                                      Image.ANTIALIAS))
            )

        root = window

        # 先横分　上　中　下　info，　四块。
        # 上部
        self.top_user_panel = tk.Frame(root, width=self.width, height=250)
        self.top_user_panel.pack(side="top", padx=1, pady=1, fill="x")

        self.top_user_name_value = tk.StringVar()
        self.top_user_name_value.set("null")
        self.top_name_label = tk.Label(self.top_user_panel, textvariable=self.top_user_name_value, font=("黑体", 16))
        self.top_name_label.pack(side="top")

        self.top_message_value = tk.StringVar()
        self.top_message_value.set("null")
        top_info_label = tk.Label(self.top_user_panel, bg="#FFFFE0", textvariable=self.top_message_value,
                                  font=("黑体", 16))
        top_info_label.pack(side="top", fill="x")

        # self.poker_canvas
        self.top_poker_canvas = tk.Canvas(self.top_user_panel, width=self.width, height=220)
        self.top_poker_canvas.pack(side="top", anchor="center")

        self.__user_ui_panel[2] = UserUIPanel(self.top_user_name_value, self.top_message_value, self.show_top_timer,
                                              self.show_top_pokers)
        # 　中部　　　又纵分了　左　中　右　三大部分。
        main_panel = tk.Frame(root)
        main_panel.pack(side="top", padx=1, pady=1, fill="both", expand=True)

        # 　下部　
        self.bottom_user_panel = tk.Frame(root, width=self.width, height=350)
        self.bottom_user_panel.pack(side="top", padx=1, pady=1, fill="x")

        # self.poker_canvas
        self.bottom_poker_canvas = tk.Canvas(self.bottom_user_panel, width=self.width, height=220)
        self.bottom_poker_canvas.pack(side="top", anchor="center")

        self.bottom_button_panel = tk.Frame(self.bottom_user_panel, width=self.width, height=100)
        self.bottom_button_panel.pack(side="top", anchor="n")

        self.user_button_start = tk.Button(self.bottom_button_panel, text="开始", font=('Arial', 16),
                                           command=self.button_start)
        self.user_button_start.pack(side="left", padx=10)

        self.user_button_handout = tk.Button(self.bottom_button_panel, text="出牌", font=('Arial', 16),
                                             command=self.button_handout)
        self.user_button_handout.pack(side="left", padx=10)

        self.user_button_skip = tk.Button(self.bottom_button_panel, text="过牌", font=('Arial', 16),
                                          command=self.button_skip)
        self.user_button_skip.pack(side="left", padx=10)

        self.user_button_alone = tk.Button(self.bottom_button_panel, text="打独", font=('Arial', 16),
                                           command=self.button_hijack_2)
        self.user_button_alone.pack(side="left", padx=10)

        self.user_button_notake = tk.Button(self.bottom_button_panel, text="不抢", font=('Arial', 16),
                                            command=self.button_no_hijack_2)
        self.user_button_notake.pack(side="left", padx=10)

        self.user_button_share = tk.Button(self.bottom_button_panel, text="平分", font=('Arial', 16),
                                           command=self.button_share_2)
        self.user_button_share.pack(side="left", padx=10)

        self.user_button_slient = tk.Button(self.bottom_button_panel, text="偷鸡", font=('Arial', 16),
                                            command=self.button_steal_chicken)
        self.user_button_slient.pack(side="left", padx=10)

        # 底部，　网络链接的一些通常消息展示。
        self.bottom_info = tk.Frame(root, width=self.width, bd=1, relief='groove', bg="#ADD8E6")
        self.bottom_info.pack(side="top", padx=1, pady=1, fill="x")

        label_login_address = tk.Label(self.bottom_info, text="登录地址", font=('Arial', 18), bg="#ADD8E6", height=1,
                                       justify="right")
        label_login_address.pack(side="left", fill="y")

        self.server_address_widget = tk.Entry(self.bottom_info, font=('Arial', 18), width=30)  # 显示成明文形式
        self.server_address_widget.insert(tk.END, 'ws://127.0.0.1:5678')
        self.server_address_widget.pack(side="left", padx=20)

        label_login_address = tk.Label(self.bottom_info, text="用户", font=('Arial', 18), bg="#ADD8E6", height=1,
                                       justify="right")
        label_login_address.pack(side="left", fill="y")

        self.bottom_user_name_value = tk.StringVar()
        self.bottom_user_name_value.set("")
        self.bottom_user_name_widget = tk.Entry(self.bottom_info, textvariable=self.bottom_user_name_value,
                                                font=('Arial', 18),
                                                width=10)  # 显示成明文形式
        self.bottom_user_name_widget.insert(tk.END, 'nian')
        self.bottom_user_name_widget.pack(side="left", padx=20)

        self.user_button_login = tk.Button(self.bottom_info, text="登陆", font=('Arial', 18),
                                           command=self.button_login)
        self.user_button_login.pack(side="left", padx=20, pady=5)

        # 底部填充
        self.bottom_message_value = tk.StringVar()
        self.bottom_message_value.set("no message here.")
        label_info = tk.Label(self.bottom_info, textvariable=self.bottom_message_value, font=('Arial', 18), height=1,
                              bg="#ADD8E6",
                              justify="left")
        label_info.pack(side="left", expand=True, fill="x")

        self.__user_ui_panel[0] = UserUIPanel(self.bottom_user_name_value, self.bottom_message_value,
                                              self.show_bottom_timer,
                                              self.show_bottom_pokers)

        # left panel
        self.left_user_panel = tk.Frame(main_panel)
        self.left_user_panel.pack(side="left", fill="y", anchor="w")

        self.left_user_name_value = tk.StringVar()
        self.left_user_name_value.set("null")
        left_name_label = tk.Label(self.left_user_panel, textvariable=self.left_user_name_value, font=("黑体", 16))
        left_name_label.pack(side="top", fill="x")

        self.left_message_value = tk.StringVar()
        self.left_message_value.set("null")
        left_info_label = tk.Label(self.left_user_panel, bg="#FFFFE0", textvariable=self.left_message_value,
                                   font=("黑体", 16))
        left_info_label.pack(side="top", fill="x")

        # self.poker_canvas
        self.left_poker_canvas = tk.Canvas(self.left_user_panel, width=300)
        self.left_poker_canvas.pack(side="top", fill="y", anchor="center", expand=True)

        self.__user_ui_panel[3] = UserUIPanel(self.left_user_name_value, self.left_message_value,
                                              self.show_left_timer,
                                              self.show_left_pokers)

        # middle panel
        self.center_panel = tk.Frame(main_panel, bd=4, relief='groove', bg="#F0FFF0")
        self.center_panel.pack(side="left", fill="both", expand=True)

        self.center_poker_canvas = tk.Canvas(self.center_panel)
        self.center_poker_canvas.pack(side="top", fill="both", anchor="center", expand=True)

        # right panel
        self.right_user_panel = tk.Frame(main_panel)
        self.right_user_panel.pack(side="right", fill="y", anchor="e")

        self.right_user_name_value = tk.StringVar()
        self.right_user_name_value.set("null")
        right_name_label = tk.Label(self.right_user_panel, textvariable=self.right_user_name_value, font=("黑体", 16))
        right_name_label.pack(side="top", fill="x")

        self.right_message_value = tk.StringVar()
        self.right_message_value.set("null")
        right_info_label = tk.Label(self.right_user_panel, bg="#FFFFE0", textvariable=self.right_message_value,
                                    font=("黑体", 16))
        right_info_label.pack(side="top", fill="x")

        # self.poker_canvas
        self.right_poker_canvas = tk.Canvas(self.right_user_panel, width=300)
        self.right_poker_canvas.pack(side="top", fill="y", anchor="center", expand=True)

        self.__user_ui_panel[1] = UserUIPanel(self.right_user_name_value, self.right_message_value,
                                              self.show_right_timer,
                                              self.show_right_pokers)

        self.disable_buttons()

    def disable_buttons(self):
        self.user_button_skip.config(state="disabled")
        self.user_button_alone.config(state="disabled")
        self.user_button_share.config(state="disabled")
        self.user_button_start.config(state="disabled")
        self.user_button_handout.config(state="disabled")
        self.user_button_notake.config(state="disabled")
        self.user_button_slient.config(state="disabled")

    def close_all(self):
        logger.info("user will go out")
        self.__window.destroy()
        if self.player:
            self.player.destroy()

    def show_bottom_pokers(self, cards):
        # clear all.
        self.bottom_poker_canvas.delete("all")
        self.__selected_poker_list.clear()

        self.bottom_canvas_draw_next_pos = 0
        self.__owned_poker_list = cards
        for idx, card in enumerate(cards):
            x = self.width // 5 + idx * 30
            y = 110  #
            image_id = self.bottom_poker_canvas.create_image(x, y, anchor='e', tags=(card,), image=self.images[card])
            self.bottom_poker_canvas.tag_bind(image_id, '<ButtonRelease-1>', self.poker_click_callback)
            self.bottom_canvas_draw_next_pos = x + 120

        logger.info("Current Poker value list {}".format(self.__owned_poker_list))

    def clear_all_canvas(self):
        self.left_poker_canvas.delete("all")
        self.top_poker_canvas.delete("all")
        self.right_poker_canvas.delete("all")
        self.bottom_poker_canvas.delete("all")

    def clear_all_message(self):
        self.show_right_message("")
        self.show_left_message("")
        self.show_top_message("")
        self.show_bottom_message("")

    def ui_msg_dispatcher(self):
        # refresh the GUI with new data from the queue
        while self.player.has_new_message():
            msg = self.player.recv_queue().get()
            if msg is None:
                logger.warning("ui msg_dispatcher received None")
                break
            logger.info("ui msg_dispatcher received {0}".format(str(msg)))

            if msg['action'] == 'network_issue':
                tkinter.messagebox.showerror(title='登录失败', message=msg['message'])
                self.show_bottom_message(msg['message'])
            elif msg['action'] == "status_broadcast":
                # draw center pokers.
                if len(msg["center_pokers"]) > 0:
                    self.__center_pokers_list = msg["center_pokers"]
                    self.show_center_pokers()
                    logger.info("Server draw the center pokers {}".format(msg["center_pokers"]))

                # login handler
                for seat_player in msg['status_all']:
                    logger.info("user {} seated at pos {} get new status {}".format(seat_player['player_name'],
                                                                                    seat_player['position'],
                                                                                    seat_player['status']))
                    player_name = seat_player['player_name']
                    seat_pos = seat_player['position']
                    player_status = seat_player['status']

                    # self login success.
                    if player_status == PlayerStatus.Logined.value:
                        if self.bottom_user_name_widget.get() == player_name and msg['notify_pos'] == seat_pos:
                            tkinter.messagebox.showinfo(title='登录成功',
                                                        message='欢迎就座, seated pos {}'.format(seat_pos))
                            self.show_bottom_message('登录成功, 位置{}'.format(seat_pos))
                            self.we_seat_pos = seat_pos
                            self.bottom_user_name_widget.config(state="disabled")
                            self.user_button_login.config(state="disabled")
                            self.user_button_start.config(state="active")

                # restore position.
                if self.we_seat_pos == -1:
                    self.we_seat_pos = msg['recover_pos']
                    self.bottom_user_name_widget.config(state="disabled")
                    self.user_button_login.config(state="disabled")
                    self.__selected_poker_list.clear()

                self.clear_all_canvas()

                active_pos = msg["active_pos"]
                if -1 < active_pos < 4:
                    self.__user_ui_panel[(active_pos + 4 - self.we_seat_pos) % 4].timer = True

                for seat_player in msg['status_all']:
                    player_name = seat_player['player_name']
                    seat_pos = seat_player['position']
                    player_status = seat_player['status']

                    layout_index = (seat_pos + 4 - self.we_seat_pos) % 4

                    if player_status == PlayerStatus.Logined.value:
                        if -1 < seat_pos < 4:
                            self.__user_ui_panel[layout_index].name = player_name
                            self.__user_ui_panel[layout_index].message = "上线了"

                    elif player_status == PlayerStatus.Started.value:
                        if -1 < seat_pos < 4:
                            self.__user_ui_panel[layout_index].name = player_name
                            self.__user_ui_panel[layout_index].message = "准备好了"

                    elif player_status == PlayerStatus.Handout.value or player_status == PlayerStatus.SingleOne.value \
                            or player_status == PlayerStatus.NoTake.value or player_status == PlayerStatus.Share2 \
                            or player_status == PlayerStatus.NoShare.value:
                        notify_message = seat_player["message"]
                        cards = seat_player['pokers']
                        if -1 < seat_pos < 4:
                            self.__user_ui_panel[layout_index].name = player_name
                            self.__user_ui_panel[layout_index].message = notify_message
                            self.__user_ui_panel[layout_index].pokers = cards

                        # Button activity status
                        if seat_pos == self.we_seat_pos:
                            # User save the poker lists.
                            self.player.set_player_owned_pokers(cards)

                            if player_status == PlayerStatus.Share2.value:
                                self.user_button_share.config(state="active")
                                self.user_button_slient.config(state="active")

                            if msg['active_pos'] == self.we_seat_pos:
                                self.show_bottom_timer()
                                if player_status == PlayerStatus.SingleOne.value:
                                    # enable single one button
                                    self.user_button_alone.config(state="active")
                                    self.user_button_notake.config(state="active")
                                elif player_status == PlayerStatus.Handout.value:
                                    self.user_button_handout.config(state="active")
                                    # 不是我们出的或没人出过牌，禁用过牌
                                    if msg['center_poker_issuer'] == self.we_seat_pos:
                                        self.user_button_skip.config(state="disabled")
                                    else:
                                        self.user_button_skip.config(state="active")

                    elif player_status == PlayerStatus.RunOut:
                        if -1 < seat_pos < 4:
                            self.__user_ui_panel[(self.we_seat_pos + 4 - seat_pos) % 4].message = "出完了"

        #  timer to refresh the gui with data from the asyncio thread
        self.__window.after(200, self.ui_msg_dispatcher)  # called only once!

    ''''''''''''''''''''''''''''''''''''''''''''''''

    def show_bottom_timer(self):
        self.bottom_poker_canvas.create_image(self.bottom_canvas_draw_next_pos, 110, anchor='e', image=self.timer_show)

    def show_bottom_message(self, message):
        self.bottom_message_value.set(message)

    def show_top_message(self, message):
        self.top_message_value.set(message)

    def show_left_message(self, message):
        self.left_message_value.set(message)

    def show_right_message(self, message):
        self.right_message_value.set(message)

    ####
    def show_left_timer(self):
        self.left_poker_canvas.create_image(150, 20, anchor='n', image=self.timer_show)

    def show_left_pokers(self, cards):
        # only 5 pokers will show real status.
        if len(cards) > 5:
            cards = [3] * 10
        for idx, card in enumerate(cards):
            x = 150
            y = (140 + idx * 20)
            self.left_poker_canvas.create_image(x, y, anchor='n', image=self.image_background)

    def show_right_timer(self):
        self.right_poker_canvas.create_image(150, 20, anchor='n', image=self.timer_show)

    def show_right_pokers(self, cards):
        # only 5 pokers will show real status.
        if len(cards) > 5:
            cards = [3] * 10

        for idx, card in enumerate(cards):
            x = 150
            y = (140 + idx * 20)
            self.right_poker_canvas.create_image(x, y, anchor='n', image=self.image_background)

    def show_top_timer(self):
        # draw timer.
        self.top_poker_canvas.create_image(self.width // 4, 110, anchor='e', image=self.timer_show)

    def show_top_pokers(self, cards):
        self.width = self.__window.winfo_screenwidth()

        # only 5 pokers will show real status.
        if len(cards) > 5:
            cards = [3] * 10

        for idx, card in enumerate(cards):
            x = self.width // 4 + 170 + idx * 30
            y = 110
            self.top_poker_canvas.create_image(x, y, anchor='e', image=self.image_background)

    def show_center_pokers(self):
        self.center_poker_canvas.delete("all")
        self.__center_pokers_list.sort(reverse=True)
        for idx, card in enumerate(self.__center_pokers_list):
            x = 160 + idx * 30
            y = 210  #
            self.center_poker_canvas.create_image(x, y, anchor='e', image=self.images[card])

    def button_login(self):
        logger.info(self.bottom_user_name_widget.get() + " will sit down.")
        self.player = ClientPlayer(self.bottom_user_name_widget.get(), pos=-1, ws=None)
        self.ui_msg_dispatcher()
        self.player.login(address=self.server_address_widget.get())

    def button_start(self):
        if self.player:
            self.player.prepare_ready()
        self.user_button_start.config(state="disabled")

    def poker_click_callback(self, event):
        # all_id = self.bottom_poker_canvas.find_closest(event.x, event.y)  # halo =3容易找到细直线
        all_id = self.bottom_poker_canvas.find_withtag('current')
        click_img_id = all_id[0]
        bounded_tag = int(self.bottom_poker_canvas.gettags(click_img_id)[0])

        logger.info("tag {}, find_item {}, id {}".format(bounded_tag, self.bottom_poker_canvas.find_withtag('current'),
                                                         all_id[0]))
        if bounded_tag in self.__selected_poker_list:
            # move to below
            self.bottom_poker_canvas.move(click_img_id, 0, 20)
            self.__selected_poker_list.remove(bounded_tag)
        else:
            # move up.
            self.bottom_poker_canvas.move(click_img_id, 0, -20)
            self.__selected_poker_list.append(bounded_tag)

        logger.info("We clicked poker value {}".format(self.__selected_poker_list))

    def button_handout(self):
        self.__selected_poker_list.sort(reverse=True)

        if self.player:
            self.player.hand_out(self.__selected_poker_list)
            logger.info(
                "User [{}] hand out pokers {}".format(self.bottom_user_name_widget.get(), self.__center_pokers_list))
            self.user_button_skip.config(state="disabled")
            self.user_button_handout.config(state="disabled")

        self.__center_pokers_list = self.__selected_poker_list
        self.show_center_pokers()

        for c in self.__center_pokers_list:
            self.__owned_poker_list.remove(c)

        self.show_bottom_pokers(self.__owned_poker_list)

    def button_skip(self):
        if self.player:
            self.player.hand_out([])
            self.user_button_skip.config(state="disabled")
            self.user_button_handout.config(state="disabled")

    def button_share_2(self):
        if self.player:
            self.user_button_slient.config(state="disabled")
            self.user_button_share.config(state="disabled")
            self.player.share_red2()

    def button_steal_chicken(self):
        if self.player:
            self.user_button_slient.config(state="disabled")
            self.user_button_share.config(state="disabled")
            self.player.stolean()

    def button_hijack_2(self):
        if self.player:
            self.user_button_notake.config(state="disabled")
            self.user_button_alone.config(state="disabled")
            self.player.single_user()

    def button_no_hijack_2(self):
        if self.player:
            self.user_button_notake.config(state="disabled")
            self.user_button_alone.config(state="disabled")
            self.player.notake2()


if __name__ == "__main__":
    window = tk.Tk()
    window.title('红二')

    icon = PhotoImage(file=SCRIPT_DIR + '/image/icon.png')
    window.geometry('1400x1080')  # 这里的乘是小x
    window.tk.call('wm', 'iconphoto', window._w, icon)
    app = Application(window)
    window.mainloop()
