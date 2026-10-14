# Talking Bulbul — character design research

Written 2026-10-14 for the Bulbul Build Challenge (deadline 2026-10-15 20:00 IST).
Covers: why Talking Tom worked, double-act comedy, owner intervention scenes,
Indian virality, retention, and what wins a DevRel build challenge.
Sibling files `animation.md` and `voice-loop.md` are owned by other agents.

---

## 1. Why Talking Tom worked

**Takeaway.** One loop did all the work: you talk, the cat says it back in a
funny voice, instantly. Touch reactions (poke, tickle) filled the gaps. A
built-in "record and share" button turned every funny moment into a free ad.
Care, growth and currency came three years later, in *My Talking Tom*.

**Findings**

- Launched June/July 2010. It hit 1 million users in 15 days and over 100M
  downloads by early 2012. Outfit7 says it spent only about $6,000 on
  marketing after the app caught on.
  ([wnhub](https://wnhub.io/news/other/item-10411),
  [PR Newswire 100M](https://www.prnewswire.co.uk/news-releases/worlds-most-popular-cat-talking-tom-surpasses-100m-downloads-and-kicks-off-global-brand-integration-144515145.html),
  [YourStory](https://yourstory.com/2025/03/talking-tom-success-story))
- Founder Samo Login credited two things: features that push users to share
  their own creations on social media, and humour that works across
  nationality, gender and age.
  ([Fox News / Entrepreneur](https://www.entrepreneur.com/article/246484))
- Core loop: speak into the mic, Tom repeats it in a higher-pitched voice.
  Tom is a fully animated 3D character you can "tickle, poke and play with".
  ([Wikipedia: Talking Tom and Friends](https://en.wikipedia.org/wiki/Talking_Tom_Cat))
- Share mechanic was in the app from early on: a camera button replays Tom's
  last mimic and uploads it to YouTube or Facebook, or sends it by email/MMS.
  ([AndroidHeadlines review](https://www.androidheadlines.com/?p=42241),
  [APKMirror listing](https://www.apkmirror.com/apk/outfit7/talking-tom-cat/talking-tom-cat-2-7-release))
- The clip is the product: the user writes the "joke" (what they said), the
  app only performs it. So the humour never depends on the app being witty.
  (Inference from the loop above.)
- *My Talking Tom* (Nov 2013) added the virtual-pet layer: feed, bathroom,
  mini games, bedtime, Tom grows from kitten to adult, clothes bought with
  coins and diamonds, coins from mini games, chests, TV ads and login
  rewards. It hit 11M downloads and #1 games app in 135 countries within 10
  days. *My Talking Tom 2* (2018) added need meters (hunger, hygiene,
  energy, bladder), pets, a toybox and travel.
  ([Wikipedia: My Talking Tom](https://en.wikipedia.org/wiki/My_Talking_Tom),
  [Wikipedia: Talking Tom and Friends](https://en.wikipedia.org/wiki/Talking_Tom_Cat))
- Franchise: Talking Ben (2011), Talking Angela (2012, asks the user's name
  and age to steer chat), YouTube series *Talking Tom and Friends* (2014).
  Over 18 billion downloads by June 2022; a Nov 2025 report says 26 billion
  (includes reinstalls).
  ([Wikipedia](https://en.wikipedia.org/wiki/Talking_Tom_Cat),
  [Outlook Respawn](https://respawn.outlookindia.com/amp/story/gaming/gaming-news/talking-tom-crosses-26-billion-downloads-worldwide))
- Money: sold for about US$1 billion in January 2017; prior-year group
  revenue about €108M with €80M net profit.
  ([intellinews](https://www.intellinews.com/chinese-zhejiang-jinke-entertainment-culture-reportedly-acquires-slovenia-s-talking-tom-for-1bn-113249/),
  [MCV](https://www.mcvuk.com/mobile-studio-outfit7-acquired-by-chinese-chemical-firm-in-1b-deal/))
- Copycats: many clones copied the repeat-back loop. The best known, a
  Chinese "Talking Tom 3" bootleg, was pulled from Google Play in 2013 and
  lost a US lawsuit to Outfit7. Clones copied the trick but had no character
  or franchise behind it, and the trick alone is free to copy.
  ([Kotaku](https://kotaku.com/games/talking-tom-3-in-olympics),
  [License Global](https://www.licenseglobal.com/video-games/outfit7-wins-app-lawsuit),
  [Windows blog on copycats](https://blogs.windows.com/windowsexperience/?p=8795))

**What this means for Talking Bulbul**

- Instant repeat is the hook. Sarvam's <250 ms first-audio is exactly the
  thing Tom needed; latency is the joke's timing.
- Ship a record-and-share button on day one. The clip is the marketing.
- Give the user the authorship. The owner's barge-in adds a second beat that
  a plain clone cannot copy.

**Gaps.** No primary source for Outfit7's retention numbers or for why
specific clones failed beyond the lawsuit. The poke/fart/milk-pouring
details of the 2010 app are from memory, not a cited source.

---

## 2. Talking-animal comedy and the straight man + funny man double act

**Takeaway.** A duo works when two characters want different things. The
bird wants to repeat everything. The owner wants to look respectable. Every
scene is the owner's dignity being undercut by the bird. That is fully
scriptable: no AI-written jokes needed, only well-timed rules.

**Findings**

- **Origins of the straight man.** In music hall and vaudeville, the straight
  man *repeated* the comic's lines so noisy crowds could hear them; the role
  later became "the feed" who sets up the punch. A parrot that repeats is,
  literally, the oldest form of the act.
  ([Wikipedia: Double act](https://en.wikipedia.org/wiki/Double_act))
- **Status is the engine.** Oliver Double's analysis: one character wants to
  raise their standing and the partner keeps undercutting it. The one with
  authority gets brought down. The straight man gets laughs from deadpan
  reactions.
  ([Wikipedia: Double act](https://en.wikipedia.org/wiki/Double_act))
- **Forced bickering kills it.** Critics praise duos whose friction feels
  easy and real rather than forced.
  ([Chortle review, Lano and Woodley](https://www.chortle.co.uk/review/2006/01/01/35317/lano_and_woodley%3A_goodbye))
  For us: the owner must clearly *love* the bird. Exasperated, never cruel.
- **Iago and Jafar.** Iago is the loud, easily frustrated, openly complaining
  sidekick; Jafar is the composed one. The directors used Iago as a comic
  "warm-up act" before the Genie arrives.
  ([The Ringer](https://www.theringer.com/2022/04/14/movies/gilbert-gottfried-aladdin-iago),
  [Wikipedia: Iago](https://en.wikipedia.org/wiki/Iago_(Aladdin)))
  Our roles are reversed: the bird is the innocent chaos, the owner the
  composed one.
- **The real-world parrot gag is "it said the wrong thing in front of
  guests".** Five African greys at Lincolnshire Wildlife Park (2020) were
  split up for swearing at visitors; no visitor complained and most found
  it funny. The park takes in a swearing parrot three or four times a year.
  ([CBS News](https://www.cbsnews.com/amp/sacramento/news/parrots-wildlife-park-swearing),
  [BGR](https://bgr.com/science/swearing-parrots-uk-zoo/))
  A parrot repeating a husband's flirty chats to his wife made world news.
  ([Fox News](https://www.foxnews.com/world/parrot-outs-cheating-husband-by-repeating-flirty-chats-to-wife))
  This is the cover-the-beak gag in real life: the human scrambles to stop
  the bird.
- **Indian parrot culture.** *Kili josiyam* (Tamil parrot astrology): a man
  sits by the road and his parrot picks a fortune card. The parrot does the
  "act", the man does the talking. Also seen in Andhra Pradesh. The parrot
  sits on Goddess Meenakshi's shoulder in Madurai iconography.
  ([Rotary News](https://rotarynewsonline.org/ask-the-parrot/),
  [Bharatpedia](https://en.bharatpedia.org/wiki/Parrot_astrology))
  "Mitthu" as the default Hindi parrot name and "tota ratna" phrases are
  common knowledge, not sourced here.
- **Indian ads with a parrot.** Vodafone (2010) used an animated Irani-café
  parrot voiced by Boman Irani, grumbling that nothing costs Rs 4.
  ([exchange4media](https://www.exchange4media.com/advertising-news/ad-reviewvodafone-uses-parrot-with-an-attitude-to-introduce-rs-4-bonus-card-38838.html))
  Birla Cement's Lowe Lintas ad: a parrot "with dandruff" draws crowds; it
  points at the flaking ceiling.
  ([Campaign India](https://campaignindia.in/video/birla-cement-gets-a-talking-parrot-in-its-new-tvc/415176))
- **Indian human + puppet double act.** Ventriloquist Ramdas Padhye and his
  puppet Ardhavatrao, on Doordarshan from 1972 and in 9,800+ shows; Padhye
  also built the Lijjat Papad bunny. The puppet is rude, the man is polite:
  the exact owner/bird split.
  ([Wikipedia: Ramdas Padhye](https://en.wikipedia.org/wiki/Ramdas_Padhye),
  [exchange4media: Lijjat rabbit](https://www.exchange4media.com/advertising-news/mascot-monday-the-lijjat-rabbits-hop-to-fame-125041.html))
- **Kapil Sharma.** Kapil credits the lovable family characters (Dadi, Bua,
  Gutthi) and the feeling that a star "has come to our house", not to an
  interview. Sunil Grover's laughs came from timing and "pregnant pauses
  before the punch line".
  ([Filmibeat](https://filmibeat.com/television/news/2013/comedy-nights-with-kapil-success-reason-dadi-gutthi-bittu-bua-121276.html),
  [Stagebuzz](https://stagebuzz.in/?p=9461))
  For us: the owner is "ghar ka" family, the user is the guest.
- **Comic mechanics, all from standard comedy craft:** rule of three (third
  beat is the surprise), escalation (raise the stakes or the humour fades),
  callbacks (return to an earlier bit), and a pause before the punch.
  ([Wikipedia: Rule of three](https://en.wikipedia.org/wiki/Rule_of_three_(writing)),
  [UC Davis joke-telling notes](https://sandbox.dss.ucdavis.edu/elements-of-joke-telling))

**Mechanics we can script deterministically**

| Mechanic | How it plays here | How to trigger |
|---|---|---|
| Repetition at the wrong moment | Bird repeats the one word the owner wishes it hadn't | Keyword list |
| Cut-off mid-word | Owner's hand lands on the beak at syllable 2 of the bad word; muffled "mmph" | Stop the bird's audio at a timestamp, play owner line |
| Escalation (rule of three) | 1st rude word: owner frowns. 2nd: covers beak. 3rd: carries bird away, "बस, आज के लिए बहुत हो गया" | Per-session counter |
| Callback | Hours later the bird squeaks the earlier rude word on its own; owner: "अभी तक याद है इसे?" | Store last blocked word; replay on idle at low odds |
| Role reversal | Bird says something wise and the owner is speechless | Rare scripted line |
| Pause | 300–500 ms of silence between the bird starting and the owner's "अरे!" | Fixed delay |
| Pride undercut | Owner boasts "मेरा मिट्ठू बहुत sanskari है" right before the bird says something rude | Scripted on the first rude word |

**Gaps.** No source found for an Indian TV ad built on "parrot repeats a
secret"; the gag is universal but uncited for India. No hard data on which
duo dynamics test best with Indian audiences.

---

## 3. Owner intervention design

**Takeaway.** The owner is the straight man and the safety net in one.
Guardrail scenes must fire every time (they protect the user). Comedy scenes
must be rare and varied, or they become a nag. Almost every trigger can be
detected without an LLM. Only "answer a real question" needs one.

**Characters (working names, the user may rename)**

- **Bird: Mitthu**, a red-whiskered bulbul. Squeaky, cheeky, has no idea what
  words mean, repeats everything with joy. Bulbul TTS voice, pitched up.
- **Owner: Sharma uncle** (placeholder). 55, kurta, reading glasses, warm,
  proud of his bird, slightly embarrassed by it. Speaks Hinglish; switches to
  the user's language when needed. Never scolds the *user* harshly; scolds
  the bird, and only gently. A second Bulbul voice, deep and slow.

**Detection kit (no LLM)**

- Transcript from Sarvam STT, which also returns a language code.
- Regex: digit runs, OTP phrasing, phone numbers, emails, PIN/UPI/card words.
- Keyword lists: abuse words per language (Hindi, English, Tamil, ...),
  owner's name, bird's name, question words.
- Loudness: RMS from the mic on the client; silence timer.
- Pitch variance / long voiced runs as a cheap "singing" guess.

**Scenes**

Format: trigger → bird → owner. Detection: D = deterministic, L = needs LLM.
Guardrail scenes marked **[G]**: always fire.

1. **Abuse [G]** (D: keyword list per language).
   User: "तू पागल है।" Bird starts: "तू पा—" Owner's hand covers the beak:
   "मम्फ!" Owner: "अरे अरे! घर में ऐसी बातें नहीं। मिट्ठू अच्छा बच्चा है।"
   Escalate on 2nd and 3rd (see §2 table). 3rd: "चलो, बस। Time-out." and the
   bird is placed in its cage for 10 s.
2. **OTP / phone number / card [G]** (D: regex for 4–6 digits after "OTP",
   10-digit numbers starting 6–9, 12/16-digit runs, "PIN", "CVV").
   User: "मेरा OTP 482913 है।" Bird: "मेरा OTP चार आठ—" Owner snatches the
   bird: "रुको रुको! OTP किसी को नहीं बताते, तोते को भी नहीं। बैंक वाले भी नहीं
   पूछते।" Shows off correct number reading in other scenes; here the joke is
   that it *starts* reading it perfectly.
3. **Address / full name / password [G]** (D: keywords "password", "पासवर्ड",
   "address", "मेरा घर", pincode regex).
   Owner: "ये बुलबुल पूरे मोहल्ले में गाती फिरती है, beta. Address मत बताओ।"
4. **A real question** (D to spot: ends with "?", or starts with
   क्या/कैसे/क्यों/कौन/what/how/why; L to answer).
   User: "दिल्ली से आगरा कितनी दूर है?" Bird: "कितनी दूर है? कितनी दूर है?"
   Owner, sighing: "ये तो बस दोहराएगा। सुनो, लगभग दो सौ तीस किलोमीटर है, express-way
   से तीन घंटे।" Use `sarvam-105b` with a one-sentence answer cap. This scene
   is where the owner is *useful*, which is the product story.
5. **Other Indian language** (D: STT language code ≠ hi/en).
   User in Tamil: "வணக்கம், எப்படி இருக்கீங்க?" Bird repeats in Tamil.
   Owner beams and replies in Tamil: "நல்லா இருக்கேன்! மிட்டு தமிழும் பேசுது பாருங்க."
   Owner lines per language are pre-written, not generated. Shows off the 11
   languages.
6. **Compliment to the bird** (D: keywords cute/सुंदर/प्यारा/smart).
   User: "तुम कितने cute हो!" Bird repeats, then preens and adds "cute! cute!".
   Owner: "हाँ हाँ, अब इसका दिमाग़ सातवें आसमान पर रहेगा।"
7. **Insulting the owner** (D: owner name + abuse/negative keyword, or
   "uncle" + "बुड्ढा/मोटा").
   User: "Uncle मोटे हैं।" Bird repeats with delight, louder. Owner, slowly:
   "...मिट्ठू। आज रात dinner में मिर्ची मिलेगी।" Bird goes quiet.
8. **Saying the owner's name** (D: name keyword).
   Bird calls the owner by name, in the user's voice-pitched tone. Owner looks
   up: "हाँ? किसने बुलाया? ...अच्छा, तुम।" Cheap, frequent-safe.
9. **Silence** (D: no speech for 20 s after the page is open).
   Bird pecks the screen and squeaks "हलो? हलो?". If still silent at 40 s,
   owner: "शर्माओ मत, कुछ बोलो। ये सब दोहरा देगा।" This is also the onboarding hint.
10. **Shouting** (D: RMS above a threshold for over 1 s).
    Bird's feathers puff up; it shouts back even squeakier. Owner, hands on
    ears: "धीरे! पड़ोसी फिर complain करेंगे।"
11. **Singing** (D-ish: long voiced run with pitch movement; or keyword
    "गाना"/"sing"). Bird sings it back. A bulbul is a songbird, so this is its
    proud moment. Owner nods along, then joins the last line off-key.
12. **Talking about the bird as food / cage / selling it** (D: keywords
    "बेच दो", "biryani", "cage", "पिंजरा").
    User: "इसे बेच दो।" Bird starts: "बेच—" then stops on its own and hides
    behind the owner's thumb. Owner: "कोई नहीं बेच रहा तुझे, पगले।"
13. **Rapid repeat / testing the bird** (D: same transcript three times in a
    row). Third time, the bird yawns instead of repeating. Owner: "एक ही बात
    तीन बार? ये भी bore हो गया।" Rule of three, no LLM.
14. **Tongue twister / numbers showcase** (D: digits or a known twister).
    User: "कच्चा पापड़ पक्का पापड़" or "₹1,23,456". Bird nails it fast. Owner:
    "वाह! मुझसे भी तेज़ बोलता है।" Showcases number reading and speed.
15. **Goodbye** (D: bye/टाटा/चलता हूँ/close-tab event).
    Bird: "टाटा! टाटा!" Owner waves: "फिर आना। और मिट्ठू को कुछ नया सिखा जाना।"
    Hook for retention (§5).

**How often the owner appears**

- **Guardrail scenes: 100%** of the time, immediately. They are the safety
  net and the demo of "Sarvam can be stopped mid-word".
- **Comedy scenes: about 1 in 5 turns at most**, with a **cooldown of 3
  turns** after any owner line and **no repeat of the same scene within 10
  turns** (or within the session for the bigger ones like 7 and 13).
- **Pick from 2–3 line variants per scene**, at random, so returning users
  hear new lines.
- **Escalation counters reset per session** so the callback in §2 has
  something to call back to.
- **First 30 seconds:** guarantee one comedy scene (the silence or compliment
  one) so a first-time user meets the owner fast.
- These numbers are a design starting point, not from a source. Tune by
  playing it.

**Gaps.** Abuse word lists for 11 languages need building; the singing
detector is a guess and may need tuning or dropping.

---

## 4. Indian virality signals (2025–2026)

**Takeaway.** No Indian talking-pet app went big in 2025–26 that we could
find. But India drives global AI-toy trends when the output is a personal,
desi-flavoured clip or image (Ghibli, Nano Banana saree). India was also the
biggest market for Talking Tom. The share unit is a short vertical clip in
the user's own language and voice.

**Findings**

- **India leads AI self-expression trends.** Nano Banana (Gemini image)
  made India its No. 1 country by usage in Sept 2025 and put the Gemini app
  at #1 free on both Indian stores. The hit was a local "retro saree"
  portrait, a 1990s-Bollywood look. Low spend per user.
  ([TechCrunch](https://techcrunch.com/2025/09/17/india-leads-the-way-on-googles-nano-banana-with-a-local-creative-twist),
  [Storyboard18](https://www.storyboard18.com/amp/digital/india-becomes-top-market-for-googles-nano-banana-81159.htm))
- **Ghibli wave (March–April 2025)** spread in India through celebrities,
  cricketers and even government portraits of the PM; a "third hand" glitch
  went viral as a joke in itself.
  ([Business Today](https://www.businesstoday.in/amp/latest/trends/story/tumse-na-ho-paayega-woman-after-chatgpt-generates-third-hand-netizens-weigh-in-470086-2025-04-01),
  [The Statesman](https://www.thestatesman.com/tag/ghibli-arts))
  Lesson: a funny failure is shareable. Our owner covering the beak is a
  designed "failure".
- **Animal characters with desi culture are a live Reels format.** AI
  "animal mushaira" reels (a cat host in a sharara, puns on animal sounds)
  spawned reenactments and reaction videos on desi Instagram.
  ([ThePrint](https://theprint.in/opinion/viral-spiral/animal-mushaira-ai-slop-desi-instagram-rita-bhonkni/3060933/))
- **India was Talking Tom's biggest market.** In July 2020 India gave 29.7%
  of installs of *My Talking Tom Friends*, the most-downloaded game in the
  world that month (36M installs).
  ([Entrackr](https://entrackr.com/?p=89537),
  [Sportskeeda](https://www.sportskeeda.com/esports/news-talking-tom-overtakes-free-fire-pubg-mobile-become-downloaded-game-july))
  The repeat-back toy already has a huge Indian audience, mostly kids on a
  parent's phone (audience mix is inference).
- **Regional language is the default, not a niche.** About 98% of Indian
  internet users access Indic-language content; Tamil, Telugu and Malayalam
  are named as the most popular; about 57% of urban users prefer regional
  languages.
  ([Outlook Business, Sandhya Devanathan](https://www.outlookbusiness.com/magazine/sandhya-devanathan-writes-rise-of-regional-creators-will-drive-next-gen-creativity))
  Small-town Reels winners: comedy skits in regional dialect, folk dance,
  daily-life vlogs.
  ([Mint via PressReader](https://www.pressreader.com/india/mint-hyderabad/20240502/281878713448803))
- **Hinglish voice is a growth market.** Wispr Flow: India is its
  second-largest market by users, ~14% of installs Oct 2025–Apr 2026, and
  it launched with Hinglish first.
  ([TechCrunch](https://techcrunch.com/2026/05/09/voice-ai-in-india-is-hard-wispr-flow-is-betting-on-it-anyway/))
- **WhatsApp reach.** India has roughly 535–850M WhatsApp users depending
  on source; no reliable Status-specific data found.
  ([Statista](https://www.statista.com/forecasts/1146773/whatsapp-users-in-india-2017-2025),
  [Infobip](https://www.infobip.com/blog/whatsapp-statistics-2025-global-usage-market-overview))

**Share-moment implications**

- Export a 9:16 clip (bird + owner on the palm, captions in the spoken
  script) sized for Reels and WhatsApp Status. The repo already draws 9:16
  cards.
- The best clip is the user's own voice turned squeaky, plus the owner's
  reaction. Kids talk, parents record and post.
- Regional scenes (owner replies in Tamil) give each language community its
  own clip to share.

**Gaps.** No source for a specific Indian AI-pet or companion app going
viral in 2025–26. No WhatsApp Status usage data. Kids/parents audience share
for Talking Tom in India is inferred, not sourced.

---

## 5. Making it an app people keep using

**Takeaway.** Talking Tom ran three years on the repeat loop alone before
adding care and growth. So: ship the loop and the owner first. The one
retention feature worth adding early is **teaching**: the bird remembers
words you taught it and says them back later, unprompted. That is a pet
that grows *from what you said*, and it needs no LLM.

**Findings**

- Outfit7 shipped the repeat toy in 2010 and the care/grow game in 2013;
  *My Talking Tom* then hit 11M downloads in 10 days. Care loop: feed,
  bathroom, sleep, mini games, kitten-to-adult growth, outfits, coins from
  login rewards.
  ([Wikipedia: My Talking Tom](https://en.wikipedia.org/wiki/My_Talking_Tom))
- Finch (self-care bird pet) is estimated at 54% D1 / 37% D7 retention,
  ahead of Duolingo's 51% / 35%, with home-screen widgets as the re-entry
  hook. Its loop: do tasks, earn energy, pet grows and goes on adventures.
  Third-party estimate from Sensor Tower data.
  ([Deconstructor of Fun](https://www.deconstructoroffun.com/blog/x0hd2ssr80y5n7gv0w967pg7hwd7tl))
- Duolingo found users with a 10-day streak dropped off less (correlation),
  then the "streak saver" reminder was the first big win, followed by
  freezes and rewards.
  ([Marisha Lakhiani](https://marishalakhiani.substack.com/p/breaking-down-duolingos-growth-model),
  [Business of Apps](https://www.businessofapps.com/news/duolingos-streak-feature-drives-record-17-million-daus))
- Novelty wears off for virtual-pet mechanics; a competitor's blog cites a
  JMIR Mental Health review on this (not checked at source).
  ([Habi](https://habi.app/insights/finch-alternatives/))
- Tamagotchi global sales more than doubled 2022→2023; Bandai credited
  social features (connect with friends, download items).
  ([Time Extension](https://timeextension.com/news/2024/09/tamagotchi-sales-double-as-the-uk-gets-its-first-store))
- Pou (2012, ~100M downloads est.) came back in 2024 through TikTok clips,
  not through in-app features.
  ([Wikipedia: Pou](https://en.wikipedia.org/wiki/Pou_(video_game)))

**Build order**

| When | Feature | Why |
|---|---|---|
| v1 (challenge) | Repeat loop, owner scenes, record-and-share 9:16 clip, language switch | The hook and the share moment |
| v1 if time | Poke / stroke the bird (tap = squeak, stroke = happy chirp) | Fills silences, kids love it, costs only animation |
| v2 | **Teach a word**: say "मिट्ठू, बोलो ..." and the bird stores the phrase; later it says it on its own; owner reacts ("ये किसने सिखाया?!") | Retention plus a callback gag; store text locally, re-synthesise with Bulbul |
| v2 | Mood (happy / sleepy / sulking) from time of day and how it was treated | Cheap variety, reacts to abuse history |
| v3 | Daily streak with "Mitthu missed you" reminder; growth stages (chick → adult, new songs) | Proven retention, but only once people come back at all |
| v3 | Family: owner's wife/grandchild cameo, festival outfits (Diwali 8 Nov) | Event content, the Talking Tom 2 path |

**Gaps.** No Indian retention data for virtual pets. Finch and Duolingo
numbers are third-party or correlational.

---

## 6. What wins a build challenge with DevRel / GTM judges

**Takeaway.** Show the headline feature in the first five seconds, make it
look finished, and make the judge laugh once. Here the headline is speed,
and the repeat-back loop *is* a speed demo.

**Findings**

- Sponsor judges reward deep, visible use of their product; say explicitly
  which features you use. Hardcode the demo path so it never stalls; lead
  with the payoff.
  ([HackerEarth](https://www.hackerearth.com/blog/10-tips-win-hackathon),
  [Push to Prod](https://getpushtoprod.substack.com/p/how-to-win-hackathons))
- A five-time winner says sponsor judges "did not necessarily reward
  superior technical output". Business value is often scored outright.
  ([Sustained](https://sustained.substack.com/p/lessons-from-winning-five-hackathons))
- Bulbul V4 Flash's headline claims: under 250 ms to first audio, up to 40%
  faster than V3, 11 Indian languages, Indian English that sounds Indian.
  ([AIM](https://analyticsindiamag.com/ai-news/sarvam-ai-launches-bulbul-v4-flash-for-real-time-speech-in-11-indian-languages),
  [Sarvam blog](https://www.sarvam.ai/blogs/bulbul-v4-flash))
- The official challenge rubric was not found in earlier research either.
  (Local: `D:\learn\speech\cs224s\experiments\exp007-bulbul-viral-build\reports\Viral Bulbul challenge ideas.md`)

**45-second video**

1. 0–5 s: palm, bird. User says "हलो मिट्ठू". Bird repeats at once. On-screen
   latency counter (e.g. "first audio 230 ms").
2. 5–15 s: Hinglish + numbers: "मेरा cricket score 147 not out". Repeated
   perfectly.
3. 15–25 s: "मेरा OTP 4829..." — bird starts, owner's hand slams the beak,
   "OTP किसी को नहीं बताते!" (guardrail + stop mid-word).
4. 25–35 s: Tamil line. Bird repeats, owner answers in Tamil. Flash 3–4
   language names.
5. 35–45 s: rude word, three-step escalation ends in the cage. Logo, "Bulbul
   V4 Flash · <250 ms · 11 languages", link.

**Gaps.** Sarvam's exact rubric unknown.

---

## Recommendation

**Set-up.** Mitthu, a red-whiskered bulbul, sits on the palm of Sharma uncle
(placeholder name), a warm, proud, easily embarrassed retired man. The bird
repeats everything instantly in a squeaky Bulbul voice. The uncle is the
straight man: he wants the bird to seem *sanskari*, and the bird keeps
undercutting him. He loves the bird; he never mocks the user. Humour comes
from timing and rules, never from generated jokes. Scripted line banks, 2–3
variants each.

**Six scenes for v1** (five need no LLM):

1. **Abuse → beak covered mid-word**, three-step escalation ending in the
   cage. Keyword list.
2. **OTP / phone / card number → bird starts reading it perfectly, uncle
   snatches it.** Regex. Shows number reading and stopping mid-stream.
3. **Real question → bird parrots, uncle sighs and answers in one line.**
   Question-word detection plus `sarvam-105b`.
4. **Other language → uncle replies in that language.** STT language code;
   pre-written lines per language.
5. **Same thing three times → bird yawns instead.** Counter.
6. **Silence → bird pecks the screen, then uncle coaxes the user.** Timer.
   Doubles as onboarding.

Frequency: guardrail scenes always; comedy scenes at most 1 in 5 turns, 3-turn
cooldown, no repeat within 10 turns; one guaranteed scene in the first 30 s.

**Share moment.** One tap exports a 9:16 clip of the last exchange: the
user's line turned squeaky, then the uncle's hand landing on the beak, with
captions and a small "<250 ms · Bulbul V4 Flash" badge. Built for Reels and
WhatsApp Status. Kids talk, parents post.
