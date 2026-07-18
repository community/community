# CL40 World International B2C Discord Bot (Pro) 2 Artists "Chico Loco 40" & "LB0025"

Features:
- /drop → publish international release announcement
- /campaign start → create B2C campaign with tracked link
- /kpi → metrics snapshot (joins/clicks/ctr)
- /brief weekly → weekly performance summary
- Welcome + auto-role
- Anti-spam / anti-link-abuse baseline
- International wording (EN/FR/AR/IT/GR-ready)

Discord invite 2 Artists (official):
https://discord.gg/Vvgmt4PFk
https://discord.gg/4ucb2Yes

# CL40 World International B2C Discord Bot (Pro)  
## 2 Artists: "Chico Loco 40" & "LB0025"

Official Discord Invites:  
- https://discord.gg/Vvgmt4PFk  
- https://discord.gg/4ucb2Yes  

## ✅ Features
- `/drop` → Publish international release announcement
- `/campaign start` → Create B2C campaign with tracked links (UTM)
- `/kpi` → KPI snapshot (joins / clicks / CTR)
- `/brief weekly` → Weekly performance summary
- Welcome + auto-role
- Anti-spam / anti-link-abuse baseline
- International wording ready: **EN / FR / AR / IT / GR**

---

## 🌍 Recommended Branding
- **Bot Name:** `CL40xLB Global Bot`
- **Bot Username:** `cl40lb_bot` (or closest available)
- **Embed Footer:** `CL40 World × LB0025 • International`

---

## 🧱 Platform Publisher Setup (Where to publish)
Use the bot to publish drops in Discord, and distribute links to:

### Streaming
- YouTube / YouTube Music
- Spotify
- Apple Music
- Deezer
- Anghami
- Audiomack

### Social
- TikTok
- Instagram Reels
- Facebook
- X (Twitter)
- Threads

### Artist/Press
- Official Website
- Google Publisher Center (news/articles via RSS)
- Press page / EPK page

---

## 🗂 Suggested Discord Channel Structure
- `#welcome`
- `#verify`
- `#announcements`
- `#drops-cl40`
- `#drops-lb0025`
- `#campaigns`
- `#kpi-dashboard`
- `#media`
- `#community-chat`
- `#support`

---

## 🤖 Core Commands
- `/drop title:<text> url:<link> market:<US|FR|MA|IT|GR|GLOBAL> artist:<CL40|LB0025>`
- `/campaign start name:<text> url:<link> market:<...>`
- `/kpi range:<7d|30d>`
- `/brief weekly`

---

## 🔐 Safety & Trust
- No fake members
- No fake streams
- No spam raids
- Respect platform policies
- Human-first community growth

---

## ⚙️ Quick Start
```bash
npm install
cp .env.example .env
npm run dev
```

Set in `.env`:
- `BOT_TOKEN`
- `CLIENT_ID`
- `GUILD_ID`
- `AUTO_ROLE_ID`
- `WELCOME_CHANNEL_ID`

---

## 📣 Publishing Workflow (Recommended)
1. Prepare release links (YouTube/Spotify/Apple...)
2. Run `/drop` in `#announcements`
3. Pin announcement
4. Share same tracked link across socials
5. Check `/kpi` after 24h, 72h, 7d
6. Post `/brief weekly` for team decisions

---

## 🧠 International Copy Templates

### EN
**New Release Live 🚀**  
{artist} — **{title}** is out now.  
Listen here: {link}

### FR
**Nouvelle sortie en ligne 🚀**  
{artist} — **{title}** est disponible maintenant.  
Écoutez ici : {link}

### AR
**إصدار جديد الآن 🚀**  
{artist} — **{title}** متوفر الآن.  
استمع من هنا: {link}

### IT
**Nuova uscita online 🚀**  
{artist} — **{title}** è ora disponibile.  
Ascolta qui: {link}

### GR
**Νέα κυκλοφορία τώρα 🚀**  
{artist} — **{title}** είναι διαθέσιμο τώρα.  
Άκου εδώ: {link}

---
Built for: **CL40 World × LB0025**  
B2C International Growth System

import 'dotenv/config';
import { Client, GatewayIntentBits, Partials, Events } from 'discord.js';
import { registerCommands } from './registerCommands';
import { onInteraction } from './modules/interactions';
import { onMemberJoin } from './modules/memberJoin';
import { onMessage } from './modules/moderation';

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ],
  partials: [Partials.Channel]
});

client.once(Events.ClientReady, async (c) => {
  console.log(`✅ Logged in as ${c.user.tag}`);
  await registerCommands();
  console.log('✅ Commands ready');
});

client.on(Events.InteractionCreate, onInteraction);
client.on(Events.GuildMemberAdd, onMemberJoin);
client.on(Events.MessageCreate, onMessage);

client.login(process.env.BOT_TOKEN);
