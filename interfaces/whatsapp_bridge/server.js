const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const http = require('http');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');

const PYTHON_BACKEND_PORT = 5678;

// Initialize WhatsApp Web client with persistent auth
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './wa_session' }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// ===== WhatsApp Events =====

client.on('qr', (qr) => {
    console.log('\n📱 Scan QR Code ini dengan WhatsApp Anda:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp Web connected and ready!');
});

client.on('message', async (msg) => {
    // Skip group messages and status updates
    if (msg.from.includes('@g.us') || msg.from === 'status@broadcast') return;

    console.log(`📩 Message from ${msg.from}: ${msg.type}`);

    try {
        if (msg.hasMedia && (msg.type === 'ptt' || msg.type === 'audio')) {
            // Voice message handling
            console.log(`🎤 Voice message from ${msg.from}`);
            const media = await msg.downloadMedia();

            if (media) {
                // Save audio to temp file
                const audioDir = path.join(__dirname, '..', '..', 'downloads');
                if (!fs.existsSync(audioDir)) fs.mkdirSync(audioDir, { recursive: true });

                const audioPath = path.join(audioDir, `wa_incoming_${Date.now()}.ogg`);
                fs.writeFileSync(audioPath, Buffer.from(media.data, 'base64'));

                // Forward to Python backend for voice processing
                const response = await forwardVoiceToPython(msg.from, audioPath);

                // Send text reply
                if (response.text_response) {
                    await msg.reply(response.text_response);
                }

                // Send voice reply if audio was generated
                if (response.audio_path && fs.existsSync(response.audio_path)) {
                    const voiceMedia = MessageMedia.fromFilePath(response.audio_path);
                    await msg.reply(voiceMedia, undefined, { sendAudioAsVoice: true });
                    console.log(`📤 Voice reply sent to ${msg.from}`);
                }
            }
        } else if (msg.body) {
            // Text message handling
            const response = await forwardToPython(msg.from, msg.body);

            if (response) {
                await msg.reply(response);
                console.log(`📤 Replied to ${msg.from}`);
            }
        }
    } catch (error) {
        console.error('Error processing message:', error);
        await msg.reply('⚠️ Maaf, terjadi error saat memproses pesan Anda.');
    }
});

client.on('disconnected', (reason) => {
    console.log('❌ WhatsApp disconnected:', reason);
});

// ===== HTTP Communication with Python =====

function forwardToPython(sender, message) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ sender, message });

        const options = {
            hostname: 'localhost',
            port: PYTHON_BACKEND_PORT,
            path: '/whatsapp/incoming',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            },
            timeout: 60000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    resolve(parsed.response || 'Task selesai.');
                } catch {
                    resolve(body || 'Task selesai.');
                }
            });
        });

        req.on('error', (err) => {
            console.error('Failed to reach Python backend:', err.message);
            reject(err);
        });

        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
        req.write(data);
        req.end();
    });
}

function forwardVoiceToPython(sender, audioPath) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ sender, audio_path: audioPath });

        const options = {
            hostname: 'localhost',
            port: PYTHON_BACKEND_PORT,
            path: '/whatsapp/voice-incoming',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            },
            timeout: 90000
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch {
                    resolve({ text_response: body || 'Task selesai.' });
                }
            });
        });

        req.on('error', (err) => {
            console.error('Voice forward failed:', err.message);
            reject(err);
        });

        req.on('timeout', () => { req.destroy(); reject(new Error('Voice processing timeout')); });
        req.write(data);
        req.end();
    });
}

// ===== Start =====
console.log('🚀 Starting WhatsApp Bridge for openApex (with voice support)...');
client.initialize();
