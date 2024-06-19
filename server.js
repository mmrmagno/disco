const express = require('express');
const axios = require('axios');
const querystring = require('querystring');
const app = express();
const port = 8888;

const clientId = 'YOUR_SPOTIFY_CLIENT_ID';
const clientSecret = 'YOUR_SPOTIFY_CLIENT_SECRET';
const redirectUri = 'https://spotify.marc-os.com/callback';
const scopes = 'user-read-private user-read-email';

app.get('/login', (req, res) => {
  res.redirect(`https://accounts.spotify.com/authorize?response_type=code&client_id=${clientId}&scope=${encodeURIComponent(scopes)}&redirect_uri=${encodeURIComponent(redirectUri)}`);
});

app.get('/callback', (req, res) => {
  const code = req.query.code || null;
  axios({
    method: 'post',
    url: 'https://accounts.spotify.com/api/token',
    data: querystring.stringify({
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: redirectUri,
    }),
    headers: {
      'content-type': 'application/x-www-form-urlencoded',
      'Authorization': 'Basic ' + Buffer.from(clientId + ':' + clientSecret).toString('base64'),
    },
  })
  .then(response => {
    if (response.status === 200) {
      const { access_token, refresh_token } = response.data;
      res.send(`Access Token: ${access_token}<br>Refresh Token: ${refresh_token}`);
    } else {
      res.send(response.data);
    }
  })
  .catch(error => {
    res.send(error);
  });
});

app.listen(port, () => {
  console.log(`Server running on https://spotify.marc-os.com:${port}`);
});

