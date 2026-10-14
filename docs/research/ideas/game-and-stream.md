# Game coach / commentator and stream chat read-aloud — research

Date: 2026-10-15. For the Bulbul Build Challenge (deadline 2026-10-15 20:00 IST).
Background already covered (not redone here): `docs/research/tts-only/*.md`,
especially AI cricket commentary (AIKash, Star Sports) in `viral-tts-cases.md` §1.28.

Status: complete (2026-10-15).

## Part A — In-game AI coach / commentator

### 1. Prior art

| Product / demo | What it does | Status and reception | Lesson for us |
|---|---|---|---|
| **Fortnite AI Darth Vader** (Epic + Disney, 16 May 2025) | NPC you talk to; Gemini 2.0 Flash writes replies, **ElevenLabs Flash v2.5** speaks them | Went viral the same day because streamers (e.g. Loserfruit) got it to swear; Epic hotfixed ([Fox News](https://www.foxnews.com/tech/epic-games-debuts-voice-interactive-darth-vader-fortnite-its-already-being-tricked-swearing), [PinkNews](https://www.thepinknews.com/2025/05/21/fortnite-darth-vader-ai-slurs/)) | The biggest "AI voice in a game" moment used a *Flash* TTS tier, i.e. latency was the buying criterion. Virality came from the voice reacting to *the player*, live |
| **Chess.com Play Coach** (ElevenLabs) | Spoken move feedback in the voices of Hikaru, Levy Rozman, Magnus | Shipped; a dialogue tree, one-way instruction ([ElevenLabs](https://elevenlabs.io/blog/chess-dot-com-iconic-voices), [GamesBeat](https://gamesbeat.com/chess-com-will-let-you-choose-your-ai-coach-based-on-celebrity-voices/)) | A coach does not need an LLM per line: a tree of pre-written lines plus a famous-sounding persona works |
| **Microsoft Gaming Copilot** (Game Bar, from 18 Sep 2025) | Voice-mode assistant reads screenshots, gives tips and lore | Rolled out to PC 18+ users; reviewers questioned accuracy and performance cost ([Outlook Respawn](https://respawn.outlookindia.com/gaming/gaming-news/microsoft-xbox-brings-ai-powered-gaming-copilot-to-pc-and-mobile), [TMCnet](https://blog.tmcnet.com/blog/rich-tehrani/ai/microsofts-gaming-copilot-ai-launches-in-windows-game-bar-beta.html)) | Pull-based (you ask). Not real-time commentary. Screenshot vision is slow; reading game state directly is faster |
| **Razer AI Game Copilot** (ex-Project Ava, CES 2025) | Esports coach; demo voice tells you which attack to dodge, what to do at boss <20% HP | Concept/beta; no firm release ([Razer](https://razer.com/mena-en/software/razer-ai-gamer-copilot), [Laptop Mag](https://laptopmag.com/laptops/gaming-laptops-pcs/razer-ai-gaming-coach-copilot-microsoft-nvidia), [Digital Trends](https://digitaltrends.com/?p=3821828)) | The demo pattern judges know: tip spoken *during* the fight. A robotic voice was the noted weak point |
| **Nvidia ACE / PUBG Ally** | AI squadmate that talks, loots, fights; small LMs | Testing from early 2026 in PUBG Arcade, EN/KO/ZH; an Nvidia demo was noted as edited ([Windows Central](https://windowscentral.com/hardware/nvidia/pubg-adds-ai-squadmates-that-listen-loot-and-fight-like-real-players-powered-by-nvidias-ace-tech), [PCWorld](https://www.pcworld.com/article/3168209/nvidias-ai-squadmate-is-finally-dropping-into-pubg.html)) | No Indian languages. A Hindi/Hinglish teammate voice is an open gap |
| **AITuberKit game commentary** (open source) | Screenshots every N s → multimodal LLM → spoken commentary with emotion ([docs](https://docs.aituberkit.com/en/guide/game-commentary-settings)) | Hobbyist VTuber tool | Periodic screenshot loop = seconds of lag. Event-driven is the better design |
| **Research: fighting-game commentator** | Raised TTS pitch/loudness with highlight intensity | Viewers rated it more entertaining ([arXiv 2108.08112](https://ar5iv.arxiv.org/html/2108.08112)); field surveyed at IJCAI 2026 ([IJCAI](https://www.ijcai.org/proceedings/2026/901)) | Excitement must scale with the event: a big moment needs a louder, faster line |
| **FanCode + Camb.AI** (Dream Sports) | AI Hindi live cricket commentary, CPL 2025 pilot | FanCode streams ~20,000 live matches/yr; human multi-language commentary called "costly and a logistical nightmare" ([Dream Sports](https://dreamsports.group/newsroom/fancode-partners-with-camb-ai-to-deliver-live-multilingual-commentary-using-ai-across-indian-sports), [exchange4media](https://www.exchange4media.com/industry-briefing-news/fancode-partners-with-cambai-to-offer-multilingual-commentary-using-ai-147552.html)) | Live Hindi AI cricket commentary is a real Indian business need. Sarvam-native version is a strong judge story |
| **AIKash, Star Sports IPL 2024** | Hinglish AI cricket commentator; overseas commentators "speaking Hindi" | Covered in `tts-only/viral-tts-cases.md` §1.28 | Cricket commentary register is instantly recognised |
| **Fliki / Noiz "gameplay commentary" tools** | Upload a clip, get AI play-by-play voiceover for Shorts ([Fliki](https://fliki.ai/features/gameplay-video-generator), [Noiz](https://noiz.ai/use-cases/en/funny-gaming-voiceover)) | Vendor testimonials of viral clips (anecdotal) | Post-hoc, not live. The shareable output is a vertical clip with commentary |

**What went viral and why:** the Vader case spread because the voice reacted live to what players did and said, and could be pushed into funny territory. Coaches (Chess.com, Razer) get attention from *a known persona* giving *specific* advice. Nobody has shipped a real-time Hindi/Hinglish game commentator; FanCode's is for broadcast cricket, not for the player.

### 2. Which game to build in 6–8 h

Reference points: the Chrome dino runner had 270 M plays a month in 2018, most from places with poor data such as India ([MCV/Develop](https://www.mcvuk.com/what-game-is-four-years-old-has-270m-monthly-players-and-yet-makes-no-money-whatsoever), [OfficeChai](https://officechai.com/stories/chrome-dinosaur-game/)). Google's 2017 Champions Trophy cricket Doodle was a one-click timing game (crickets bat against snails) that people "couldn't stop playing"; Google called it its smallest interactive Doodle ([VOA](https://learningenglish.voanews.com/a/cricket-doodle-google-/3899068.html), [Shropshire Star](https://shropshirestar.com/news/science-and-technology/2017/06/01/google-creates-awesome-cricket-game-doodle-to-mark-start-of-the-champions-trophy)). In India's Apr 2024–Mar 2025 downloads, *Cricket League*, Ludo King and Carrom Pool sit near the top ([GameDev Reports](https://gamedevreports.substack.com/p/weekly-gaming-reports-recap-june-de7)); India supplied >15% of Subway Surfers' decade downloads ([PocketGamer.biz](https://www.pocketgamer.biz/subway-surfers-most-downloaded-mobile-game-of-the-decade)).

| Game | Events to comment on | Speech fits play? | Indian flavour | Art | Build h | Verdict |
|---|---|---|---|---|---|---|
| **Gully cricket batting** (one-tap timing, Doodle-style) | Every ball: dot, 1, 2, 4, 6, edge, bowled, caught; streaks; target chase | **Yes.** Natural 2–3 s gap between balls; ball flight (~0.8 s) hides TTS latency | Strongest: cricket commentary is India's most-heard sports register | Side view, flat shapes: batter, stumps, ball, a wall as boundary | 5–7 | **Pick this** |
| Auto-rickshaw runner (Mumbai traffic, dino-style) | Near miss, crash, coin, speed-up, lane habit | Hard. Events every ~0.5 s; lines overlap or go stale | Good (potholes, cows, "bhaiya side do") | 3 lanes, sprites | 6–8 | Second. Good coach-tip demo ("tu hamesha late jump karta hai") but speech must be sparse |
| Flappy | Pass pipe, die | Few interesting events; death every 10 s | Weak | Trivial | 3–4 | Too thin |
| Snake | Eat, grow, die | Slow, few events | Weak | Trivial | 3 | Too thin |
| Typing race (Hinglish words) | Each word, WPM, mistakes | Yes, but voice competes with reading | Medium | Text only | 4 | Fine as a coach, dull video |
| Carrom / ludo | Strike outcome, cut, capture | Yes (turn-based) | Strong | Physics (carrom) or board logic (ludo) is slow to build | 8–12 | Too long for today |

**Recommendation: gully cricket, one-tap batting, chase a target in 2 overs.**
- Every ball yields a clear event with a number attached (runs, balls left, required rate), which shows Bulbul's number reading: "12 gend, 25 run chahiye".
- Turn-based rhythm means a line never has to be dropped, and the gap after contact is exactly where ~300 ms first audio (plus ~200 ms LLM) is felt: the comment lands while the ball is still in the air. A slow TTS would speak over the next ball.
- Personalisation is trivial to measure: tap timing error per ball (early/late in ms), which side the shots go.
- Art is cheap and "gully" excuses rough art: brick wall, plastic chair as stumps, "one tip one hand" rules as jokes.

### 3. Design: commentator "Gully Bhaiya" for the cricket game

#### 3.1 Events and what they say

| Event (game state) | Priority | Line source | Example (Devanagari for Hindi, Latin for English) |
|---|---|---|---|
| Six | 1 | LLM, personalised, with fallback | "और ये गया सीधा छत पर! Ball ढूँढो भाई, 6 run!" |
| Out (bowled / caught) | 1 | LLM, mentions the habit that caused it | "फिर से late! तीसरी बार stumps उड़े।" |
| Four | 2 | Cached pool, 8 variants | "चौका! दीवार से टकराई!" |
| Dot ball, streak ≥ 3 | 2 | Cached + number | "तीन dot balls, pressure बन रहा है।" |
| 1 or 2 runs | 3 | Cached short | "एक run, चलो strike घुमाओ।" |
| Chase update (balls left, required) | 2 | Template, numbers filled live | "12 गेंद, 25 run चाहिए।" |
| End of over | 1 | LLM coach tip from stats | "बेटा, तू हर बार 80 ms जल्दी swing कर रहा है, थोड़ा रुक के मार।" |
| Win / loss | 1 | LLM summary, used in the share clip | "18 गेंद में 30 run, गली का Dhoni!" |

#### 3.2 Keeping speech in sync with play

- **Start work at bat contact, not at the result screen.** Outcome is known at the tap (timing error → shot). Fire LLM + TTS immediately; the ~0.8 s ball-flight animation covers ~200 ms LLM + ~300 ms first audio (the brief's measured numbers). This is the visible speed demo.
- **One audio channel, a priority queue, a time-to-live.** Each item: `{text, priority, created_at, ttl_ms}`. Drop on dequeue if `now - created_at > ttl` (e.g. 1500 ms for run lines, 4000 ms for over summaries). A priority-1 line interrupts a playing priority-3 line; never the reverse.
- **Pace the game to the voice, a little.** Next delivery waits until the current line ends, capped (max 2.5 s). In cricket this looks natural (bowler walking back).
- **Short lines.** 4–10 words for ball lines (~1–2 s of audio). Only over-end tips run to ~2 sentences.
- **Cache + live mix.** Pre-synthesise ~40 common lines on page load (4 s, dots, singles, "chase" templates split so numbers are synthesised live) into the server's disk cache, so repeated plays cost nothing. LLM-personalised lines are for sixes, wickets, over-ends and the finale. If the live line is not ready by the time the ball lands + 300 ms, play the cached variant and discard the late one.
- **Streaming option.** Sarvam has a TTS WebSocket (`wss://api.sarvam.ai/text-to-speech/ws`) that returns audio chunks as text is processed ([Sarvam docs](https://docs.sarvam.ai/api-reference-docs/text-to-speech/stream), [WebSocket guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/streaming-api/web-socket.md)). Whether it accepts `bulbul:v4-flash` was not verified; the REST call already gives ~300 ms, which is enough for 1–2 s lines.
- **Excitement scales with the moment.** Research found louder/higher-pitched commentary on highlights was rated more entertaining ([arXiv 2108.08112](https://ar5iv.arxiv.org/html/2108.08112)). Use a faster `pace` and exclamation-heavy text for 6s and wickets; calm pace for dots. (Which prosody controls v4-flash exposes is unverified; the docs list pitch/loudness for v2 and not for v3.)

#### 3.3 Persona

"Gully Bhaiya": the neighbourhood elder brother who commentates every street match, Hinglish, teasing, warm. Rules in the system prompt: max 12 words per ball line; Hindi in Devanagari, English words in Latin; always use the live numbers given; one gully reference per over (chhat pe ball, "one tip one hand", "jo maarega wohi laayega"). Avoid naming real commentators or players' voices. Optional second voice ("Aunty from the balcony") for wickets only, which makes the clip funnier and shows two Bulbul voices.

#### 3.4 Personalisation

Track per game (all client-side, no login):
- timing error per ball in ms (mean and spread) → "early" / "late" / "consistent";
- shot direction (off/leg) and loft rate → "always goes leg side";
- dot-ball streaks and the over in which wickets fall → "panics in the last over".
At each over-end the client sends a compact JSON of these stats to `sarvam-105b` via `chat_json` with a `Tip` schema (`tip_hi: str ≤ 20 words`, `tone: tease|praise`). This is one call per over, so it never blocks a ball. Stats also feed the six/wicket lines ("finally! on time for once").

#### 3.5 Shareable output

- **Highlight clip, 15–20 s, 9:16**: record the canvas with `canvas.captureStream()` and the commentary audio through `AudioContext.createMediaStreamDestination()`, mixed into one `MediaRecorder` ([MDN captureStream](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream), [MDN createMediaStreamDestination](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/createMediaStreamDestination)). Keep a rolling buffer of the last N balls; at game end export the best ball (six or the winning shot) plus the finale line. Chrome's MP4 output lacks duration metadata, so transcode server-side if needed (see `tts-only/no-stt-formats.md`).
- **Text scoreline** for WhatsApp, Wordle-style: "Gully Bhaiya 🏏 31/2 (12) ✅ 6️⃣4️⃣•1️⃣W6️⃣ … + link".
- **Challenge link** with the target pre-set ("Beat my 31 in 2 overs").

#### 3.6 Cost of one game (list price)

TTS list price in this repo's ledger: Rs 2 per 1,000 characters (`src/bulbul_build/budget.py`). A 2-over game ≈ 12 ball lines + 2 tips + 1 finale ≈ 900 characters live ≈ **Rs 1.8**, less with cached common lines; LLM cost not estimated here.

## Part B — Live-stream chat read aloud for chosen people

### 4. Indian streaming and TTS-donation culture

**Audience size**
- India had ~511 M game players in 2025, projected >550 M in 2026 (Niko Partners via [gamedev.net](https://gamedev.net/news/5102-niko-partners-india-games-market-exceeds-1bn-forecast-to-reach-12bn-by-end-of/)); ~520 M of ~700 M smartphone owners play at least one game (BITKRAFT/Redseer via [GameDev Reports](https://gamedevreports.substack.com/p/bitkraft-ventures-and-redseer-indias)). These count players, not stream viewers; no sourced 2025 India game-*stream* viewer figure was found.
- **Rooter** (Indian game-streaming app): FY25 revenue Rs 82 crore, "over 85 million gamers" on the platform ([Business Today](https://www.businesstoday.in/amp/latest/corporate/story/rooters-gaming-push-pays-off-fy25-revenue-hits-rs-82-crore-user-spends-average-rs-24k-a-month-478152-2025-05-28)); MAU quoted as 16–18 M by profile sites (undated, unverified: [Crunchbase](https://crunchbase.com/organization/rooter), [Dealroom](https://app.dealroom.co/companies/rooter_1_1)). **Loco** (Krafton/Lumikai-backed) has no recent public user figure found ([Entrackr](https://entrackr.com/?p=119194), [afaqs, 2020](https://www.afaqs.com/companies/pocket-aces-loco-sees-over-6x-rise-in-daily-active-users)).
- Most big Indian game streamers are on **YouTube Live**, and **Super Chat** is a main income: e.g. Snax (2 M+ subs) gets Rs 100 to Rs 1,000+ per Super Chat; one executive estimates Rs 2–3 lakh per session for a loyal audience (estimate, unverified) ([exchange4media](https://www.exchange4media.com/influence-zone-news/game-stream-earn-how-much-do-top-gamers-make-144867.html)).

**TTS donation alerts**
- On Twitch the robotic donation voice is a ritual: communities make running jokes of its mispronunciations ([Voxbooster](https://voxbooster.com/blog/robot-voice-tts), [Donoclip](https://blog.donoclip.com/?p=18)).
- Streamlabs and StreamElements read donations aloud with min-amount, volume and spam filters ([Streamscheme](https://www.streamscheme.com/how-to-set-up-twitch-text-to-speech/), [Tutkit](https://www.tutkit.com/en/text-tutorials/7246-text-to-speech-function-in-streamlabs-for-donations-and-subscriptions)); third-party voice packs plug in (TTS.Monster, [callin.io](https://callin.io/ai-tools/tts-monster)). **Whether they offer a natural Hindi voice was not confirmed** in this search; no page about Hindi donation TTS on either was found.
- These tools are built around Streamlabs/PayPal-style tips. A UPI donation + Hindi TTS product for streamers was **not found**; the nearest Hindi "payment read aloud" products are shop soundbox apps (AutoAlert, Khatabook AlertPay) ([apkcombo](https://apkcombo.com/alertpay-upi-mobile-soundbox/com.khatabook.alertpay/), [Androxus](https://androxus.com/blogs/upi-sound-alerts-in-your-language)).
- Specific complaints about robotic Hindi in Indian donation alerts: **none sourced**; the claim is plausible but unverified. Names and typical voices of Indian streamers' TTS setups: not found in this pass.

**Takeaway:** the habit (paid message → read aloud on stream) is established; the Hindi/Hinglish voice and UPI rails are the gap. Bulbul reading "Rahul ne 500 rupaye bheje" with correct numbers and Hinglish is exactly the PhonePe-soundbox register Indians already know (see `tts-only/viral-tts-cases.md`).

### 5. Design: "Shoutout" — only chosen fans are spoken

**Who gets voiced:** Super Chat senders (amount ≥ streamer's minimum), channel members, mods, or a named list the streamer sets ("my top 10 fans"). Everyone else stays text.

**Pipeline**
1. Source: YouTube `liveChatMessages.list` (or simulated feed). Filter by `snippet.type` (Super Chat vs text) and author flags.
2. LLM rewrite with `sarvam-105b` `chat_json` → `{speak: bool, line_hi: str ≤ 20 words, reason}`: shorten, drop spam/abuse (`speak=false`), turn romanised Hindi into Devanagari (Bulbul reads it better, per repo notes), and frame it as a shoutout: "Rahul bhai ne ₹500 bheje, bolte hain: aaj chicken dinner pakka!" Amount read with the right number words.
3. Bulbul V4 Flash speaks it in the streamer's chosen voice; queue one at a time; paid messages outrank member messages; non-paid lines expire after ~20 s; cap queue at ~5.
4. OBS browser-source overlay shows the card while it speaks.

**Speed shown:** message appears → voiced in ~0.5 s (LLM ~200 ms + first audio ~300 ms). A side-by-side "Streamlabs-style robot vs Bulbul" clip makes the quality point.

**Demo without a real stream**
- **Simulated chat overlay** (recommended for the judged video): a fake YouTube-style chat scrolling scripted messages, with a "Send Super Chat ₹100/₹500" button the viewer can press. Fully controlled, works offline from the API.
- **Real public live chat**: `videos.list` → `liveStreamingDetails.activeLiveChatId`, then poll `liveChatMessages.list`. It costs **5 quota units per call**; respect `pollingIntervalMillis` or get `rateLimitExceeded`; Google recommends `liveChatMessages.streamList`, which pushes messages ([liveChatMessages.list](https://developers.google.com/youtube/v3/live/docs/liveChatMessages/list)). Default quota is 10,000 units/day ([API overview](https://developers.google.com/youtube/v3/getting-started)) → ~2,000 polls ≈ 2.8 h at one poll per 5 s. Whether an API key alone (no OAuth) can read a public stream's chat was not verified here; plan for OAuth if it fails. Use it as a 20-s "it works on a real stream" moment in the video, pointed at any big Indian live stream.

## 6. Ranked demo ideas

Build hours assume one person + Claude Code, reusing this repo's server, `sarvam.py` client, ledger and disk cache.

| # | Idea | User | Input | Output | Why viral / why judges like it | Bulbul feature shown | Build h | Risk |
|---|---|---|---|---|---|---|---|---|
| 1 | **Gully Cricket with Gully Bhaiya** — one-tap batting chase, live Hinglish commentary + over-end coaching tip | Anyone with a phone; cricket fans | Taps | Live commentary; 15-s 9:16 highlight clip; Wordle-style score line; challenge link | Cricket commentary is India's most-heard register; teasing personal tips ("tu har baar late hai") are funny and shareable; judges see real-time voice that a slow TTS could not do | ~300 ms first audio inside ball flight; numbers ("12 गेंद, 25 run"); Hinglish; excitement via pace | 6–8 | Game feel takes tuning; MediaRecorder MP4 quirks; LLM line may miss the window (fallback to cache) |
| 2 | **Shoutout** — only Super Chat / chosen fans' messages voiced in natural Hindi, LLM-shortened, OBS overlay | Indian YouTube game streamers | Live chat (simulated or real) | Spoken shoutouts + overlay card | Super Chat is real streamer income; "robot voice vs Bulbul" comparison is instantly clear; a B2B use judges can picture | Speed per message; ₹ amounts and names read right; Hinglish; 11 languages for regional streamers | 4–6 | Demo needs a convincing fake stream; YouTube API quota/auth; less viral for non-streamers |
| 3 | **Auto-rickshaw runner with a coach** — Mumbai traffic endless runner; voice tips on habits ("hamesha left jaata hai") | Casual players | Swipes | Live tips; death recap line; clip | Indian visuals (potholes, cows); coaching is the Razer/Copilot pattern done in Hindi | Speed under dense events; short lines; priority/drop queue | 7–9 | Speech overlaps fast play; more art; harder to make good in a day |
| 4 | **Commentary for any browser game you play** — tiny JS hook (or keyboard/score watcher) sends events, Bulbul commentates | Devs, streamers | Game events via a script tag | Live commentary layer | "Add a Hindi commentator to your game in one line" is a strong platform pitch | Same as #1, generic | 3 on top of #1 | Only a pitch unless #1 exists; generic events give bland lines |
| 5 | **Fantasy-cricket / match ticker read-aloud** — ball-by-ball text feed → spoken Hinglish updates for your team | Fantasy players | Pasted or simulated ball-by-ball feed | Live spoken updates | Real need (FanCode's AI Hindi commentary shows it); IPL is not on now, so timing is weak | Numbers, names, speed | 4–5 | No live match today; real feeds are paid/scraped; looks like FanCode/Camb.AI already did it |
| 6 | **Typing race with a Hinglish coach** — type Hinglish phrases; voice cheers WPM and mistakes | Students | Keyboard | Live tips; WPM card | Speaks on every word: speed is obvious | Per-word speed; numbers | 4–5 | Voice competes with reading; dull video |

## 7. Recommendation

- **Best game: Gully Cricket (#1).** Turn-based rhythm fits speech; each ball is an event with numbers; the ball-flight window is where ~300 ms TTS + ~200 ms LLM is visibly felt; cheapest art; the strongest Indian hook.
- **Best stream idea: Shoutout (#2)**, demoed with a simulated YouTube chat and a 20-s real-chat proof.
- **Enter #1.** It is a product anyone can play from the link, it produces its own share clip, and it shows Flash's speed in a way a stream overlay cannot match in a 60-s video. If time is left, add #2 as a second mode, reusing the same queue/priority code.
