using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace ShittyJellyfin
{
    // The whole app. One file. We don't do architecture here.
    public class MainForm : Form
    {
        private readonly HttpClient _http = new HttpClient();
        private string _baseUrl, _token, _userId;
        private TextBox _serverBox, _userBox, _passBox;
        private FlowLayoutPanel _moviePanel;

        public MainForm()
        {
            Text = "shitty jellyfin client (yes it looks like this on purpose)";
            Width = 1000; Height = 700;

            var top = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 40 };
            _serverBox = new TextBox { Width = 220, Text = "http://192.168.1.10:8096" };
            _userBox = new TextBox { Width = 120, Text = "username" };
            _passBox = new TextBox { Width = 120, UseSystemPasswordChar = true };
            var login = new Button { Text = "Login" };
            login.Click += async (s, e) => await Login();
            top.Controls.AddRange(new Control[] { _serverBox, _userBox, _passBox, login });

            _moviePanel = new FlowLayoutPanel { Dock = DockStyle.Fill, AutoScroll = true };

            Controls.Add(_moviePanel);
            Controls.Add(top);
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
                MessageBox.Show("login died: " + ex.Message); // error handling is a MessageBox, cope
            }
        }

        private async Task LoadMovies()
        {
            var url = _baseUrl + "/Users/" + _userId + "/Items?IncludeItemTypes=Movie&Recursive=true&Fields=PrimaryImageAspectRatio";
            var resp = await _http.GetStringAsync(url);
            using var doc = JsonDocument.Parse(resp);
            _moviePanel.Controls.Clear();
            foreach (var item in doc.RootElement.GetProperty("Items").EnumerateArray())
            {
                var name = item.GetProperty("Name").GetString();
                var id = item.GetProperty("Id").GetString();
                var btn = new Button { Width = 220, Height = 60, Text = name };
                btn.Click += (s, e) => Play(id); // double click?? nah. single click. deal with it.
                _moviePanel.Controls.Add(btn);
            }
        }

        private void Play(string id)
        {
            // "media player" = your browser. we are not writing a video decoder today.
            var streamUrl = _baseUrl + "/Videos/" + id + "/stream.mp4?api_key=" + _token;
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(streamUrl) { UseShellExecute = true });
        }

        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            Application.Run(new MainForm());
        }
    }
}
