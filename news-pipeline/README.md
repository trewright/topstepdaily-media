# News card pipeline (Top Step Daily, NEWS pillar)

Builds the 10 s animated 1080x1920 news video (Week 01 branding) from a data.json and a photo.

    python3 news-pipeline/build.py --data data.json --photo photo.jpg --outdir news --date YYYY-MM-DD

- `card_template.html` + `fonts/`: the branded card (Barlow Condensed italic, lime/navy, steps motif). Fits text automatically.
- `music/01-10.m4a`: 10 s clips cut from the Gold Medals instrumentals (cleared). `music_log.json` rotates through 01-10 in order; each build advances `last_used`. Commit `music_log.json` after every build.
- Output name: `topstepdaily_news_<date>_<slug>.mp4` (+ `_firstframe.png` for a thumbnail check; do not publish the PNG).
- Day count is computed to 2028-07-14.

data.json: slug, line1, line2 (headline, 2 lines), tag, credit, source, rows (exactly 3, `*lime*` emphasis), optional label, crop {cx,cy,w}, focus.
