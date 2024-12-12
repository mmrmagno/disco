# 🎵 Disco

A professional and feature-rich Discord music bot with advanced playlist management, audio controls, and detailed statistics tracking. Built with discord.py and yt-dlp.

## ✨ Features

### Core Music Features
- 🎵 High-quality YouTube audio playback
- 📑 Advanced playlist management
- 🔄 Queue system with history tracking
- 🔊 Volume control and audio settings
- 🎯 Precise playback control (play, pause, skip, seek)

### Advanced Features
- 📊 Detailed statistics tracking
- 📝 Song history logging
- 🔁 Multiple loop modes (off/single/queue)
- 🔀 Queue shuffling
- 📈 User activity monitoring
- 💾 Playlist saving and loading
- 📱 Now playing status with thumbnails

### Technical Features
- 🔒 Secure environment variable configuration
- 📋 Comprehensive error handling and logging
- ⚡ Asynchronous operation
- 🔍 Advanced YouTube search
- 💻 Cross-platform compatibility

## 📋 Requirements

- Python 3.8 or higher
- Discord.py 2.0 or higher
- FFmpeg
- Required Python packages (see requirements.txt)

## 🚀 Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/discord-music-bot.git
cd discord-music-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
DISCORD_TOKEN=your_bot_token_here
MAX_QUEUE_SIZE=100
DEFAULT_VOLUME=0.5
```

4. **Run the bot**
```bash
python bot.py
```

## 🎮 Commands

### Music Commands
- `/play <query>` - Play a song or playlist from YouTube
- `/pause` - Pause the current song
- `/resume` - Resume playback
- `/skip` - Skip the current song
- `/queue` - View the current queue
- `/nowplaying` - Show current song information
- `/volume <0-100>` - Adjust playback volume
- `/seek <seconds>` - Seek to a specific position

### Playlist Management
- `/playlist create <name>` - Create a new playlist
- `/playlist add <name> <song>` - Add a song to a playlist
- `/playlist load <name>` - Load and play a playlist
- `/playlist list` - Show all saved playlists
- `/playlist delete <name>` - Delete a playlist

### Queue Controls
- `/shuffle` - Shuffle the current queue
- `/loop` - Toggle loop mode (off/single/queue)
- `/clear` - Clear the current queue
- `/history` - View recently played songs

### Statistics and Info
- `/stats` - View bot statistics
- `/mystats` - View your listening statistics
- `/topplayed` - Show most played songs
- `/servertop` - Show server's top tracks

## 📊 Statistics Tracking

The bot tracks various statistics including:
- Most played songs
- User listening time
- Popular genres
- Peak usage times
- Server activity
- Playlist popularity

Statistics are stored locally and can be exported or reset by server administrators.

## 🛠️ Configuration

Advanced configuration options can be set in `config.json`:
```json
{
    "max_queue_size": 100,
    "default_volume": 50,
    "stats_tracking": true,
    "history_size": 50,
    "playlist_limit": 10
}
```

## 🔧 Troubleshooting

Common issues and solutions:
1. **Bot won't play audio**
   - Ensure FFmpeg is installed and in PATH
   - Check voice channel permissions

2. **Command not working**
   - Verify bot has required permissions
   - Check command syntax

3. **Statistics not updating**
   - Verify database permissions
   - Check disk space

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

If you need help with the bot:
1. Check the [Troubleshooting](#troubleshooting) section
2. Open an issue on GitHub

## ✨ Acknowledgments

- Discord.py team
- yt-dlp developers
- FFmpeg project
- All contributors

---
Made with ❤️ by Marc
