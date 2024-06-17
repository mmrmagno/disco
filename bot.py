import discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import asyncio
from collections import deque
import subprocess

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['token']
PREFIX_TYPE = config['prefix']
DEVELOPER_ID = 249992281573031936

SPOTIPY_CLIENT_ID = config['spotify_client_id']
SPOTIPY_CLIENT_SECRET = config['spotify_client_secret']
SPOTIPY_REDIRECT_URI = config['spotify_redirect_uri']

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read"
)

intents = discord.Intents.default()
intents.message_content = True

if PREFIX_TYPE == "@mention":
    bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents, description="A versatile music bot supporting YouTube and Spotify streaming.")
else:
    bot = commands.Bot(command_prefix=PREFIX_TYPE, intents=intents, description="A versatile music bot supporting YouTube and Spotify streaming.")

queue = deque()
current_track = None
progress_task = None

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if PREFIX_TYPE == "@mention" and bot.user.mentioned_in(message):
        await bot.process_commands(message)
    elif PREFIX_TYPE != "@mention":
        await bot.process_commands(message)

@bot.command(name=config['commands']['play'])
async def play(ctx, *, query):
    global current_track, progress_task

    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            return

    if 'spotify.com' in query:
        track = await play_spotify(ctx, query)
    else:
        track = await play_youtube(ctx, query)

    if track:
        queue.append(track)
        await ctx.send(f"Added {track['title']} to the queue.")

        if not ctx.voice_client.is_playing():
            await play_next(ctx)
    else:
        await ctx.send("Could not retrieve the track information. Please try again with a different query.")

async def play_next(ctx):
    global current_track, progress_task

    if queue:
        current_track = queue.popleft()
        try:
            # Direct FFmpeg command method
            ffmpeg_command = [
                'ffmpeg', '-i', current_track['url'], '-f', 'opus', 'pipe:1'
            ]
            process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE)
            source = discord.FFmpegOpusAudio(process.stdout, pipe=True)
            ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
            progress_task = asyncio.create_task(progress_bar(ctx, current_track))
            await send_track_info(ctx, current_track)
        except Exception as e:
            print(f"Error playing track: {e}")
            await ctx.send(f"An error occurred while trying to play the track: {e}")
            await play_next(ctx)
    else:
        current_track = None
        if progress_task:
            progress_task.cancel()

async def play_youtube(ctx, query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': 'in_playlist',
        'default_search': 'ytsearch',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            # Extract audio URL
            url2 = info['url']
            formats = info.get('formats', None)
            if formats:
                for f in formats:
                    if f['ext'] == 'm4a':
                        url2 = f['url']
                        break
        except Exception as e:
            print(f"Error extracting info: {e}")
            await ctx.send("Could not retrieve information from YouTube.")
            return None
    
    return {
        'title': info['title'],
        'duration': info['duration'],
        'url': url2,
        'thumbnail': info.get('thumbnail', '')
    }

async def play_spotify(ctx, url):
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        await ctx.send(f"Please authorize the bot to access your Spotify account: {auth_url}")
        return None

    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.track(url)
    track = results['name']
    artist = results['artists'][0]['name']
    thumbnail = results['album']['images'][0]['url']
    duration = results['duration_ms'] / 1000
    query = f"{track} {artist} audio"
    track_info = await play_youtube(ctx, query)
    if track_info:
        track_info['thumbnail'] = thumbnail
    return track_info

async def send_track_info(ctx, track):
    if not track:
        await ctx.send("Could not play the track.")
        return
    embed = discord.Embed(title=track['title'], url=track['url'])
    if track['thumbnail']:
        embed.set_thumbnail(url=track['thumbnail'])
    await ctx.send(embed=embed)

async def progress_bar(ctx, track):
    duration = track['duration']
    elapsed = 0
    message = await ctx.send(embed=create_progress_embed(track['title'], elapsed, duration))
    while elapsed < duration and ctx.voice_client.is_playing():
        await asyncio.sleep(10)
        elapsed += 10
        embed = create_progress_embed(track['title'], elapsed, duration)
        await message.edit(embed=embed)

def create_progress_embed(title, elapsed, duration):
    progress = elapsed / duration
    bar_length = 30
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    embed = discord.Embed(title=title)
    embed.add_field(name="Progress", value=f"`[{bar}] {elapsed // 60}:{elapsed % 60:02d} / {duration // 60}:{duration % 60:02d}`")
    return embed

@bot.command(name=config['commands']['pause'])
async def pause(ctx):
    ctx.voice_client.pause()

@bot.command(name=config['commands']['resume'])
async def resume(ctx):
    ctx.voice_client.resume()

@bot.command(name=config['commands']['stop'])
async def stop(ctx):
    ctx.voice_client.stop()
    global queue
    queue.clear()

@bot.command(name=config['commands']['skip'])
async def skip(ctx):
    ctx.voice_client.stop()

@bot.command(name=config['commands']['queue'])
async def queue_command(ctx):
    if not queue:
        await ctx.send("The queue is empty.")
        return

    queue_list = "\n".join([track['title'] for track in queue])
    await ctx.send(f"Current queue:\n{queue_list}")

@bot.command(name=config['commands']['join'])
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f"{ctx.message.author.name} is not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name=config['commands']['leave'])
async def leave(ctx):
    await ctx.voice_client.disconnect()
    global queue
    queue.clear()

@bot.command(name=config['commands']['playlist'])
async def playlist(ctx, action, name=None, *, url=None):
    if action == 'create' and name:
        # Logic to create a playlist
        await ctx.send(f"Playlist '{name}' created.")
    elif action == 'add' and name and url:
        # Logic to add a song to a playlist
        await ctx.send(f"Added song to playlist '{name}'.")
    elif action == 'play' and name:
        # Logic to play a playlist
        await ctx.send(f"Playing playlist '{name}'.")
    else:
        await ctx.send("Invalid playlist command.")

@bot.command(name=config['commands']['bothelp'])
async def bothelp(ctx):
    prefix = PREFIX_TYPE if PREFIX_TYPE != "@mention" else f"@{bot.user.name}"
    help_text = f"""
    **Disco Bot Commands:**
    **Music Commands**
    - **Play a song**: `{prefix} play [url or song name]`
    - **Pause the music**: `{prefix} pause`
    - **Resume the music**: `{prefix} resume`
    - **Stop the music and clear the queue**: `{prefix} stop`
    - **Skip the current track**: `{prefix} skip`
    - **Show the current queue**: `{prefix} queue`
    - **Join your voice channel**: `{prefix} join`
    - **Leave the voice channel and clear the queue**: `{prefix} leave`
    
    **Playlist Commands**
    - **Create a playlist**: `{prefix} playlist create [name]`
    - **Add a song to a playlist**: `{prefix} playlist add [name] [url]`
    - **Play a playlist**: `{prefix} playlist play [name]`
    
    For more details, use `{prefix} help` in any channel.

    This bot was developed by <@{DEVELOPER_ID}>.
    """
    await ctx.author.send(help_text)
    await ctx.send("I have sent you a DM with all the commands.")

bot.run(TOKEN)

