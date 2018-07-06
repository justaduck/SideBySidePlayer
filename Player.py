import os
import tkFileDialog
from Tkinter import *
import vlc
import threading

video = r'Video Goes Here'


class Reader:
    def __init__(self, path, frame):
        self.path = path
        self.frame = frame
        self.read_frames()

    def read_frames(self):
        self.inst = vlc.Instance()
        self.player = self.inst.media_player_new()
        media = self.inst.media_new(video)
        self.player.set_media(media)
        self.player.set_hwnd(self.frame.winfo_id())
        self.player.play()

    def get_frames(self):
        return self.frames


    def get_frame_number(self, number):
        try:
            return self.frames[number]
        except IndexError:
            print("Could not load frame {0}".format(number))


class Video(Frame):
    def __init__(self, master, title=None):
        Frame.__init__(self, master)
        self.master = master
        self.title = StringVar()
        self.title.set(title if title else "Select a Video")
        self.setup_video()
        self.current_frame = 0

    def setup_video(self):
        self.title_label = Label(self, textvar=self.title)
        self.title_label.grid(row=0)
        self.canvas = Canvas(self)
        self.canvas.grid(row=1)
        return

    def update_title(self, title):
        self.title.set(title)
        return

    def set_location(self, location):
        self.location = location
        return

    def get_location(self):
        return self.location


class Player(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.create_widgets()



    def create_widgets(self):
        self.menubar = Menu(self)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label='Open Video 1', command=lambda: self.open_video(1))
        self.fileMenu.add_command(label='Open Video 2', command=lambda: self.open_video(2))
        self.config(menu=self.menubar)

        self.video1 = Video(self)
        self.video1.grid(row=0, column=0)
        self.video2 = Video(self)
        self.video2.grid(row=0, column=1)
        self.buttonBox()
        self.reader1 = Reader(self.video1.get_location(), self.video1)
        self.reader2 = Reader(self.video2.get_location(), self.video2)
        self.volume = 100


    def buttonBox(self):
        frm = Frame()
        frm.grid(row=1, columnspan=2)
        play = Button(frm, text="Play", command=self.play)
        pause = Button(frm, text="Pause", command=self.pause)
        rewind = Button(frm, text="Rewind", command=self.rewind)
        volume_up = Button(frm, text="Vol Up", command=self.vup)
        volume_down = Button(frm, text="Vol Down", command=self.vdown)
        play.pack()
        pause.pack()
        rewind.pack()
        volume_down.pack()
        volume_up.pack()


    def play(self):
        threading.Thread(target=self.reader1.play())
        threading.Thread(target=self.reader2.play())

    def pause(self):
        self.reader1.player.pause()
        self.reader2.player.pause()

    def rewind(self):
        self.reader1.player.rewind()
        self.reader2.player.rewind()

    def volume_up(self):
        if self.volume == 100:
            pass
        else:
            self.reader1.player.audio_set_volume(self.volume+5)
            self.reader2.player.audio_set_volume(self.volume+5)
            self.volume += 5

    def volume_down(self):
        if self.volume == 0:
            pass
        else:
            self.reader1.player.audio_set_volume(self.volume-5)
            self.reader2.player.audio_set_volume(self.volume-5)
            self.volume -= 5

    def open_video(self, number):
        fname = tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~"))
        title = os.path.split(fname)[1]
        if number == 1:
            self.video1.set_location(fname)
            self.video1.update_title(title)
        if number == 2:
            self.video2.set_location(fname)
            self.video2.update_title(title)


if __name__ == "__main__":
    p = Player()
    p.mainloop()
