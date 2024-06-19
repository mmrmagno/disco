const fs = require('fs');
const Discord = require('discord.js');
const ytdl = require('ytdl-core');
const SpotifyWebApi = require('spotify-web-api-node');
const config = JSON.parse(fs.readFileSync('config.json', 'utf8'));

const client = new Discord.Client();
const prefix = config.prefix;
const altprefix = config.altprefix;

// Spotify API setup
const spotifyApi = new SpotifyWebApi({
    clientId: config.spotify.client_id,
    clientSecret: config.spotify.client_secret,
    redirectUri: config.spotify.redirect_uri
});

let currentTrack = null;
let queue = [];

client.once('ready', () => {
    console.log('Bot is online!');
    client.user.setActivity(config.game, { type: 'LISTENING' });
});

client.on('message', async message => {
    if (!message.content.startsWith(prefix) && !message.content.startsWith(altprefix) || message.author.bot) return;

    const args = message.content.startsWith(prefix) ?
        message.content.slice(prefix.length).trim().split(/ +/) :
        message.content.slice(altprefix.length).trim().split(/ +/);

    const command = args.shift().toLowerCase();

    switch (command) {
        case 'play':
        case ...config.aliases.music.play:
            execute(message, args);
            break;
        case 'skip':
        case ...config.aliases.music.skip:
            skip(message);
            break;
        case 'stop':
        case ...config.aliases.dj.stop:
            stop(message);
            break;
        case 'help':
            sendHelpMessage(message);
            break;
        case 'queue':
        case ...config.aliases.music.queue:
            showQueue(message);
            break;
        case 'lyrics':
        case ...config.aliases.music.lyrics:
            fetchLyrics(message, args);
            break;
        case 'nowplaying':
        case ...config.aliases.music.nowplaying:
            nowPlaying(message);
            break;
        case 'remove':
        case ...config.aliases.music.remove:
            remove(message, args);
            break;
        case 'shuffle':
        case ...config.aliases.music.shuffle:
            shuffleQueue(message);
            break;
        case 'prefix':
        case ...config.aliases.admin.prefix:
            setPrefix(message, args);
            break;
        case 'volume':
        case ...config.aliases.dj.volume:
            setVolume(message, args);
            break;
        case 'pause':
            pause(message);
            break;
        case 'playnext':
            playNext(message, args);
            break;
        case 'repeat':
            repeat(message, args);
            break;
        // Add more commands and their aliases here as per config.json
        default:
            message.channel.send(`${config.emojis.error} Unknown command! Use \`${prefix}help\` for a list of commands.`);
    }
});

async function execute(message, args) {
    const voiceChannel = message.member.voice.channel;
    if (!voiceChannel) return message.channel.send(`${config.emojis.error} You need to be in a voice channel to play music!`);

    const permissions = voiceChannel.permissionsFor(message.client.user);
    if (!permissions.has('CONNECT') || !permissions.has('SPEAK')) {
        return message.channel.send(`${config.emojis.error} I need the permissions to join and speak in your voice channel!`);
    }

    const songInfo = await getSongInfo(args.join(' '));
    const song = {
        title: songInfo.title,
        url: songInfo.url,
    };

    if (!queue.length) {
        queue.push(song);
        play(message, voiceChannel);
    } else {
        queue.push(song);
        message.channel.send(`${config.emojis.success} **${song.title}** has been added to the queue!`);
    }
}

async function getSongInfo(query) {
    if (ytdl.validateURL(query)) {
        const songInfo = await ytdl.getInfo(query);
        return { title: songInfo.videoDetails.title, url: songInfo.videoDetails.video_url };
    } else {
        const spotifyData = await spotifyApi.searchTracks(query);
        if (spotifyData.body.tracks.items.length) {
            const track = spotifyData.body.tracks.items[0];
            return { title: track.name, url: track.external_urls.spotify };
        } else {
            // Implement YouTube search if Spotify search fails
            // For simplicity, returning a dummy response here
            return { title: "Unknown Song", url: "https://youtube.com" };
        }
    }
}

function play(message, voiceChannel) {
    const song = queue[0];

    voiceChannel.join().then(connection => {
        currentTrack = connection.play(ytdl(song.url, { filter: 'audioonly' }));

        currentTrack.on('finish', () => {
            queue.shift();
            if (queue.length) {
                play(message, voiceChannel);
            } else {
                voiceChannel.leave();
            }
        });

        message.channel.send(`${config.emojis.success} Now playing: **${song.title}**`);
    }).catch(err => {
        console.error(err);
        queue = [];
        message.channel.send(`${config.emojis.error} There was an error playing the track.`);
        voiceChannel.leave();
    });
}

function skip(message) {
    if (!message.member.voice.channel) return message.channel.send(`${config.emojis.error} You have to be in a voice channel to stop the music!`);
    if (!currentTrack) return message.channel.send(`${config.emojis.error} There is no song that I could skip!`);

    currentTrack.end();
    message.channel.send(`${config.emojis.success} Skipped the current track.`);
}

function stop(message) {
    if (!message.member.voice.channel) return message.channel.send(`${config.emojis.error} You have to be in a voice channel to stop the music!`);
    queue = [];
    if (currentTrack) currentTrack.end();
    message.member.voice.channel.leave();
    message.channel.send(`${config.emojis.success} Stopped the music.`);
}

function sendHelpMessage(message) {
    const helpMessage = `
        ${config.emojis.success} **Music Bot Commands:**
        \`${prefix}play <song name or URL>\` - Play a song from YouTube or Spotify.
        \`${prefix}skip\` - Skip the current song.
        \`${prefix}stop\` - Stop the music and clear the queue.
        \`${prefix}queue\` - Show the current queue.
        \`${prefix}lyrics <song name>\` - Fetch the lyrics of the song.
        \`${prefix}nowplaying\` - Show the currently playing song.
        \`${prefix}remove <queue number>\` - Remove a song from the queue.
        \`${prefix}shuffle\` - Shuffle the queue.
        \`${prefix}volume <value>\` - Set the volume of the music.
    `;

    message.author.send(helpMessage).then(() => {
        message.channel.send(`${config.emojis.success} Help has been sent to your DM!`);
    }).catch(err => {
        message.channel.send(`${config.emojis.error} I can't send you the help message via DM.`);
    });
}

function showQueue(message) {
    if (!queue.length) return message.channel.send(`${config.emojis.warning} The queue is empty.`);
    const queueMessage = queue.map((song, index) => `${index + 1}. **${song.title}**`).join('\n');
    message.channel.send(`${config.emojis.success} **Queue:**\n${queueMessage}`);
}

function fetchLyrics(message, args) {
    const songName = args.join(' ');
    // Dummy response for lyrics fetching
    message.channel.send(`${config.emojis.success} **Lyrics for ${songName}**: [Link to lyrics](https://www.azlyrics.com)`);
}

function nowPlaying(message) {
    if (!currentTrack) return message.channel.send(`${config.emojis.warning} No song is currently playing.`);
    message.channel.send(`${config.emojis.success} Now playing: **${queue[0].title}**`);
}

function remove(message, args) {
    const index = parseInt(args[0]);
    if (isNaN(index) || index < 1 || index > queue.length) {
        return message.channel.send(`${config.emojis.error} Invalid queue number.`);
    }
    const removed = queue.splice(index - 1, 1);
    message.channel.send(`${config.emojis.success} Removed **${removed[0].title}** from the queue.`);
}

function shuffleQueue(message) {
    for (let i = queue.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [queue[i], queue[j]] = [queue[j], queue[i]];
    }
    message.channel.send(`${config.emojis.success} The queue has been shuffled.`);
}

function setPrefix(message, args) {
    if (message.author.id !== config.owner_id) return message.channel.send(`${config.emojis.error} You do not have permission to change the prefix.`);
    const newPrefix = args[0];
    if (!newPrefix) return message.channel.send(`${config.emojis.warning} Please provide a new prefix.`);
    config.prefix = newPrefix;
    fs.writeFileSync('config.json', JSON.stringify(config, null, 2));
    message.channel.send(`${config.emojis.success} Prefix has been changed to ${newPrefix}`);
}

function setVolume(message, args) {
    const volume = parseInt(args[0]);
    if (isNaN(volume) || volume < 0 || volume > 100) {
        return message.channel.send(`${config.emojis.error} Please provide a valid volume between 0 and 100.`);
    }
    if (currentTrack) currentTrack.setVolumeLogarithmic(volume / 100);
    message.channel.send(`${config.emojis.success} Volume set to ${volume}`);
}

function pause(message) {
    if (currentTrack) currentTrack.pause();
    message.channel.send(`${config.emojis.success} Paused the current track.`);
}

function playNext(message, args) {
    const songInfo = getSongInfo(args.join(' '));
    const song = {
        title: songInfo.title,
        url: songInfo.url,
    };
    queue.unshift(song);
    message.channel.send(`${config.emojis.success} **${song.title}** will be played next.`);
}

function repeat(message, args) {
    const option = args[0];
    if (!['off', 'one', 'all'].includes(option)) {
        return message.channel.send(`${config.emojis.error} Invalid repeat option. Use \`off\`, \`one\`, or \`all\`.`);
    }
    // Implement repeat functionality based on option
    message.channel.send(`${config.emojis.success} Repeat mode set to ${option}.`);
}

client.login(config.token);

