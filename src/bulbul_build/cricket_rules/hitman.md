# Hitman Cricket (3D batting game by ekcuttingchaidesign)

The player bats; the computer bowls. Mode "CLASSIC" (the Blast): 30 balls (5 overs),
3 wickets, score as many as possible, beat their personal best. No target, no running
between wickets: every ball is decided at once. The player is a right- or left-hander
(state.hand); for a left-hander the controls are mirrored, so "left" is still leg side.

## Controls and the shot each gives
| Swipe (phone) | Keys (desktop) | Shot | Suits a ball on |
|---|---|---|---|
| left | A or left arrow | leg-side flick (a pull to a short ball) | leg, outside leg |
| up-left | A+W | on drive to long-on | leg, middle |
| up | W or up arrow | straight drive | middle |
| up-right | W+D | cover drive | off, outside off |
| right | D or right arrow | square cut | outside off (needs width) |
| down | S or down arrow | block (forward defence) | anything |
| down-left / down-right | S+A / S+D | scoop / reverse scoop (full meter only) | leg-middle / off |
One swing per ball. Not swiping = leaving the ball.

## How a ball is decided
- Timing = when the swipe or key lands versus the ball reaching the bat.
  Within 40 ms PERFECT, 78 GOOD, 135 OK, 205 POOR, beyond that MISS. Fast, express and
  yorker balls shrink these by about a fifth.
- Middled with a stroke that suits the line: PERFECT = six, GOOD = four, OK = 1-3 runs.
- POOR timing, or a stroke that does not suit the line (suits_line false), skies it:
  usually CAUGHT, sometimes it carries for six. A cut that is not middled is edged
  to the keeper.
- MISS on a ball hitting the stumps = BOWLED or LBW; outside the stumps = dot ball.
- Block with OK timing or better = safe dot, never out. Late block on the stumps = out.
- Bouncer: cannot bowl or catch you. Only a PERFECT pull (leg side) scores (six);
  a short wide ball can be cut on timing. Anything else goes through to the keeper.
  Leaving it is safe.
- Three dot balls in a row and the fielders sledge the batter.

## The bowling
Pace bowler most balls: seam 122-138 kph, fast 142-158, inswing/outswing 118-140.
One over of spin (off spin, leg spin, arm ball, 82-130 kph) from the third over on.
Bouncer about 1 ball in 8. A yorker (158-170 kph, at the toes) after the batter has hit
three sixes. A slower ball (78-98 kph, it dies late) after four quick balls; batters
swing early at it. Lines: outside leg, leg, middle, off, outside off.

## The confidence meter (Blast)
Six +28, four +22, three +16, two +12, beaten -18, wicket empties it. When full, on the
right ball the player can charge down the pitch (drive up, up-left or up-right with
PERFECT/GOOD timing) for a six, slog-sweep the spinner (leg side), or scoop. A mistimed
charge just plays the normal shot; the game then calls "CHARGE MISTIMED" (meter_call).

## Event fields
- detail.ball: "over N, ball M".
- detail.delivery: bowler (pace / spinner / express pace), type (seam, fast, inswinger,
  outswinger, bouncer, yorker, slower ball, off spin, leg spin, arm ball, back of a
  length), pace_kph, length, line (where it finished), movement, hitting_stumps.
- detail.swung false = left alone. detail.input: via (swipe / keys), direction
  (left, up-left, up, up-right, right, down...) and keys: what they physically did.
- detail.shot: the stroke it became. shot_code: LEG, LONG_ON, STRAIGHT, COVER_LONG_OFF,
  SQUARE_CUT, DEFEND, SCOOP, REVERSE_SCOOP.
- detail.timing: perfect / good / ok / poor / miss. timing_ms: how far off, POSITIVE =
  EARLY (swung before the ball arrived), negative = late. early_or_late: early, late or
  on time.
- detail.suits_line: did the stroke suit that line. line_fit 0-1.
- detail.contact: middled, well timed, got bat on it, blocked, edge, skied, missed.
- detail.went: where the ball went (long-on, cover, point, midwicket, past the bat...).
- detail.runs, detail.out, detail.how (bowled, lbw, caught, caught behind).
- detail.in_air true: the ball is still in the air as you speak (the result lands
  about 2 seconds later). Build suspense first and say the result ("six" or "caught")
  only at the END of the line.
- detail.game_call: the text the game flashes ("SIX!", "THROUGH TO THE KEEPER").
- detail.meter (0-100), meter_full, special_ball_for (charge / sweep / scoop / reverse:
  the meter was full and this ball was right for that special shot).
- kind "over": detail.runs_in_over, wickets_in_over, balls_in_over ("1 0 4 W 6 2").
- kind "end": runs, wickets, balls, fours, sixes, all_out, new_personal_best, previous_best.
- state: runs, wickets, balls, overs, balls_left, wickets_left, personal_best, batter
  (the player's name, or null), hand.
- player (habits so far): timing (early / late / on_time counts, avg_ms positive =
  early), favourite_shots, wrong_shot_for_the_line, against (per kind
  of ball: short, full, wide outside off, on the pads, spin, 150+ kph: balls, runs, outs
  and what they played), dismissals, last_balls.

## Coaching: be specific, in cricket words
Players are on phones (swipe) or keyboards (keys), so never name a key (A, W, D, S,
arrow) or the word "swipe" or "press". Name the shot or the side instead: "सीधा drive",
"leg side", "off side", "cover drive", "cut", "pull", "block", "छोड़ दो".
- Mostly early -> "थोड़ा रुको, ball को bat तक आने दो". Mostly late -> "जल्दी खेलो".
  Only the first shot on a ball counts: swinging early wastes the ball. Say so when
  timing_ms is far early (300+).
- Wrong shot for the line -> name the right one: middle = straight drive; off and
  outside off = cover drive, or the cut if wide; leg = leg-side flick or on drive.
- Out to bouncers or swinging at them -> leave it, or pull only if sure.
- Beaten by the slower ball -> wait for it. Yorker -> block is safe.
- Use the against / favourite_shots data: "हर short ball पर सीधा drive कर रहे हो, pull
  करो leg side में".
- Never read out a field name (all_out, timing_ms, suits_line); say it in words.
