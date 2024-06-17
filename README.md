### Discord Music Bot 

![Disco Logo](https://www.marc-os.com/disco.webp)

#### Table of Contents

1.  [Introduction](#introduction)
2.  [Installation](#installation)
3.  [Configuration](#configuration)
4.  [Running the Bot](#running-the-bot)
5.  [Commands](#commands)
6.  [Usage](#usage)
7.  [Contributing](#contributing)
8.  [License](#license)

* * * * *

### Introduction

This Discord Music Bot allows users to play music from YouTube and Spotify in their Discord voice channels. It supports queue functionality, allowing users to add multiple songs to the queue and play them in order.

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/discord-music-bot.git
    cd discord-music-bot
    ```

2.  **Install the required dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3.  **Set up your Spotify developer account:**

    -   Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    -   Log in with your Spotify account.
    -   Create a new application and get your Client ID and Client Secret.
    -   Set the Redirect URI to `http://localhost:8888/callback`.

### Configuration

1.  **Create a `config.json` file in the root directory:**

    ```json
     {
      "token": "YOUR_DISCORD_BOT_TOKEN",
      "prefix": "@mention",
      "spotify_client_id": "YOUR_SPOTIFY_CLIENT_ID",
      "spotify_client_secret": "YOUR_SPOTIFY_CLIENT_SECRET",
      "spotify_redirect_uri": "http://localhost:8888/callback",
      "commands": {
        "play": "play",
        "pause": "pause",
        "resume": "resume",
        "stop": "stop",
        "skip": "skip",
        "queue": "queue",
        "join": "join",
        "leave": "leave",
        "help": "help",
        "playlist": "playlist"
      }
    }
    ```

2.  **Replace the placeholders with your actual values:**

    -   `YOUR_DISCORD_BOT_TOKEN`: Your Discord bot token.
    -   `YOUR_SPOTIFY_CLIENT_ID`: Your Spotify Client ID.
    -   `YOUR_SPOTIFY_CLIENT_SECRET`: Your Spotify Client Secret.

### Running the Bot

1.  **Start the OAuth server:**

    

    sh```    
    python oauth_server.py
    ```

2.  **Run the bot:**

    sh

    Copy code

    `python bot.py`

### Commands

Here are the available commands:

-   **Play a song by URL or name:**

    css

    Copy code

    `@BotName play [url or song name]`

-   **Pause the music:**

    css

    Copy code

    `@BotName pause`

-   **Resume the music:**

    css

    Copy code

    `@BotName resume`

-   **Stop the music and clear the queue:**

    arduino

    Copy code

    `@BotName stop`

-   **Skip the current track:**

    sql

    Copy code

    `@BotName skip`

-   **Show the current queue:**

    arduino

    Copy code

    `@BotName queue`

-   **Join your voice channel:**

    perl

    Copy code

    `@BotName join`

-   **Leave the voice channel and clear the queue:**

    css

    Copy code

    `@BotName leave`

-   **Create a playlist:**

    sql

    Copy code

    `@BotName playlist create [name]`

-   **Add a song to a playlist:**

    sql

    Copy code

    `@BotName playlist add [name] [url]`

-   **Play a playlist:**

    css

    Copy code

    `@BotName playlist play [name]`

-   **Get help with commands:**

    bash

    Copy code

    `@BotName help`

### Usage

1.  **Play a song by name:**

    css

    Copy code

    `@BotName play Bohemian Rhapsody`

2.  **Play a song from Spotify:**

    less

    Copy code

    `@BotName play https://open.spotify.com/track/3ZFTkvIE7kyPt6Nu3PEa7V`

3.  **View the queue:**

    arduino

    Copy code

    `@BotName queue`

4.  **Skip the current song:**

    sql

    Copy code

    `@BotName skip`

5.  **Stop the music and clear the queue:**

    arduino

    Copy code

    `@BotName stop`

6.  **Join a voice channel:**

    perl

    Copy code

    `@BotName join`

7.  **Leave a voice channel and clear the queue:**

    css

    Copy code

    `@BotName leave`

### Contributing

If you would like to contribute to this project, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature-branch`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature-branch`).
5.  Create a new Pull Request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
