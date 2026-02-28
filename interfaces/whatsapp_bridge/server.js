const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion,
    makeCacheableSignalKeyStore,
    isJidGroup,
    downloadContentFromMessage
} = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const pino = require('pino');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const PYTHON_BACKEND_PORT = 5678;
const logger = pino({ level: 'info' });

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    const { version, isLatest } = await fetchLatestBaileysVersion();
    console.log(`using WA v${version.join('.')}, isLatest: ${isLatest}`);

    const sock = makeWASocket({
        version,
        logger,
        printQRInTerminal: true,
        auth: state,
        getMessage: async (key) => {
            return {
                conversation: 'hello'
            };
        }
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log('\n📱 Scan QR Code ini dengan WhatsApp Anda (Baileys):');
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect.error instanceof Boom) ?
                lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut : true;
            console.log('connection closed due to ', lastDisconnect.error, ', reconnecting ', shouldReconnect);
            if (shouldReconnect) {
                connectToWhatsApp();
            }
        } else if (connection === 'open') {
            console.log('✅ WhatsApp (Baileys) connected and ready!');
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        if (m.type === 'notify') {
            for (const msg of m.messages) {
                if (!msg.key.fromMe && !isJidGroup(msg.key.remoteJid)) {
                    const sender = msg.key.remoteJid;
                    const messageContent = msg.message?.conversation ||
                        msg.message?.extendedTextMessage?.text ||
                        msg.message?.imageMessage?.caption ||
                        "";

                    console.log(`📩 Message from ${sender}: ${messageContent.substring(0, 50)}...`);

                    try {
                        // Handle Voice Messages
                        if (msg.message?.audioMessage) {
                            console.log(`🎤 Voice message received from ${sender}`);
                            const stream = await downloadContentFromMessage(msg.message.audioMessage, 'audio');
                            let buffer = Buffer.from([]);
                            for await (const chunk of stream) {
                                buffer = Buffer.concat([buffer, chunk]);
                            }

                            const audioDir = path.join(__dirname, '..', '..', 'downloads');
                            if (!fs.existsSync(audioDir)) fs.mkdirSync(audioDir, { recursive: true });

                            const audioPath = path.join(audioDir, `wa_incoming_${Date.now()}.ogg`);
                            fs.writeFileSync(audioPath, buffer);

                            const response = await forwardVoiceToPython(sender, audioPath);

                            if (response.text_response) {
                                await sock.sendMessage(sender, { text: response.text_response }, { quoted: msg });
                            }

                            if (response.audio_path && fs.existsSync(response.audio_path)) {
                                const audioBuffer = fs.readFileSync(response.audio_path);
                                await sock.sendMessage(sender, {
                                    audio: audioBuffer,
                                    mimetype: 'audio/mp4',
                                    ptt: true
                                }, { quoted: msg });
                                console.log(`📤 Voice reply sent to ${sender}`);
                            }
                        } else if (messageContent) {
                            // Handle Text Messages
                            const pythonResponse = await forwardToPython(sender, messageContent);
                            if (pythonResponse) {
                                await sock.sendMessage(sender, { text: pythonResponse }, { quoted: msg });
                                console.log(`📤 Replied to ${sender}`);
                            }
                        }
                    } catch (err) {
                        console.error('Error processing message:', err);
                    }
                }
            }
        }
    });
}

async function forwardToPython(sender, message) {
    try {
        const response = await axios.post(`http://localhost:${PYTHON_BACKEND_PORT}/whatsapp/incoming`, {
            sender,
            message
        }, { timeout: 60000 });
        return response.data.response || 'Task selesai.';
    } catch (error) {
        console.error('Failed to reach Python backend:', error.message);
        return null;
    }
}

async function forwardVoiceToPython(sender, audioPath) {
    try {
        const response = await axios.post(`http://localhost:${PYTHON_BACKEND_PORT}/whatsapp/voice-incoming`, {
            sender,
            audio_path: audioPath
        }, { timeout: 90000 });
        return response.data;
    } catch (error) {
        console.error('Voice forward failed:', error.message);
        return { text_response: '⚠️ Maaf, terjadi error saat memproses pesan suara Anda.' };
    }
}

console.log('🚀 Starting WhatsApp Bridge with Baileys for openApex...');
connectToWhatsApp().catch(err => console.error('Unexpected error:', err));
