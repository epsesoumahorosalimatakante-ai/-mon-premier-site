"""Génère une bande-son électro simple (124 BPM) calée sur l'animation : video/musique.m4a.
Aucune dépendance : Python standard + ffmpeg. Usage : python3 tools/musique.py"""
import math, random, struct, subprocess, wave, os

SR, TOTAL, BPM = 44100, 34.0, 124
N = int(SR * TOTAL)
L = [0.0] * N
R = [0.0] * N
beat = 60 / BPM
random.seed(7)
ROOT = os.path.join(os.path.dirname(__file__), '..', 'video')

def add(t0, samples, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    gl, gr = gain * (1 - max(pan, 0)), gain * (1 + min(pan, 0))
    for k, v in enumerate(samples):
        i = i0 + k
        if 0 <= i < N:
            L[i] += v * gl; R[i] += v * gr

def kick():
    out, ph = [], 0.0
    for k in range(int(.35 * SR)):
        t = k / SR
        ph += 2 * math.pi * (45 + 110 * math.exp(-t * 30)) / SR
        out.append(math.sin(ph) * math.exp(-t * 9))
    return out

def noise(dur, decay, hp=True):
    out, prev = [], 0.0
    for k in range(int(dur * SR)):
        n = random.uniform(-1, 1)
        v = n - prev if hp else n; prev = n
        out.append(v * math.exp(-k / SR * decay))
    return out

def whoosh(dur=1.0):
    out, lp = [], 0.0
    for k in range(int(dur * SR)):
        t = k / dur / SR
        env = math.sin(math.pi * t) ** 2
        a = 0.02 + 0.25 * env           # filtre passe-bas qui s'ouvre puis se referme
        lp += a * (random.uniform(-1, 1) - lp)
        out.append(lp * env * 2.2)
    return out

def boom():
    out, ph = [], 0.0
    for k in range(int(1.6 * SR)):
        t = k / SR
        ph += 2 * math.pi * (38 + 60 * math.exp(-t * 6)) / SR
        out.append((math.sin(ph) + random.uniform(-.15, .15) * math.exp(-t * 20)) * math.exp(-t * 2.2))
    return out

def tone(freq, dur, kind='saw', decay=3.0, attack=.01):
    out = []
    for k in range(int(dur * SR)):
        t = k / SR
        p = (freq * t) % 1
        v = (2 * p - 1) if kind == 'saw' else math.sin(2 * math.pi * freq * t)
        env = min(1, t / attack) * math.exp(-t * decay)
        out.append(v * env)
    return out

def lowpass(x, a):
    y, s = [], 0.0
    for v in x:
        s += a * (v - s); y.append(s)
    return y

K, H, C = kick(), noise(.05, 90), noise(.18, 25)
BOOM, WH = boom(), whoosh(1.0)
# progression : Am - F - C - G (notes graves en Hz)
prog = [55.0, 43.65, 65.41, 49.0]
chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
bass_cache = {f: lowpass(tone(f, beat * .45, 'saw', 6), .08) for f in prog}
pad_cache = {}

start = 1.3          # le rythme démarre à l'apparition du logo
nbeats = int((TOTAL - start - 1.5) / beat)
for b in range(nbeats):
    t = start + b * beat
    bar = (b // 4) % 4
    if not (5.3 < t < 5.6 or 9.3 < t < 9.6):          # petites pauses avant les transitions
        add(t, K, .9)
    add(t + beat / 2, H, .25, .3)
    if b % 4 in (1, 3):
        add(t, C, .35, -.2)
    f = prog[bar]
    add(t + beat / 2, bass_cache[f], .45)
    add(t + beat * .75, bass_cache[f], .3)
    if b % 4 == 0:
        if bar not in pad_cache:
            pad_cache[bar] = lowpass([sum(v) / 3 for v in zip(*[tone(n, beat * 4, 'saw', .6, .3) for n in chords[bar]])], .05)
        add(t, pad_cache[bar], .35, .25 if bar % 2 else -.25)
    if b % 2 == 0:     # arpège pluck
        n = chords[bar][(b // 2) % 3] * 2
        add(t + beat * .25, tone(n, .25, 'sine', 14), .12, .5 if (b // 2) % 2 else -.5)

# montée initiale + impacts + whooshs de transition
add(0, [v * (k / (1.3 * SR)) for k, v in enumerate(whoosh(1.3))], .6)
for t in (1.3, 6.45, 28.8):
    add(t, BOOM, .9)
for cut in (5.5, 9.5, 16.5, 23.0, 28.5):
    add(cut - .5, WH, .7, -.4)
    add(cut - .45, WH, .5, .4)

# fondu de sortie + normalisation
fade = int(2.0 * SR)
for i in range(N - fade, N):
    g = (N - i) / fade; L[i] *= g; R[i] *= g
peak = max(max(abs(v) for v in L), max(abs(v) for v in R)) or 1
g = .89 / peak

os.makedirs(ROOT, exist_ok=True)
wav = os.path.join(ROOT, '_musique.wav')
with wave.open(wav, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<hh', int(L[i] * g * 32767), int(R[i] * g * 32767)) for i in range(N)))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                os.path.join(ROOT, 'musique.m4a')], check=True)
os.remove(wav)
print('Bande-son : video/musique.m4a')
