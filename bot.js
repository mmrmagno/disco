const { Client, Intents } = require('discord.js');
const { Manager } = require('erela.js');
const Spotify = require('erela.js-spotify');
const { getPreview } = require('spotify-url-info');
const config = require('./config.json');

const client = new Client({
    intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_VOICE_STATES, Intents.FLAGS.GUILD_MESSAGES, Intents.FLAGS.MESSAGE_CONTENT],
});

client.manager = new Manager({
    nodes: [{ host: 'localhost', port: 2333, password: 'youshallnotpass' }],
    plugins: [new Spotify({ clientID: config.spotify.client_id, clientSecret: config.spotify.client_secret })],
    send(id, payload) {
        const guild = client.guilds.cache.get(id);
        if (guild) guild.shard.send(payload);
    },
})
.on('nodeConnect', node => console.log(`Node ${node.options.identifier} connected`))
.on('nodeError', (node, error) => console.log(`Node ${node.options.identifier} had an error: ${error.message}`))
.on('trackStart', (player, track) => {
    const channel = client.channels.cache.get(player.textChannel);
    channel.send(`${config.emojis.success} Now playing: **${track.title}** by **${track.author}**`);
})
.on('queueEnd', player => {
    const channel = client.channels.cache.get(player.textChannel);
    channel.send(`${config.emojis.warning} Queue has ended.`);
    player.destroy();
});

client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
    client.manager.init(client.user.id);
    client.user.setActivity(config.game, { type: 'LISTENING' });
});

client.on('messageCreate', async (message) => {
    if (!message.guild || message.author.bot) return;

    const mentionPrefix = `<@!${client.user.id}>`;
    const prefixes = [config.prefix, config.altprefix, mentionPrefix];
    let prefix = false;

    for (const thisPrefix of prefixes) {
        if (message.content.startsWith(thisPrefix)) prefix = thisPrefix;
    }

    if (!prefix) return;

    const args = message.content.slice(prefix.length).trim().split(/ +/g);
    const cmd = args.shift().toLowerCase();

    switch (cmd) {
        case 'play':
            if (!args[0]) return message.reply(`${config.emojis.error} Please provide a song name or link.`);
            const { channel } = message.member.voice;
            if (!channel) return message.reply(`${config.emojis.error} You need to join a voice channel first.`);
            const player = client.manager.players.spawn({
                guild: message.guild,
                voiceChannel: channel.id,
                textChannel: message.channel.id,
            });
            let res;
            if (args[0].includes('spotify.com')) {
                const data = await getPreview(args[0]);
                res = await client.manager.search(`${data.title} ${data.artist}`, message.author);
            } else {
                res = await client.manager.search(args.join(' '), message.author);
            }
            if (res.loadType === 'LOAD_FAILED') return message.reply(`${config.emojis.error} Load failed.`);
            if (res.loadType === 'NO_MATCHES') return message.reply(`${config.emojis.error} No matches found.`);
            player.queue.add(res.tracks[0]);
            if (!player.playing && !player.paused && !player.queue.size) player.play();
            message.reply(`${config.emojis.success} Queued: **${res.tracks[0].title}**`);
            break;

        case 'skip':
            const playerSkip = client.manager.players.get(message.guild.id);
            if (!playerSkip) return message.reply(`${config.emojis.error} No song is currently playing.`);
            playerSkip.stop();
            message.reply(`${config.emojis.success} Skipped the current song.`);
            break;

        case 'stop':
            const playerStop = client.manager.players.get(message.guild.id);
            if (!playerStop) return message.reply(`${config.emojis.error} No song is currently playing.`);
            playerStop.destroy();
            message.reply(`${config.emojis.success} Stopped the music and left the voice channel.`);
            break;

        default:
            message.reply(`${config.emojis.warning} Unknown command.`);
    }
});

client.login(config.token);

