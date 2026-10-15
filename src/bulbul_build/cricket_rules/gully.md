# Gully Cricket (top-down pixel game)

- One batter, 12 balls (2 overs), 3 wickets, chasing a target of 26-36.
- The batter moves left/right (arrow keys or drag) to line up with the ball,
  and swings with Space or a tap. Up arrow / LOFT button = lofted shot (6 runs
  70% of the time, otherwise caught out). Down arrow / GROUND = along the ground
  (4 runs, sometimes 2). No mode = normal shot, 1-4 runs. The power meter fills
  with each hit; at 100% the next swing is a guaranteed 6 ("POWER").
- Bowlers: FAST, SWING (drifts sideways), SPINNER (slow), MEDIUM PACE.
- A ball that passes the batter is BOWLED (a wicket) if it was on the stumps,
  otherwise a dot ball.
- Event fields: detail.runs, detail.shot (NORMAL/LOFT/GROUND/POWER),
  detail.timing_ms (positive = swung early, negative = late), detail.swung
  (did they swing at all), detail.how (caught/bowled). player.early / player.late
  count early and late swings; player.avg_timing_ms is the average.
- Players are on phones (tap, drag) or keyboards, so never name a key, a button or
  "tap"; say the shot instead ("lofted shot", "ज़मीन पर खेलो", "line में आओ"). Never
  read out a field name; say it in words.
