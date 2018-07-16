import os
import time
import tkFileDialog
from Tkinter import *
from datetime import datetime
import vlc
import threading

lock = threading.Lock()


class Reader:
    def __init__(self, frame_id, play_button):
        self.frame_id = frame_id
        self.play_button = play_button
        self.inst = vlc.Instance()
        self.player = self.inst.media_player_new()
        self.player.set_hwnd(self.frame_id.winfo_id())
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.eov)
        self.video = None
        self.media = None
        self.isPlaying = False

    def eov(self, evt):
        self.isPlaying = False
        self.play_button.configure(text="Play")

    def read_video(self, video):
        self.video = video
        self.media = self.inst.media_new(os.path.normpath(video))
        self.player.set_media(self.media)

        self.player.set_time(0)
        self.player.set_pause(1)
        return

    def get_player(self):
        return self.player

    def set_playing(self, playing):
        self.isPlaying = playing


class Video(Frame):
    def __init__(self, master, path=None):
        Frame.__init__(self, master)
        self.master = master
        self.title = StringVar()
        self.title.set(os.path.split(path)[1] if path else "Select a Video")
        self.path = path
        self.time = StringVar()
        self.setup_video()

    def setup_video(self):
        self.title_label = Label(self, textvar=self.title)
        self.title_label.grid(row=0, column=0)
        self.timer = Label(self, textvar=self.time)
        self.timer.grid(row=0, column=1)
        self.video_frame = Frame(self, width=(self.master.winfo_screenwidth()-100)/2,
                                 height=self.master.winfo_screenheight()-200)
        self.video_frame.grid(row=1, column=0, columnspan=2)
        return

    def get_frame_id(self):
        return self.video_frame

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

    def set_time(self, time):
        return self.time.set(time)


class Timer(threading.Thread):
    def __init__(self, callback, tick, video_number, video):
        threading.Thread.__init__(self)
        self.stopFlag = threading.Event()
        self.callback = callback
        self.tick = tick
        self.num = video_number
        self.is_running = False
        self.time = 0
        self.video = video

    def run(self):
        while True:
            lock.acquire(True)
            while not self.stopFlag.wait(self.tick) and self.is_running and self.video.isPlaying:
                lock.release()
                self.callback(self.num, self.time)
                done = datetime.now()
                delta = (done-self.previous).total_seconds() * 1000
                self.time += delta
                self.previous = datetime.now()
                lock.acquire(True)
            if lock.locked():
                lock.release()
        return

    def play(self):
        self.time = self.video.get_player().get_time()
        self.previous = datetime.now()
        self.is_running = True
        return

    def stop(self):
        self.time = self.video.get_player().get_time()
        self.callback(self.num, self.time)
        self.is_running = False
        return

    def time_delta(self, delta):
        self.time += delta

    def grab_time(self):
        self.time = self.video.get_player().get_time()


class Player(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.readers = {}
        self.height = self.winfo_screenheight()
        self.width = self.winfo_screenwidth()
        self.volume = 0
        self.create_widgets()
        self.wm_resizable(0, 0)
        self.readers = {1: Reader(self.video1.get_frame_id(), self.play_button),
                        2: Reader(self.video2.get_frame_id(), self.play_button)}
        threading.Thread(target=self.readers[1])
        threading.Thread(target=self.readers[2])

        self.timer1 = Timer(self.update_timer, 0.01, 1, self.readers[1])
        self.timer1.start()
        self.timer2 = Timer(self.update_timer, 0.01, 2, self.readers[2])
        self.timer2.start()

        self.open_video(1, r'C:\Users\FirschingJ\Desktop\test_player\1b4594ef00d9a398798009eaafe20ec9-A.mov')
        self.open_video(2, r'C:\Users\FirschingJ\Desktop\test_player\1b4594ef00d9a398798009eaafe20ec9-B.mp4')

        self.bind_all("<space>", lambda e: self.play())
        self.bind_all("<Right>", lambda e: self.step_forward())
        self.bind_all("<Left>", lambda e: self.step_back())
        self.bind_all("<Up>", lambda e: self.volume_up())
        self.bind_all("<Down>", lambda e: self.volume_down())

    def create_widgets(self):
        self.menubar = Menu(self)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label='Open Video 1', command=lambda: self.open_video(1))
        self.fileMenu.add_command(label='Open Video 2', command=lambda: self.open_video(2))
        self.config(menu=self.menubar)

        self.video1 = Video(self)
        self.video1.grid(row=0, column=0, padx=5)
        self.video2 = Video(self)
        self.video2.grid(row=0, column=1, padx=5)

        frm = Frame()
        frm.grid(row=1, columnspan=2)
        self.play_button = Button(frm, text="Play", command=self.play)
        rewind = Button(frm, text="Restart", command=self.restart)
        volume_up = Button(frm, text="Vol Up", command=self.volume_up)
        volume_down = Button(frm, text="Vol Down", command=self.volume_down)
        minus_5s = Button(frm, text="-5s", command=self.go_back)
        plus_5s = Button(frm, text="+5s", command=self.go_forward)
        minus_1f = Button(frm, text="-1f", command=self.step_back)
        plus_1f = Button(frm, text="+1f", command=self.step_forward)

        self.play_button.grid(row=1, column=0)
        rewind.grid(row=1, column=1)
        volume_down.grid(row=1, column=2)
        volume_up.grid(row=1, column=3)
        minus_5s.grid(row=1, column=4)
        plus_5s.grid(row=1, column=5)
        minus_1f.grid(row=1, column=6)
        plus_1f.grid(row=1, column=7)

    def ended(self, num):
        if num == 1:
            self.open_video(1, self.video1.get_location())
        if num == 2:
            self.open_video(2, self.video2.get_location())
        self.play()

    def update_timer(self, num, video_time_in_ms):
        tstamp = datetime.fromtimestamp(video_time_in_ms/1000.0)
        epoch = datetime.fromtimestamp(0)

        if num == 1:
            t = str(tstamp - epoch)
            t = t[:-4] if '.' in t else t + ".00"
            self.video1.set_time(t)
        if num == 2:
            t = str(tstamp - epoch)
            t = t[:-4] if '.' in t else t + ".00"
            self.video2.set_time(t)

    def play(self):
        line_up_needed = False
        if self.readers[1].get_player().get_state() == vlc.State.Ended:
            self.ended(1)
            line_up_needed = True
        if self.readers[2].get_player().get_state() == vlc.State.Ended:
            self.ended(2)
            line_up_needed = True

        if line_up_needed:
            self.line_up()

        if self.play_button['text'] == "Play":
            if self.video1.get_location():
                self.readers[1].get_player().play()
                self.readers[1].set_playing(True)
            if self.video2.get_location():
                self.readers[2].get_player().play()
                self.readers[2].set_playing(True)
            if self.video1.get_location() or self.video2.get_location():
                self.play_button.configure(text="Pause")
                self.timer1.play()
                self.timer2.play()
        else:
            if self.video2.get_location():
                self.readers[2].get_player().pause()
                self.update_timer(2, self.readers[2].get_player().get_time())
                self.readers[2].set_playing(False)
                self.timer2.stop()
            if self.video1.get_location():
                self.readers[1].get_player().pause()
                self.update_timer(1, self.readers[1].get_player().get_time())
                self.readers[1].set_playing(False)
                self.timer1.stop()
            self.play_button.configure(text="Play")

    def restart(self):
        if self.readers[1].get_player().get_state() != vlc.State.Ended:
            self.readers[1].get_player().set_time(0)
            self.readers[2].get_player().set_time(0)
        else:
            self.ended(1)
            self.ended(2)

    def volume_up(self):
        if self.volume == 100:
            pass
        else:
            self.volume += 5
            self.readers[1].get_player().audio_set_volume(self.volume)
            self.readers[2].get_player().audio_set_volume(self.volume)
        return

    def volume_down(self):
        if self.volume == 0:
            pass
        else:
            self.readers[1].get_player().audio_set_volume(self.volume-5)
            self.readers[2].get_player().audio_set_volume(self.volume-5)
            self.volume -= 5
        return

    def go_back(self):
        curr_1 = self.readers[1].get_player().get_time()
        curr_2 = self.readers[2].get_player().get_time()

        target1 = curr_1 - 5000 if curr_1 - 5000 > 0 else 0
        target2 = curr_2 - 5000 if curr_2 - 5000 > 0 else 0

        self.readers[1].get_player().set_time(target1)
        self.readers[2].get_player().set_time(target2)

        self.timer1.grab_time()
        self.timer2.grab_time()
        return

    def go_forward(self):
        curr_1 = self.readers[1].get_player().get_time()
        curr_2 = self.readers[2].get_player().get_time()

        len1 = self.readers[1].get_player().get_length()
        len2 = self.readers[1].get_player().get_length()

        target1 = curr_1 + 5000 if curr_1 + 5000 < len1 else len1
        target2 = curr_2 + 5000 if curr_2 + 5000 < len2 else len2

        self.readers[1].get_player().set_time(target1)
        self.readers[2].get_player().set_time(target2)

        self.timer1.grab_time()
        self.timer2.grab_time()
        return

    def step_back(self):
        curr_1 = self.readers[1].get_player().get_time()
        curr_2 = self.readers[2].get_player().get_time()

        frm_1 = self.readers[1].get_player().get_fps()
        frm_2 = self.readers[2].get_player().get_fps()

        mspf1 = 1000/frm_1
        mspf2 = 1000/frm_2

        target1 = int(curr_1 - mspf1)
        target2 = int(curr_2 - mspf2)

        self.readers[1].get_player().set_time(target1)
        self.readers[2].get_player().set_time(target2)
        self.readers[1].get_player().set_pause(1)
        self.readers[2].get_player().set_pause(1)
        self.play_button.configure(text='Play')

        return

    def step_forward(self):
        curr_1 = self.readers[1].get_player().get_time()
        curr_2 = self.readers[2].get_player().get_time()

        frm_1 = self.readers[1].get_player().get_fps()
        frm_2 = self.readers[2].get_player().get_fps()

        mspf1 = 1000 / frm_1
        mspf2 = 1000 / frm_2

        target1 = int(curr_1 + mspf1)
        target2 = int(curr_2 + mspf2)

        self.readers[1].get_player().set_time(target1)
        self.readers[2].get_player().set_time(target2)
        self.readers[1].get_player().set_pause(1)
        self.readers[2].get_player().set_pause(1)
        self.play_button.configure(text='Play')

        return

    def open_video(self, number, fname=None):
        self.readers[number].get_player().stop()
        self.readers[(number % 2) + 1].get_player().pause()
        fname = fname if fname else tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~"))
        if fname:
            title = os.path.split(fname)[1]
            if number == 1:
                self.video1.set_location(fname)
                self.video1.update_title(title)
                self.readers[1].read_video(self.video1.get_location())
            if number == 2:
                self.video2.set_location(fname)
                self.video2.update_title(title)
                self.readers[2].read_video(self.video2.get_location())
            self.readers[number].get_player().audio_set_volume(self.volume)

            self.line_up()

        else:
            self.readers[number].get_player().play()

    def line_up(self):
        self.play()
        time.sleep(1)
        self.play()
        self.video1.set_time(0)
        self.video2.set_time(0)
        self.readers[1].get_player().set_time(0)
        self.readers[2].get_player().set_time(0)


if __name__ == "__main__":
    p = Player()
    p.mainloop()
    os._exit(0)
