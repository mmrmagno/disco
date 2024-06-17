from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

app = FastAPI()

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

SPOTIPY_CLIENT_ID = config['spotify_client_id']
SPOTIPY_CLIENT_SECRET = config['spotify_client_secret']
SPOTIPY_REDIRECT_URI = config['spotify_redirect_uri']

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read"
)

@app.get("/")
async def login():
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get('code')
    token_info = sp_oauth.get_access_token(code)
    return {"access_token": token_info['access_token']}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
