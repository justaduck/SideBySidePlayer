import os
import time
import tkFileDialog
from Tkinter import *
from datetime import datetime
import vlc
import threading

lock = threading.Lock()


class ButtonBox(Frame):
    def __init__(self, master, open_video_cb, links=None, play_buttons=None, needs_lineup=False):
        Frame.__init__(self, master)
        self.master = master
        self.links = links
        self.needs_line_up = needs_lineup
        self.open_video = open_video_cb
        self.volume = 0
        self.play_buttons = play_buttons
        self.create_widgets()
    
    def create_widgets(self):
        self.play_button = Button(self, text="Play", command=self.play)
        rewind = Button(self, text="Restart", command=self.restart)
        volume_up = Button(self, text="Vol Up", command=self.volume_up)
        volume_down = Button(self, text="Vol Down", command=self.volume_down)
        minus_5s = Button(self, text="-5s", command=self.go_back)
        plus_5s = Button(self, text="+5s", command=self.go_forward)
        minus_1f = Button(self, text="-1f", command=self.step_back)
        plus_1f = Button(self, text="+1f", command=self.step_forward)

        self.play_button.grid(row=0, column=0)
        rewind.grid(row=0, column=1)
        volume_down.grid(row=0, column=2)
        volume_up.grid(row=0, column=3)
        minus_5s.grid(row=0, column=4)
        plus_5s.grid(row=0, column=5)
        minus_1f.grid(row=0, column=6)
        plus_1f.grid(row=0, column=7)

    def set_links(self, links):
        self.links = links
        return

    def restart(self):
        if any(self.links[n]["video"].get_player().get_state() != vlc.State.Ended for n in self.links):
            for n in self.links:
                self.links[n]["video"].get_player().set_time(0)
        else:
            for n in self.links:
                self.ended(n)

    def volume_up(self):
        if self.volume == 100:
            pass
        else:
            self.volume += 5
            for n in self.links:
                self.links[n]["video"].get_player().audio_set_volume(self.volume)
        return

    def volume_down(self):
        if self.volume == 0:
            pass
        else:
            self.volume -= 5
            for n in self.links:
                self.links[n]["video"].get_player().audio_set_volume(self.volume)
        return

    def go_back(self):
        currents = [self.links[v]["video"].get_player().get_time() for v in self.links]
        targets = [curr - 5000 if curr - 5000 > 0 else 0 for curr in currents]

        # set times
        for i, t in enumerate(self.links):
            self.links[t]["video"].get_player().set_time(targets[i])

        # update timers
        for t in self.links:
            self.links[t]["timer"].update_time()
        return

    def go_forward(self):
        currents = [(self.links[v]["video"].get_player().get_time(), self.links[v]["video"].get_player().get_length())
                    for v in self.links]
        targets = [curr[0] + 5000 if curr[0] + 5000 < curr[1] else curr[1] for curr in currents]

        # set times
        for i, t in enumerate(self.links):
            self.links[t]["video"].get_player().set_time(targets[i])

        # update timers
        for t in self.links:
            self.links[t]["timer"].update_time()
        return

    def step_back(self):
        currents = [self.links[v]["video"].get_player().get_time() for v in self.links]
        frm = [self.links[v]["video"].get_player().get_fps() for v in self.links]
        mspf = [1000/f for f in frm]
        targets = [int(currents[i] - mspf[i]) if currents[i] - mspf[i] > 0 else 0 for i in xrange(len(currents))]

        for i, v in enumerate(self.links):
            self.links[v]["video"].get_player().set_time(targets[i])
            self.links[v]["video"].get_player().set_pause(1)
            try:
                self.links[v]["timer"].stop()
            except KeyError:
                pass
        self.play_button.configure(text='Play')
        return

    def step_forward(self):
        currents = [(self.links[v]["video"].get_player().get_time(),
                     self.links[v]["video"].get_player().get_length()) for v in self.links]
        frm = [self.links[v]["video"].get_player().get_fps() for v in self.links]
        mspf = [1000 / f for f in frm]
        targets = [int(currents[i][0] + mspf[i]) if i <= currents[i][1] else currents[i][1]
                   for i in xrange(len(currents))]
        for i, v in enumerate(self.links):
            self.links[v]["video"].get_player().set_time(targets[i])
            self.links[v]["video"].get_player().set_pause(1)
            try:
                self.links[v]["timer"].stop()
            except KeyError:
                pass
        self.play_button.configure(text='Play')
        return

    def ended(self, num):
        self.open_video(num, self.links[num]["video"].get_location())
        return

    def play(self):
        for v in self.links:
            if self.links[v]["video"].get_player().get_state() == vlc.State.Ended:
                self.ended(v)
                self.needs_line_up = True
        if self.needs_line_up:
            self.line_up()

        if self.play_button['text'] == "Play":
            for v in self.links:
                if self.links[v]["video"].get_location():
                    self.links[v]["video"].get_player().play()
                    self.links[v]["video"].set_playing(True)
            if any([self.links[v]["video"].get_location() for v in self.links]):
                self.play_button.configure(text="Pause")
                if self.play_button == self.play_buttons["master"]:
                    for b in self.play_buttons["children"]:
                        b.configure(text="Pause")
                else:
                    self.play_buttons["master"].master.needs_line_up = False
                    if all(b["text"] == "Pause" for b in self.play_buttons["children"]):
                        self.play_buttons["master"].configure(text="Pause")
                for t in self.links:
                    try:
                        self.links[t]["timer"].play()
                    except KeyError:
                        continue
        else:
            for v in self.links:
                if self.links[v]["video"].get_location():
                    self.links[v]["video"].get_player().set_pause(1)
                    self.links[v]["video"].set_playing(False)
            if any([self.links[v]["video"].get_location() for v in self.links]):
                self.play_button.configure(text="Play")
                if self.play_button == self.play_buttons["master"]:
                    for b in self.play_buttons["children"]:
                        b.configure(text="Play")
                else:
                    if all(b["text"] == "Play" for b in self.play_buttons["children"]):
                        self.play_buttons["master"].configure(text="Play")
                for t in self.links:
                    try:
                        self.links[t]["timer"].stop()
                    except KeyError:
                        continue
        return

    def line_up(self):
        self.needs_line_up = False
        self.play()
        time.sleep(1)
        self.play()
        for v in self.links:
            self.links[v]["video"].set_timer(0)
            self.links[v]["video"].get_player().set_time(0)


class Video(Frame):
    def __init__(self, master, video_number, path=None):
        # Frame Init
        Frame.__init__(self, master)
        self.master = master
        self.title = StringVar()
        self.title.set(os.path.split(path)[1] if path else "Select a Video")
        self.path = path
        self.time = StringVar()
        self.number = video_number

        # VLC Init
        self.media = None  # Media Instance
        self.isPlaying = False

        self.setup_video()

        if path:
            self.read_video(path)

    def setup_video(self):
        # Frame Setup
        self.title_label = Label(self, textvar=self.title)
        self.title_label.grid(row=0, column=0)
        self.timer = Label(self, textvar=self.time)
        self.timer.grid(row=0, column=1)
        self.video_frame = Frame(self, width=(self.master.winfo_screenwidth()-100)/2,
                                 height=self.master.winfo_screenheight()-200)
        self.video_frame.grid(row=1, column=0, columnspan=2)

        # Button Box
        links = {self.number: {"video": self,
                               "timer": self.master.timer1 if self.number == 1 else self.master.timer2}}
        self.buttons = ButtonBox(self, self.master.open_video, links=links, play_buttons=self.master.play_buttons)
        self.master.play_buttons["children"].append(self.buttons.play_button)
        self.buttons.grid(row=2, column=0, columnspan=2)

        # VLC Setup
        self.inst = vlc.Instance()
        self.player = self.inst.media_player_new()
        self.player.set_hwnd(self.video_frame.winfo_id())
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.eov)
        return

    # Frame Functions
    def update_title(self, title):
        self.title.set(title)
        return

    def set_location(self, location):
        self.path = location
        return

    def get_location(self):
        return self.path

    def get_time(self):
        return self.time.get()

    def set_timer(self, timer_time):
        return self.time.set(timer_time)

    # VLC Functions
    def eov(self, evt):
        self.isPlaying = False

        self.master.update_timer(self.number, self.player.get_length())
        self.buttons.play_button.configure(text="Play")
        self.master.buttons.play_button.configure(text="Play")

    def read_video(self, video):
        self.media = self.inst.media_new(os.path.normpath(video))
        self.player.set_media(self.media)

        self.player.set_time(0)
        self.player.set_pause(1)
        return

    def get_player(self):
        return self.player

    def set_playing(self, playing):
        self.isPlaying = playing
        return


class Timer(threading.Thread):
    def __init__(self, timer_update_cb, tick, video_number, playing_cb, time_cb):
        threading.Thread.__init__(self)
        self.stopFlag = threading.Event()
        self.timer_cb = timer_update_cb
        self.tick = tick
        self.num = video_number
        self.is_running = False
        self.time = 0
        self.get_playing = playing_cb
        self.get_time = time_cb

    def run(self):
        while True:
            lock.acquire(True)
            while not self.stopFlag.wait(self.tick) and self.is_running and self.get_playing(self.num):
                lock.release()
                self.timer_cb(self.num, self.time)
                done = datetime.now()
                delta = (done-self.previous).total_seconds() * 1000
                self.time += delta
                self.previous = datetime.now()
                lock.acquire(True)
            if lock.locked():
                lock.release()
        return

    def play(self):
        self.time = self.get_time(self.num)
        self.is_running = True
        self.previous = datetime.now()
        return

    def stop(self):
        self.time = self.get_time(self.num)
        lock.acquire(True)
        self.timer_cb(self.num, self.time)
        lock.release()
        self.is_running = False
        return

    def time_delta(self, delta):
        self.time += delta
        return

    def update_time(self):
        self.time = self.get_time(self.num)
        return


class Player(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.height = self.winfo_screenheight()
        self.width = self.winfo_screenwidth()

        self.videos = {}
        self.play_buttons = {"master": None,
                             "children": []}

        self.timer1 = Timer(self.update_timer, 0.01, 1, self.get_playing, self.get_time)
        self.timer1.start()
        self.timer2 = Timer(self.update_timer, 0.01, 2, self.get_playing, self.get_time)
        self.timer2.start()

        self.create_widgets()
        self.wm_resizable(0, 0)
        threading.Thread(target=self.videos[1])
        threading.Thread(target=self.videos[2])

        button_links = {1: {"video": self.videos[1],
                            "timer": self.timer1},
                        2: {"video": self.videos[2],
                            "timer": self.timer2}}
        self.buttons.set_links(button_links)

    def create_widgets(self):
        self.menubar = Menu(self)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label='Open Video 1', command=lambda: self.open_video(1))
        self.fileMenu.add_command(label='Open Video 2', command=lambda: self.open_video(2))
        self.config(menu=self.menubar)

        self.videos[1] = Video(self, 1)
        self.videos[1].grid(row=0, column=0, padx=5)
        self.videos[2] = Video(self, 2)
        self.videos[2].grid(row=0, column=1, padx=5)

        self.buttons = ButtonBox(self, self.open_video, play_buttons=self.play_buttons, needs_lineup=True)
        self.play_buttons["master"] = self.buttons.play_button
        self.buttons.grid(row=1, columnspan=2)

        self.bind_all("<space>", lambda e: self.buttons.play())
        self.bind_all("<Right>", lambda e: self.buttons.step_forward())
        self.bind_all("<Left>", lambda e: self.buttons.step_back())
        self.bind_all("<Up>", lambda e: self.buttons.volume_up())
        self.bind_all("<Down>", lambda e: self.buttons.volume_down())
        self.bind_all("<equal>", lambda e: self.buttons.go_forward())
        self.bind_all("<plus>", lambda e: self.buttons.go_forward())
        self.bind_all("<minus>", lambda e: self.buttons.go_back())
        self.bind_all("<KP_Add>", lambda e: self.buttons.go_forward())
        self.bind_all("<KP_Subtract>", lambda e: self.buttons.go_back())

    def update_timer(self, num, video_time_in_ms):
        if video_time_in_ms < 0:
            return

        tstamp = datetime.fromtimestamp(video_time_in_ms/1000.0)
        epoch = datetime.fromtimestamp(0)

        if num == 1:
            t = str(tstamp - epoch)
            t = t[:-4] if '.' in t else t + ".00"
            self.videos[1].set_timer(t)
        if num == 2:
            t = str(tstamp - epoch)
            t = t[:-4] if '.' in t else t + ".00"
            self.videos[2].set_timer(t)
        return

    def get_playing(self, number):
        p = self.videos[number].isPlaying
        return p

    def get_time(self, number):
        t = self.videos[number].get_player().get_time()
        return t

    def open_video(self, number, fname=None):
        self.videos[number].get_player().stop()
        self.videos[(number % 2) + 1].get_player().pause()
        fname = fname if fname else tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~"))
        if fname:
            title = os.path.split(fname)[1]
            if number == 1:
                self.videos[1].set_location(fname)
                self.videos[1].update_title(title)
                self.videos[1].read_video(self.videos[1].get_location())
            if number == 2:
                self.videos[2].set_location(fname)
                self.videos[2].update_title(title)
                self.videos[2].read_video(self.videos[2].get_location())
            self.videos[number].get_player().audio_set_volume(0)
        else:
            self.videos[number].get_player().play()


if __name__ == "__main__":
    p = Player()
    p.mainloop()
    os._exit(0)


'''
To Do List:
Improve video restart at eov
'''