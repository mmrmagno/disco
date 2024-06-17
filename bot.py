import discord
from discord.ext import commands, tasks
import youtube_dl
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import asyncio
from collections import deque

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

    queue.append(track)
    await ctx.send(f"Added {track['title']} to the queue.")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    global current_track, progress_task

    if queue:
        current_track = queue.popleft()
        source = await discord.FFmpegOpusAudio.from_probe(current_track['url'])
        ctx.voice_client.play(source, after=lambda e: bot.loop.create_task(play_next(ctx)))
        progress_task = asyncio.create_task(progress_bar(ctx, current_track))
        await send_track_info(ctx, current_track)
    else:
        current_track = None
        if progress_task:
            progress_task.cancel()

async def play_youtube(ctx, query):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        if 'youtube.com' in query or 'youtu.be' in query:
            info = ydl.extract_info(query, download=False)
        else:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url2 = info['formats'][0]['url']
    
    return {
        'title': info['title'],
        'duration': info['duration'],
        'url': url2,
        'thumbnail': info.get('thumbnail', '')
    }

async def play_spotify(ctx, url):
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    results = sp.track(url)
    track = results['name']
    artist = results['artists'][0]['name']
    thumbnail = results['album']['images'][0]['url']
    duration = results['duration_ms'] / 1000
    query = f"{track} {artist} audio"
    return await play_youtube(ctx, query)

async def send_track_info(ctx, track):
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

@bot.command(name=config['commands']['help'])
async def help_command(ctx):
    help_text = (
        "Here are the available commands:\n"
        f"{PREFIX_TYPE}play [url or song name] - Play music from a URL or search for a song\n"
        f"{PREFIX_TYPE}pause - Pause the music\n"
        f"{PREFIX_TYPE}resume - Resume the music\n"
        f"{PREFIX_TYPE}stop - Stop the music and clear the queue\n"
        f"{PREFIX_TYPE}skip - Skip the current track\n"
        f"{PREFIX_TYPE}queue - Show the current queue\n"
        f"{PREFIX_TYPE}join - Join your voice channel\n"
        f"{PREFIX_TYPE}leave - Leave the voice channel and clear the queue\n"
        f"{PREFIX_TYPE}playlist create [name] - Create a playlist\n"
        f"{PREFIX_TYPE}playlist add [name] [url] - Add a song to a playlist\n"
        f"{PREFIX_TYPE}playlist play [name] - Play a playlist\n\n"
        f"This bot was developed by <@{DEVELOPER_ID}>."
    )
    await ctx.author.send(help_text)
    await ctx.send("I have sent you a DM with all the commands.")

bot.run(TOKEN)

