"""Génère la bande-son de la pub (35 s, 120 BPM) : rythme afro-pop, basse,
accords, marimba, whooshs sur les transitions, « ding » de confirmation.
Chaque changement de plan tombe sur un temps (0,5 s)."""
import wave
import numpy as np

SR = 44100
DUREE = 35.0
BPM = 120
BEAT = 60 / BPM
N = int(SR * DUREE)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(7)


def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))


def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def lowpass(x, fc):
    n = x.shape[-1]
    X = np.fft.rfft(x, axis=-1)
    f = np.fft.rfftfreq(n, 1 / SR)
    X /= np.sqrt(1 + (f / fc) ** 4)
    return np.fft.irfft(X, n, axis=-1)


def highpass(x, fc):
    return x - lowpass(x, fc)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.18)


def clap():
    n = int(0.25 * SR)
    x = highpass(rng.standard_normal(n), 900)
    e = env(n, 0.001, 0.07)
    for k in (0.008, 0.017):
        e += np.roll(env(n, 0.001, 0.01), int(k * SR)) * 0.6
    return x * e * 0.5


def hat(d=0.035):
    n = int(0.12 * SR)
    return highpass(rng.standard_normal(n), 7000) * env(n, 0.0005, d) * 0.35


def shaker():
    n = int(0.09 * SR)
    return highpass(rng.standard_normal(n), 4500) * env(n, 0.012, 0.025) * 0.18


def note_hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = note_hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t)
    return np.tanh(1.6 * s) * env(n, 0.004, dur * 0.7) * 0.55


def stab(ms, dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(sum(np.sin(2 * np.pi * note_hz(m) * k * t) / k for k in range(1, 6)) for m in ms)
    return lowpass(s, 2600) * env(n, 0.003, 0.08) * 0.10


def marimba(m):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = note_hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 40)
    return s * env(n, 0.002, 0.12) * 0.22


def pad(ms, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * note_hz(m) * t + np.sin(2 * np.pi * 5 * t) * 0.3) for m in ms)
    e = np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.3)
    return s * e * 0.045


def whoosh(dur=0.5):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    lo, hi = lowpass(x, 600), lowpass(x, 5000)
    m = np.linspace(0, 1, n)
    s = lo * (1 - m) + hi * m
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return s * e * 0.35


def ding(f=1318.5):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)
    return s * env(n, 0.002, 0.35) * 0.22


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = highpass(rng.standard_normal(n), 2000) * (t / dur) ** 2 * 0.3
    f = 200 + 1400 * (t / dur) ** 2
    return x + np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 2 * 0.12


def impact():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-t * 10)) / SR) * np.exp(-t / 0.5)
    crash = highpass(rng.standard_normal(n), 3000) * np.exp(-t / 0.6) * 0.25
    return boom * 0.9 + crash


# progression I-V-vi-IV en do majeur, une mesure (2 s) par accord
CHORDS = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
MEL = [0, 2, 1, 2, 0, 2, 1, 2]

K, C = kick(), clap()
for b in range(int(DUREE / BEAT)):
    t = b * BEAT
    if t >= 34.5:
        break
    bar = int(t // 2)
    root, ch = CHORDS[bar % 4]
    pause = 28.0 <= t < 29.0  # coupure avant le plan final
    intro = t < 1.0
    if not pause and not intro:
        add(K, t, 0.95)
    if b % 2 == 1 and not pause:
        add(C, t, 0.8)
    for s in range(4):  # doubles croches
        ts = t + s * BEAT / 4 + (0.012 if s % 2 else 0)
        if not pause:
            add(hat(0.05 if s == 2 else 0.03), ts, 1.0 if s == 2 else 0.55, pan=0.3)
            add(shaker(), ts, 0.8, pan=-0.3)
    if b % 4 == 0:
        add(pad(ch, 2.0), t, 1.0)
    if not pause and t >= 1.0:
        # basse 3+3+2
        for off, dur in ((0, 0.36), (0.375, 0.36), (0.75, 0.24)):
            if b % 2 == 0:
                add(bass(root - 12 + (7 if off == 0.75 else 0), dur), t + off, 1.0)
        add(stab(ch), t + BEAT / 2, 1.0, pan=-0.2)
    if t >= 3.0 and not pause:
        for s in range(2):
            m = ch[MEL[(b * 2 + s) % 8]] + 12
            add(marimba(m), t + s * BEAT / 2 + (BEAT / 4 if s else 0), 1.0, pan=0.25 if s else -0.25)

# transitions synchronisées avec les coupes
for c in (3, 7, 11, 15, 20, 24, 29):
    add(whoosh(0.5), c - 0.4, 1.0)
for c in (16.8, 18.4, 25, 26, 27.5):
    add(whoosh(0.3), c - 0.22, 0.6)
add(ding(), 7 + 1.85, 0.35)       # appui sur +
add(ding(), 7 + 2.62, 0.8)        # appui sur RÉSERVER
add(ding(1760), 7 + 3.0, 0.6)     # confirmation
add(ding(1568), 11.3, 0.7)        # notification
add(ding(1318.5), 21.0, 0.5)      # « déjà réservé »
add(riser(1.0), 28.0, 1.0)
add(impact(), 29.0, 0.9)
add(impact(), 30.1, 0.35)
add(K, 34.5, 1.0)
add(impact(), 34.5, 0.5)

mix = np.stack([L, R], 1)
mix = highpass(mix.T, 25).T
mix = np.tanh(mix * 1.4)
mix *= 0.92 / np.abs(mix).max()
fade = int(0.35 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
with wave.open('musique.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print('musique.wav ok')
