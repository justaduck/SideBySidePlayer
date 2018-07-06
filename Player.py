import os
import tkFileDialog
from Tkinter import *
import vlc
import threading


class Reader:
    def __init__(self, frame_id):
        self.frame_id = frame_id
        self.video = None
        self.inst = vlc.Instance()

    def read_video(self, video):
        self.player = self.inst.media_player_new()
        events = self.player.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, self.eov)
        self.player.set_hwnd(self.frame_id)
        media = self.inst.media_new_path(video)
        self.player.set_media(media)

    def get_player(self):
        return self.player

    def eov(self, evt):
        self.player.release()
        print(evt)


class Video(Frame):
    def __init__(self, master, path=None):
        Frame.__init__(self, master)
        self.master = master
        self.title = StringVar()
        self.title.set(os.path.split(path)[1] if path else "Select a Video")
        self.path = path
        self.setup_video()
        self.current_frame = 0

    def setup_video(self):
        self.title_label = Label(self, textvar=self.title)
        self.title_label.pack(side=TOP)
        self.video_frame = Frame(self, width=(self.master.winfo_screenwidth()-100)/2,
                                 height=self.master.winfo_screenheight()-200)
        self.video_frame.pack(side=BOTTOM, fill=BOTH)
        return

    def get_frame_id(self):
        return self.video_frame.winfo_id()

    def update_title(self, title):
        self.title.set(title)
        return

    def set_location(self, location):
        self.path = location
        return

    def get_location(self):
        return self.path


class Player(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.readers = {}
        self.height = self.winfo_screenheight()
        self.width = self.winfo_screenwidth()
        self.create_widgets()

    def create_widgets(self):
        self.menubar = Menu(self)
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label='Open Video 1', command=lambda: self.open_video(1))
        self.fileMenu.add_command(label='Open Video 2', command=lambda: self.open_video(2))
        self.config(menu=self.menubar)

        self.volume = 0
        self.state = "paused"
        self.video1 = Video(self)
        self.open_video(1, r'C:\Users\FirschingJ\Desktop\test_player\1b4594ef00d9a398798009eaafe20ec9-A.mov')
        self.video1.grid(row=0, column=0, padx=5)
        self.video2 = Video(self)
        self.open_video(2, r'C:\Users\FirschingJ\Desktop\test_player\1b4594ef00d9a398798009eaafe20ec9-B.mp4')
        self.video2.grid(row=0, column=1, padx=5)
        self.buttonBox()

    def buttonBox(self):
        frm = Frame()
        frm.grid(row=1, columnspan=2)
        self.play = Button(frm, text="Play", command=self.play)
        rewind = Button(frm, text="Restart", command=self.restart)
        volume_up = Button(frm, text="Vol Up", command=self.volume_up)
        volume_down = Button(frm, text="Vol Down", command=self.volume_down)
        self.play.grid(row=1, column=0)
        rewind.grid(row=1, column=1)
        volume_down.grid(row=1, column=2)
        volume_up.grid(row=1, column=3)

    def play(self):
        if self.readers[1].get_player().get_state() == vlc.State.Ended:
            self.readers[1].get_player().set_time(0)
            self.readers[1].play()
            self.readers[2].get_player().set_time(0)
            self.readers[2].play()
        elif self.state != "playing":
            self.readers[1].get_player().play()
            self.readers[2].get_player().play()
            self.play.configure(text="Pause")
            self.state = "playing"
        else:
            self.readers[1].get_player().pause()
            self.readers[2].get_player().pause()
            self.play.configure(text="Play")
            self.state = "paused"

    def restart(self):
        self.readers[1].get_player().set_time(0)
        self.readers[2].get_player().set_time(0)

    def volume_up(self):
        if self.volume == 100:
            pass
        else:
            self.volume += 5
            self.readers[1].get_player().audio_set_volume(self.volume)
            self.readers[2].get_player().audio_set_volume(self.volume)

    def volume_down(self):
        if self.volume == 0:
            pass
        else:
            self.readers[1].get_player().audio_set_volume(self.volume-5)
            self.readers[2].get_player().audio_set_volume(self.volume-5)
            self.volume -= 5

    def open_video(self, number, fname=None):
        fname = fname if fname else tkFileDialog.askopenfilename(initialdir=os.path.expanduser("~"))
        if fname:
            title = os.path.split(fname)[1]
            if number == 1:
                self.video1.set_location(fname)
                self.video1.update_title(title)
                if 1 not in self.readers:
                    self.readers[1] = Reader(self.video1.get_frame_id())
                    threading.Thread(target=self.readers[1])
                self.readers[1].read_video(self.video1.get_location())
                self.readers[1].get_player().audio_set_volume(self.volume)
            if number == 2:
                self.video2.set_location(fname)
                self.video2.update_title(title)
                if 2 not in self.readers:
                    self.readers[2] = Reader(self.video2.get_frame_id())
                    threading.Thread(target=self.readers[2])
                self.readers[2].read_video(self.video2.get_location())
                self.readers[2].get_player().audio_set_volume(self.volume)
        else:
            return


if __name__ == "__main__":
    p = Player()
    p.mainloop()
