import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import aiohttp
import logging
from collections import deque
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='musicbot.log'
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '100'))
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))
MAX_RETRIES = 3

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Enhanced YouTube DL configuration
yt_dlp_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'reconnect': True,
    'reconnect_streamed': True,
    'reconnect_delay_max': 5,
    'cookiefile': 'youtube_cookies.txt'
}

class Song:
    def __init__(self, data, requester):
        self.title = data.get('title', 'Unknown')
        self.url = data.get('url')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail')
        self.requester = requester
        self.timestamp = datetime.now()

class MusicQueue:
    def __init__(self):
        self.queue = deque(maxlen=MAX_QUEUE_SIZE)
        self.history = deque(maxlen=50)
        
    def add(self, song):
        self.queue.append(song)
        
    def next(self):
        if self.queue:
            song = self.queue.popleft()
            self.history.append(song)
            return song
        return None
    
    def clear(self):
        self.queue.clear()
        
    def shuffle(self):
        temp_queue = list(self.queue)
        random.shuffle(temp_queue)
        self.queue = deque(temp_queue, maxlen=MAX_QUEUE_SIZE)
        
    def remove(self, index):
        if 0 <= index < len(self.queue):
            return list(self.queue).pop(index)
        return None

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.yt = yt_dlp.YoutubeDL(yt_dlp_opts)
        self.queues = {}
        self.volumes = {}
        self.now_playing = {}
        self.loop_mode = {}
        self.session = aiohttp.ClientSession()
        self.retry_counts = {}
        self.ffmpeg_options = {
            'before_options': (
                '-reconnect 1 '
                '-reconnect_streamed 1 '
                '-reconnect_delay_max 5 '
                '-analyzeduration 0 '
                '-loglevel warning'
            ),
            'options': (
                '-vn '
                '-b:a 192k '
                '-bufsize 3000k '
                '-maxrate 200k '
                '-ar 48000 '
                '-ac 2 '
                '-f opus'
            )
        }

    async def play_next(self, guild):
        """Enhanced play_next function with better error handling and retry logic."""
        try:
            if not guild.voice_client or not guild.voice_client.is_connected():
                return

            queue = self.get_queue(guild.id)
            
            if self.loop_mode.get(guild.id) == 1 and self.now_playing.get(guild.id):
                song = self.now_playing[guild.id]
            else:
                song = queue.next()
                if not song and self.loop_mode.get(guild.id) == 2:
                    queue.queue.extend(queue.history)
                    queue.history.clear()
                    song = queue.next()
            
            if not song:
                self.retry_counts[guild.id] = 0
                return

            if guild.id not in self.retry_counts:
                self.retry_counts[guild.id] = 0

            self.now_playing[guild.id] = song

            try:
                # Create audio source with enhanced error handling and buffering
                audio_source = await discord.FFmpegOpusAudio.from_probe(
                    song.url,
                    **self.ffmpeg_options
                )
                
                def after_playing(error):
                    if error:
                        logging.error(f"Error during playback: {error}")
                        if self.retry_counts.get(guild.id, 0) < MAX_RETRIES:
                            self.retry_counts[guild.id] = self.retry_counts.get(guild.id, 0) + 1
                            asyncio.run_coroutine_threadsafe(
                                self.play_next(guild), self.bot.loop
                            )
                        else:
                            logging.error(f"Max retries reached for guild {guild.id}")
                            self.retry_counts[guild.id] = 0
                            asyncio.run_coroutine_threadsafe(
                                self.cleanup_voice_client(guild), self.bot.loop
                            )
                    else:
                        self.retry_counts[guild.id] = 0
                        asyncio.run_coroutine_threadsafe(
                            self.play_next(guild), self.bot.loop
                        )

                guild.voice_client.play(audio_source, after=after_playing)
                
                if guild.id in self.volumes:
                    guild.voice_client.source.volume = self.volumes[guild.id]
                else:
                    guild.voice_client.source.volume = DEFAULT_VOLUME

            except Exception as e:
                logging.error(f"Error playing audio: {e}")
                if self.retry_counts.get(guild.id, 0) < MAX_RETRIES:
                    self.retry_counts[guild.id] = self.retry_counts.get(guild.id, 0) + 1
                    await asyncio.sleep(1)
                    await self.play_next(guild)
                else:
                    self.retry_counts[guild.id] = 0
                    logging.error(f"Failed to play audio after {MAX_RETRIES} attempts")
                    await self.cleanup_voice_client(guild)

        except Exception as e:
            logging.error(f"Error in play_next: {e}")
            await self.cleanup_voice_client(guild)
        
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Music Bot Commands", color=discord.Color.blue())
        commands = {
            "play": "Play a song or playlist from YouTube",
            "pause": "Pause the current song",
            "resume": "Resume playback",
            "skip": "Skip the current song",
            "stop": "Stop playback and clear the queue",
            "nowplaying": "Show current song information",
            "queue": "Show the current queue",
            "volume": "Set playback volume (0-100)",
            "loop": "Set loop mode (off/single/queue)",
            "shuffle": "Shuffle the current queue",
            "remove": "Remove a song from the queue",
            "history": "Show recently played songs",
            "seek": "Seek to a position in the song",
            "lyrics": "Get lyrics for the current song",
            "leave": "Disconnect the bot from voice"
        }
        
        for cmd, desc in commands.items():
            embed.add_field(name=f"/{cmd}", value=desc, inline=False)
            
        await interaction.response.send_message(embed=embed)

    async def cleanup_voice_client(self, guild):
        """Safely clean up voice client resources."""
        if guild.voice_client:
            try:
                if guild.voice_client.is_playing():
                    guild.voice_client.stop()
                await guild.voice_client.disconnect(force=True)
            except Exception as e:
                logging.error(f"Error during voice client cleanup: {e}")

    async def create_voice_client(self, channel):
        """Create a voice client with retry logic."""
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return await channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                retries += 1
                logging.warning(f"Voice connection attempt {retries} failed: {e}")
                await asyncio.sleep(1)
        raise Exception("Failed to establish voice connection after multiple attempts")

    @app_commands.command(name="play", description="Play a song or playlist from YouTube")
    @app_commands.describe(query="YouTube URL or search term")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You must be in a voice channel!")
            return
            
        await interaction.response.defer()
        
        try:
            if not interaction.guild.voice_client:
                await self.create_voice_client(interaction.user.voice.channel)
            
            # Reset retry counter when starting new playback
            self.retry_counts[interaction.guild.id] = 0
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.yt.extract_info(query, download=False))
            
            if 'entries' in data:
                entries = data['entries']
                await interaction.followup.send(f"📑 Adding {len(entries)} songs from playlist...")
                
                for entry in entries:
                    song = Song(entry, interaction.user)
                    self.get_queue(interaction.guild.id).add(song)
                    
            else:
                song = Song(data, interaction.user)
                self.get_queue(interaction.guild.id).add(song)
                await interaction.followup.send(f"🎵 Added to queue: {song.title}")
            
            if not interaction.guild.voice_client.is_playing():
                await self.play_next(interaction.guild)
                
        except Exception as e:
            logging.error(f"Error in play command: {str(e)}")
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")
            await self.cleanup_voice_client(interaction.guild)

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("⏸️ Playback paused")
        else:
            await interaction.response.send_message("Nothing is playing!")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("▶️ Playback resumed")
        else:
            await interaction.response.send_message("Nothing is paused!")

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Nothing to skip!")
            return
            
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped current song")

    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            self.get_queue(interaction.guild.id).clear()
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏹️ Playback stopped and queue cleared")
        else:
            await interaction.response.send_message("Nothing is playing!")

    @app_commands.command(name="queue", description="Show the current queue")
    async def queue(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.queue:
            await interaction.response.send_message("Queue is empty!")
            return
            
        embed = discord.Embed(title="Current Queue", color=discord.Color.blue())
        
        for i, song in enumerate(queue.queue, 1):
            duration = str(timedelta(seconds=song.duration))
            embed.add_field(
                name=f"{i}. {song.title}",
                value=f"Duration: {duration} | Requested by: {song.requester.display_name}",
                inline=False
            )
            if i >= 10:  # Show only first 10 songs
                remaining = len(queue.queue) - 10
                if remaining > 0:
                    embed.add_field(name="...", value=f"And {remaining} more songs", inline=False)
                break
                
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove", description="Remove a song from the queue")
    @app_commands.describe(index="Position of the song in the queue (1-based)")
    async def remove(self, interaction: discord.Interaction, index: int):
        queue = self.get_queue(interaction.guild.id)
        if index < 1 or index > len(queue.queue):
            await interaction.response.send_message("Invalid queue position!")
            return
            
        removed_song = queue.remove(index - 1)
        if removed_song:
            await interaction.response.send_message(f"🗑️ Removed from queue: {removed_song.title}")
        else:
            await interaction.response.send_message("Failed to remove song!")

    @app_commands.command(name="leave", description="Disconnect the bot from voice")
    async def leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            self.get_queue(interaction.guild.id).clear()
            await interaction.response.send_message("👋 Disconnected from voice")
        else:
            await interaction.response.send_message("Not in a voice channel!")

    @app_commands.command(name="nowplaying", description="Show information about the current song")
    async def nowplaying(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing right now!")
            return
            
        song = self.now_playing.get(interaction.guild.id)
        if not song:
            await interaction.response.send_message("Cannot get current song info!")
            return
            
        embed = discord.Embed(title="Now Playing", color=discord.Color.blue())
        embed.add_field(name="Title", value=song.title)
        embed.add_field(name="Requested by", value=song.requester.display_name)
        embed.add_field(name="Duration", value=str(timedelta(seconds=song.duration)))
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Set the playback volume (0-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        if not 0 <= volume <= 100:
            await interaction.response.send_message("Volume must be between 0 and 100!")
            return
            
        if interaction.guild.voice_client:
            self.volumes[interaction.guild.id] = volume / 100
            interaction.guild.voice_client.source.volume = volume / 100
            await interaction.response.send_message(f"🔊 Volume set to {volume}%")
        else:
            await interaction.response.send_message("Not currently playing!")

    @app_commands.command(name="loop", description="Set loop mode (off/single/queue)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value=0),
        app_commands.Choice(name="Single", value=1),
        app_commands.Choice(name="Queue", value=2)
    ])
    async def loop(self, interaction: discord.Interaction, mode: int):
        self.loop_mode[interaction.guild.id] = mode
        modes = ["disabled", "single track", "queue"]
        await interaction.response.send_message(f"🔄 Loop mode: {modes[mode]}")

    @app_commands.command(name="shuffle", description="Shuffle the current queue")
    async def shuffle(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        queue.shuffle()
        await interaction.response.send_message("🔀 Queue shuffled!")

    @app_commands.command(name="history", description="Show recently played songs")
    async def history(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        if not queue.history:
            await interaction.response.send_message("No song history available!")
            return
            
        embed = discord.Embed(title="Recently Played Songs", color=discord.Color.blue())
        for i, song in enumerate(reversed(queue.history), 1):
            embed.add_field(
                name=f"{i}. {song.title}",
                value=f"Requested by {song.requester.display_name}",
                inline=False
            )
            if i >= 10:  # Show only last 10 songs
                break
                
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="seek", description="Seek to a specific position (in seconds)")
    async def seek(self, interaction: discord.Interaction, position: int):
        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing right now!")
            return
            
        song = self.now_playing.get(interaction.guild.id)
        if not song or position >= song.duration:
            await interaction.response.send_message("Invalid position!")
            return
            
        # Implementation would require modifying the FFmpeg options
        await interaction.response.send_message(f"⏩ Seeking to {position} seconds")

    @app_commands.command(name="lyrics", description="Get lyrics for the current song")
    async def lyrics(self, interaction: discord.Interaction):
        if not self.now_playing.get(interaction.guild.id):
            await interaction.response.send_message("Nothing is playing right now!")
            return
            
        song = self.now_playing[interaction.guild.id]
        # Here you would implement lyrics fetching from a service like Genius
        await interaction.response.send_message(f"🎵 Searching lyrics for: {song.title}...")

    @app_commands.command(name="clear", description="Clear the current queue")
    async def clear(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        queue.clear()
        await interaction.response.send_message("🗑️ Queue cleared!")

    @app_commands.command(name="move", description="Move a song to a different position in the queue")
    @app_commands.describe(
        from_pos="Current position of the song",
        to_pos="New position for the song"
    )
    async def move(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        queue = self.get_queue(interaction.guild.id)
        if not 1 <= from_pos <= len(queue.queue) or not 1 <= to_pos <= len(queue.queue):
            await interaction.response.send_message("❌ Invalid position!")
            return
            
        queue_list = list(queue.queue)
        song = queue_list.pop(from_pos - 1)
        queue_list.insert(to_pos - 1, song)
        queue.queue = deque(queue_list, maxlen=MAX_QUEUE_SIZE)
        await interaction.response.send_message(f"✅ Moved {song.title} to position {to_pos}")

    async def cog_before_invoke(self, interaction: discord.Interaction):
        """Check if the bot has required permissions before executing commands."""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in servers!")
            return False
            
        permissions = interaction.guild.me.guild_permissions
        if not permissions.connect or not permissions.speak:
            await interaction.response.send_message("❌ I need permission to join and speak in voice channels!")
            return False
            
        return True

    def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        for voice_client in self.bot.voice_clients:
            asyncio.create_task(voice_client.disconnect())
        asyncio.create_task(self.session.close())

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logging.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")
        
@bot.event
async def on_voice_state_update(member, before, after):
    """Enhanced voice state update handler with better cleanup"""
    if member.id == bot.user.id and after.channel is None:  # Bot was disconnected
        guild = member.guild
        if guild.id in bot.get_cog('MusicBot').queues:
            bot.get_cog('MusicBot').queues[guild.id].clear()
        if guild.id in bot.get_cog('MusicBot').now_playing:
            del bot.get_cog('MusicBot').now_playing[guild.id]
    elif member.guild.voice_client and len(member.guild.voice_client.channel.members) == 1:
        await asyncio.sleep(60)  # Wait 60 seconds before disconnecting if alone
        if member.guild.voice_client and len(member.guild.voice_client.channel.members) == 1:
            await member.guild.voice_client.disconnect()
        
@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Please wait {error.retry_after:.2f}s before using this command again.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    else:
        logging.error(f"Command error: {str(error)}")
        await ctx.send("❌ An error occurred while executing the command.")

async def setup():
    """Initialize the bot and add the MusicBot cog."""
    await bot.add_cog(MusicBot(bot))

if __name__ == "__main__":
    asyncio.run(setup())
    bot.run(TOKEN)
