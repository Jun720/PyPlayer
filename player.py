import vlc
import os
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as st
from tkinter.filedialog import askopenfilenames
import TkinterDnD2 as tkdnd


class PyPlayer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.master.title("PyPlayer")
        self.master.geometry("500x400")
        self.pack()
        self.create_menu()
        self.create_palylist_panel()
        self.create_media_panel()
        self.create_control_panel()

        self.type = [("", "*.flac;*.mp3;*.wav;*.m4a")]
        self.init_dir = os.path.abspath(os.path.dirname(__file__))
        self.player = vlc.MediaListPlayer()
        self.media_list = vlc.MediaList()
        self.player.set_media_list(self.media_list)

        # Define drag-and-drop event
        self.master.drop_target_register(tkdnd.DND_FILES)
        self.master.dnd_bind('<<DropEnter>>', self.drop_enter)
        self.master.dnd_bind('<<Drop>>', self.drop)

        # Set volume bar
        self.volume = tk.DoubleVar()
        self.volume.set(100)
        self.volume_bar = ttk.Scale(self.master,
                                    variable=self.volume,
                                    command=self.set_volume,
                                    from_=0,
                                    to=100)
        self.volume_bar.pack()

    def create_menu(self):
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        self.menu_file = tk.Menu(self.menu_bar,  tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.menu_file)
        self.menu_file.add_command(label="Open", command=self.open_file)
        self.menu_file.add_command(label="Clear One", command=self.clear_one)
        self.menu_file.add_command(label="Clear All", command=self.clear_playlist)

    def create_control_panel(self):
        self.control_panel = ttk.Frame(self.master)
        self.control_panel.pack()
        self.previous_button = ttk.Button(self.control_panel, text="Pre", command=self.previous)
        self.previous_button.pack(side='left')
        self.play_button = ttk.Button(self.control_panel, text="Play", command=self.play_pause)
        self.play_button.pack(side='left')
        self.next_button = ttk.Button(self.control_panel, text="Next", command=self.next)
        self.next_button.pack(side='left')

    def create_palylist_panel(self):
        self.palylist_panel = ttk.Frame(self.master)
        self.palylist_panel.pack()
        self.playlist_log = st.ScrolledText(self.palylist_panel)
        self.playlist_log.configure(state='disable')
        self.playlist_log.pack()

    def create_media_panel(self):
        self.media_panel = ttk.Frame(self.master)
        self.media_panel.pack()
        self.now_playing_label = ttk.Label(self.media_panel, text="Now Playing:")
        self.now_playing_label.pack()
        self.now_playing = ttk.Label(self.media_panel)
        self.now_playing.pack()

    def open_file(self):
        files = askopenfilenames(filetypes=self.type, initialdir=self.init_dir)
        if files != "":
            for file in files:
                print(file)
                print(type(file))
                media = vlc.Media(file)
                self.media_list.add_media(media)
                self.player.set_media_list(self.media_list)
                self.update_playlist_log()

    def clear_one(self):
        self.media_list.remove_index(0)
        self.player.set_media_list(self.media_list)
        self.update_playlist_log()

    def clear_playlist(self):
        for i in range(self.media_list.count()):
            self.media_list.remove_index(0)
        self.player.set_media_list(self.media_list)
        self.update_playlist_log()

    def drop_enter(self, event):
        self.master.focus_force()

    def drop(self, event):
        if event.data:
            files = event.data.strip('{}').split('} {')
            print(files)
            for file in files:
                media = vlc.Media(file)
                self.media_list.add_media(media)
                self.player.set_media_list(self.media_list)
                self.update_playlist_log()

    def play_pause(self):
        if self.play_button['text'] == "Play":
            self.play_button['text'] = "Pause"
            self.player.play()

        elif self.play_button['text'] == "Pause":
            self.play_button['text'] = "Play"
            self.player.pause()

        self.update_now_playing()

    def play(self):
        self.player.stop()
        self.player.play()

    def stop(self):
        self.player.stop()
        if self.play_button['text'] == "Pause":
            self.play_button['text'] = "Play"

    def pause(self):
        self.player.pause()

    def next(self):
        self.player.next()
        self.update_now_playing()
        if self.play_button['text'] == "Play":
            self.play_button['text'] = "Pause"

    def previous(self):
        self.player.previous()
        self.update_now_playing()
        if self.play_button['text'] == "Play":
            self.play_button['text'] = "Pause"

    def get_now_playing(self):
        if self.player.get_media_player().get_media() is not None:
            return self.player.get_media_player().get_media()

    def update_now_playing(self):
        playing = self.get_now_playing()
        if playing is not None:
            self.now_playing['text'] = playing.get_meta(vlc.Meta.Title)

    def update_playlist_log(self):
        self.playlist_log.configure(state='normal')
        self.playlist_log.delete(1.0, 'end')
        for i in range(self.media_list.count()):
            log = self.media_list.item_at_index(i).get_meta(vlc.Meta.Title)
            self.playlist_log.insert('end', log + "\n", i)
        self.playlist_log.configure(state='disable')

    def set_volume(self, event=None):
        self.player.get_media_player().audio_set_volume(int(self.volume.get()))


if __name__ == '__main__':
    root = tkdnd.TkinterDnD.Tk()
    app = PyPlayer(master=root)
    app.mainloop()
