import discord
from discord.ext import commands
import youtube_dl
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import soundcloud_lib

with open('config.json') as config_file:
    config = json.load(config_file)

token = config['token']


