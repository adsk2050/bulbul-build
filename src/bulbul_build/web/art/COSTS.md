# Art generation costs

Model `gpt-image-2`. Prices: text in $5/1M, image in $8/1M, image out $30/1M.
Budget: $4.00, at most 30 calls.

| time | sprite | model | quality | size | text in | image in | out | cost | running total |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-14 22:55:14 | bird_base | gpt-image-2 | high | 1024x1024 | 245 | 0 | 7024 | $0.2119 | $0.2119 |
| 2026-10-14 22:57:14 | uncle_base | gpt-image-2 | high | 1024x1024 | 236 | 0 | 7024 | $0.2119 | $0.4238 |
| 2026-10-14 22:58:22 | uncle_open_raw | gpt-image-2 | medium | 1024x1024 | 82 | 1024 | 1756 | $0.0613 | $0.4851 |
| 2026-10-14 22:59:10 | uncle_half_raw | gpt-image-2 | medium | 1024x1024 | 81 | 1024 | 1756 | $0.0613 | $0.5464 |
| 2026-10-14 22:59:50 | uncle_blink_raw | gpt-image-2 | medium | 1024x1024 | 65 | 1024 | 1756 | $0.0612 | $0.6076 |
| 2026-10-14 23:01:01 | bird_open_raw | gpt-image-2 | medium | 1024x1024 | 68 | 1024 | 1756 | $0.0612 | $0.6688 |
| 2026-10-14 23:01:34 | bird_half_raw | gpt-image-2 | medium | 1024x1024 | 70 | 1024 | 1756 | $0.0612 | $0.7300 |
| 2026-10-14 23:02:10 | bird_blink_raw | gpt-image-2 | medium | 1024x1024 | 60 | 1024 | 1756 | $0.0612 | $0.7912 |
| 2026-10-14 23:02:45 | bird_covered_raw | gpt-image-2 | medium | 1024x1024 | 122 | 1024 | 1756 | $0.0615 | $0.8527 |
| 2026-10-14 23:04:25 | palm_raw | gpt-image-2 | medium | 1024x1536 | 182 | 1024 | 1372 | $0.0503 | $0.9030 |
| 2026-10-14 23:04:52 | bg_raw | gpt-image-2 | medium | 1024x1536 | 170 | 0 | 1372 | $0.0420 | $0.9450 |
| 2026-10-14 23:05:31 | uncle_sigh_raw | gpt-image-2 | medium | 1024x1024 | 88 | 1024 | 1756 | $0.0613 | $1.0063 |
| 2026-10-14 23:06:10 | uncle_surprised_raw | gpt-image-2 | medium | 1024x1024 | 77 | 1024 | 1756 | $0.0613 | $1.0676 |
| 2026-10-14 23:07:49 | uncle_sigh_raw2 | gpt-image-2 | medium | 1024x1024 | 119 | 1024 | 1756 | $0.0615 | $1.1291 |
| 2026-10-14 23:08:27 | uncle_surprised_raw2 | gpt-image-2 | medium | 1024x1024 | 105 | 1024 | 1756 | $0.0614 | $1.1905 |
| 2026-10-14 23:39:58 | uncle2_base | gpt-image-2 | high | 1024x1536 | 294 | 1024 | 5488 | $0.1743 | $1.3648 |
| 2026-10-14 23:40:56 | uncle2_open_raw | gpt-image-2 | medium | 1024x1536 | 83 | 1536 | 1372 | $0.0539 | $1.4187 |
| 2026-10-14 23:41:28 | uncle2_half_raw | gpt-image-2 | medium | 1024x1536 | 80 | 1536 | 1372 | $0.0538 | $1.4725 |
| 2026-10-14 23:41:58 | uncle2_blink_raw | gpt-image-2 | medium | 1024x1536 | 67 | 1536 | 1372 | $0.0538 | $1.5263 |
| 2026-10-14 23:42:28 | uncle2_surprised_raw | gpt-image-2 | medium | 1024x1536 | 82 | 1536 | 1372 | $0.0539 | $1.5802 |
| 2026-10-14 23:43:28 | uncle2_surp_eyes_raw | gpt-image-2 | medium | 1024x1536 | 91 | 1536 | 1372 | $0.0539 | $1.6341 |
| 2026-10-14 23:44:01 | uncle2_surp_mouth_raw | gpt-image-2 | medium | 1024x1536 | 77 | 1536 | 1372 | $0.0538 | $1.6879 |
| 2026-10-14 23:44:41 | bird_surprised_raw | gpt-image-2 | medium | 1024x1024 | 62 | 1024 | 1756 | $0.0612 | $1.7491 |
| 2026-10-14 23:45:39 | uncle2_cover_raw | gpt-image-2 | medium | 1024x1536 | 160 | 1536 | 1372 | $0.0542 | $1.8033 |
| 2026-10-14 23:46:48 | uncle2_cover_raw2 | gpt-image-2 | medium | 1024x1536 | 170 | 1536 | 1372 | $0.0543 | $1.8576 |
