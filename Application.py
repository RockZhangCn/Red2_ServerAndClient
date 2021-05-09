import tkinter as tk
from PIL import Image, ImageTk
from GameEngine import GameEngine
from Human import Human

def flattenAlpha(img):
    alpha = img.split()[-1]  # Pull off the alpha layer
    ab = alpha.tobytes()  # Original 8-bit alpha
    checked = []  # Create a new array to store the cleaned up alpha layer bytes
    # Walk through all pixels and set them either to 0 for transparent or 255 for opaque fancy pants
    transparent = 50  # change to suit your tolerance for what is and is not transparent
    p = 0
    for pixel in range(0, len(ab)):
        if ab[pixel] < transparent:
            checked.append(0)  # Transparent
        else:
            checked.append(255)  # Opaque
        p += 1
    mask = Image.frombytes('L', img.size, bytes(checked))
    img.putalpha(mask)
    return img

class Application(tk.Tk):
    images = []
    image_numbers = []
    def __init__(self, master):
        self.init_images()
        self.game = GameEngine()
        self.game.registerPlayer(0, Human())
        self.game.registerPlayer(1, Human())
        self.game.registerPlayer(2, Human())
        self.master = master
        master.title("斗地主 - 桌面版")

        self.main = tk.Canvas(master, width = 1100, height = 750)
        self.main.pack(side = tk.LEFT)
        self.selected = []

        self.upperside = tk.Frame(master, width = 300, height = 150, pady = 30)
        self.upperside.pack(side = tk.TOP)
        self.middleside = tk.Frame(master, width=300, height = 150, pady=30)
        self.middleside.pack(side = tk.TOP)
        self.lowerside = tk.Frame(master, width = 300, height = 400, pady = 30, padx = 50)
        self.lowerside.pack()

        self.startbutton = tk.Button(self.main, text = "开始游戏", command = self.startgame)
        self.startbutton.place(x = 500, y = 400, anchor = "s")

        self.main.bind("<Button-1>", self.select)

        self.label1 = tk.Label(self.upperside, text = "底分: ")
        self.label2 = tk.Label(self.upperside, text = "倍数: ")
        self.label3 = tk.Label(self.upperside, text = "庄家: ")
        self.value1 = tk.Label(self.upperside, text = "")
        self.value2 = tk.Label(self.upperside, text = "")
        self.value3 = tk.Label(self.upperside, text = "")
        self.label1.grid(row = 0, column = 0)
        self.label2.grid(row = 1, column = 0)
        self.label3.grid(row = 2, column = 0)
        self.value1.grid(row = 0, column = 1)
        self.value2.grid(row = 1, column = 1)
        self.value3.grid(row = 2, column = 1)

        self.label4 = tk.Label(self.middleside, text="玩家")
        self.label5 = tk.Label(self.middleside, text="上一轮")
        self.label6 = tk.Label(self.middleside, text="总分")
        self.label7 = tk.Label(self.middleside, text="玩家1")
        self.label8 = tk.Label(self.middleside, text="玩家2")
        self.label9 = tk.Label(self.middleside, text="玩家3")
        self.label10 = tk.Label(self.middleside, text="")
        self.label11 = tk.Label(self.middleside, text="")
        self.label12 = tk.Label(self.middleside, text="")
        self.label13 = tk.Label(self.middleside, text="")
        self.label14 = tk.Label(self.middleside, text="")
        self.label15 = tk.Label(self.middleside, text="")
        self.label4.grid(row = 4, column = 0)
        self.label5.grid(row=4, column=1)
        self.label6.grid(row=4, column=2)
        self.label7.grid(row=5, column=0)
        self.label8.grid(row=6, column=0)
        self.label9.grid(row=7, column=0)
        self.label10.grid(row=5, column=1)
        self.label11.grid(row=6, column=1)
        self.label12.grid(row=7, column=1)
        self.label13.grid(row=5, column=2)
        self.label14.grid(row=6, column=2)
        self.label15.grid(row=7, column=2)

        self.reveal = tk.IntVar()
        self.hide_radio = tk.Radiobutton(self.lowerside, text = "Hide Others", var = self.reveal, value = 0)
        self.reveal_radio = tk.Radiobutton(self.lowerside, text="Reveal Others", var=self.reveal, value=1)
        self.hide_radio.grid(row = 0, column = 0)
        self.reveal_radio.grid(row = 1, column = 0)
        self.reveal.set(0)

        self.bid0 = tk.Button(self.main, text="不叫", command=self.bid0func)
        self.bid1 = tk.Button(self.main, text="1分", command=self.bid1func)
        self.bid2 = tk.Button(self.main, text="2分", command=self.bid2func)
        self.bid3 = tk.Button(self.main, text="3分", command=self.bid3func)

        self.passround = tk.Button(self.main, text="不出", command=self.passfunc)
        self.playround = tk.Button(self.main, text="出牌", command=self.playfunc)

    def bid0func(self):
        self.game.step(0)

    def bid1func(self):
        self.game.step(1)

    def bid2func(self):
        self.game.step(2)

    def bid3func(self):
        self.game.step(3)

    def passfunc(self):
        self.game.step([])

    def playfunc(self):
        cards = [self.game.getPlayerHand(self.game.curplayer)[i] for i in self.selected]
        self.game.step(cards)
        self.selected = []

    def init_images(self):
        for i in range(54):
            self.images.append(
                ImageTk.PhotoImage(flattenAlpha(Image.open(f"./image/{i}.png").resize((90, 137), Image.ANTIALIAS)))
            )
        self.image_timer = ImageTk.PhotoImage(flattenAlpha(Image.open(f"./image/timer.png").resize((30, 40), Image.ANTIALIAS)))
        for i in range(4):
            self.image_numbers.append(
                #ImageTk.PhotoImage(flattenAlpha(Image.open(f"./image/ui_num{i}.png").resize((45, 45), Image.ANTIALIAS)))
                ImageTk.PhotoImage(Image.open(f"./image/ui_num{i}.png").resize((45, 45), Image.ANTIALIAS).convert("RGB"))
            )
        self.image_NT = ImageTk.PhotoImage(flattenAlpha(Image.open(f"./image/NT-color.png").resize((40, 40), Image.ANTIALIAS)))
        self.image_background = ImageTk.PhotoImage(flattenAlpha(Image.open(f"./image/blue_back.png").resize((90, 137), Image.ANTIALIAS)))

    def startgame(self):
        self.game.newgame()
        self.startbutton.place_forget()
        self.update()

    def update(self):
        #print(self.game.stage)
        #print(self.selected)
        self.main.delete("all")
        self.show_below()
        self.show_left()
        self.show_right()
        self.show_public()
        self.show_stuff()
        if self.game.stage == "叫牌阶段":
            self.show_bids()
        elif self.game.stage == "出牌阶段":
            self.hide_bids()
            self.show_play()
        else:
            self.hide_play()
            self.startbutton.place(x = 500, y = 400, anchor = "s")
            self.startbutton.config(text="再来一局")

        self.master.after(200, self.update)


    def show_below(self):
        cards = self.game.getPlayerHand(0)
        n = len(cards)
        half_overlap = 15
        first_x = 570 - half_overlap * n - 45
        if self.game.players[0].isHuman or self.reveal.get() == 1:
            for id, card in enumerate(cards):
                if id in self.selected and self.game.curplayer == 0:
                    self.main.create_image(first_x + 2 * half_overlap * id, 670, anchor = 'sw', image = self.images[card])
                else:
                    self.main.create_image(first_x + 2 * half_overlap * id, 700, anchor='sw', image=self.images[card])
        else:
            for id, card in enumerate(cards):
                self.main.create_image(first_x + 2 * half_overlap * id, 700, anchor='sw', image=self.image_background)

    def show_left(self):
        cards = self.game.getPlayerHand(2)
        n = len(cards)
        half_overlap = 15
        first_y = 306 - half_overlap * n
        if self.game.players[2].isHuman or self.reveal.get() == 1:
            for id, card in enumerate(cards):
                if id in self.selected and self.game.curplayer == 2:
                    self.main.create_image(75, first_y + 2 * half_overlap * id, anchor = 'nw', image = self.images[card])
                else:
                    self.main.create_image(50, first_y + 2 * half_overlap * id, anchor='nw', image=self.images[card])
        else:
            for id, card in enumerate(cards):
                self.main.create_image(50, first_y + 2 * half_overlap * id, anchor='nw', image=self.image_background)

    def show_right(self):
        cards = self.game.getPlayerHand(1)
        n = len(cards)
        half_overlap = 15
        first_y = 306 - half_overlap * n
        if self.game.players[1].isHuman or self.reveal.get() == 1:
            for id, card in enumerate(cards):
                if id in self.selected and self.game.curplayer == 1:
                    self.main.create_image(1025, first_y + 2 * half_overlap * id, anchor='ne', image=self.images[card])
                else:
                    self.main.create_image(1050, first_y + 2 * half_overlap * id, anchor='ne', image=self.images[card])
        else:
            for id, card in enumerate(cards):
                self.main.create_image(1050, first_y + 2 * half_overlap * id, anchor='ne', image=self.image_background)


    def show_public(self):
        cards = self.game.getPublicHand()
        n = len(cards)
        half_overlap = 65
        first_x = 630 - half_overlap * n
        for id, card in enumerate(cards):
            if self.reveal.get() == 1 or self.game.stage != "叫牌阶段":
                self.main.create_image(first_x + 2 * half_overlap * id, 100, anchor='n', image=self.images[card])
            else:
                self.main.create_image(first_x + 2 * half_overlap * id, 100, anchor='n', image=self.image_background)

    def show_stuff(self):
        cur_id = self.game.curplayer
        if cur_id == 0:
            self.main.create_image(550, 450, anchor='n', image=self.image_timer)
        elif cur_id == 2:
            self.main.create_image(190, 375, anchor='w', image=self.image_timer)
        elif cur_id == 1:
            self.main.create_image(910, 375, anchor='e', image=self.image_timer)
        if self.game.lord is not None:
            self.value1.config(text = str(self.game.base))
            self.value3.config(text = ["本家","右家","左家"][self.game.lord])
            self.value2.config(text = str(self.game.multiplier))
        self.label10.config(text = str(self.game.lastscores[0]))
        self.label11.config(text=str(self.game.lastscores[1]))
        self.label12.config(text=str(self.game.lastscores[2]))
        self.label13.config(text=str(self.game.cumscores[0]))
        self.label14.config(text=str(self.game.cumscores[1]))
        self.label15.config(text=str(self.game.cumscores[2]))

    def show_bids(self):
        bids = self.game.bids
        for id, bid in enumerate(bids):
            if id == 0:
                self.main.create_image(550, 450, anchor='n', image=self.image_numbers[bid])
            elif id == 2:
                self.main.create_image(190, 375, anchor='w', image=self.image_numbers[bid])
            elif id == 1:
                self.main.create_image(910, 375, anchor='e', image=self.image_numbers[bid])
        if self.game.players[self.game.curplayer].isHuman:
            self.bid0.place(x=450, y=400, anchor="s")
            self.bid1.place(x=525, y=400, anchor="s")
            self.bid2.place(x=575, y=400, anchor="s")
            self.bid3.place(x=625, y=400, anchor="s")

    def hide_bids(self):
        self.bid0.place_forget()
        self.bid1.place_forget()
        self.bid2.place_forget()
        self.bid3.place_forget()

    def show_play(self):
        round = self.game.round
        if self.game.curplayer == 0:
            self.show_left_pack(round[2])
            self.show_right_pack(round[1])
        elif self.game.curplayer == 1:
            self.show_left_pack(round[2])
            self.show_below_pack(round[0])
        else:
            self.show_right_pack(round[1])
            self.show_below_pack(round[0])
        self.passround.place(x = 475, y = 400, anchor = "s")
        self.playround.place(x = 625, y = 400, anchor = "s")

    def hide_play(self):
        self.passround.place_forget()
        self.playround.place_forget()


    def show_below_pack(self, cards):
        n = len(cards)
        half_overlap = 15
        first_x = 570 - half_overlap * n - 45
        for id, card in enumerate(cards):
            self.main.create_image(first_x + 2 * half_overlap * id, 550, anchor='sw', image=self.images[card])
        if n == 0:
            self.main.create_image(570, 550, anchor = 'sw', image = self.image_NT)

    def show_left_pack(self, cards):
        n = len(cards)
        half_overlap = 15
        first_y = 390 - half_overlap * n
        for id, card in enumerate(cards):
            self.main.create_image(150, first_y + 2 * half_overlap * id, anchor='nw', image=self.images[card])
        if n == 0:
            self.main.create_image(150, 350, anchor = 'nw', image = self.image_NT)

    def show_right_pack(self, cards):
        n = len(cards)
        half_overlap = 15
        first_y = 390 - half_overlap * n
        for id, card in enumerate(cards):
            self.main.create_image(950, first_y + 2 * half_overlap * id, anchor='ne', image=self.images[card])
        if n == 0:
            self.main.create_image(950, 350, anchor = 'ne', image = self.image_NT)

    def select(self, event):
        pos = event.x, event.y
        print(pos)
        if self.game.stage == "出牌阶段" and self.game.players[self.game.curplayer].isHuman:
            if self.game.curplayer == 0:
                cards = self.game.getPlayerHand(0)
                n = len(cards)
                half_overlap = 15
                first_x = 570 - half_overlap * n - 45
                if 563 <= event.y <= 700 and first_x <= event.x <= first_x + 90 + half_overlap * 2 * n:
                    p = min(n - 1, (event.x - first_x) // (2 * half_overlap))
                    print(p)
                    if p in self.selected:
                        self.selected.remove(p)
                    else:
                        self.selected.append(p)
            elif self.game.curplayer == 1:
                cards = self.game.getPlayerHand(1)
                n = len(cards)
                half_overlap = 15
                first_y = 306 - half_overlap * n
                if 960 <= event.x <= 1050 and first_y <= event.y <= first_y + 137 + half_overlap * 2 * n:
                    p = min(n - 1, (event.y - first_y) // (2 * half_overlap))
                    if p in self.selected:
                        self.selected.remove(p)
                    else:
                        self.selected.append(p)
            elif self.game.curplayer == 2:
                cards = self.game.getPlayerHand(2)
                n = len(cards)
                half_overlap = 15
                first_y = 306 - half_overlap * n
                if 50 <= event.x <= 140 and first_y <= event.y <= first_y + 137 + half_overlap * 2 * n:
                    p = min(n - 1, (event.y - first_y) // (2 * half_overlap))
                    if p in self.selected:
                        self.selected.remove(p)
                    else:
                        self.selected.append(p)
