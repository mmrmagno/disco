const express = require('express');
const bodyParser = require('body-parser');
const SpotifyWebApi = require('spotify-web-api-node');
const fs = require('fs');

// Load configuration
const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));

const app = express();
app.use(bodyParser.json());

const spotifyApi = new SpotifyWebApi({
    clientId: config.spotify.client_id,
    clientSecret: config.spotify.client_secret,
    redirectUri: config.spotify.redirect_uri
});

// Scopes for the access token
const scopes = ['user-read-private', 'user-read-email', 'playlist-read-private', 'playlist-read-collaborative', 'user-library-read', 'user-top-read', 'user-read-playback-state', 'user-modify-playback-state'];

// Redirect user to the Spotify authorization page
app.get('/login', (req, res) => {
    const authorizeURL = spotifyApi.createAuthorizeURL(scopes);
    res.redirect(authorizeURL);
});

// Callback route to handle the response from Spotify
app.get('/callback', async (req, res) => {
    const code = req.query.code || null;

    try {
        const data = await spotifyApi.authorizationCodeGrant(code);
        const accessToken = data.body['access_token'];
        const refreshToken = data.body['refresh_token'];

        // Store the access and refresh token in a secure place
        fs.writeFileSync('spotify_tokens.json', JSON.stringify({ accessToken, refreshToken }));

        // Set the access and refresh token on the API object
        spotifyApi.setAccessToken(accessToken);
        spotifyApi.setRefreshToken(refreshToken);

        res.send('Successfully authenticated with Spotify!');
    } catch (err) {
        console.error('Error getting Spotify access token:', err);
        res.send('Error during Spotify authentication.');
    }
});

// Endpoint to refresh the access token
app.get('/refresh_token', async (req, res) => {
    try {
        const data = await spotifyApi.refreshAccessToken();
        const accessToken = data.body['access_token'];

        // Update the access token in our storage
        let tokens = JSON.parse(fs.readFileSync('spotify_tokens.json', 'utf8'));
        tokens.accessToken = accessToken;
        fs.writeFileSync('spotify_tokens.json', JSON.stringify(tokens));

        // Update the access token on the API object
        spotifyApi.setAccessToken(accessToken);

        res.send('Access token refreshed!');
    } catch (err) {
        console.error('Error refreshing access token:', err);
        res.send('Error refreshing access token.');
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

