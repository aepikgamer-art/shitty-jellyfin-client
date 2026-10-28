# shitty jellyfin client - powershell + wpf edition
# no .net sdk. no browser. no dignity.
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

$script:BaseUrl = $null
$script:Token  = $null
$script:UserId = $null

[xml]$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        Title="shitty jellyfin client (powershell edition, somehow worse)"
        Height="720" Width="1100" Background="#121218" WindowStartupLocation="CenterScreen">
  <Grid>
    <Grid.ColumnDefinitions>
      <ColumnDefinition Width="260"/>
      <ColumnDefinition Width="*"/>
    </Grid.ColumnDefinitions>
    <Grid.RowDefinitions>
      <RowDefinition Height="Auto"/>
      <RowDefinition Height="*"/>
      <RowDefinition Height="Auto"/>
    </Grid.RowDefinitions>
    <StackPanel Grid.Row="0" Grid.ColumnSpan="2" Orientation="Horizontal" Background="#1b1b24">
      <TextBox Name="ServerBox" Width="220" Margin="6">http://192.168.1.10:8096</TextBox>
      <TextBox Name="UserBox" Width="120" Margin="6">username</TextBox>
      <PasswordBox Name="PassBox" Width="120" Margin="6"/>
      <Button Name="LoginBtn" Content="Login" Margin="6" Padding="10,4"/>
    </StackPanel>
    <ScrollViewer Grid.Row="1" Grid.Column="0" Background="#1b1b24">
      <StackPanel Name="MovieList"/>
    </ScrollViewer>
    <MediaElement Name="Player" Grid.Row="1" Grid.Column="1" LoadedBehavior="Manual" ScrubbingEnabled="True"/>
    <DockPanel Grid.Row="2" Grid.ColumnSpan="2" Background="#1b1b24" Margin="0,4">
      <Button Name="PlayPauseBtn" Content="play/pause" Width="80" Margin="4"/>
      <Slider Name="SeekBar" Minimum="0" Maximum="1000" VerticalAlignment="Center" Margin="4"/>
      <TextBlock Name="StatusText" Text="waiting for login..." Foreground="#888" VerticalAlignment="Center" Margin="8,0,8,0"/>
    </DockPanel>
  </Grid>
</Window>
"@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$win = [Windows.Markup.XamlReader]::Load($reader)

function Get-Control { param($name) $win.FindName($name) }

$serverBox  = Get-Control 'ServerBox'
$userBox    = Get-Control 'UserBox'
$passBox    = Get-Control 'PassBox'
$loginBtn   = Get-Control 'LoginBtn'
$movieList  = Get-Control 'MovieList'
$player     = Get-Control 'Player'
$playPause  = Get-Control 'PlayPauseBtn'
$seekBar    = Get-Control 'SeekBar'
$statusText = Get-Control 'StatusText'

$script:seeking = $false

function Do-Login {
  try {
    $script:BaseUrl = $serverBox.Text.Trim().TrimEnd('/')
    $body = @{ Username = $userBox.Text; Pw = $passBox.Password } | ConvertTo-Json
    $uri = $script:BaseUrl + '/Users/AuthenticateByName'
    $resp = Invoke-RestMethod -Method Post -Uri $uri -ContentType 'application/json' -Body $body
    $script:Token  = $resp.AccessToken
    $script:UserId = $resp.User.Id
    $statusText.Text = 'logged in. somehow.'
    Load-Items
  } catch {
    # error handling is a messagebox. we stay consistent.
    [System.Windows.MessageBox]::Show('login died: ' + $_.Exception.Message) | Out-Null
  }
}

function Load-Items {
  $url = $script:BaseUrl + '/Users/' + $script:UserId + '/Items?IncludeItemTypes=Movie,Episode&Recursive=true'
  $items = (Invoke-RestMethod -Uri $url -Headers @{ 'X-Emby-Token' = $script:Token }).Items
  $movieList.Children.Clear()
  foreach ($item in $items) {
    $btn = New-Object System.Windows.Controls.Button
    $btn.Content = $item.Name
    $btn.Margin = '2,2,2,2'
    $btn.Padding = '6,6,6,6'
    $btn.Background = '#2a2a36'
    $btn.Foreground = '#eeeeee'
    $btn.BorderThickness = '0'
    $id = $item.Id
    $name = $item.Name
    $btn.Add_Click({ Play-Item $id $name }.GetNewClosure())
    $movieList.Children.Add($btn) | Out-Null
  }
  $statusText.Text = ([string]$items.Count + ' things. no posters, no taste.')
}

function Play-Item {
  param($id, $name)
  $player.Source = $script:BaseUrl + '/Videos/' + $id + '/stream.mp4?api_key=' + $script:Token
  $player.Play()
  $statusText.Text = 'now playing: ' + $name
}

$loginBtn.Add_Click({ Do-Login })

$playPause.Add_Click({
  if ($player.IsPlaying) { $player.Pause() } else { $player.Play() }
})

$seekBar.Add_PreviewMouseDown({ $script:seeking = $true })
$seekBar.Add_PreviewMouseUp({
  $script:seeking = $false
  if ($player.NaturalDuration.HasTimeSpan) {
    $player.Position = [TimeSpan]::FromSeconds($seekBar.Value / 1000.0 * $player.NaturalDuration.TimeSpan.TotalSeconds)
  }
})

# seek bar polling timer. yes it is a hack. everything here is.
$timer = New-Object System.Windows.Threading.DispatcherTimer
$timer.Interval = [TimeSpan]::FromMilliseconds(500)
$timer.Add_Tick({
  if (-not $script:seeking -and $player.NaturalDuration.HasTimeSpan -and $player.NaturalDuration.TimeSpan.TotalSeconds -gt 0) {
    $seekBar.Value = [int]($player.Position.TotalSeconds / $player.NaturalDuration.TimeSpan.TotalSeconds * 1000)
  }
})
$timer.Start()

$win.ShowDialog() | Out-Null
