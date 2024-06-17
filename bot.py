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
    await ctx.send(f"Added {track.title} to the queue.")

@bot.command(name=config['commands']['help'])
async def custom_help(ctx):
    prefix = PREFIX_TYPE if PREFIX_TYPE != "@mention" else f"@{bot.user.name}"
    help_message = f"""
    **Disco Bot Commands:**
    - **Play a song**: `{prefix} play [url or song name]`
    - **Pause the music**: `{prefix} pause`
    - **Resume the music**: `{prefix} resume`
    - **Stop the music and clear the queue**: `{prefix} stop`
    - **Skip the current track**: `{prefix} skip`
    - **Show the current queue**: `{prefix} queue`
    - **Join your voice channel**: `{prefix} join`
    - **Leave the voice channel and clear the queue**: `{prefix} leave`
    - **Create a playlist**: `{prefix} playlist create [name]`
    - **Add a song to a playlist**: `{prefix} playlist add [name] [url]`
    - **Play a playlist**: `{prefix} playlist play [name]`
    - **Get help with commands**: `{prefix} help`
    """
    help_message += f"\n\nDeveloped by <@{DEVELOPER_ID}>"
    await ctx.author.send(help_message)
    await ctx.send("Help message sent to your DM.")

async def play_spotify(ctx, query):
    # Function implementation here
    pass

async def play_youtube(ctx, query):
    # Function implementation here
    pass

bot.run(TOKEN)

