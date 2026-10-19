#!/usr/bin/env python3
"""Top Step Daily NEWS card builder.
Usage: python3 build.py --data data.json --photo photo.jpg --outdir OUT [--date YYYY-MM-DD] [--music auto|NN]
data.json keys: slug, line1, line2, tag, credit, source, rows[3] (use *...* for lime emphasis),
  optional: label (default News), crop {cx,cy,w} (fractions, default .5,.5,1.0), focus ("44% 62%")
Writes OUT/topstepdaily_news_<date>_<slug>.mp4 and updates music_log.json (rotation) next to this file.
Run from anywhere. Needs: playwright+chromium, ffmpeg, PIL.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, datetime
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
GAMES_OPEN = datetime.date(2028, 7, 14)  # day-count anchor (634 days out on 2026-10-19)

ap = argparse.ArgumentParser()
ap.add_argument('--data', required=True); ap.add_argument('--photo', required=True)
ap.add_argument('--outdir', required=True); ap.add_argument('--date')
ap.add_argument('--music', default='auto'); ap.add_argument('--keep-frames', action='store_true')
a = ap.parse_args()

D = json.load(open(a.data))
date = datetime.date.fromisoformat(a.date) if a.date else datetime.date.today()
D['days'] = (GAMES_OPEN - date).days
for k in ('slug', 'line1', 'line2', 'tag', 'credit', 'source', 'rows'):
    assert k in D, f'missing {k}'
assert len(D['rows']) == 3, 'exactly 3 rows'

# music rotation
log_path = os.path.join(HERE, 'music_log.json')
log = json.load(open(log_path))
order = log['order']
if a.music == 'auto':
    nxt = order[(order.index(log['last_used']) + 1) % len(order)] if log.get('last_used') in order else order[0]
else:
    nxt = a.music
music = os.path.join(HERE, 'music', nxt + '.m4a')
assert os.path.exists(music), music

W = tempfile.mkdtemp(prefix='tsdnews_')
shutil.copytree(os.path.join(HERE, 'fonts'), os.path.join(W, 'fonts'))
shutil.copy(os.path.join(HERE, 'card_template.html'), os.path.join(W, 'card.html'))

# photo crop to panel aspect (880x420), 2x
im = Image.open(a.photo).convert('RGB')
c = D.get('crop', {}); cx, cy, cw = c.get('cx', .5), c.get('cy', .5), c.get('w', 1.0)
aspect = 880 / 420
w = im.width * cw; h = w / aspect
if h > im.height: h = im.height; w = h * aspect
x0 = min(max(cx * im.width - w / 2, 0), im.width - w); y0 = min(max(cy * im.height - h / 2, 0), im.height - h)
im = im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((1760, 840), Image.LANCZOS)
im.save(os.path.join(W, 'panel.jpg'), quality=92)

fr = os.path.join(W, 'frames'); os.makedirs(fr)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto('file://' + W + '/card.html'); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(600)
    pg.evaluate('setup(%s)' % json.dumps(D)); pg.wait_for_timeout(300)
    for i in range(300):
        pg.evaluate('render(0,true)' if i == 0 else f'render({i/30},false)')
        pg.screenshot(path=f'{fr}/f{i:04d}.png')
    b.close()

os.makedirs(a.outdir, exist_ok=True)
out = os.path.join(a.outdir, f"topstepdaily_news_{date.isoformat()}_{D['slug']}.mp4")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', f'{fr}/f%04d.png', '-i', music,
    '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', '10', '-movflags', '+faststart', out], check=True)
# keep a thumbnail-check frame next to the video
shutil.copy(f'{fr}/f0000.png', out.replace('.mp4', '_firstframe.png'))
if not a.keep_frames: shutil.rmtree(W, ignore_errors=True)

log['last_used'] = nxt
log['history'].append({'date': date.isoformat(), 'track': nxt, 'post': D['slug']})
json.dump(log, open(log_path, 'w'), indent=2)
print('OUT', out, 'MUSIC', nxt, log['tracks'][nxt], 'DAYS', D['days'])
