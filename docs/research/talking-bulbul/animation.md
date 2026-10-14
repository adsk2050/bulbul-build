# Talking Bulbul: animation research

Date: 2026-10-14. Scope: how to animate a cartoon bulbul on a palm, drive its mouth from streamed Sarvam TTS audio, make it look polished, and record a 9:16 video. No paid calls were made.

## 1. How Talking Tom (Outfit7) animates

**Takeaway.** Outfit7 builds on Unity with a large library of pre-made animation clips driven by a state machine. The core "repeat in a squeaky voice" loop is: record the mic, pitch it up, play back while a talking clip runs. No public source explains their lip sync, so treat amplitude-driven mouth flaps as the likely approach, not a confirmed one.

**Findings**
- Talking Tom Cat launched on iOS on 2010-06-26; Tom repeats what you say "in a high-pitched voice". Source: https://en.wikipedia.org/wiki/Talking_Tom_%26_Friends
- One history piece describes the playback as a "high-pitched helium squeak whatever is spoken into an iPhone's microphone". Source: https://www.fierce-network.com/developer/outfit7-claws-its-way-to-top-talking-tom-cat-2
- Engine for My Talking Tom (2013) is Unity. Source: https://en.wikipedia.org/wiki/My_Talking_Tom
- My Talking Tom Friends 2: "almost 1,000 animations", with a custom system that keeps animation data at 10–15 MB of app size. Animation runs on Unity's C# Job System (retargeting, IK, look-at). Character activity is a state machine. Source: https://unity.com/blog/bringing-my-talking-tom-friends-2-to-life
- Same article: dialogue lives in a spreadsheet that Unity imports into a conversation graph; actions (sitting, eating) gate which lines are available; cooldowns keep reactions from repeating. This is the pattern to copy for "uncle barges in" reactions. Source: https://unity.com/blog/bringing-my-talking-tom-friends-2-to-life
- Tom is a 3D character (Wikipedia: "fully animated interactive 3D character"). Source: https://en.wikipedia.org/wiki/Talking_Tom_%26_Friends

**Gaps**
- No public talk or postmortem found on Talking Tom lip sync, the listening pose (ears up while you speak), or the pitch-shift algorithm. Observed behaviour in the app: a "listening" pose while mic level is above a threshold, then a talk clip with mouth moving while the pitched audio plays. That is from use of the app, not a source.
- tcrf.net page for Talking Tom Cat had no technical content.

## 2. Web character-animation options for our case

**Takeaway.** Rive is the best fit: one `.riv` file with a state machine (idle, listen, talk, covered-beak, sigh) and a number input for mouth-open, with the same file running on web, iOS, Android, Flutter and React Native. Spine and Live2D look as good but cost more setup time. Lottie and plain SVG cannot do reactive, blended states well. Unity WebGL is too heavy for a share-link web toy.

**Comparison** (one person, one day)

| Option | Smoothness | Web runtime size | Audio-driven mouth | Mobile port | One-day learning | Editor cost |
|---|---|---|---|---|---|---|
| **Rive** | Very high: vector, bones, meshes, blend states, runs 60fps | webgl2 ~648 KB brotli; canvas ~567 KB; canvas-lite ~222 KB | Yes: number input -> 1D blend state (mouth open 0-100), or viseme number input | Same `.riv` file on iOS, Android, Flutter, RN, Unity, Unreal | Medium. Editor is Figma-like; state machines take a few hours | Free (exports with a splash screen); Cadet $9/seat/mo removes it |
| **Lottie / dotLottie** | High for fixed clips | dotLottie player uses ThorVG (~150 KB WASM) | Weak: scrub a mouth clip by frame from code; no blending between clips | lottie-ios / lottie-android exist | Low for playback, but needs After Effects or Lottie Creator to author | LottieFiles free tier; AE is paid |
| **Spine 2D** | Very high (game industry standard), meshes and IK | spine-player / spine-pixi, a few hundred KB | Yes, set a mouth bone/slot or blend track from code | Runtimes for Unity, iOS, Android, etc. | Medium-high; rigging takes skill | Essential $69 (no meshes, no IK), Professional $379, one-time; runtime use tied to owning a licence |
| **Live2D Cubism** | Very high for face "2.5D" (VTuber look) | Cubism SDK for Web + model files | Built in: wav-volume lip sync sample; MotionSync plugin for vowels | Native/Unity SDKs | High; models take days to rig | Editor FREE/PRO; SDK release free for individuals and firms under 10M yen sales |
| **PixiJS / Three.js custom** | As good as the art and your code | PixiJS v8 ~244 KB gzip | Easy: you write it | Needs rewrite or webview | Low to start, high to make it look good | Free |
| **Plain SVG / CSS** | Looks cheap unless hand-tuned | Tiny | Easy (scale a mouth path) | Webview only | Low | Free |
| **Unity WebGL** | High | Tens to hundreds of MB; mobile browser support limited | Yes | Strong (native builds) | High | Free tier |

**Findings**
- Rive state machine: inputs are queried after `onLoad`; trigger inputs `.fire()`, boolean/number set `.value`. Source: https://rive.app/docs/runtimes/web/inputs
- Rive now marks Inputs as legacy; new projects should use **Data Binding** (view-model properties) instead. Source: https://rive.app/docs/runtimes/web/inputs
- Rive web packages: `@rive-app/webgl2` (recommended, Rive Renderer, supports vector feathering), `@rive-app/canvas` (Canvas2D), `@rive-app/canvas-lite` (drops text, layout, audio, scripting). Source: https://rive.app/docs/runtimes/web/canvas-vs-webgl
- Rive runtime sizes (Jan 2026, brotli -9): webgl2 2179 KB raw / 648 KB; canvas 1728 / 567 KB; canvas-lite 707 / 222 KB. Most of it is the WASM. Source: https://rive.app/docs/runtimes/runtime-sizes.md
- Rive plans: Free $0 (exports `.riv` with a splash screen, 3 collaborative files, 1 project), Cadet $9/seat/mo, Voyager $32, Enterprise $120. Runtimes listed: JS, Flutter, iOS, Android, React, React Native, C++, Defold, Unity, Unreal. Source: https://rive.app/pricing
- Duolingo chose Rive for compact files across Android, iOS and Web, and for the state machine that controls "how they transition and blend together". Source: https://blog.duolingo.com/world-character-visemes
- Rive forum answer on lip sync: build a state machine of visemes triggered by a number, and convert audio to those values in code. Source: https://rive.app/community/forums/support/fsnLLkXUaA62/lip-sync/ftyrdnSzhsd7
- Community write-up: RMS amplitude -> number input -> 1D blend state (0 closed, 100 open) works but every vowel looks the same; visemes (12-15 shapes) look better. Source: https://dev.to/uianimation/dont-build-just-another-chatbot-architecting-a-duolingo-style-ai-companion-with-rive-49g5
- Lottie: Rive says Lottie interactivity must be coded by hand; LottieFiles says dotLottie state machines now add transitions, triggers and data-bound states. Sources: https://rive.app/blog/rive-as-a-lottie-alternative , https://lottiefiles.com/dotlottie
- Spine prices: Essential $69 (was $99), Professional $379, Enterprise $2,499 + $379/user for firms with $500k+ revenue. Essential has no meshes and no IK. Source: https://esotericsoftware.com/spine-purchase
- Spine staff: a public website using the runtimes generally needs the developer's own Spine licence. Source: https://esotericsoftware.com/forum/d/29824-spine-43--2d-animation-buy-form
- Live2D SDK release licence: free for individuals and small businesses (annual sales under 10M yen), except "Expandable Applications" such as avatar systems. Source: https://www.live2d.com/en/sdk/license/
- Live2D Web sample drives lip sync from wav volume via `LAppWavFileHandler`. Source: https://docs.live2d.com/en/cubism-sdk-tutorials/native-lipsync-from-wav-web
- Live2D also ships a MotionSync plugin for Web (vowel-shape lip sync from audio). Source: https://docs.live2d.com/en/cubism-sdk-manual/cubism-sdk-motionsync-plugin-for-web/
- PixiJS v8.18.1: ~244 KB gzip, ~858 KB minified (third-party measure). Source: https://depscope.dev/pkg/npm/pixi.js
- Unity WebGL: older docs say mobile is not supported and show a warning; Unity's roadmap targets high-end iOS/Android browsers only. Sources: https://docs.unity3d.com/2020.3/Documentation/Manual/webgl-browsercompatibility.html , https://activation.unity3d.com/roadmap/415-web-mobile-browser-support

**Gaps**
- Did not benchmark Rive vs Spine fps on a low-end Android phone. Rive's own claim of 60fps is marketing; test on a cheap phone early.
- Exact Live2D Editor PRO price not confirmed (sale pages only).
- Whether Rive's Free-plan splash screen shows at runtime on web or only in exports: check before launch; $9 removes it either way.

## 3. Audio-driven mouth / lip sync in the browser

**Takeaway.** For a bird with a beak, amplitude is enough and is the only method that works on all three audio sources (the user's mic replay, streamed Sarvam TTS, and the uncle's voice) in any Indian language. Use an AnalyserNode on the same Web Audio graph that plays the sound, compute RMS each frame, apply fast-attack / slow-release smoothing, and feed a 0-100 number into a Rive blend state. Visemes add little for a beak and need phoneme timing that Sarvam does not appear to return.

**Findings**
- `AnalyserNode.getFloatTimeDomainData()` fills a Float32Array with the current waveform; compute RMS over it. `smoothingTimeConstant` only affects frequency data, so write your own attack/release. Sources: https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/getFloatTimeDomainData , https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode/smoothingTimeConstant
- Amplitude -> Rive 1D blend (0 closed, 100 open) works but all vowels look alike. For a human face that is a flaw; for a beak it is the expected look. Source: https://dev.to/uianimation/dont-build-just-another-chatbot-architecting-a-duolingo-style-ai-companion-with-rive-49g5
- Live2D's own web sample uses plain wav volume for lip sync, so amplitude is an accepted production method. Source: https://docs.live2d.com/en/cubism-sdk-tutorials/native-lipsync-from-wav-web
- **wawa-lipsync** (MIT): browser TypeScript library; connect an `<audio>` element, call `processAudio()` each animation frame, read `viseme`. Documented input is only an audio element, which does not fit a Web Audio stream of PCM chunks without adaptation. Source: https://cdn.jsdelivr.net/npm/wawa-lipsync@0.0.2/README.md
- **HeadAudio** (MIT): AudioWorklet, MFCC features, outputs Oculus viseme values from audio alone; the author says it is less accurate than text-driven methods. Source: https://github.com/kyr0/HeadAudio
- **Rhubarb Lip Sync**: offline tool (needs the full file), outputs mouth shapes A-H plus X (rest). PocketSphinx recognizer is English-only; the "phonetic" recognizer is language-independent but less precise. Not usable on a live stream. Sources: https://github.com/DanielSWolf/rhubarb-lip-sync , https://www.sourcepulse.org/projects/1841021
- **Azure visemes**: 22 viseme IDs via the `VisemeReceived` event; SVG and blend-shape output only for en-US (and zh-CN for blend shapes). It only covers Azure's own TTS, so it does not apply to Sarvam audio. Source: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-speech-synthesis-viseme
- **Duolingo**: TTS gave no timing, so they ran generated speech through their own speech recognition / pronunciation models to get per-phoneme timing, mapped phonemes to 20+ mouths per character. That is a pipeline, not a one-day job. Source: https://blog.duolingo.com/world-character-visemes
- Sarvam streaming TTS: one WebSocket, config once, stream text in, audio out. No timestamp or alignment message was found in the docs. Sources: https://docs.sarvam.ai/api-reference/text-to-speech/stream , https://docs.sarvam.ai/api/api-guides-tutorials/text-to-speech/streaming-api/web-socket.md

**Practical recipe (from the sources above, tuned values are starting points to test)**
1. One `AudioContext`. Every sound (pitched mic replay, TTS chunks, uncle) goes `source -> GainNode -> AnalyserNode -> destination`. One analyser per speaker (bird, uncle) so each mouth follows only its own voice.
2. `fftSize = 1024` (~21 ms at 48 kHz). Each `requestAnimationFrame`: RMS -> dB -> map roughly -50 dB..-10 dB to 0..1 (a noise gate below the floor keeps the beak shut on hiss).
3. Smooth: if target > current, `current += (target-current) * 0.5` (attack ~1-2 frames); else `current += (target-current) * 0.15` (release ~100 ms). Instant open plus soft close reads as "speech"; symmetric smoothing looks mushy.
4. Optional: quantise to 3-4 beak positions with a little hysteresis. Snappy cartoon beaks often look better than a continuous slider.
5. Add a little extra on top: tie head bob or chest puff to the slow (~300 ms) envelope, so loud syllables move the body too.
6. Latency: the analyser reads the same buffer that is playing, so mouth lag is one frame (~16 ms) plus `outputLatency`. If the scheduled audio is ahead, delay the mouth by `audioContext.outputLatency` (Bluetooth can add 100-200 ms).

**Gaps**
- Did not confirm whether Sarvam returns any timestamps in non-streaming mode. If it does, a word-level "accent" (bigger beak open on word starts) is possible, but not needed.
- No browser test of wawa-lipsync on Hindi audio.
- Meta/Oculus OVRLipSync has no official web build that I found.

## 4. Production-quality polish for 2D characters

**Takeaway.** "Cheap" is a character that is frozen between actions and moves everything at once on linear timing. "Duolingo-quality" is a character that is never fully still (layered idle loops that combine randomly), reacts to every state change with anticipation and overshoot, and splits head, body and face into separate layers that blend. Rive's state machine gives most of this if the art is split into parts.

**Findings**
- Duolingo's Lily (Rive): 8 head and 8 body idle animations that combine at random into 64+ neutral movements, so idle never loops visibly. Head and body are nested artboards that move on their own. Eyes, brows and mouth are separate layers that combine into expressions. Final file under 1 MB. Source: https://rive.app/blog/duolingo-s-ai-powered-video-call-brings-lily-to-life
- Lily covers processing delay with a "thinking" pose: "if there's any processing delay, it looks like she's pondering what you said". This is exactly the trick for TTS latency: play a listening/thinking clip while the first audio chunk arrives. Source: https://rive.app/blog/duolingo-s-ai-powered-video-call-brings-lily-to-life
- Duolingo World Characters: body-pose states and mouth states run in parallel in one state machine; idle has head nods, blinks and eyebrow moves; a final state reacts to right or wrong answers; the character stops talking in time if the learner moves on. Source: https://blog.duolingo.com/world-character-visemes
- Duolingo characters are built from simple geometric shapes, which makes them easy to reuse and animate. Source: https://blog.duolingo.com/designing-new-characters-internship
- Duolingo bought its animation partner studio Gunner; the polish is a full-time studio's work, not a one-day job. Source: https://investors.duolingo.com/news-releases/news-release-details/duolingo-acquires-gunner-accelerate-product-brand-development
- Squash and stretch shows weight and flexibility; keep volume constant (squash wide = shorter). Anticipation is a small opposite move before a big one, so the eye catches the action. Sources: https://people.wku.edu/joon.sung/edu/anim/3d/theory/principles.html , https://www.animaker.com/hub/?p=7967
- In Rive, these principles map to: layered state machine (separate layers for body, head, eyes, beak, so blinks run independently of talking); blend states for continuous inputs (beak open); easing curves per keyframe; and mesh deformation / bones for squash and stretch. Source: https://rive.app/docs/runtimes/web/inputs (inputs) and https://blog.duolingo.com/world-character-visemes (parallel mouth and body states)

**Checklist for the bulbul (applying the principles above; my synthesis, not a sourced fact)**
- Idle layer: breathing (chest scale 1.00 -> 1.03, ~2.5 s loop, ease in-out), tail flick every 4-8 s at random, head tilt variants. Never stop this layer.
- Blink layer: random 2-6 s interval, 120-150 ms close-open, sometimes a double blink.
- Crest feathers (the red-whiskered bulbul's crest is its signature): follow-through, lagging the head by 2-4 frames. Cheapest big win for "alive".
- Listening state (user speaking): head tilt toward the mic, crest up, eyes wide. Triggered by mic level above a threshold.
- Talking: beak from amplitude (section 3), plus small head bob on loud syllables, plus a squash on each phrase start.
- Uncle barges in: anticipation (hand shadow enters first), hand covers beak, bird squashes and eyes go wide, muffled squeak, then a sigh pose. Hand is a separate layer in the same file.
- Palm: the hand should rise and fall slightly with breathing; a static hand looks like a sticker.
- Use eased curves everywhere; no linear tweens. Overshoot (back-out easing) on poses landing.
- Render at device pixel ratio, cap at 60 fps, and test on a low-end Android early.

**Gaps**
- No public Duolingo doc gives their blink timing or exact easing curves. The numbers above are common starting values to tune by eye.

## 5. Getting the art in one day

**Takeaway.** No tool turns a flat image into a clean, rigged bird in one click. The fastest route that still looks polished: generate the bulbul and the palm with an AI image model in a flat-vector style, redraw or vectorise them as separate parts (body, head, crest, eyes, upper beak, lower beak, wings, tail, palm, thumb/covering hand), then rig in Rive with bones and a few meshes. Budget 4-6 hours for art and rig. In parallel, post a Rive commission (2-6 days) to replace it later.

**Findings**
- Rive Marketplace has free bird files ("A happy bird", "Idle bird", "Bird"), all CC BY and remixable, but none has lip sync and they are simple. Good for learning the rig, not for the final look. Sources: https://rive.app/community/2777-5729-a-happy-bird , https://rive.app/community/5762-11268-idle-bird , https://rive.app/marketplace/6349-12314-bird , https://rive.app/docs/community/marketplace-overview
- Rive Marketplace also has a paid/listed "Custom Talking Avatar: Real-Time Lip Sync" and a CC BY lip-sync-tagged "The Coach MVP 1" to study how others wire mouth inputs. Sources: https://rive.app/marketplace/21097-39950-custom-talking-avatar-real-time-lip-sync-for-your-app/ , https://rive.app/marketplace/8519-16327-the-coach-mvp-1/
- Commissioning on Fiverr: Rive mascot gigs list 3/4/6-day tiers; some start "up to $50"; one freelancer.in Rive mascot job averaged $20 bids. Sellers want layered vector input (Figma, Illustrator, SVG); a flat PNG needs a vectorising add-on. Sources: https://fiverr.com/anush_bars/design-a-modern-business-logo , https://www.freelancer.in/projects/react-native/rive-interactive-app-animations , https://fiverr.com/angie_nation23/create-interactive-rive-character-animation-and-mascot-rigging
- No Rive AI feature turns an image into a rigged file; recent Rive updates added vector drawing, keyframe editing, rigging and data-driven animation. Turning AI art into rig-ready vectors is done by hand. Sources: https://schoolofmotion.com/blog/motion-mondays-august-10-2026 , https://contra.com/community/S2vGvRpH-transform-ai-art-into-rig-ready-vector
- **Qwen-Image-Layered** (open model): splits one image into 2-8 RGBA layers, exports PSD; layers can be split again. Subject-level, not guaranteed part-level. Could give a first cut of body/wing/tail layers to clean up. Sources: https://github.com/QwenLM/Qwen-Image-Layered , https://replicate.com/qwen/qwen-image-layered
- AI "image -> puppet" tools (Puppetflow, Charios, Pixa 2D rigging) exist but are vendor-claimed, mostly humanoid, and unreviewed. Sources: https://aiindigo.com/tool/puppetflow , https://www.hunted.space/product/charios , https://www.pixa.com/create/2d-character-rigging
- Meta Animated Drawings (open source): auto-rigs drawings of humanoid figures (two arms, two legs, head). Not suited to a bird. Source: https://about.fb.com/news/2021/12/using-ai-to-animate-childrens-drawings/
- Adobe Character Animator: puppets are layered Photoshop/Illustrator files; mouth group has 14 shapes (11 visemes) picked from live mic or audio. Output is video, not a web runtime, so it cannot drive the live app. Useful only for pre-rendered promo clips. Source: https://www.adobe.com/learn/adobe-character-animator/web/lip-sync-mouth-shapes
- Live2D: a hand-rigged model takes days; the free "small business" route exists but rigging time does not fit one day. Source: https://www.live2d.com/en/sdk/license/
- Keep the shapes simple and geometric like Duolingo's cast: they rig and animate cleanly. Source: https://blog.duolingo.com/designing-new-characters-internship

**Realistic quality and time (my estimate from the above)**

| Route | Time to first working rig | Look |
|---|---|---|
| Remix a free Rive bird | 1-2 h | Basic, generic |
| AI art -> manual vector parts -> rig in Rive yourself | 4-6 h | Good if the art style is flat and simple |
| AI art -> Qwen-Image-Layered -> clean up -> Rive | 4-6 h, less redraw if it splits well | Same, riskier |
| Fiverr Rive commission | 3-6 days | Best, but misses the 20-hour window |
| Live2D / Spine hand rig | 1-3 days | Very good |

**Gaps**
- Did not test Qwen-Image-Layered on a bird image; part separation quality is unknown.
- Commission prices above are a small sample of listings.

## 6. Recording the scene + audio to a shareable MP4

**Takeaway.** Record in the browser with `canvas.captureStream(30)` plus a `MediaStreamAudioDestinationNode` from the same AudioContext, fed to `MediaRecorder`. Ask for MP4 first (Safari and Chrome 126+ support it), fall back to WebM. Then upload the blob to our FastAPI server and run one native `ffmpeg` pass to H.264/AAC, 1080x1920, `+faststart`, because browser MP4s are fragmented with zero duration. Share with `navigator.share({files})`, with a download fallback.

**Findings**
- MediaRecorder accepts any MediaStreamTrack, including tracks from Canvas and Web Audio. Safari records MP4 with H.264 + AAC. Feature-detect with `isTypeSupported`. Source: https://webkit.org/blog/11353/mediarecorder-api/
- Chrome added MP4 to MediaRecorder in Chrome 126 (June 2024); a 2025 Intent to Ship added more H.264/HEVC MP4 and Matroska options. Sources: https://blog.addpipe.com/mediarecorder-api , https://groups.google.com/a/chromium.org/g/blink-dev/c/YJ1QijNiHeM/m/3EhMjMVwAgAJ
- Codec-string strictness differs: Safari is loose about `avc1` strings, Chrome rejects some forms such as plain `video/mp4` in places. Probe a list at runtime. Source: https://lists.w3.org/Archives/Public/public-webrtc-logs/2025Jul/0111.html
- Browser MP4 output is **fragmented** (Chrome 147 and Safari) and the `moov` atom has **duration 0**; some players show no duration and cannot seek. Source: https://blog.addpipe.com/duration-in-mp4-files-produced-by-chrome-safari/
- `isTypeSupported` support: Chrome 47+, Safari 14.1+ desktop, iOS Safari 14+. Source: https://caniuse.com/mdn-api_mediarecorder_istypesupported_static
- Canvas capture and audio routing: `HTMLCanvasElement.captureStream(fps)` gives a video track; `AudioContext.createMediaStreamDestination()` gives an audio track to add to the same MediaStream. Sources: https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream , https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/createMediaStreamDestination
- **WebCodecs route** (Mediabunny, successor to mp4-muxer): `CanvasSource` + audio source -> `Mp4OutputFormat` -> real, non-fragmented MP4 in the browser. Better files, more code. Sources: https://mediabunny.dev/guide/introduction , https://mediabunny.dev/
- WebCodecs `AudioEncoder` on iOS Safari: partial 16.4-18.7, full from iOS 26. AAC is optional in the spec, and a WebKit bug (Nov 2025) reports wrong AAC decoder-config bytes. Sources: https://caniuse.com/webcodecs , https://bugs.webkit.org/show_bug.cgi?id=302253
- **ffmpeg.wasm**: ~30-32 MB core download, roughly 10-100x slower than native (unsourced estimate), multi-thread build needs COOP/COEP headers. Too heavy for a share button. Sources: https://dev.to/felix-tech/building-a-privacy-first-video-to-audio-converter-with-ffmpegwasm-1kd0 , https://openskillindex.com/skills/majiayu000-claude-skill-registry-ffmpeg-webassembly-workers
- **WhatsApp status**: MP4, H.264 recommended, 9:16 at 1080x1920, 16 MB max, up to 90 s (raised from 60 s in Android beta 2.25.12.9, July 2025). WhatsApp re-compresses on upload. No official WhatsApp spec page found. Sources: https://help.superchat.com/en/articles/701423-whatsapp-media-sizes-formats , https://moda.app/resources/sizes/whatsapp-status , https://green-api.com/en/blog/2025/whatsapp-increases-status-length-to-90-seconds/
- **Web Share API**: `video/mp4` is a shareable type; call `navigator.canShare({files})` first. Chrome 128+, Safari 12.1+ (`share`) / 14+ (`canShare`); Firefox behind a flag. Offer a download fallback. Sources: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/share , https://web.dev/web-share

**Recipe**
1. Draw the Rive scene into a 1080x1920 (or 720x1280 to keep files small) canvas, with caption/brand drawn on the same canvas.
2. `stream = canvas.captureStream(30)`; `stream.addTrack(audioCtx.createMediaStreamDestination().stream.getAudioTracks()[0])` with every voice also connected to that destination.
3. `MediaRecorder` with the first supported of: `video/mp4;codecs=avc1,mp4a.40.2`, `video/mp4`, `video/webm;codecs=vp9,opus`, `video/webm`.
4. POST the blob to `/api/render`; server runs `ffmpeg -i in -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4` (re-encode also fixes variable frame rate from captureStream). A 20 s clip is a few MB.
5. `navigator.share({files:[new File([mp4], 'bulbul.mp4', {type:'video/mp4'})]})`, else download link.

**Gaps**
- Not tested: whether WhatsApp accepts the raw fragmented browser MP4 without the server pass. Assume no; the server pass is cheap.
- Not tested: `captureStream` on Rive's WebGL2 canvas on iOS Safari. If frames come out blank, use `@rive-app/canvas` (Canvas2D) for the recording view.
- A background tab throttles `requestAnimationFrame`, so recording must happen with the page visible.

## Recommendation for a 20-hour build, with an app later

**Stack**
- **Rive** for the bird, the palm and the covering hand, in one `.riv` file. Web runtime `@rive-app/webgl2` (or `@rive-app/canvas` if recording from WebGL2 fails on iOS). The same file later runs in Rive's iOS, Android, Flutter and React Native runtimes, so the app port keeps the art and state machine as-is. (sections 2, 4)
- State machine layers: `idle` (breathing, random tail/head variants), `blink` (random), `body` (listen, talk, covered, sigh, happy), `beak` (1D blend on a 0-100 number). Use Data Binding if the editor version pushes it; plain inputs still work on the web runtime. (sections 2, 4)
- **Mouth from amplitude**: one AnalyserNode per speaker on the Web Audio graph that plays the sound, RMS each frame, fast attack / slow release, write to the beak number. Works for mic replay, Sarvam stream and uncle, in every language. No visemes. (section 3)
- Hide TTS latency with a "thinking" pose, as Duolingo's Lily does. (section 4)
- **Recording**: canvas `captureStream` + Web Audio destination -> MediaRecorder (MP4 if supported, else WebM) -> server `ffmpeg` to H.264/AAC `+faststart` 9:16 -> Web Share, download fallback. (section 6)

**Art route**
1. Hour 0-1: generate a flat-vector red-whiskered bulbul and an Indian man's palm with an AI image model. Simple geometric shapes, big eyes, visible crest, side-on 3/4 view, plain background.
2. Hour 1-4: trace or rebuild as separate vector parts (body, head, crest x2-3, eyes + lids, upper and lower beak, wing, tail, feet, palm, thumb, second hand for covering). Try Qwen-Image-Layered for a first split; redraw where it fails.
3. Hour 4-8: rig in Rive (bones on head, crest, tail; mesh on body for squash), build the state machine.
4. Fallback if the art stalls at hour 4: remix a CC BY Rive marketplace bird and restyle colours.
5. In parallel, post a Fiverr Rive commission for v2 (3-6 days).

**Top 5 risks**
1. **Art + rig time.** This is the biggest risk. Rigging a good-looking character in Rive for the first time can eat the whole day. Mitigation: hard stop at hour 4 on art, keep shapes simple, fallback to a remixed bird.
2. **Barge-in audio control.** Stopping the bird's audio mid-chunk while the uncle starts, without the beak freezing open. Every audio node must be stoppable and the beak must read 0 when its analyser goes silent.
3. **iOS Safari quirks.** AudioContext needs a user tap to start; mic plus playback can switch the audio route; `captureStream` on a WebGL2 canvas and MP4 recording need a real-device test on day one.
4. **Low-end Android performance.** Rive WebGL2 with meshes plus a live mic and an encoder at the same time may drop frames. Test on a cheap phone early; record at 720x1280 / 30 fps.
5. **Rive Free plan.** Free exports carry a splash screen and only 3 collaborative files; Cadet is $9/seat/month. Also, Rive marks Inputs as legacy in favour of Data Binding, so check which the current editor exports before writing glue code.
