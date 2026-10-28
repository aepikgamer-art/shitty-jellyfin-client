# shitty jellyfin client - python + tkinter + vlc edition
# no .net sdk, no browser, no web app. SAC stays ON. dignity stays OFF.
# deps: pip install python-vlc pillow
import io
import json
import os
import ssl
import urllib.request
import tkinter as tk
from tkinter import messagebox

import vlc
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False  # no posters then. sadge.

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.json')


class ShittyClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('shitty jellyfin client (agent-touched, still no taste)')
        self.geometry('1200x760')
        self.configure(bg='#121218')

        self.base_url = None
        self.token = None
        self.user_id = None
        self.items = []
        self.item_widgets = {}  # id -> widget
        self.poster_refs = {}   # id -> PhotoImage (tk garbage collection avoidance hack)
        self.seeking = False
        self.fullscreen = False

        self._load_config()
        self._build_ui()

        # VLC: the actual media player. we outsourced the hard part, again.
        self.instance = vlc.Instance('--no-osd')
        self.player = self.instance.media_player_new()
        self.video_frame.after(50, lambda: self.player.set_hwnd(self.video_frame.winfo_id()))
        self.video_frame.bind('<Double-1>', lambda e: self.toggle_fullscreen())

        self.bind('<space>', lambda e: self.toggle_play())
        self.bind('<Escape>', lambda e: self.toggle_fullscreen() if self.fullscreen else None)
        self.bind('<Left>', lambda e: self.nudge(-10000))
        self.bind('<Right>', lambda e: self.nudge(10000))
        self.bind('<Up>', lambda e: self.nudge_volume(5))
        self.bind('<Down>', lambda e: self.nudge_volume(-5))

        self.protocol('WM_DELETE_WINDOW', self.quit_app)
        self.after(300, self.tick)

    # ---------- config (remembering things is a feature now, apparently) ----------
    def _load_config(self):
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            self._saved_server = cfg.get('server', '')
            self._saved_user = cfg.get('user', '')
        except Exception:
            self._saved_server = 'http://192.168.1.10:8096'
            self._saved_user = 'username'

    def _save_config(self):
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump({'server': self.server_box.get(), 'user': self.user_box.get()}, f)
        except Exception:
            pass  # forgetting your settings is not fatal. disappointing, but not fatal.

    # ---------- ui ----------
    def _build_ui(self):
        top = tk.Frame(self, bg='#1b1b24')
        top.pack(side='top', fill='x')
        self.server_box = self._entry(top, self._saved_server, 28)
        self.user_box = self._entry(top, self._saved_user, 12)
        self.pass_box = self._entry(top, '', 12, show='*')
        tk.Button(top, text='Login', command=self.do_login, bg='#3a3a4a', fg='#eee',
                  activebackground='#4a4a5a', relief='flat').pack(side='left', padx=4, pady=6)
        self.pass_box.bind('<Return>', lambda e: self.do_login())

        body = tk.Frame(self, bg='#121218')
        body.pack(side='top', fill='both', expand=True)

        # sidebar: search + scrollable list with posters
        self.movie_list = tk.Frame(body, bg='#1b1b24', width=300)
        self.movie_list.pack(side='left', fill='y')
        self.movie_list.pack_propagate(False)
        search_bar = tk.Frame(self.movie_list, bg='#1b1b24')
        search_bar.pack(side='top', fill='x')
        self.search_box = self._entry(search_bar, '', 26)
        self.search_box.configure(placeholder=None) if False else None
        self.search_box.insert(0, 'search (it filters, wow)')
        self.search_box.bind('<FocusIn>', lambda e: self._search_focus_in())
        self.search_box.bind('<KeyRelease>', lambda e: self.render_list())
        self.search_box.pack(side='left', padx=6, pady=6)

        self.scroll = tk.Canvas(self.movie_list, bg='#1b1b24', highlightthickness=0)
        self.scroll.pack(side='left', fill='both', expand=True)
        sb = tk.Scrollbar(self.movie_list, orient='vertical', command=self.scroll.yview)
        sb.pack(side='right', fill='y')
        self.scroll.configure(yscrollcommand=sb.set)
        self.inner = tk.Frame(self.scroll, bg='#1b1b24')
        self.scroll.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda e: self.scroll.configure(scrollregion=self.scroll.bbox('all')))
        self.scroll.bind('<Enter>', lambda e: self.scroll.bind_all('<MouseWheel>', self._wheel))
        self.scroll.bind('<Leave>', lambda e: self.scroll.unbind_all('<MouseWheel>'))

        self.video_frame = tk.Frame(body, bg='#000')
        self.video_frame.pack(side='left', fill='both', expand=True)
        self.now_playing = tk.Label(self.video_frame, text='double-click video = fullscreen',
                                   bg='#000', fg='#444')
        self.now_playing.place(relx=0.5, rely=0.5, anchor='center')

        # bottom: controls
        bottom = tk.Frame(self, bg='#1b1b24')
        bottom.pack(side='bottom', fill='x')
        self.play_pause = tk.Button(bottom, text='play/pause', command=self.toggle_play,
                                    bg='#3a3a4a', fg='#eee', relief='flat')
        self.play_pause.pack(side='left', padx=4, pady=4)
        tk.Button(bottom, text='stop', command=self.stop, bg='#3a3a4a', fg='#eee',
                  relief='flat').pack(side='left', padx=2)
        self.seek_var = tk.DoubleVar()
        self.seek = tk.Scale(bottom, variable=self.seek_var, from_=0, to=1000, orient='horizontal',
                             bg='#1b1b24', fg='#888', highlightthickness=0, showvalue=False)
        self.seek.bind('<ButtonPress-1>', lambda e: setattr(self, 'seeking', True))
        self.seek.bind('<ButtonRelease-1>', self.do_seek)
        self.seek.pack(side='left', fill='x', expand=True, padx=4)
        self.time_label = tk.Label(bottom, text='0:00 / 0:00', bg='#1b1b24', fg='#888', width=16)
        self.time_label.pack(side='left', padx=2)
        self.vol_var = tk.IntVar(value=100)
        tk.Scale(bottom, variable=self.vol_var, from_=0, to=100, orient='horizontal',
                 command=lambda v: self.player.audio_set_volume(int(float(v))),
                 bg='#1b1b24', fg='#888', highlightthickness=0, length=120, showvalue=False
                 ).pack(side='left', padx=2)
        self.status = tk.Label(bottom, text='waiting for login... (space=pause, arrows=seek/vol)',
                               bg='#1b1b24', fg='#888')
        self.status.pack(side='left', padx=8)

    def _entry(self, parent, initial, width, show=None):
        e = tk.Entry(parent, width=width, bg='#2a2a36', fg='#eee', insertbackground='#eee',
                     relief='flat', show=show)
        e.insert(0, initial)
        e.pack(side='left', padx=4, pady=6)
        return e

    def _search_focus_in(self):
        if self.search_box.get() == 'search (it filters, wow)':
            self.search_box.delete(0, 'end')

    def _wheel(self, e):
        self.scroll.yview_scroll(-1 * (e.delta // 120), 'units')

    # ---------- jellyfin api ----------
    def api(self, path, data=None, headers=None):
        req = urllib.request.Request(self.base_url + path,
                                     data=(json.dumps(data).encode() if data else None),
                                     headers={'Content-Type': 'application/json', **(headers or {})})
        ctx = ssl._create_unverified_context()  # yes we ignore ssl errors. no we will not apologize.
        with urllib.request.urlopen(req, context=ctx) as r:
            return json.loads(r.read().decode())

    def fetch_bytes(self, path, headers=None):
        req = urllib.request.Request(self.base_url + path, headers=headers or {})
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=ctx) as r:
            return r.read()

    def do_login(self):
        try:
            self.base_url = self.server_box.get().strip().rstrip('/')
            resp = self.api('/Users/AuthenticateByName',
                            {'Username': self.user_box.get(), 'Pw': self.pass_box.get()})
            self.token = resp['AccessToken']
            self.user_id = resp['User']['Id']
            self._save_config()
            self.load_items()
        except Exception as e:
            messagebox.showerror('shitty client', 'login died: ' + str(e))

    def load_items(self):
        data = self.api('/Users/' + self.user_id +
                        '/Items?IncludeItemTypes=Movie,Episode&Recursive=true&Fields=MediaSources',
                        headers={'X-Emby-Token': self.token})
        self.items = data['Items']
        self.render_list()
        self.status.config(text=str(len(self.items)) + ' things found. some even have posters now.')

    # ---------- list rendering (with posters, if pillow deigned to install) ----------
    def render_list(self):
        query = self.search_box.get().strip().lower()
        if query == 'search (it filters, wow)':
            query = ''
        for w in self.inner.winfo_children():
            w.destroy()
        self.item_widgets.clear()
        self.poster_refs.clear()
        shown = 0
        for item in self.items:
            if query and query not in item['Name'].lower():
                continue
            shown += 1
            self._add_list_item(item)
        if shown == 0:
            tk.Label(self.inner, text='nothing matches. skill issue?', bg='#1b1b24', fg='#666',
                     pady=8).pack()

    def _add_list_item(self, item):
        frame = tk.Frame(self.inner, bg='#23232e', cursor='hand2')
        frame.pack(fill='x', padx=4, pady=3)
        iid, name = item['Id'], item['Name']
        if HAS_PIL:
            img_label = tk.Label(frame, bg='#23232e')
            img_label.pack(side='left', padx=4, pady=4)
            img_label.bind('<Button-1>', lambda e: self.play(iid, name))
            self.after(10, lambda: self._fetch_poster(iid, img_label))
        text_label = tk.Label(frame, text=name, bg='#23232e', fg='#eee', anchor='w',
                              justify='left', wraplength=170)
        text_label.pack(side='left', fill='x', expand=True, padx=6, pady=4)
        sub = item.get('SeriesName') or (item.get('ProductionYear') and str(item['ProductionYear'])) or ''
        if sub:
            tk.Label(frame, text=sub, bg='#23232e', fg='#777', anchor='w').pack(side='right', padx=6)
        text_label.bind('<Button-1>', lambda e: self.play(iid, name))
        for lbl in (text_label,):
            lbl.bind('<Double-1>', lambda e: self.play(iid, name))
        self.item_widgets[iid] = frame

    def _fetch_poster(self, iid, label):
        def worker():
            try:
                raw = self.fetch_bytes('/Items/' + iid + '/Images/Primary?maxWidth=160',
                                       headers={'X-Emby-Token': self.token})
                img = Image.open(io.BytesIO(raw))
                img.thumbnail((160, 160))
                photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: (self.poster_refs.update({iid: photo}),
                                       label.config(image=photo) if iid in self.item_widgets else None))
            except Exception:
                pass  # no poster. it is fine. we are fine. everything is fine.
        import threading
        threading.Thread(target=worker, daemon=True).start()

    # ---------- playback ----------
    def play(self, item_id, name):
        item = next((i for i in self.items if i['Id'] == item_id), None)
        url = self.base_url + '/Videos/' + item_id + '/stream.mp4?api_key=' + self.token
        media = self.instance.media_new(url)
        self._try_subtitles(media, item, item_id)
        self.player.set_media(media)
        self.player.play()
        self.now_playing.config(text='')
        self.status.config(text='now playing: ' + name)

    def _try_subtitles(self, media, item, item_id):
        # best effort subtitles. if this fails we simply do not care.
        try:
            sources = (item or {}).get('MediaSources') or []
            for src in sources:
                for stream in src.get('MediaStreams', []):
                    if stream.get('Type') == 'Subtitle' and stream.get('IsExternal') and stream.get('IsTextSubtitleStream'):
                        sub_url = (self.base_url + '/Videos/' + item_id + '/' + src['Id'] +
                                   '/Subtitles/' + str(stream['Index']) + '/Stream.vtt?api_key=' + self.token)
                        try:
                            media.slave_add(sub_url, 2, 4)  # 2 = subtitle, priority 4. trust me.
                        except Exception:
                            pass
                        return
        except Exception:
            pass

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()
        self.now_playing.config(text='double-click video = fullscreen')
        self.status.config(text='stopped. sitting there. menacingly.')

    def nudge(self, ms):
        if self.player.get_length() > 0:
            self.player.set_time(max(0, self.player.get_time() + ms))

    def nudge_volume(self, d):
        v = max(0, min(100, self.vol_var.get() + d))
        self.vol_var.set(v)
        self.player.audio_set_volume(v)

    def do_seek(self, _event):
        self.seeking = False
        length = self.player.get_length()
        if length > 0:
            self.player.set_time(int(self.seek_var.get() / 1000.0 * length))

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.attributes('-fullscreen', self.fullscreen)
        if self.fullscreen:
            self.movie_list.pack_forget()
            top_for_pack = self.nametowidget(self.winfo_children()[0])  # keep top bar, hide sidebar only
        else:
            self.movie_list.pack(side='left', fill='y')  # reflow happens via geometry manager

    @staticmethod
    def _fmt(ms):
        s = int(ms // 1000)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return ('%d:%02d:%02d' % (h, m, s)) if h else ('%d:%02d' % (m, s))

    def tick(self):
        length = self.player.get_length()
        if not self.seeking and length > 0:
            self.seek_var.set(self.player.get_time() / length * 1000)
            self.time_label.config(text='%s / %s' % (self._fmt(self.player.get_time()), self._fmt(length)))
        self.after(300, self.tick)

    def quit_app(self):
        self.player.stop()
        self.destroy()


if __name__ == '__main__':
    ShittyClient().mainloop()
