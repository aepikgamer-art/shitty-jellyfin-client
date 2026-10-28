# shitty jellyfin client - python + tkinter + vlc edition
# no .net sdk, no browser, no web app, and smart app control stays ON.
# needs: python (python.org) + VLC (videolan.org) + 'pip install python-vlc'
import tkinter as tk
from tkinter import messagebox
import json, ssl, urllib.request
import vlc

class ShittyClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('shitty jellyfin client (python edition, now SAC-proof-ish)')
        self.geometry('1100x720')
        self.configure(bg='#121218')

        self.base_url = None
        self.token = None
        self.user_id = None

        # --- top bar: login nonsense ---
        top = tk.Frame(self, bg='#1b1b24')
        top.pack(side='top', fill='x')
        tk.Label(top, text='server:', bg='#1b1b24', fg='#888').pack(side='left', padx=(6, 0))
        self.server_box = tk.Entry(top, width=28, bg='#2a2a36', fg='#eee', insertbackground='#eee')
        self.server_box.insert(0, 'http://192.168.1.10:8096')
        self.server_box.pack(side='left', padx=4, pady=6)
        tk.Label(top, text='user:', bg='#1b1b24', fg='#888').pack(side='left')
        self.user_box = tk.Entry(top, width=12, bg='#2a2a36', fg='#eee', insertbackground='#eee')
        self.user_box.insert(0, 'username')
        self.user_box.pack(side='left', padx=4)
        tk.Label(top, text='pass:', bg='#1b1b24', fg='#888').pack(side='left')
        self.pass_box = tk.Entry(top, width=12, bg='#2a2a36', fg='#eee', show='*', insertbackground='#eee')
        self.pass_box.pack(side='left', padx=4)
        tk.Button(top, text='Login', command=self.do_login, bg='#3a3a4a', fg='#eee',
                  activebackground='#4a4a5a', relief='flat').pack(side='left', padx=4)

        # --- body: sidebar + video ---
        body = tk.Frame(self, bg='#121218')
        body.pack(side='top', fill='both', expand=True)
        self.movie_list = tk.Frame(body, bg='#1b1b24', width=260)
        self.movie_list.pack(side='left', fill='y')
        self.movie_list.pack_propagate(False)
        self.scroll = tk.Canvas(self.movie_list, bg='#1b1b24', highlightthickness=0)
        self.scroll.pack(side='left', fill='both', expand=True)
        self.sb = tk.Scrollbar(self.movie_list, orient='vertical', command=self.scroll.yview)
        self.sb.pack(side='right', fill='y')
        self.scroll.configure(yscrollcommand=self.sb.set)
        self.inner = tk.Frame(self.scroll, bg='#1b1b24')
        self.scroll.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda e: self.scroll.configure(scrollregion=self.scroll.bbox('all')))

        self.video_frame = tk.Frame(body, bg='#000')
        self.video_frame.pack(side='left', fill='both', expand=True)

        # --- VLC: the actual media player. we outsourced the hard part again. ---
        self.instance = vlc.Instance('--no-osd')
        self.player = self.instance.media_player_new()
        self.player.set_hwnd(self.video_frame.winfo_id())  # embedded. inside the app. as requested.

        # --- bottom bar: seek + play/pause ---
        bottom = tk.Frame(self, bg='#1b1b24')
        bottom.pack(side='bottom', fill='x')
        self.play_pause = tk.Button(bottom, text='play/pause', command=self.toggle_play,
                                    bg='#3a3a4a', fg='#eee', relief='flat')
        self.play_pause.pack(side='left', padx=4, pady=4)
        self.seek_var = tk.DoubleVar()
        self.seeking = False
        self.seek = tk.Scale(bottom, variable=self.seek_var, from_=0, to=1000, orient='horizontal',
                             bg='#1b1b24', fg='#888', highlightthickness=0, length=600, showvalue=False)
        self.seek.bind('<ButtonPress-1>', lambda e: setattr(self, 'seeking', True))
        self.seek.bind('<ButtonRelease-1>', self.do_seek)
        self.seek.pack(side='left', fill='x', expand=True, padx=4)
        self.status = tk.Label(bottom, text='waiting for login...', bg='#1b1b24', fg='#888')
        self.status.pack(side='left', padx=8)

        self.protocol('WM_DELETE_WINDOW', self.quit_app)
        self.after(500, self.tick)  # polling hack. it is us. we are the polling hack.

    def api(self, path, data=None, headers=None):
        req = urllib.request.Request(self.base_url + path, data=(json.dumps(data).encode() if data else None),
                                     headers={'Content-Type': 'application/json', **(headers or {})})
        ctx = ssl._create_unverified_context()  # yes we ignore ssl errors. no we will not apologize.
        with urllib.request.urlopen(req, context=ctx) as r:
            return json.loads(r.read().decode())

    def do_login(self):
        try:
            self.base_url = self.server_box.get().strip().rstrip('/')
            resp = self.api('/Users/AuthenticateByName',
                            {'Username': self.user_box.get(), 'Pw': self.pass_box.get()})
            self.token = resp['AccessToken']
            self.user_id = resp['User']['Id']
            self.load_items()
        except Exception as e:
            messagebox.showerror('shitty client', 'login died: ' + str(e))  # error handling: still a popup. cope.

    def load_items(self):
        items = self.api('/Users/' + self.user_id + '/Items?IncludeItemTypes=Movie,Episode&Recursive=true',
                         headers={'X-Emby-Token': self.token})['Items']
        for w in self.inner.winfo_children():
            w.destroy()
        for item in items:
            b = tk.Button(self.inner, text=item['Name'], anchor='w', relief='flat',
                         bg='#2a2a36', fg='#eee', activebackground='#3a3a4a',
                         command=lambda i=item['Id'], n=item['Name']: self.play(i, n))
            b.pack(fill='x', padx=2, pady=2)
        self.status.config(text=str(len(items)) + ' things. no posters, no taste.')

    def play(self, item_id, name):
        url = self.base_url + '/Videos/' + item_id + '/stream.mp4?api_key=' + self.token
        media = self.instance.media_new(url)
        self.player.set_media(media)
        self.player.play()
        self.status.config(text='now playing: ' + name)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def do_seek(self, _event):
        self.seeking = False
        length = self.player.get_length()
        if length > 0:
            self.player.set_time(int(self.seek_var.get() / 1000.0 * length))

    def tick(self):
        length = self.player.get_length()
        if not self.seeking and length > 0:
            self.seek_var.set(self.player.get_time() / length * 1000)
        self.after(500, self.tick)

    def quit_app(self):
        self.player.stop()
        self.destroy()

if __name__ == '__main__':
    ShittyClient().mainloop()
