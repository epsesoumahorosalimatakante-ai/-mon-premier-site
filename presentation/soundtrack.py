"""Génère la bande-son (musique 120 BPM + effets synchronisés) de la présentation.
Usage : python3 soundtrack.py audio/soundtrack.wav
"""
import sys
import wave
import numpy as np

SR = 44100
DUR = 51.0
N = int(SR * DUR)
rng = np.random.default_rng(3)
BEAT = 0.5  # 120 BPM

mus = np.zeros((N, 2))   # musique
sfx = np.zeros((N, 2))   # effets (envoyés dans la réverb)
dry = np.zeros((N, 2))   # effets secs


def add(buf, t0, sig, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        sig = np.stack([sig * l, sig * r], 1) * np.sqrt(2)
    j = min(N, i + len(sig))
    s = max(0, -i)
    buf[max(i, 0):j] += sig[s:j - i] * gain


def tt(d):
    return np.arange(int(d * SR)) / SR


def fft_filter(x, lo=0, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = (f >= lo) & (f <= (hi or SR))
    return np.fft.irfft(X * m, len(x))


def env_ad(t, a, d):
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)


# ---------------- instruments ----------------
def kick():
    t = tt(0.5)
    f = 45 + 120 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.3 * rng.standard_normal(len(t)) * np.exp(-t * 300)


def hat(open_=False):
    t = tt(0.25)
    n = np.diff(rng.standard_normal(len(t) + 1))
    return n * np.exp(-t * (14 if open_ else 55)) * 0.35


def clap():
    t = tt(0.35)
    n = fft_filter(rng.standard_normal(len(t)), 900, 6000)
    e = sum(np.exp(-np.maximum(0, t - o) * 60) * (t >= o) for o in (0, 0.01, 0.022))
    return n * (e * 0.6 + np.exp(-t * 14) * 0.5) * 0.9


def saw_add(freq, t, nh=10, detune=0.0):
    out = np.zeros_like(t)
    for h in range(1, nh + 1):
        if freq * h > 9000:
            break
        out += np.sin(2 * np.pi * freq * h * (1 + detune) * t + h) / h
    return out


def pluck(freq, d=0.45):
    t = tt(d)
    out = np.zeros_like(t)
    for h in range(1, 9):
        out += np.sin(2 * np.pi * freq * h * t) / h * np.exp(-t * (6 + 4 * h))
    return out * 0.5


def whoosh(d=0.7, f0=300, f1=3500, rise=True, amp=1.0):
    t = tt(d)
    k = t / d
    g = (f0 * (f1 / f0) ** k) if rise else (f1 * (f0 / f1) ** k)
    out = np.zeros_like(t)
    for _ in range(70):
        r = 2 ** rng.uniform(-1, 1)
        out += np.sin(2 * np.pi * np.cumsum(g * r) / SR + rng.uniform(0, 6.3))
    e = np.sin(np.pi * k) ** 1.5 if rise else np.exp(-k * 4) * np.minimum(1, k * 40)
    return out / 70 * e * 2.2 * amp


def riser(d, f0=200, f1=5000):
    t = tt(d)
    k = t / d
    g = f0 * (f1 / f0) ** (k ** 1.6)
    out = np.zeros_like(t)
    for _ in range(90):
        r = 2 ** rng.uniform(-0.8, 0.8)
        out += np.sin(2 * np.pi * np.cumsum(g * r) / SR + rng.uniform(0, 6.3))
    return out / 90 * (k ** 2) * 2.6


def impact(size=1.0):
    t = tt(2.2)
    f = 32 + 70 * np.exp(-t * 10)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    n = fft_filter(rng.standard_normal(len(t)), 40, 2500) * np.exp(-t * 9) * 0.8
    return (boom * 1.1 + n) * size


def pop(f0=700, f1=1400):
    t = tt(0.12)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(t, 0.003, 0.04) * 0.6


def blip(f=1800, d=0.08):
    t = tt(d)
    return np.sign(np.sin(2 * np.pi * f * t)) * env_ad(t, 0.001, d / 4) * 0.12


def ding(f=1318.5):
    t = tt(1.4)
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) + 0.25 * np.sin(2 * np.pi * f * 2.0 * t)) * env_ad(t, 0.002, 0.35) * 0.35


def key_click():
    t = tt(0.03)
    n = fft_filter(rng.standard_normal(len(t)), 2000, 9000)
    return (n * np.exp(-t * 300) + 0.4 * np.sin(2 * np.pi * rng.uniform(2500, 4000) * t) * np.exp(-t * 400)) * 0.35


def glitch(d):
    out = []
    while sum(len(o) for o in out) < d * SR:
        seg = int(rng.uniform(0.015, 0.06) * SR)
        kind = rng.integers(3)
        t = np.arange(seg) / SR
        if kind == 0:
            hold = int(rng.uniform(20, 200))
            v = np.repeat(rng.uniform(-1, 1, seg // hold + 1), hold)[:seg]
        elif kind == 1:
            v = np.sign(np.sin(2 * np.pi * rng.uniform(200, 3000) * t))
        else:
            v = np.zeros(seg)
        out.append(v * rng.uniform(0.2, 0.55))
    return np.concatenate(out)[: int(d * SR)]


def sonar(f=1046.5):
    t = tt(1.2)
    return np.sin(2 * np.pi * f * t) * np.sin(2 * np.pi * 6 * t) ** 2 * np.exp(-t * 3.5) * 0.4


def swish(d=0.25):
    return whoosh(d, 1500, 6000, True, 0.5)


# ---------------- music ----------------
NOTE = lambda m: 440 * 2 ** ((m - 69) / 12)
CHORDS = [(57, [69, 72, 76]), (53, [65, 69, 72]), (60, [67, 72, 76]), (55, [67, 71, 74])]  # Am F C G


def active(t, spans):
    return any(a <= t < b for a, b in spans)


DRUMS = [(2.0, 40.0), (42.6, 50.0)]
HATS = [(6.0, 40.0), (42.6, 50.0)]
CLAPS = [(12.5, 40.0), (42.6, 49.0)]
ARPS = [(16.0, 21.0), (26.0, 40.0), (42.6, 49.0)]
BASS = [(2.0, 40.0), (42.6, 50.0)]

kicks = []
for b in range(int(DUR / BEAT)):
    t0 = b * BEAT
    if active(t0, DRUMS):
        add(mus, t0, kick(), 0.95)
        kicks.append(t0)
    if active(t0, HATS):
        add(mus, t0 + BEAT / 2, hat(b % 4 == 3), 0.5, 0.3)
        add(mus, t0 + BEAT / 4 * 3, hat(), 0.22, -0.3)
    if active(t0, CLAPS) and b % 2 == 1:
        add(mus, t0, clap(), 0.5)

# pad + basse par mesure (2 s)
t_all = np.arange(N) / SR
pad = np.zeros((N, 2))
bass = np.zeros(N)
for bar in range(int(DUR / 2) + 1):
    t0 = bar * 2.0
    root, notes = CHORDS[bar % 4]
    seg = tt(2.08)
    e = np.minimum(1, seg / 0.25) * np.minimum(1, (2.08 - seg) / 0.12)
    for side, det in ((0, -0.004), (1, 0.004)):
        v = sum(saw_add(NOTE(n), seg, 7, det) for n in notes) * e
        i = int(t0 * SR)
        j = min(N, i + len(v))
        if i < N:
            pad[i:j, side] += v[: j - i]
    if active(t0 + 0.01, BASS):
        for eighth in range(8):
            st = t0 + eighth * 0.25
            if st >= DUR:
                break
            s = tt(0.24)
            f = NOTE(root - 24 + (12 if eighth in (3, 7) else 0))
            v = (np.sin(2 * np.pi * f * s) + 0.35 * np.sin(4 * np.pi * f * s) + 0.12 * np.sin(6 * np.pi * f * s)) * env_ad(s, 0.005, 0.18)
            i = int(st * SR)
            j = min(N, i + len(v))
            bass[i:j] += v[: j - i]
pad[:, 0] = fft_filter(pad[:, 0], 0, 2600)
pad[:, 1] = fft_filter(pad[:, 1], 0, 2600)

# arpège
arp = np.zeros((N, 2))
for s16 in range(int(DUR / 0.125)):
    st = s16 * 0.125
    if not active(st, ARPS):
        continue
    root, notes = CHORDS[int(st // 2) % 4]
    seq = [notes[0], notes[1], notes[2], notes[1] + 12, notes[2], notes[0] + 12, notes[1], notes[2]]
    add(arp, st, pluck(NOTE(seq[s16 % 8])), 0.16, 0.4 if s16 % 2 else -0.4)

# sidechain
sc = np.ones(N)
for k in kicks:
    i = int(k * SR)
    s = tt(0.4)
    g = 1 - 0.75 * np.exp(-s / 0.09)
    j = min(N, i + len(s))
    sc[i:j] = np.minimum(sc[i:j], g[: j - i])

# enveloppes de sections
pad_env = np.interp(t_all, [0, 1.2, 1.3, 40, 40.2, 42.5, 42.6, 49, 51], [0.15, 0.3, 0.7, 0.7, 0.9, 1.0, 0.75, 0.75, 0])
pad_env *= np.interp(t_all, [16, 16.3, 20.8, 21], [1, 0.45, 0.45, 1])
mus[:, 0] += pad[:, 0] * 0.045 * pad_env * sc
mus[:, 1] += pad[:, 1] * 0.045 * pad_env * sc
mus[:, 0] += bass * 0.42 * sc
mus[:, 1] += bass * 0.42 * sc
mus += arp * sc[:, None]

# ---------------- effets synchronisés ----------------
CUTS = [6, 12.5, 16, 21, 26, 33, 40, 45.2]
for c in CUTS:
    add(sfx, c - 0.35, whoosh(0.6), 0.55)
add(sfx, 0.0, riser(1.25, 120, 3000), 0.5)
add(dry, 1.22, impact(1.0), 0.75)
add(sfx, 1.22, ding(880), 0.35)
add(sfx, 2.2, swish(0.5), 0.35)
add(sfx, 2.5, whoosh(0.9, 2500, 400, False), 0.25)

# chat
for st in (6.6, 7.7, 9.5, 10.9):
    add(sfx, st, pop(650, 1300), 0.6)
add(sfx, 8.5, pop(900, 1700), 0.6)
for i in range(6):
    add(dry, 7.75 + i * 0.12, blip(900 + 120 * (i % 3), 0.04), 0.4)

# recherche
for i in range(15):
    add(dry, 12.9 + i * (1.3 / 15), key_click(), 0.9, rng.uniform(-0.3, 0.3))
add(sfx, 14.4, ding(1568), 0.45)
add(dry, 15.2, key_click(), 1.6)
add(dry, 15.2, pop(1200, 900), 0.4)
add(dry, 12.35, glitch(0.25), 0.4)
add(dry, 15.55, glitch(0.62), 0.45)

# terminal
add(dry, 16.02, impact(0.6), 0.6)
for st in (16.25, 16.95, 17.45, 17.95, 18.45, 18.95, 19.45, 19.95):
    for k in range(9):
        add(dry, st + k * 0.042, key_click(), 0.55, rng.uniform(-0.4, 0.4))
    add(dry, st + 0.4, blip(2200 if st != 16.95 else 1500, 0.06), 0.6)
add(sfx, 19.95, riser(0.75, 400, 6000), 0.35)
add(dry, 20.45, glitch(0.65), 0.45)

# globe
for i in range(5):
    add(dry, 21.4 + i * 0.36, blip(1400 + 200 * i, 0.07), 0.5)
add(sfx, 21.6, whoosh(1.4, 200, 1800), 0.4)
add(sfx, 23.6, sonar(), 0.6)
add(sfx, 24.2, pop(500, 1000), 0.6)
add(sfx, 24.4, blip(1700, 0.05), 0.5)
add(sfx, 25.0, blip(2100, 0.05), 0.5)

# Adobe
add(sfx, 26.2, swish(0.4), 0.4)
for i in range(5):
    st = 26.75 + i * 0.38
    add(sfx, st, whoosh(0.5, 400, 4000), 0.4, -0.6 + i * 0.3)
    add(sfx, st + 0.45, ding(NOTE([69, 72, 76, 79, 81][i])), 0.28, -0.6 + i * 0.3)
for i in range(5):
    add(sfx, 30.2 + i * 0.12, ding(NOTE(84 + [0, 3, 7, 10, 12][i])), 0.12)
add(sfx, 29.6, swish(0.3), 0.3)

# profil
add(sfx, 33.2, pop(500, 1100), 0.6)
for i in range(6):
    add(sfx, 34.2 + i * 0.22, swish(0.18), 0.35, -0.2 + i * 0.12)
for i in range(11):
    add(dry, 34.3 + i * 0.1, blip(1300 + i * 60, 0.03), 0.5)
add(sfx, 35.5, pop(800, 1500), 0.4)

# compteur + drop
add(sfx, 40.0, riser(2.6, 150, 7000), 0.75)
for i in range(40):
    st = 40.3 + 2.0 * (i / 40) ** 0.8
    add(dry, st, blip(1500 + i * 25, 0.03), 0.45)
for i in range(16):  # roulement de caisse claire
    st = 41.0 + 1.6 * (1 - (1 - i / 16) ** 1.6)
    add(mus, st, clap(), 0.18 + 0.025 * i)
add(dry, 42.58, impact(1.4), 0.95)
add(sfx, 42.6, ding(880), 0.4)
add(sfx, 42.6, whoosh(1.2, 4000, 300, False), 0.4)

# outro
add(dry, 45.25, impact(1.1), 0.8)
add(sfx, 45.5, whoosh(0.9, 2500, 300, False), 0.3)
add(sfx, 46.6, pop(500, 1000), 0.7)
add(sfx, 46.65, ding(NOTE(76)), 0.3)
for i in range(5):
    add(sfx, 47.6 + i * 0.12, pop(700 + i * 120, 1400 + i * 150), 0.35, -0.5 + i * 0.25)
add(sfx, 50.0, ding(NOTE(69)), 0.3)

# ---------------- réverb ----------------
irt = tt(1.8)
ir = rng.standard_normal((len(irt), 2)) * np.exp(-irt * 3.2)[:, None]
ir[:, 0] = fft_filter(ir[:, 0], 0, 6000)
ir[:, 1] = fft_filter(ir[:, 1], 0, 6000)
ir /= np.sqrt((ir ** 2).sum(0))
L = N + len(irt)
wet = np.stack([np.fft.irfft(np.fft.rfft(sfx[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:N] for c in range(2)], 1)
rev_m = np.stack([np.fft.irfft(np.fft.rfft(mus[:, c], L) * np.fft.rfft(ir[:, c], L), L)[:N] for c in range(2)], 1)

mix = mus * 0.85 + rev_m * 0.12 + sfx * 0.9 + wet * 0.35 + dry * 0.9
fade = np.interp(t_all, [0, 0.02, 49.3, 51], [0, 1, 1, 0])
mix *= fade[:, None]
mix /= np.percentile(np.abs(mix), 99.9) * 1.1
mix = np.tanh(mix * 1.25) / np.tanh(1.25) * 0.92

out = sys.argv[1] if len(sys.argv) > 1 else 'soundtrack.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('ok', out)
