"""Procedurally synthesizes the soundtrack (original adventure music + sound effects) synced to index.html.
Output: assets/audio/soundtrack.wav (48 kHz stereo, 15 s). Everything is generated from scratch — no samples."""
import numpy as np, os
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')
os.makedirs(OUT, exist_ok=True)

music = np.zeros((N, 2)); sfx = np.zeros((N, 2)); amb = np.zeros((N, 2))
tt = lambda d: np.arange(int(SR * d)) / SR

def add(buf, x, t0, gain=1.0, pan=0.0):
    """mix mono/stereo x into buf at time t0 with constant-power pan (-1..1)."""
    i = int(t0 * SR)
    if i >= N: return
    if x.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        x = np.stack([x * l, x * r], 1) * np.sqrt(2)
    x = x[: N - i]
    buf[i:i + len(x)] += x * gain

def env(n, a, d, s=0.0, r=None, sus=None):
    """simple ADSR-ish envelope in seconds."""
    a, d = int(a * SR), int(d * SR)
    e = np.ones(n) * s
    e[:a] = np.linspace(0, 1, max(a, 1))[:min(a, n)] if a else e[:a]
    if a < n: e[a:a + d] = np.linspace(1, s, d)[: max(0, min(d, n - a))]
    if r: rr = int(r * SR); e[-rr:] *= np.linspace(1, 0, rr)
    return e

def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99)); return signal.lfilter(b, a, x)
def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi / (SR / 2), 0.99)], 'band'); return signal.lfilter(b, a, x)

def noise(d): return rng.standard_normal(int(SR * d))
def midi(n): return 440 * 2 ** ((n - 69) / 12)

# ───────────────────────── instruments ─────────────────────────
def tom(f0=70, d=0.6, drop=0.5):
    t = tt(d); f = f0 * (1 + drop * np.exp(-t * 25))
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6)
    click = lp(noise(d), 3000) * np.exp(-t * 60) * 0.3
    return np.tanh((body + click) * 1.4)

def taiko(d=1.2):
    return tom(52, d, 0.8) * 1.2 + lp(noise(d), 400) * np.exp(-tt(d) * 9) * 0.5

def shaker(d=0.09):
    t = tt(d); return hp(noise(d), 5000) * np.exp(-t * 55) * (1 - np.exp(-t * 400))

def marimba(n, d=0.7):
    t = tt(d); f = midi(n)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 22) \
        + 0.12 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 45)
    return x * (1 - np.exp(-t * 900))

def pad(notes, d):
    t = tt(d); x = np.zeros_like(t)
    for n in notes:
        for det in (-0.08, 0.0, 0.08):
            f = midi(n + det); ph = rng.random() * 6.28
            x += signal.sawtooth(2 * np.pi * f * t + ph) * 0.33
    x = lp(x, 1400, 2) / len(notes)
    return x * env(len(t), 0.6, 0.1, 1.0, r=0.7)

def brass(n, d, vib=True):
    t = tt(d); f = midi(n) * (1 + (0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t - 0.15, 0, 1) if vib else 0))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = signal.sawtooth(ph) * 0.6 + signal.sawtooth(ph * 1.003) * 0.4
    e = env(len(t), 0.05, 0.15, 0.8, r=min(0.25, d * 0.4))
    # filter "opens" with the attack (brassy blat): crossfade dark → bright by envelope
    y = lp(x, 900) * (1 - e ** 2) + lp(x, 3400) * e ** 2
    return y * e

def bass(n, d):
    t = tt(d); f = midi(n)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return x * env(len(t), 0.01, 0.2, 0.6, r=0.08)

def chime(n, d=1.6):
    t = tt(d); f = midi(n)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)) * np.exp(-t * 2.5)

# ───────────────────────── sound effects ─────────────────────────
def whoosh(d=0.6, f0=400, f1=2500, rev=False):
    n = noise(d); t = tt(d)
    fc = np.geomspace(f0, f1, len(t)) if not rev else np.geomspace(f1, f0, len(t))
    y = np.zeros_like(n)
    for i in range(0, len(n), 256):
        b, a = signal.butter(2, [fc[i] * 0.6 / (SR / 2), min(fc[i] * 1.5 / (SR / 2), 0.99)], 'band')
        y[i:i + 256] = signal.lfilter(b, a, n[i:i + 256])
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    return y * e * 2.2

def wood_thunk(d=0.5, f=180):
    t = tt(d)
    body = (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 2.3 * t) + 0.3 * np.sin(2 * np.pi * f * 3.9 * t)) * np.exp(-t * 18)
    knock = bp(noise(d), 600, 2500) * np.exp(-t * 70)
    low = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 10)
    return np.tanh((body + knock * 0.8 + low * 0.7) * 1.3)

def creak(d=0.9, f0=110):
    t = tt(d)
    # stick-slip friction: pulse train with jittering rate, resonated
    rate = f0 * (1 + 0.35 * np.sin(2 * np.pi * 1.7 * t) + 0.1 * rng.standard_normal(len(t)).cumsum() / np.sqrt(len(t)))
    ph = np.cumsum(rate) / SR; pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    y = bp(pulses, 500, 1800) + 0.5 * bp(pulses, 1900, 3200)
    return y * np.sin(np.pi * t / d) ** 1.5 * 3

def roar(d=1.6, f0=95):
    t = tt(d)
    f = f0 * (0.85 + 0.5 * np.exp(-((t - 0.35) / 0.35) ** 2)) * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = signal.sawtooth(ph) * (1 + 0.6 * np.sin(2 * np.pi * 31 * t)) + 0.9 * noise(d)   # rasp
    y = 1.0 * bp(src, 120, 420) + 0.8 * bp(src, 500, 900) + 0.45 * bp(src, 1100, 2000) + 0.2 * bp(src, 2400, 3800)
    e = np.clip(t / 0.18, 0, 1) * np.exp(-np.clip(t - 0.8, 0, None) * 3.2)
    sub = np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR) * e * 0.6
    return np.tanh((y * e + sub) * 2.2) * 0.9

def call(d=1.0, f0=150, glide=0.6):  # long-neck "hoot" / triceratops grunt
    t = tt(d); f = f0 * (1 + glide * np.sin(np.pi * t / d))
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.15 * noise(d)
    y = bp(src, 80, 900)
    return y * np.sin(np.pi * t / d) ** 0.8

def grunt(d=0.55, f0=75):
    t = tt(d); ph = 2 * np.pi * np.cumsum(f0 * (1 - 0.3 * t / d)) / SR
    src = signal.sawtooth(ph) * (1 + 0.8 * np.sin(2 * np.pi * 22 * t)) + 0.6 * noise(d)
    return np.tanh(bp(src, 70, 700) * 3) * np.sin(np.pi * t / d) * 0.7

def screech(d=0.7):
    t = tt(d); f = 1500 + 900 * np.sin(np.pi * t / d) - 400 * t
    ph = 2 * np.pi * np.cumsum(f) / SR
    src = signal.sawtooth(ph) + 0.4 * noise(d)
    y = bp(src, 1200, 4500) * (1 + 0.5 * np.sin(2 * np.pi * 38 * t))
    return y * np.sin(np.pi * t / d) ** 1.2 * 0.6

def flap(d=0.22):
    t = tt(d); return lp(noise(d), 900) * np.sin(np.pi * t / d) ** 2 * 1.8

def bird(t0dur=0.35):
    d = t0dur; t = tt(d); base = rng.uniform(2600, 4200)
    f = base * (1 + 0.25 * np.sin(2 * np.pi * rng.uniform(14, 26) * t)) * (1 + 0.2 * t / d * rng.choice([-1, 1]))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2

def pop(d=0.18, f=520):
    t = tt(d); return np.sin(2 * np.pi * f * (1 + 2 * np.exp(-t * 40)) * t) * np.exp(-t * 28) + bp(noise(d), 1500, 5000) * np.exp(-t * 90) * 0.4

def rustle(d=0.5):
    t = tt(d); return bp(noise(d), 1500, 7000) * (np.abs(np.sin(2 * np.pi * 9 * t)) ** 3) * np.sin(np.pi * t / d) * 0.8

def boom(d=1.6):
    t = tt(d); f = 60 * (1 + 1.5 * np.exp(-t * 12))
    return np.tanh((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3) + lp(noise(d), 300) * np.exp(-t * 8) * 0.6) * 1.6)

def sparkle(d=1.4):
    x = np.zeros(int(SR * d))
    for k, n in enumerate([86, 90, 93, 98, 102]):
        c = chime(n, d - k * 0.07) * 0.5
        i = int(k * 0.07 * SR); x[i:i + len(c)] += c[: len(x) - i]
    return x

# ───────────────────────── MUSIC (original theme, D dorian, 120 bpm) ─────────────────────────
BPM = 120; B = 60 / BPM          # beat = 0.5 s
M0 = 1.0                         # drums/groove start on the logo impact
# chord progression (2 bars each, 8 beats = 4 s): Dm  Bb  C  Dm(sus)
chords = [([50, 57, 62, 65], 0.0), ([46, 53, 58, 62], 4.0), ([48, 55, 60, 64], 8.0), ([50, 57, 62, 64], 12.0)]
for notes, t0 in chords:
    seg_d = 4.2 if t0 < 12 else 3.0
    add(music, pad([n + 12 for n in notes[1:]], seg_d), t0, 0.16, -0.3)
    add(music, pad(notes, seg_d), t0, 0.12, 0.3)
roots = {0: 38, 4: 34, 8: 36, 12: 38}
# bass ostinato (8ths "da-da-DUM") from the groove start
t = M0
while t < 14.0:
    r = roots[int(t // 4) * 4 if t < 12 else 12]
    for k, (dt, dn) in enumerate([(0, 0), (0.25, 0), (0.5, 7), (0.75, 12)]):
        add(music, bass(r + dn, 0.24), t + dt, 0.28 if k == 0 else 0.18)
    t += 1.0
# tribal drums on an 8th-note grid
step = 0
while M0 + step * B / 2 < 14.0:
    t = M0 + step * B / 2; beat = step % 8
    if beat in (0, 3, 6): add(music, tom(68, 0.5), t, 0.55, -0.2)
    if beat in (2, 5, 7): add(music, tom(98, 0.35, 0.4), t, 0.35, 0.35)
    if step % 16 == 0: add(music, taiko(), t, 0.6)
    step += 1
# shaker on 16ths with accent
k = 0
while M0 + k * B / 4 < 14.0:
    add(music, shaker(), M0 + k * B / 4, 0.09 if k % 2 == 0 else 0.045, 0.5)
    k += 1
# marimba ostinato (original pattern) over the chords
pat = [0, 7, 12, 10, 7, 12, 14, 12]
k = 0
while M0 + k * B / 2 < 13.9:
    tk = M0 + k * B / 2; r = roots[int(tk // 4) * 4 if tk < 12 else 12] + 24
    add(music, marimba(r + pat[k % 8] + 12, 0.6), tk, 0.13, 0.4 * np.sin(k))
    k += 1
# heroic brass theme (original melody) from the reveal of the date until the finale
theme = [  # (beat offset, midi, beats)
    (0, 62, 1.5), (1.5, 65, 0.5), (2, 69, 2), (4, 67, 1), (5, 65, 1), (6, 67, 2),
    (8, 69, 1.5), (9.5, 72, 0.5), (10, 74, 3), (13, 72, 1),
    (14, 70, 1.5), (15.5, 69, 0.5), (16, 67, 2), (18, 72, 1), (19, 69, 1),
]
T0 = 3.8
for off, n, ln in theme:
    ts = T0 + off * B
    if ts > 13.5: break
    add(music, brass(n, ln * B + 0.05), ts, 0.16, -0.15)
    add(music, brass(n - 12, ln * B + 0.05), ts, 0.10, 0.15)
# finale: big Dm chord + taiko roll + cymbal-ish swell
for i in range(8): add(music, tom(60 + i * 2, 0.4), 13.0 + i * 0.125, 0.25 + i * 0.03)
add(music, taiko(1.8), 14.0, 0.9)
fin = sum(brass(n, 1.0, vib=False) for n in [50, 57, 62, 65, 69]) / 3
add(music, fin, 14.0, 0.35)
add(music, pad([62, 65, 69, 74], 1.0), 14.0, 0.2)
swell = hp(noise(1.2), 4000) * np.linspace(0, 1, int(SR * 1.2)) ** 2
add(music, swell, 12.8, 0.12)

# ───────────────────────── SFX timeline (matches index.html) ─────────────────────────
add(sfx, whoosh(0.9, 300, 1800, rev=True), 0.3, 0.35)          # logo falls
add(sfx, boom(), 0.95, 0.55)                                     # logo impact
add(sfx, whoosh(0.7, 500, 2600), 1.25, 0.32, 0.7)                # T-Rex enters (right)
add(sfx, roar(1.7), 1.55, 0.75, 0.55)                            # T-Rex roar
add(sfx, whoosh(0.7, 400, 2200), 1.45, 0.28, -0.7)               # long-neck enters (left)
add(sfx, call(1.1, 140, 0.7), 2.2, 0.35, -0.6)                   # long-neck call
for i in range(6): add(sfx, flap(), 1.6 + i * 0.22, 0.35, -0.8 + i * 0.08)   # pterosaur wings
add(sfx, screech(0.75), 2.35, 0.32, -0.5)
add(sfx, whoosh(0.6, 500, 2400), 1.65, 0.25, 0.8)                # triceratops
add(sfx, grunt(0.6), 2.45, 0.6, 0.7)
add(sfx, whoosh(0.5, 2200, 500), 2.85, 0.3)                      # invitation plank drops
add(sfx, wood_thunk(0.5, 170), 3.3, 0.55)
add(sfx, creak(1.0, 95), 3.4, 0.12, -0.3); add(sfx, creak(0.8, 120), 3.9, 0.09, 0.3)
add(sfx, pop(0.2, 420), 3.82, 0.3); add(sfx, wood_thunk(0.45, 210), 3.95, 0.45)   # date pops
add(sfx, whoosh(0.4, 600, 2000), 4.35, 0.2); add(sfx, wood_thunk(0.4, 240), 4.7, 0.4)  # time
add(sfx, whoosh(0.55, 400, 2400), 5.05, 0.28); add(sfx, wood_thunk(0.5, 160), 5.5, 0.5)  # address
add(sfx, rustle(0.5), 5.5, 0.35, -0.7); add(sfx, pop(0.16, 700), 5.75, 0.22, -0.6)   # picnic
add(sfx, rustle(0.45), 5.65, 0.3, 0.7); add(sfx, pop(0.16, 560), 5.9, 0.22, 0.7)     # eggs
add(sfx, sparkle(1.5), 6.4, 0.28)                                # "Esperamos você!"
add(sfx, roar(1.2, 110), 9.6, 0.28, 0.6)                         # distant ambient roar
add(sfx, call(0.9, 160, 0.5), 11.4, 0.18, -0.6)
for i in range(4): add(sfx, flap(0.25), 8.0 + i * 0.45, 0.14, -0.8)

# ───────────────────────── jungle ambience ─────────────────────────
pink = lp(rng.standard_normal(N), 1800); amb[:, 0] += pink * 0.05; amb[:, 1] += np.roll(pink, 999) * 0.05
water = bp(rng.standard_normal(N), 300, 6000) * 0.035
amb[:, 0] += water * 1.2; amb[:, 1] += water * 0.6                                 # waterfall sits left
for _ in range(16):
    t0 = rng.uniform(0.2, 14.0); b = bird(rng.uniform(0.12, 0.3))
    for k in range(rng.integers(1, 4)): add(amb, b, t0 + k * 0.16, 0.05, rng.uniform(-0.9, 0.9))
# insects (high pulsed tone)
ti = np.arange(N) / SR
amb += (np.sin(2 * np.pi * 5200 * ti) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * ti)) * 0.006)[:, None]

# ───────────────────────── mix & master ─────────────────────────
def reverb(x, d=1.8, mix=0.18):
    ir_t = tt(d); ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 3.4)[:, None]
    ir[:, 0] = lp(ir[:, 0], 5000); ir[:, 1] = lp(ir[:, 1], 5000)
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], 1)
    wet *= np.abs(x).max() / (np.abs(wet).max() + 1e-9)
    return x * (1 - mix) + wet * mix
music = reverb(music, 2.2, 0.22); sfx = reverb(sfx, 1.4, 0.14)
# duck the music slightly under the big roar
duck = np.ones(N); i0, i1 = int(1.5 * SR), int(3.2 * SR); duck[i0:i1] = 0.7
mix = music * duck[:, None] * 0.95 + sfx * 0.9 + amb
mix[:, 0] = hp(mix[:, 0], 28); mix[:, 1] = hp(mix[:, 1], 28)
fade_in = np.clip(np.arange(N) / (0.25 * SR), 0, 1); fade_out = np.clip((N - np.arange(N)) / (0.6 * SR), 0, 1)
mix *= (fade_in * fade_out)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.15) ; mix *= 0.89 / np.abs(mix).max()    # soft-clip, peak ≈ -1 dBFS
wavfile.write(os.path.join(OUT, 'soundtrack.wav'), SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape, 'rms', np.sqrt((mix ** 2).mean()).round(3))
