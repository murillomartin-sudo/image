"""Fixes the uploaded looping invitation video (assets/video2/original.mp4) and adds the synthesized soundtrack.

Problems in the source: a 1.4 s clip repeated 7x with a visible jump at every seam, duplicated frames (stutter),
720x1280 HEVC. Fix: keep one cycle, drop duplicate frames, ping-pong it (seamless), motion-interpolate to 30 fps,
upscale to 1080x1920 with light sharpening/colour, H.264 + AAC.
Usage: python3 tools/make_audio.py video2 && python3 tools/adjust_video2.py"""
import glob, os, shutil, subprocess, tempfile
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'assets', 'video2', 'original.mp4')
WAV = os.path.join(ROOT, 'assets', 'audio', 'soundtrack-video2.wav')
OUT = os.path.join(ROOT, 'output', 'video2', 'convite-vicente-5anos-ajustado.mp4')
CYCLE, REPEATS = 42, 4                         # source loop length (frames @30fps), ping-pong repeats
ff = lambda *a: subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *a], check=True)

tmp = tempfile.mkdtemp()
ff('-i', SRC, '-frames:v', str(CYCLE), f'{tmp}/h%03d.png')
fs = sorted(glob.glob(f'{tmp}/h*.png'))
small = [np.asarray(Image.open(f).convert('L').resize((360, 640))).astype(float) for f in fs]
keep = [0]
for i in range(1, len(fs)):                    # drop duplicated (stutter) frames
    if np.abs(small[i] - small[keep[-1]]).mean() > 0.45: keep.append(i)
seq = keep + keep[-2:0:-1]                     # forward + backward → no seam
order = seq * REPEATS + [seq[0]]
os.makedirs(f'{tmp}/q')
for j, i in enumerate(order): shutil.copy(fs[i], f'{tmp}/q/q{j:03d}.png')
silent = f'{tmp}/silent.mp4'
ff('-framerate', '18', '-i', f'{tmp}/q/q%03d.png', '-vf',
   'minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,'
   'scale=1080:1920:flags=lanczos,unsharp=5:5:0.6:5:5:0.0,eq=saturation=1.08:contrast=1.03',
   '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', silent)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
ff('-i', silent, '-i', WAV, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
   '-shortest', '-movflags', '+faststart', OUT)
shutil.rmtree(tmp)
print('OK', OUT, f'({len(keep)} unique frames/cycle)')
