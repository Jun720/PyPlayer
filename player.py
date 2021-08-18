import vlc
import os
import threading
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as st
from tkinter.filedialog import askopenfilenames
import TkinterDnD2 as tkdnd


def ms_to_min(ms):
    m, s = divmod(ms / 1000, 60)
    h, m = divmod(m, 60)
    return str(round(h)).zfill(2) + ":" + str(round(m)).zfill(2) + ":" + str(round(s)).zfill(2)


class PyPlayer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.master.title("PyPlayer")
        self.master.geometry("500x330")
        self.pack()
        self.create_menu()
        self.create_playlist_panel()

        # Set media seek bar
        self.media_pos = tk.DoubleVar()
        self.media_pos.set(0)
        self.pos_seeker = tk.Scale(self.master,
                                   orient='h',
                                   resolution=0.01,
                                   variable=self.media_pos,
                                   command=self.set_position,
                                   length=450,
                                   from_=0.0,
                                   to=1.0)
        self.pos_seeker.bind('<MouseWheel>', self.pos_wheel)
        self.pos_seeker.pack()

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
        self.volume_bar = tk.Scale(self.master,
                                   label="Vol.",
                                   orient='h',
                                   variable=self.volume,
                                   command=self.set_volume,
                                   length=450,
                                   from_=0,
                                   to=100)
        self.volume_bar.bind('<MouseWheel>', self.volume_wheel)
        self.volume_bar.pack()

        self.master.bind('<KeyPress>', self.key_event)

        self.thread1 = threading.Thread(target=self.recursive_update_seeker)
        self.thread1.start()
        self.thread2 = threading.Thread(target=self.recursive_update_now_playing)
        self.thread2.start()

    def create_menu(self):
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        self.menu_file = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.menu_file)
        self.menu_file.add_command(label="Open", command=self.open_file)
        self.menu_file.add_command(label="Clear One", command=self.clear_one)
        self.menu_file.add_command(label="Clear All", command=self.clear_playlist)

    def create_control_panel(self):
        self.control_panel = ttk.Frame(self.master)
        self.control_panel.pack()
        self.shuffle_button = ttk.Button(self.control_panel, text="Shuffle:off", takefocus=False, command=self.shuffle)
        self.shuffle_button.pack(side='left')
        self.previous_button = ttk.Button(self.control_panel, text="Pre", takefocus=False, command=self.previous)
        self.previous_button.pack(side='left')
        self.play_button = ttk.Button(self.control_panel, text="Play", takefocus=False, command=self.play_pause)
        self.play_button.pack(side='left')
        self.next_button = ttk.Button(self.control_panel, text="Next", takefocus=False, command=self.next)
        self.next_button.pack(side='left')
        self.playback_button = ttk.Button(self.control_panel, text="Normal", takefocus=False, command=self.change_playback_mode)
        self.playback_button.pack(side='left')

    def create_playlist_panel(self):
        self.playlist_panel = ttk.Frame(self.master)
        self.playlist_panel.pack()
        self.playlist_log = st.ScrolledText(self.playlist_panel,
                                            cursor='hand2',
                                            height=10,
                                            selectbackground='white',
                                            selectforeground='black',
                                            state='disable')
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
                media = vlc.Media(file)
                self.media_list.add_media(media)
                self.player.set_media_list(self.media_list)
                self.update_playlist_log()

    def clear_one(self):
        txt = tk.Entry(width=20)
        txt.place(x=350, y=0)
        btn = tk.Button(text="Remove", command=lambda: [self.remove_at_index(txt.get()), txt.destroy(), btn.destroy()])
        btn.place(x=400, y=0)

    def remove_at_index(self, idx):
        try:
            self.media_list.remove_index(int(idx))
            self.player.set_media_list(self.media_list)
            self.update_playlist_log()
            self.update_now_playing()
        except:
            return

    def clear_playlist(self):
        for i in range(self.media_list.count()):
            self.media_list.remove_index(0)
        self.player.set_media_list(self.media_list)
        self.update_playlist_log()

    def drop_enter(self, event=None):
        self.master.focus_force()

    def drop(self, event):
        if event.data:
            paths = event.data.strip('{}').split('} {')
            for path in paths:
                if os.path.isdir(path):
                    found = []
                    for base, dirs, files in os.walk(path):
                        for filename in files:
                            found.append(os.path.join(base, filename))
                        for dirname in dirs:
                            found.append(os.path.join(base, dirname))

                    for file in found:
                        if not os.path.isdir(file) and os.path.splitext(file)[1] in self.type[0][1]:
                            media = vlc.Media(file)
                            self.media_list.add_media(media)
                            self.player.set_media_list(self.media_list)
                            self.update_playlist_log()
                else:
                    if os.path.splitext(path)[1] in self.type[0][1]:
                        media = vlc.Media(path)
                        self.media_list.add_media(media)
                        self.player.set_media_list(self.media_list)
                        self.update_playlist_log()

    def play_pause(self):
        if self.player.get_media_player().is_playing():
            self.player.pause()
            self.play_button['text'] = "Play"
        else:
            self.player.play()
            self.play_button['text'] = "Pause"

        self.update_now_playing()

    def next(self):
        self.player.next()
        self.update_now_playing()

    def previous(self):
        self.player.previous()
        self.update_now_playing()

    def shuffle(self):

        temp = list()
        print(self.media_list.count())
        print(len(self.media_list))
        if self.shuffle_button['text'] == "Shuffle:on":
            self.shuffle_button['default'] = 'normal'
            self.shuffle_button['text'] = 'Shuffle:off'
        else:
            self.shuffle_button['default'] = 'active'
            self.shuffle_button['text'] = 'Shuffle:on'
            print(self.shuffle_button['default'])

    def change_playback_mode(self):
        if self.playback_button['text'] == "Normal":
            self.player.set_playback_mode(vlc.PlaybackMode.repeat)
            self.playback_button['default'] = 'active'
            self.playback_button['text'] = "Repeat"
        elif self.playback_button['text'] == "Repeat":
            self.player.set_playback_mode(vlc.PlaybackMode.loop)
            self.playback_button['text'] = "Loop"
        else:
            self.player.set_playback_mode(vlc.PlaybackMode.default)
            self.playback_button['default'] = 'normal'
            self.playback_button['text'] = "Normal"

    def key_event(self, event):
        key = event.keysym
        if key == "Up":
            self.previous()
        elif key == "Down":
            self.next()
        elif key == "Right":
            self.player.get_media_player().set_time(self.player.get_media_player().get_time() + 5000)
            self.media_pos.set(self.player.get_media_player().get_position())
        elif key == "Left":
            self.player.get_media_player().set_time(self.player.get_media_player().get_time() - 5000)
            self.media_pos.set(self.player.get_media_player().get_position())
        elif key == "space":
            self.play_pause()

    def set_position(self, event=None):
        self.player.get_media_player().set_position(float(self.media_pos.get()))

    def set_volume(self, event=None):
        self.player.get_media_player().audio_set_volume(int(self.volume.get()))

    def pos_wheel(self, event):
        self.player.get_media_player().set_time(self.player.get_media_player().get_time() - int(5000*event.delta/120))
        self.media_pos.set(self.player.get_media_player().get_position())

    def volume_wheel(self, event):
        self.volume.set(self.volume.get() + event.delta/60)
        self.set_volume()

    def get_now_playing(self):
        if self.player.get_media_player().get_media() is not None:
            return self.player.get_media_player().get_media()

    def update_now_playing(self):
        playing = self.get_now_playing()
        if playing is not None and self.now_playing.cget('text') != playing.get_meta(vlc.Meta.Title):
            self.now_playing['text'] = playing.get_meta(vlc.Meta.Title)
            idx = self.media_list.index_of_item(playing)
            for i in range(self.media_list.count()):
                self.playlist_log.tag_config(i, foreground="black")
            self.playlist_log.tag_config(str(idx), foreground="blue")

        if self.player.get_media_player().is_playing():
            self.play_button['text'] = "Pause"
        else:
            self.play_button['text'] = "Play"

    def update_playlist_log(self):
        self.playlist_log.configure(state='normal')
        self.playlist_log.delete(1.0, 'end')
        for i in range(self.media_list.count()):
            log = self.media_list.item_at_index(i).get_meta(vlc.Meta.Title)
            self.playlist_log.insert('end', log + "\n", i)
            self.playlist_log.tag_bind(str(i), '<Double-Button-1>', self.play_selected)
            self.playlist_log.tag_bind(str(i), '<Double-Button-3>', self.remove_selected)
        self.playlist_log.configure(state='disable')

    def remove_selected(self, event=None):
        line = int(float(self.playlist_log.index('current')))
        self.remove_at_index(line - 1)

    def play_selected(self, event=None):
        line = int(float(self.playlist_log.index('current')))
        self.player.play_item_at_index(line-1)
        self.play_button['text'] = "Pause"
        self.update_now_playing()

    def recursive_update_seeker(self):
        pos = self.player.get_media_player().get_position()
        self.media_pos.set(pos)
        self.pos_seeker['label'] = ms_to_min(self.player.get_media_player().get_time()) + "/" + \
                                   ms_to_min(self.player.get_media_player().get_length())
        self.after(1000, self.recursive_update_seeker)

    def recursive_update_now_playing(self):
        self.update_now_playing()
        self.after(10000, self.recursive_update_now_playing)


if __name__ == '__main__':
    root = tkdnd.TkinterDnD.Tk()
    app = PyPlayer(master=root)
    app.mainloop()
