"""Fixes the uploaded looping invitation video (assets/video2/original.mp4), restores detail with AI super-resolution
and adds the synthesized soundtrack.

Problems in the source: a 1.4 s clip repeated 7x with a visible jump at every seam, duplicated frames (stutter),
soft/blurry 720x1280 HEVC. Fix:
  1. keep one cycle and drop duplicated frames
  2. Real-ESRGAN (realesr-general-x4v3) x4 on every unique frame → 2880x5120, then Lanczos down to the target size
  3. ping-pong the cycle (seamless loop), motion-interpolate to 30 fps
  4. H.264 high bitrate + AAC soundtrack
Usage:
  python3 tools/make_audio.py video2
  python3 tools/adjust_video2.py --model path/to/realesr-general-x4v3.pth [--height 1920] [--work DIR]
Model: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth (BSD-3)."""
import argparse, glob, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..')
ap = argparse.ArgumentParser()
ap.add_argument('--model', required=True)
ap.add_argument('--height', type=int, default=1920)        # 1920 → 1080x1920 (Full HD), 3840 → 2160x3840 (4K)
ap.add_argument('--work', default=None, help='work dir (re-uses upscaled frames if present)')
ap.add_argument('--out', default=None)
A = ap.parse_args()
SRC = os.path.join(ROOT, 'assets', 'video2', 'original.mp4')
WAV = os.path.join(ROOT, 'assets', 'audio', 'soundtrack-video2.wav')
H = A.height; W = H * 9 // 16
OUT = A.out or os.path.join(ROOT, 'output', 'video2', f'convite-vicente-5anos-HD-{W}x{H}.mp4')
CYCLE, REPEATS = 42, 4                         # source loop length (frames @30fps), ping-pong repeats
ff = lambda *a: subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)

work = A.work or tempfile.mkdtemp(); os.makedirs(work, exist_ok=True)
src_dir, sr_dir, fin_dir = (os.path.join(work, d) for d in ('src', 'sr4x', f'final{H}'))
for d in (src_dir, sr_dir, fin_dir): os.makedirs(d, exist_ok=True)
if not glob.glob(f'{src_dir}/*.png'):
    ff('-i', SRC, '-frames:v', str(CYCLE), '-start_number', '0', f'{src_dir}/u%03d.png')
fs = sorted(glob.glob(f'{src_dir}/u*.png'))
small = [np.asarray(Image.open(f).convert('L').resize((360, 640))).astype(float) for f in fs]
keep = [0]
for i in range(1, len(fs)):                    # drop duplicated (stutter) frames
    if np.abs(small[i] - small[keep[-1]]).mean() > 0.45: keep.append(i)
print(f'{len(keep)} unique frames per cycle')

import torch, sr                                # Real-ESRGAN x4 (CPU)
torch.set_num_threads(os.cpu_count()); net = sr.load(A.model)
for n, i in enumerate(keep):
    o4, of = os.path.join(sr_dir, f'u{i:03d}.png'), os.path.join(fin_dir, f'u{i:03d}.png')
    if not os.path.exists(o4): sr.upscale(net, Image.open(fs[i])).save(o4)
    if not os.path.exists(of):
        im = Image.open(o4).resize((W, H), Image.LANCZOS)
        im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=35, threshold=2)).save(of)
    print(f'  SR {n + 1}/{len(keep)}', flush=True)

seq = keep + keep[-2:0:-1]                     # forward + backward → no seam
order = seq * REPEATS + [seq[0]]
qdir = tempfile.mkdtemp()
for j, i in enumerate(order): os.symlink(os.path.join(fin_dir, f'u{i:03d}.png'), f'{qdir}/q{j:03d}.png')
silent = os.path.join(qdir, 'silent.mp4')
ff('-framerate', '18', '-i', f'{qdir}/q%03d.png', '-vf',
   'minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,eq=saturation=1.06:contrast=1.02',
   '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-pix_fmt', 'yuv420p', silent)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
ff('-i', silent, '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
   '-shortest', '-movflags', '+faststart', OUT)
shutil.rmtree(qdir)
if not A.work: shutil.rmtree(work)
print('OK', OUT)
