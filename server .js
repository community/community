const express = require('express');
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const QRCode = require('qrcode');
const basicAuth = require('express-basic-auth');
const pino = require('pino');

const app = express();
const PORT = process.env.PORT || 10000;

// ============ এখানে তোমার নাম ============
const SITE_NAME = "WhatsApp QR - FATEMA AKTER";
const SITE_LOGO = "FATEMA"; // QR এর উপরে বড় অক্ষরে দেখাবে

// লগইন সিকিউরিটি - ইচ্ছা করলে পরিবর্তন করতে পারো
const AUTH_USER = process.env.AUTH_USER || "fatema";
const AUTH_PASS = process.env.AUTH_PASS || "fatema123";

let qrString = null;
let isConnected = false;

app.use(basicAuth({
  users: { [AUTH_USER]: AUTH_PASS },
  challenge: true,
  unauthorizedResponse: 'Unauthorized - Login Required'
}));

async function startSock() {
  const { state, saveCreds } = await useMultiFileAuthState('auth_info');
  const sock = makeWASocket({
    auth: state,
    logger: pino({ level: 'silent' }),
    printQRInTerminal: false,
    browser: [SITE_NAME, 'Chrome', '1.0.0']
  });

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;
    
    if(qr) {
      qrString = await QRCode.toDataURL(qr);
      console.log("New QR Generated");
    }
    
    if(connection === 'open') {
      isConnected = true;
      qrString = null;
      console.log("FATEMA AKTER Bot Connected!");
    }
    
    if(connection === 'close') {
      const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      isConnected = false;
      if(shouldReconnect) {
        startSock();
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);
}

// Main Page
app.get('/', async (req, res) => {
  if(isConnected) {
    return res.send(`
      <html>
      <head><title>${SITE_NAME} - Connected</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body{font-family:sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; height:100vh; margin:0}
        .card{background:#fff; padding:40px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1); text-align:center}
        h1{color:#25D366}
      </style>
      </head>
      <body>
        <div class="card">
          <h1>✅ System Operational</h1>
          <h2>${SITE_NAME}</h2>
          <p>WhatsApp Connected Successfully!</p>
          <p style="color:gray; font-size:12px">Powered by FATEMA AKTER</p>
        </div>
      </body>
      </html>
    `);
  }

  if(qrString) {
    res.send(`
      <html>
      <head><title>${SITE_NAME}</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body{font-family:sans-serif; background:#f0f2f5; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0}
        .card{background:#fff; padding:30px; border-radius:20px; box-shadow:0 10px 30px rgba(0,0,0,0.1); text-align:center; max-width:400px}
        img{width:300px; border-radius:15px}
        .logo{width:80px; height:80px; background:#25D366; color:#fff; border-radius:50%; display:flex; justify-content:center; align-items:center; font-size:30px; font-weight:bold; margin:0 auto 15px}
      </style>
      </head>
      <body>
        <div class="card">
          <div class="logo">${SITE_LOGO}</div>
          <h2>${SITE_NAME}</h2>
          <img src="${qrString}" />
          <p><b>WhatsApp > Linked Devices > Link a Device</b> দিয়ে স্ক্যান করুন</p>
          <p style="color:gray; font-size:12px">QR 20 সেকেন্ড পর পর অটো পরিবর্তন হবে</p>
        </div>
        <script>setTimeout(()=>location.reload(), 20000)</script>
      </body>
      </html>
    `);
  } else {
    res.send(`<h2 style="text-align:center; margin-top:100px; font-family:sans-serif">QR Generating... Please reload after 10 seconds<br><br>${SITE_NAME}</h2><script>setTimeout(()=>location.reload(), 5000)</script>`);
  }
});

startSock();
app.listen(PORT, () => console.log(SITE_NAME + " Running on " + PORT));
