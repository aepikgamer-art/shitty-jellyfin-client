using System;
using System.Drawing;
using System.Text;
using System.Text.Json;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows.Forms;
using LibVLCSharp.Shared;
using LibVLCSharp.WinForms;

namespace ShittyJellyfin
{
    // Still one file. We're consistent about being inconsistent.
    public class MainForm : Form
    {
        private readonly HttpClient _http = new HttpClient();
        private string _baseUrl, _token, _userId;
        private TextBox _serverBox, _userBox, _passBox;
        private FlowLayoutPanel _moviePanel;
        private VideoView _videoView;
        private TrackBar _seekBar;
        private Timer _tickTimer;
        private LibVLC _libvlc;
        private MediaPlayer _player;
        private bool _seeking;

        public MainForm()
        {
            Text = "shitty jellyfin client (now with REAL playback, still no taste)";
            Width = 1100; Height = 720;

            Core.Initialize();
            _libvlc = new LibVLC("--no-osd");
            _player = new MediaPlayer(_libvlc);

            var top = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
            _serverBox = new TextBox { Width = 220, Text = "http://192.168.1.10:8096" };
            _userBox = new TextBox { Width = 120, Text = "username" };
            _passBox = new TextBox { Width = 120, UseSystemPasswordChar = true };
            var login = new Button { Text = "Login" };
            login.Click += async (s, e) => await Login();
            top.Controls.AddRange(new Control[] { _serverBox, _userBox, _passBox, login });

            var bottom = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 50 };
            _seekBar = new TrackBar { Width = 500, Minimum = 0, Maximum = 1000 };
            _seekBar.MouseDown += (s, e) => _seeking = true;
            _seekBar.MouseUp += async (s, e) =>
            {
                _seeking = false;
                if (_player.Length > 0)
                    await _player.SetTimeAsync((long)(_seekBar.Value / 1000.0 * _player.Length));
            };
            bottom.Controls.Add(new Label { Text = "seek:", AutoSize = true, Padding = new Padding(0, 12, 0, 0) });
            bottom.Controls.Add(_seekBar);

            _videoView = new VideoView { Dock = DockStyle.Fill };
            _videoView.MediaPlayer = _player;

            _moviePanel = new FlowLayoutPanel { Dock = DockStyle.Left, Width = 240, AutoScroll = true, BackColor = Color.FromArgb(18, 18, 24) };

            Controls.Add(_videoView);
            Controls.Add(_moviePanel);
            Controls.Add(bottom);
            Controls.Add(top);

            _tickTimer = new Timer { Interval = 500 };
            _tickTimer.Tick += (s, e) =>
            {
                if (!_seeking && _player.Length > 0)
                    _seekBar.Value = (int)(_player.Time / (double)_player.Length * 1000);
            };
            _tickTimer.Start();
        }

        private async Task Login()
        {
            try
            {
                _baseUrl = _serverBox.Text.Trim().TrimEnd('/');
                var body = JsonSerializer.Serialize(new { Username = _userBox.Text, Pw = _passBox.Text });
                var resp = await _http.PostAsync(_baseUrl + "/Users/AuthenticateByName",
                    new StringContent(body, Encoding.UTF8, "application/json"));
                resp.EnsureSuccessStatusCode();
                using var doc = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
                _token = doc.RootElement.GetProperty("AccessToken").GetString();
                _userId = doc.RootElement.GetProperty("User").GetProperty("Id").GetString();
                _http.DefaultRequestHeaders.Add("X-Emby-Token", _token);
                await LoadMovies();
            }
            catch (Exception ex)
            {
                MessageBox.Show("login died: " + ex.Message); // error handling is still a MessageBox, cope
            }
        }

        private async Task LoadMovies()
        {
            var url = _baseUrl + "/Users/" + _userId + "/Items?IncludeItemTypes=Movie,Episode&Recursive=true";
            var resp = await _http.GetStringAsync(url);
            using var doc = JsonDocument.Parse(resp);
            _moviePanel.Controls.Clear();
            foreach (var item in doc.RootElement.GetProperty("Items").EnumerateArray())
            {
                var name = item.GetProperty("Name").GetString();
                var id = item.GetProperty("Id").GetString();
                var btn = new Button { Width = 220, Height = 50, Text = name, FlatStyle = FlatStyle.Flat };
                btn.Click += (s, e) => Play(id);
                _moviePanel.Controls.Add(btn);
            }
        }

        private void Play(string id)
        {
            // REAL in-app playback. VLC does the heavy lifting, we take the credit.
            var streamUrl = _baseUrl + "/Videos/" + id + "/stream.mp4?api_key=" + _token;
            using var media = new Media(_libvlc, new Uri(streamUrl));
            _player.Play(media);
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _player?.Dispose();
            _libvlc?.Dispose();
            base.OnFormClosed(e);
        }

        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            Application.Run(new MainForm());
        }
    }
}
