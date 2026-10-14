# No-STT formats: zero-friction TTS and LLM+TTS products that get shared

Research date: 2026-10-15. Question: which product formats let people use TTS (or LLM + TTS) with no speech input, feel instant, get shared, and can show off Bulbul V4 Flash's ~300 ms first audio?

Status: complete. Sections 1b and the Top 8 were written last; section numbers follow the brief.

## 1. Zero- and one-input entry points

### Share-to-app (Android share target, PWA)

- A web app can appear in Android's share sheet by adding a `share_target` entry to its manifest. Text, titles and links use a plain GET to the `action` URL, so the page just reads query params on load. Files need POST with `multipart/form-data`, handled by a service worker. Only one `share_target` per manifest ([Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target)).
- **Catch 1: the PWA must be installed** (added to home screen) before it shows in the share sheet ([Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target); [Microsoft Edge docs](https://learn.microsoft.com/en-us/microsoft-edge/progressive-web-apps/how-to/share)). That is one extra step a first-time user will not take, so share-to-speak only helps repeat users.
- **Catch 2:** on Android, shared links arrive in `text`, not `url`, because Android's share system has no URL field ([Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target)).
- Supported from Chrome 76 on Android, Chrome 89 on desktop ([Chrome for Developers](https://developer.chrome.com/docs/capabilities/web-apis/web-share-target)). A service worker can handle the share with no backend ([web.dev Workbox](https://web.dev/workbox-share-targets/)).

### Sharing the output out (Web Share API with files)

- `navigator.canShare({files})` then `navigator.share({files, text})` hands a file to the OS share sheet; audio, image, video and PDF types are on Chromium's allowed list ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share), [web.dev](https://web.dev/articles/web-share)). This is how a page puts an MP4 or audio file straight into WhatsApp on a phone. No source confirmed WhatsApp's handling of MP4 via this path; test on a real device.

### Personalised links and QR

- Cadbury "Shah Rukh Khan-My-Ad": AI recreated SRK's face and voice and let local shop owners create and share their own ad naming their store ([D&AD](https://www.dandad.org/work/d-ad-awards-archive/shah-rukh-khan-my-ad)). The output was a personalised video that the shop owner forwarded. The exact QR/link mechanics were not found in public sources.

## 3. Bots and channels without STT (part 1: WhatsApp)

- **Policy facts.** From 15 Jan 2026, Meta's WhatsApp Business Solution terms bar general-purpose AI chatbots where the AI is the core product; ChatGPT, Perplexity and Luzia left WhatsApp. AI as part of a business service (support, bookings, order tracking, FAQs) stays allowed ([respond.io](https://respond.io/blog/whatsapp-general-purpose-chatbots-ban), [Business Standard](https://www.business-standard.com/technology/tech-news/meta-bans-ai-chatbots-from-whatsapp-business-api-chatgpt-to-shut-down-jan-2026-125102200335_1.html), [Gulf News](https://gulfnews.com/technology/no-more-chatgpt-and-perplexity-on-whatsapp-meta-bans-major-ai-chatbots-from-2026-1.500316016)). A bot that does one fixed job (text in, a specific voice note out) is on the task-specific side of that line as the sources describe it.
- **Voice notes via Cloud API.** Send an `audio` message with an `.ogg` OPUS file and the `voice: true` flag; it then shows as a voice note (mic icon, play inline). Any other audio type is sent as a plain audio file ([Meta docs](https://developers.facebook.com/documentation/business-messaging/whatsapp/messages/audio-messages), [360dialog](https://docs.360dialog.com/docs/messaging/media/voice-message-beta-program), [Gupshup](https://partner-docs.gupshup.io/reference/voice-notes-message)). One mirror says the inline play icon appears only for files up to 512 KB ([ChatArchitect](https://support.chatarchitect.com/books/meta-whatsapp/page/audio-messages-developer-documentation)); unverified against Meta's page.
- **Build cost for a 16 h solo build:** a WhatsApp Business number needs Meta business setup and verification, which is not in a builder's control in one day. A Telegram bot or a `wa.me` deep link from a web page avoids it (see below).

## 2. Making speed visible: "speaks as you type" and speed demos

What the public speed demos had in common:

| Demo | What people saw | What spread | Source |
|---|---|---|---|
| Groq (Feb 2024) | Text appearing at hundreds of tokens/s in a public chat page; Matt Shumer's answer engine writing cited answers "in less than a second" | Public benchmark numbers and a third-party demo on X; "overnight sensation". Artificial Analysis measured 241 tok/s, more than 2x other hosts | [Cointelegraph via TradingView](https://vn.tradingview.com/news/cointelegraph:b5cde52dc094b:0-groq-ai-model-goes-viral-and-rivals-chatgpt-challenges-elon-musk-s-grok), [VentureBeat](https://venturebeat.com/ai/groq-releases-blazing-fast-llm-engine-passes-270000-user-mark) |
| Kokoro TTS in the browser (Xenova, 2025) | "10 seconds of speech in ~1 second", runs locally with WebGPU, no server, $0 | A single claim with a number, plus a link anyone could open and try | [Aliyun repost of Xenova's post](https://startup.aliyun.com/info/1092141.html), [HN thread](https://hn.svelte.dev/item/42973769), [kokoro-js](https://www.npmjs.com/package/kokoro-js) |
| OpenAI.fm (Mar 2025) | Free, no sign-up playground: pick a voice, type a "vibe" in plain words, play; download or share the clip; a toggle shows the code | Zero sign-up and a one-line style prompt; output can be downloaded and shared | [Analytics Vidhya](https://www.analyticsvidhya.com/blog/2025/03/openai-audio-models/), [Habr](https://habr.com/ru/post/893044) |
| ElevenLabs Flash (Dec 2024) | Claimed 75 ms model latency | Mostly a number in a launch post; a competitor measured 255 ms median TTFB including network | [The Decoder](https://the-decoder.com/elevenlabs-launches-flash-its-fastest-text-to-speech-ai-yet/), [Deepgram](https://deepgram.com/learn/is-elevenlabs-real-time-what-developers-need-to-know) |
| Cartesia Sonic | Claims sub-90 ms; third parties measure ~166–190 ms end to end; public playground | Numbers in comparisons, not a consumer moment | [invideo](https://invideo.io/blog/cartesia-sonic-ai-voice/), [Cartesia vs ElevenLabs](https://cartesia.ai/vs/cartesia-vs-elevenlabs) |
| Deepgram Aura-2 | Claims sub-200 ms TTFB; playground | No consumer moment found | [Deepgram changelog](https://developers.deepgram.com/changelog/2025/5/14) |
| Hume Octave 2 | Claims under 200 ms | Launch clips; no viral latency video found | [Hume blog](https://hume.ai/blog/octave-2-launch) |

**Findings.**

- No viral *TTS* speed demo was found in any source. TTS vendors compete on latency numbers in blog posts; none turned speed into a consumer moment. Groq is the nearest case, and it was text you could watch arriving fast, with a public number to quote. This is an opening, not proof of demand.
- The demos that spread let anyone try them at once with no sign-up (OpenAI.fm, Kokoro web) and came with one quotable number (Groq tok/s, Kokoro "10 s in 1 s").
- 300 ms is not perceptibly "instant" for one tap; it feels like a normal button. Speed only shows when **many short clips play back to back** (a rapid-fire game, a language carousel, a live reaction to each keystroke) or when there is **a visible timer** next to a slower baseline. That is an inference from the cases above, not a measured result.
- "Speaks as you type" was not found as a shipped product from any vendor; ElevenLabs documents WebSocket input streaming for text that arrives in pieces ([ElevenLabs docs](https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization)). Per-keystroke speech is noisy; speaking on each word or sentence boundary (space or full stop) is the workable version.

## 3. Bots and channels without STT (part 2)

- **Telegram:** `sendVoice` shows audio as a voice message; OGG/OPUS is the safe format (newer docs also list MP3/M4A), up to 50 MB; a bot is created in minutes via BotFather with no business verification ([aiogram docs](https://docs.aiogram.dev/en/latest/api/methods/send_voice.html)). Inference (no usage figure checked here): WhatsApp, not Telegram, is where the target user lives, so Telegram is a demo channel at best.
- **WhatsApp without the Business API:** a web page can make the file and hand it to WhatsApp through the Web Share API (section 1). This keeps WhatsApp as the place the output lands, without running a bot.
- **Android share-to-speak:** Android has built-in Select to Speak; third-party "Voice Reading" apps read any text shared to them ([Chicago Lighthouse](https://chicagolighthouse.org/wp-content/uploads/2024/11/Android-Select-to-Speak.pdf), [MixRank listing](https://mixrank.com/playstore/apps/com.lproduct.textaloudreader)). Read-aloud is a crowded utility, not a shareable moment.
- **Chrome read-aloud extensions:** "Read Aloud" (open source) reads the current article with one click and lets users pick cloud voices ([GitHub](https://github.com/Jordanlw/read-aloud)). Reliable user counts were not found. A desktop extension does not reach the WhatsApp-Status user.

## 4. Games and toys with tap input and TTS output

| Example | Mechanic | Evidence | Fit for Flash |
|---|---|---|---|
| The Great Language Game (2013) | Hear a short clip, tap which language it is; three mistakes and you are out | 15 million guesses on 400 clips of 78 languages, analysed in a 2017 paper; players confuse geographically close languages ([All Things Linguistic](https://allthingslinguistic.com/post/160278817135), [ANU repository](https://openresearch-repository.anu.edu.au/items/1f5c4ebc-d580-4a2d-931d-ddd3f83b901e), [Laughing Squid](https://laughingsquid.com/the-great-language-game-challenges-players-to-identify-languages-by-listening-to-language-being-spoken/)) | Strong. 11 Indian languages make a native version ("Kaunsi bhasha?"). Rapid rounds make 300 ms visible: the next clip plays the instant you tap. The paper says close languages are the hard ones, so Kannada/Telugu or Bengali/Odia are the fun rounds |
| Wordle (2021–22) | One puzzle a day, spoiler-free emoji grid to share | Share button added Dec 2021 after players made grids by hand; 90 players in Nov 2021 to 300,000+ in two months (NYT via Know Your Meme); people shared grids in WhatsApp chats ([Know Your Meme](https://knowyourmeme.com/memes/subcultures/wordle), [CUNY Pressbooks](https://pressbooks.cuny.edu/inspire/part/the-wordle-effect-how-five-letters-changed-the-internet/)) | The share pattern to copy: a text result (score + emoji + link) that pastes into WhatsApp and needs no file |
| Antakshari | Turn-based song chain on the last letter | A living format: Amazon Music India ran an antakshari ad in Aug 2026; Big FM made a radio version ([Manifest](https://manifest-media.in/video/campaigns/060826/amazon-music-cues-sonu-nigam-and-usha-uthup-for-a-nostalgic-game-of-an.html), [ThePrint](https://theprint.in/feature/vigyapanti/amazon-music-india-antakshari-streaming-era/3009040/), [radioinfo](https://radioinfo.asia/news/big-fm-launches-musical-game-show/)) | Weak. V4 Flash cannot sing, and the game needs voice input. A spoken word-chain loses the music |
| AI prank call apps (PrankGPT, Prankify) | Pick a persona, the AI calls a number | Mostly US traffic; India about 3% for PrankGPT per one listing ([creati.ai PrankGPT](https://creati.ai/ai-tools/prankgpt/), [creati.ai Prankify](https://creati.ai/ai-tools/prankify-ai/)) | A real call needs telephony and STT. The no-STT version is a prank *voice note* (fake announcement or "official call" about a friend), which the repo's railway and udhaar modes already do |
| Choose-your-path story | Tap one of 2–3 choices, hear the next scene | No sourced viral TTS example found | Each tap is a new short clip, so speed shows. Risk: LLM latency (seconds) hides TTS speed unless scenes are pre-generated or the LLM streams into TTS |

**Notes.**

- Tap games are the cleanest way to make 300 ms felt: tap, the next voice plays at once, many times a minute. A slow TTS would visibly stall the game.
- The share artefact for a game should be text (score line + link), Wordle-style. It pastes into WhatsApp with no file handling. A short "my score" video is a bonus.

## 5. TTS + images to 9:16 video in the browser

### What creators use today

- Indian creator guides name InVideo AI (Hindi templates), CapCut (auto-captions in ~10 languages), Revid.ai (Hindi story videos with AI voiceover), Canva Magic Studio, Runway and Pika ([Storyboard18](https://www.storyboard18.com/how-it-works/how-to-create-viral-reels-and-posts-with-ai-tools-a-step-by-step-guide-for-indian-creators-83757.htm), [animateai roundup](https://animateai.pro/blog/top-10-best-ai-powered-video-editing-tools-2026-india-creators/), [Revid Hindi story](https://www.revid.ai/category/hindi-story)). The common pipeline is "type a topic or script, pick a voiceover, export a vertical video", no face on camera ([FluxNote](https://fluxnote.io/guides/ai-reel-maker-india)). These are multi-step editors. None found is a one-tap "make my shop's status video" for a non-creator.

### What makes a 9:16 clip look good

- **Captions burned in.** Muted viewing is common (vendor estimates 70–85%; directional only) ([kompozy](https://kompozy.io/how-to/video-captions-for-retention)). Word-by-word highlighted captions are claimed to beat static ones on retention, but only vendor numbers exist; one review calls it "probably true" with murky evidence ([blitzcut](https://blitzcutai.com/blog/animated-captions-vs-static-captions), [clipspeed](https://clipspeed.ai/blog/ai-captions-increase-views.html)). Style advice: 2–5 words per screen, bold sans-serif, high contrast, highlight by colour shift ([openclip](https://openclip.app/guides/caption-animation-guide.md), [opus.pro](https://www.opus.pro/blog/best-caption-presets-styles-boost-retention)).
- **Safe zones on 1080×1920:** keep key text out of roughly the top 270 px, bottom ~670 px and right ~230 px (Reels UI); the safe centre is about 950×980 px ([Hopper HQ](https://www.hopperhq.com/blog/instagram-reel-size/)). Other guides give smaller margins ([trymypost](https://www.trymypost.com/blog/instagram-reels-safe-zones-text-placement-2026)); plan for the larger.
- **WhatsApp Status length:** 30 s, then 60 s (2024 beta), and 90 s in beta in 2025 ([Green API](https://green-api.com/en/blog/2025/whatsapp-increases-status-length-to-90-seconds/), [Dynamite News](https://www.dynamitenews.com/technology/whatsapp-extends-video-status-limit-to-90-seconds)). Keep clips under 30 s to be safe on every phone.
- **Hook in 0–3 s, sound on purpose:** see the playbook's short-video section (`exp007` report).

### Building it

- **MediaRecorder** records a canvas + audio stream. Chrome 126 (June 2024) added MP4 output; Chrome writes fragmented MP4 without duration metadata, which some players mishandle ([addpipe](https://blog.addpipe.com/duration-in-mp4-files-produced-by-chrome-safari/), [MDN](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/mimeType), [blink-dev](https://groups.google.com/a/chromium.org/g/blink-dev/c/YJ1QijNiHeM/m/3EhMjMVwAgAJ)). Recording runs in real time and can drop frames on slow phones ([SitePoint](https://www.sitepoint.com/video-processing-in-browser-with-Web-Codecs/), [dev.to](https://dev.to/sabigara/how-to-capture-3d-animation-and-encode-it-into-video-by-webcodecs-3505)).
- **WebCodecs + mp4-muxer** encodes frame by frame, faster than real time, with audio passed as Float32 arrays ([mp4maker](https://github.com/tlecoz/Mp4Maker/blob/main/README.md)); WebAV and Diffusion Studio wrap this ([WebAV](https://docsearch.algolia.com/mcp/docs/repo/webav-tech/webav), [Diffusion Studio](https://docs.diffusion.studio/docs/rendering)).
- **Server ffmpeg** (H.264 + AAC, `+faststart`) is the safest bet for WhatsApp. Inference: for a 16 h build, render on the server and skip browser encoding.
- **Lip-flap avatar:** the PNGtuber method swaps mouth-open and mouth-closed images when audio volume crosses a threshold; a third "shout" image for loud parts is a common add-on ([AITuberKit docs](https://docs.aituberkit.com/en/guide/character/pngtuber), [OBS forum](https://obsproject.com/forum/threads/flood-tuber-native-pngtuber-plugin.193671/)). It needs only amplitude, so it works with Bulbul. The repo's Talking Bulbul art fits this.
- **Captions without timestamps:** Sarvam's TTS docs show no word timestamps ([Sarvam docs](https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/which-api-to-use); also `docs/research/talking-bulbul/animation.md`). Synthesise one line per caption and show it for that clip's duration; spread words across the clip by character count for a word-highlight effect. An approximation, fine for short lines.

## 1b. More entry-point facts (personalised links, WhatsApp hand-off, autoplay)

- **Personalised `?name=` greeting links** are a common Indian festive format, but no source documenting their spread was found. Personalised wish-card makers that share on WhatsApp do exist ([customwishcards tutorial](https://customwishcards.onrender.com/create-wish), [Morphic Diwali wishes generator](https://morphic.com/resources/tools/diwali-wishes-generator)).
- **`wa.me` links** open WhatsApp with pre-filled text: `wa.me/<number>?text=<urlencoded>`, or `wa.me/?text=...` with no number to open the contact picker. The user still taps send ([bird.com](https://bird.com/explained/whatsapp/what-is-a-whatsapp-click-to-chat-link), [Unipile](https://www.unipile.com/fr/?p=275019)). This works on desktop and phones without any WhatsApp API.
- **Link previews in WhatsApp:** the `og:image` must be small; help-centre and forum reports put the limit around 300 KB, above which no preview shows. 1200×630 JPG compressed under 300 KB is the safe choice ([QR Code Chimp help](https://help.qrcodechimp.com/article/234-when-some-digital-business-card-qr-code-links-are-shared-the-image-is-not-appearing-in-the-shared-link-on-whatsapp), [Branch](https://help.branch.io/faq/docs/why-are-some-quick-link-thumbnails-not-shown-in-whatsapp), [Flarum forum](https://discuss.flarum.org/d/39207-whatsapp-embed)). A per-name OG image ("Rahul, Sharma uncle has a message for you") makes the link itself the hook.
- **Autoplay:** Chrome blocks audible autoplay until the user has made a gesture on the page; muted autoplay is allowed ([Chrome blog](https://developer.chrome.com/blog/autoplay), [Chromium rationale](https://chromium.org/audio-video/autoplay/autoplay-policy-design-rationale)). So a link cannot "just speak" on open. The minimum is one big tap-to-play button. That single tap is where 300 ms shows: tap, voice starts at once.

## Top 8 formats

Ordered by fit with the bar (a shop owner who posts AI video to WhatsApp Status daily), with speed as the tie-breaker. Build sizes assume the existing repo (FastAPI, Sarvam client, ledger, mode pattern, 9:16 card drawing) and one person with Claude Code. "Exists" names a repo mode that already covers part of it.

| # | Format | First 10 seconds | Input | Output / share artefact | How speed is felt | Build (16 h budget) | Main risk |
|---|---|---|---|---|---|---|---|
| 1 | **Dukaan Status video** (one box: shop name + today's offer, festival preset) | Opens page, Diwali preset already picked, types "Gupta Sweets, kaju katli 20% off", taps; the voice says it back in under half a second while the 9:16 video renders | 1 text box + 1 tap (language chip optional) | 15–25 s 9:16 MP4 with burned captions, Ken Burns on a preset image, shop name card; Web Share to WhatsApp Status | Instant voice preview on tap; re-roll a line and hear it at once | ~8–10 h (exists in part: `shop_diwali_ad.py`; add server ffmpeg MP4 and share) | Video render takes seconds, so the speed story is the preview, not the file. MP4 must be H.264/AAC for WhatsApp |
| 2 | **Personalised voice link** (`site/?to=Rahul&from=Anmol&m=diwali`) | Receiver sees a WhatsApp preview card with their name, opens, taps one big button, hears "Rahul, Anmol ne aapke liye Diwali ka sandesh bheja hai…" in ~0.3 s; "Make one back" button | Sender: 2 names + preset. Receiver: zero input, one tap | The link (with per-name OG image) plus optional MP4/voice note | Receiver's single tap gives audio at once; making a reply is equally instant | ~5–7 h (OG image render, cache by text, wa.me hand-off) | Name links look like scam forwards; autoplay needs a tap; needs a live server through the share window |
| 3 | **Kaunsi Bhasha? tap game** (Great Language Game for 11 Indian languages) | Tap Start; a voice says a sentence in some Indian language; tap one of 4 chips; next clip plays the instant you tap; 10 rounds in about a minute | Taps only | Text score line, Wordle-style ("Kaunsi Bhasha 8/10 🟩🟩🟥…" + link), pastes into WhatsApp; optional result card | Many back-to-back clips with no wait; a slow TTS would visibly stall | ~6–8 h (sentence bank per language, live synth, score card) | Live synthesis per round costs per play; pre-caching saves money but hides the speed. Novelty may be one-off |
| 4 | **Bolta Card: type and hear, with a stopwatch** (speaks on each space or full stop; one tap repeats in all 11 languages back to back) | Types a name or a line; hears it as they finish each word; a counter shows "first audio 0.31 s"; taps "11 bhashayein" and hears it carouselled | 1 text box | Screen-record-ready page; "my name in 11 languages" card (exists: `say_my_name.py`) | Directly: the counter plus audio keeping up with typing | ~5–6 h on top of WebSocket client | It is a tech demo, not a reason to come back; translation calls add latency to the carousel |
| 5 | **Talking character clip** (Mitthu or Sharma uncle says your line, lip-flap) | Picks a character, picks a preset line or types one, taps; the character starts talking in ~0.3 s with mouth flapping on volume | 1 tap (preset) or 1 text box | 9:16 MP4 of the character speaking with captions | Character reacts as fast as a person would | ~6–8 h (art exists; PNGtuber flap on amplitude; reuse MP4 renderer from #1) | Two-frame lip-flap looks cheap next to AI video avatars creators already use |
| 6 | **Prank/announcement voice notes about a friend** (railway, udhaar desk, Ravan roast) | Types friend's name, picks a preset, taps; the station chime and announcement start at once | 1 name + 1 tap | Voice note (OGG/OPUS) or 9:16 MP4 with board graphic | Preview on tap; switch preset or language and it replays instantly | ~2–4 h to polish (exists: `railway_announcement.py`, `udhaar_wapas.py`, `dashanan_roast.py`) | One-time joke; low repeat use; it does not serve the shop-owner bar |
| 7 | **Share-to-Bulbul PWA** (share any forward or article from WhatsApp/Chrome; hear it in your language) | Long-press text, Share, Bulbul; the page opens and starts reading within 0.3 s of the tap | Zero typing (share sheet) | Audio playback; optional "send as voice note" | Text shared from another app is speaking almost before the page settles | ~4–6 h (manifest `share_target`, GET handler, translate + TTS) | Must be installed to the home screen first, which first-time users will not do; read-aloud is a crowded utility |
| 8 | **Telegram bot: text in, voice note out** (task-specific: e.g. "send a shop offer, get a voice ad") | Opens bot, sends one line, gets a voice note back in about a second | 1 message | Native voice note, forwardable | Reply lands like a human voice note, near instantly | ~3–4 h (BotFather, `sendVoice`, OGG/OPUS encode) | Wrong channel for the Indian target user; WhatsApp needs Business API setup not doable in a day |

### Single best bet

**#1 Dukaan Status video, with #2's personalised link as its share loop.** It matches the bar exactly (a shop owner's daily Status), needs one text box and one tap, the voice preview shows the ~300 ms speed on every tap and re-roll, and the MP4 is the artefact that gets posted. The repo already has `shop_diwali_ad.py` and the card renderer, so the new work is the server MP4 render and the Web Share hand-off. Add the tap game (#3) only if time is left: it is the clearest pure speed demo.

### Gaps

- No viral TTS speed demo was found at all; the "speed is felt in rapid back-to-back playback" point is an inference.
- WhatsApp's handling of an MP4 passed through the Web Share API was not confirmed by any source; test on a real Android phone.
- Whether the 90 s WhatsApp Status limit reached all users is unconfirmed; 30 s clips avoid the question.
- Sarvam returns no word timestamps per the docs found, so word-highlight captions are approximate.
