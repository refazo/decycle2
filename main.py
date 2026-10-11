"""
DeCycle MOBILE 2.0 - orbital boss-fight minigame
TELEFON: o'ngda katta tugma - yo'nalishni almashtirish, chapda - o'q otishni yoqish/o'chirish,
         pastda o'rtada - pauza. Android'da sensorli boshqaruv avtomatik yoqiladi (Settings > Touch controls).
         Same device (2 players) faqat kompyuterda.

Ishga tushirish:  pip install pygame   ->   python DeCycle_1.5.py

MULTIPLAYER (menyu: Multiplayer -> Same device). Akkaunt kerak emas, kemalar rangi bilan ajraladi:
  1-o'yinchi (chap HP, havorang):  Z - yo'nalishni almashtirish,  X - o'q otishni yoqish/o'chirish
  2-o'yinchi (o'ng HP, sariq):     Left/Right - yurish,  Down - o'q otishni yoqish/o'chirish
  Yiqilgan (HP 0) jamoadoshni tiriltirish: uning yonida 3 soniya yo'nalishni tez-tez almashtiring
  Ikkalasi yiqilsa - yutqazasiz. Boss HP x1.5. "Connect" (online) - keyingi versiyada.
  Bosslar nishonni aralash tanlaydi (o'q otayotgan/tiriltirayotganga ko'proq, lekin ketma-ket 2 martadan ortiq emas).

Qiyinchilik tanlashda o'ng pastki burchakdagi qizil LASTHIT: bitta zarbada o'lasiz (yurakcha).
Ilk 4 bossni LASTHIT'da yengsangiz - sirli achivka va yashirin kema rangi beriladi.

Yakka o'yin boshqaruvi (o'zgarmagan):

Boshqaruv:
  Left / Right - orbita bo'ylab chapga / o'ngga (menyuda tanlash)
  X            - o'q otishni yoqish/o'chirish (menyuda tasdiqlash)
  Z            - ushlab turilsa joyida to'xtaydi
  P yoki Esc   - pauza menyusi

YANGI BOSS QO'SHISH: fayldagi "BOSSLAR" bo'limining oxiriga @register_boss bilan
yangi klass qo'shing. Level ro'yxati va saqlash o'zi moslashadi.
"""
import array
import gc
import json
import math
import os
import random
import sys

import pygame

ANDROID = "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")
W, H = (1440, 720) if ANDROID else (1280, 720)       # telefonda eni kengroq (yon tomonda bo'sh joy kam)
CX, CY = W // 2, H // 2 + 10
ORBIT_R = 270
BOSS_R = 66
PLAYER_R = 11
PLAYER_SPEED = 1.9           # rad/s
SLOW_FACTOR = 0.6            # Slowness paytida tezlik ko'paytmasi
FIRE_INTERVAL = 0.10         # sekundiga 10 ta o'q
SHOT_SPEED = 850
SHOT_DMG = 0.7             # har bir o'q bossga beradigan zarar
PLAYER_HP = 20
HEAL_DELAY = 3.0
HEAL_RATE = 1.5              # sekundiga HP
TAU = math.tau

PHASE2_RATE = 1.5            # 2-faza: hujum chastotasi
PHASE2_SPEED = 1.3           # 2-faza: o'q tezligi

# ---- zararlar (HP 20 ga moslashtirilgan) ----
DMG_POISON = 4               # zahar koptokchasi (+3 soniya zahar, sekundiga 1 HP, o'ldirmaydi)
DMG_BLUE = 3                 # moviy lazer
DMG_TONGUE = 5               # til (+3 soniya Slowness)
DMG_BEAM = 2                 # qizil lazer (har 0.3 soniyada, tegib turguncha)
DMG_ROCK = 4                 # KRATUS: katta tosh
DMG_PEBBLE = 1               # KRATUS: tosh bo'roni (+2 soniya Slowness)
DMG_METEOR = 3               # KRATUS: meteor
DMG_RIFT = 4                 # KRATUS: yorilish
DMG_VIOLET = 4               # LASSER: siyohrang lazerchalar
DMG_GREAT = 4                # LASSER: katta nur (har 0.6 soniyada, ichida turguncha)
DMG_FIRE = 2                 # LASSER: olovli lazer (+3 soniya yonish)
DMG_SQUEAK = 4               # GOOSMO: yopishqoq bomba portlashi (+2 soniya zahar)
DMG_STICKY = 2               # GOOSMO: shilliq oqimi to'g'ridan tegsa (+1.5 soniya Slowness)
DMG_CHASE = 3                # GOOSMO: quvlovchi shilliq tegsa
DMG_BUBBLE = 0               # GOOSMO: pufakcha (0 = zarar yo'q, faqat ekranni to'sadi)
BURN_DMG = 1.5               # yonish: sekundiga HP (O'LDIRA OLADI)

# ---- qizil lazer ----
BEAM_MAX = 1.75              # rad/s  (PLAYER_SPEED=1.9 dan oshmaydi)
BEAM_MIN = 1.10
BEAM_HALF = 13               # lazer yarim kengligi (urilish)
BEAM_WARN = 0.8
BEAM_LEN = 1000

TONGUE_LOCK = 0.40           # til nishonini qotirishdan oldingi oxirgi soniyalar
TONGUE_ERR = 0.05            # til nishonidagi tasodifiy xato (rad)
TONGUE_FACTOR = 0.8          # taxminning aniqligi (1.0 = mukammal)

GREAT_HUNT = (0.30, 0.50)          # LASSER katta nur ("ov"): xavfli yoy orbitaning shu qismi
GREAT_SAFE = (0.30, 0.40, 0.50)    # LASSER katta nur ("xavfsiz yoy"): shu qismi xavfsiz, qolgani yonadi
GREAT_TIME = 2.0                   # katta nur otib turish vaqti (soniya)
RIFT_R = 40                        # KRATUS yorilish radiusi

GOO_BOMB_R = BOSS_R                # GOOSMO: bomba portlash radiusi (boss kattaligida)
GOO_BOMB_FUSE = 3.0                # bomba portlashigacha soniya
GOO_PUDDLE_R = 24                  # shilliq ko'lmak radiusi
GOO_PUDDLE_LIFE = (1.2, 2.0)       # ko'lmak yo'qolish vaqti (soniya)
GOO_SLOW = 1.5                     # ko'lmakdan chiqqandan keyin Slowness qancha qoladi
GOO_TONGUE_ERR = 0.20              # GOOSMO tili nishonidagi xato (ALDEMOda 0.05)
GOO_TONGUE_FACTOR = 0.7            # GOOSMO til taxmini aniqligi (ALDEMOda 0.9)
CH_R = 17                          # POSTICK: quvlovchi shilliq radiusi
CH_TIME = 8.0                      # quvlash vaqti (soniya)
CH_SPEED = 1.45                    # quvlash tezligi, rad/s (o'yinchi tezligi 1.9 dan sekin)
CH_FLEE_SPEED = 2.3                # qochish tezligi
CH_FLEE_DIST = 0.30                # shu burchak masofasiga yaqinlashsa qochadi (rad)
CH_FLEE_TIME = 0.9                 # qochish davomiyligi (soniya)
CH_FLEE_LEAD = 0.03                # tez yaqinlashsa oldinroq qochadi: masofa += LEAD * yaqinlashish tezligi
GOO_MINE_R = 22                    # orbitadagi squek ustiga shu masofaga kirsa "mina" ishga tushadi
GOO_MINE_FUSE = 0.5                # minadan qochish uchun vaqt (soniya)
GOO_HOME_RANGE = 60                # squek o'qi yo'lidan shu masofadagi o'yinchiga magnit kabi buriladi (px)
GOO_HOME_TURN = 2.4                # magnit burilish tezligi (rad/s)
GOO_STICK_PAD = 5                  # yopishish radiusiga qo'shimcha (px)
GOO_BOOM_T = 0.6                   # portlash effekti davomiyligi (soniya)

# ---- boss heal: biz hujum qilmayotganimizda ----
BOSS_HEAL_DELAY = 1.0
BOSS_HEAL_PCT = 0.005        # sekundiga max HP ning foizi

MOUTH = (CX, CY + 40)
EYES = {"L": (-30, -22, 15), "R": (30, -22, 15), "C": (0, 6, 20)}   # ALDEMO ko'zlari
BEAM_EYES = ("C", "L", "R")

NUM_LEVELS = 15
MAX_ACCOUNTS = 6

# ---- MULTIPLAYER (test 0.1) ----
MP_BOSS_HP = 1.5             # 2 o'yinchi: boss HP ko'paytmasi
MP_COLORS = (0, 7)           # 1-/2-o'yinchi kema rangi (COLORS indeksi): havorang / sariq
REVIVE_TIME = 3.0            # tiriltirish uchun kerak soniya
REVIVE_NEAR = 0.55           # rad: jamoadoshga qanchalik yaqin bo'lish kerak
REVIVE_DECAY = 0.5           # tiriltirilmayotganda progress kamayish tezligi (soniya/soniya)
WIGGLE_WIN = 0.8             # shu soniya ichida 2 marta yo'nalish almashsa = "tez-tez bosish"
REVIVE_HP = 0.5              # tirilganda HP ulushi
REVIVE_INV = 2.0             # tirilgandan keyingi dahlsizlik (soniya)
DIFF_ORDER = ["Easy", "Mid", "Hard"]
DIFFS = {
    "Easy": dict(boss_hp=250,  speed=0.85, rate=0.80),
    "Mid":  dict(boss_hp=350,  speed=1.00, rate=1.00),
    "Hard": dict(boss_hp=500, speed=1.20, rate=1.30),
}

# kema ranglari (12 ta + yashirin TOTEM). Effektlar kema rangini o'zgartirmaydi - atrofida halqa bo'lib chiqadi.
COLORS = [(90, 220, 255), (70, 140, 255), (150, 110, 255), (220, 110, 255),
          (255, 120, 190), (255, 90, 100), (255, 150, 60), (255, 215, 70),
          (170, 240, 80), (70, 230, 150), (240, 240, 250), (150, 160, 185),
          (250, 225, 60)]                    # 13-chi: TOTEM (yashirin, achivka bilan ochiladi)
TOTEM_IDX = 12                     # COLORS[12] = TOTEM kemasi (sariq + yashil qanot)
TOTEM_COL2 = (70, 235, 110)
TOTEM_LIFE_INV = 2.0               # TOTEM qo'shimcha jon ishlaganda dahlsizlik (soniya)
SURVIVOR_BOSSES = 4                # "I'M SURVIVOR": ilk 4 ta bossni LASTHIT'da yengish

# dushman snaryadlari: radius va urilganda: (zarar, dahlsizlik, ovoz, (effekt, soniya) yoki None)
METEOR_TRAIL = (((60, 8, (255, 110, 40)), (22, 6, (255, 215, 120))) if ANDROID else
                ((75, 5, (150, 50, 20)), (48, 9, (255, 110, 40)), (22, 6, (255, 215, 120))))
PROJ_R = dict(poison=12, blue=5, rock=24, pebble=11, meteor=15, violet=5, fire=8)
HITS = {
    "poison": (DMG_POISON, 0.6, "poison_hit", ("poison", 3.0)),
    "blue":   (DMG_BLUE,   0.3, "light",      None),
    "rock":   (DMG_ROCK,   0.7, "hurt",       None),
    "pebble": (DMG_PEBBLE, 0.4, "light",      ("slow", 2.0)),
    "meteor": (DMG_METEOR, 0.6, "hurt",       ("burn", 2.0)),
    "violet": (DMG_VIOLET, 0.5, "hurt",       None),
    "fire":   (DMG_FIRE,   0.5, "hurt",       ("burn", 3.0)),
}
BOLT_STYLE = {   # chiziq ko'rinishidagi o'qlar: (tashqi rang, ichki rang, uzunlik, qalinlik)
    "blue":   ((50, 140, 255), (220, 245, 255), 16, 7),
    "violet": ((140, 60, 230), (235, 210, 255), 14, 6),
    "fire":   ((255, 110, 20), (255, 240, 150), 20, 8),
}


def angdiff(a, b):
    return abs((a - b + math.pi) % TAU - math.pi)


def orbit_pt(a):
    return CX + math.cos(a) * ORBIT_R, CY + math.sin(a) * ORBIT_R


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


# --------------------------------------------------------------------------- #
#  OBJECT POOLING
# --------------------------------------------------------------------------- #
class Pool:
    """Oldindan yaratilgan obyektlar: o'yin paytida new/del yo'q -> GC qotishi yo'q."""

    def __init__(self, cls, size):
        self.cls = cls
        self.free = [cls() for _ in range(size)]
        self.live = []

    def get(self):
        o = self.free.pop() if self.free else self.cls()
        o.dead = False
        self.live.append(o)
        return o

    def sweep(self):
        live = self.live
        i = 0
        while i < len(live):
            o = live[i]
            if o.dead:
                live[i] = live[-1]
                live.pop()
                self.free.append(o)
            else:
                i += 1

    def clear(self):
        for o in self.live:
            o.dead = True
        self.sweep()


class Proj:
    __slots__ = ("x", "y", "vx", "vy", "r", "kind", "dead")

    def __init__(self):
        self.dead = True


class Shot:
    __slots__ = ("r", "a", "c", "dead")

    def __init__(self):
        self.dead = True


class Tongue:
    __slots__ = ("a", "t", "warn", "ext", "hold", "ret", "hit", "struck", "err", "p", "dead")

    def __init__(self):
        self.dead = True


# --------------------------------------------------------------------------- #
#  KESH: matnlar va tayyor sprite'lar (har kadrda qayta yaratilmaydi)
# --------------------------------------------------------------------------- #
_TC = {}
SPR = {}
HP_W, HP_H, HP_PAD = 160, 14, 16


def txt(font, s, color):
    k = (id(font), s, color)
    r = _TC.get(k)
    if r is None:
        r = font.render(s, True, color)
        _TC[k] = r
    return r


def make_bg(ring, red=False):
    surf = pygame.Surface((W, H))
    surf.fill((38, 5, 10) if red else (8, 6, 20))
    rng = random.Random(7)
    for _ in range(110):
        c = rng.randint(60, 190)
        surf.set_at((rng.randint(0, W - 1), rng.randint(0, H - 1)),
                    (min(255, c + 50), c // 2, c // 2) if red else (c, c, min(255, c + 40)))
    if ring:
        pygame.draw.circle(surf, (130, 30, 45) if red else (45, 50, 90), (CX, CY), ORBIT_R, 2)
    return surf


def make_rock(r, base, dark, seed, glow=None):
    pad = 10 if glow else 3
    size = 2 * (r + pad)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    if glow:
        pygame.draw.circle(surf, glow + (70,), (c, c), r + 8)
        pygame.draw.circle(surf, glow + (110,), (c, c), r + 4)
    rng = random.Random(seed)
    n = 9
    pts = []
    for k in range(n):
        a = TAU * k / n
        rr = r * (1 - 0.28 * rng.random())
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr))
    pygame.draw.polygon(surf, base, pts)
    pygame.draw.polygon(surf, dark, pts, 3)
    pygame.draw.circle(surf, tuple(min(255, v + 45) for v in base), (c - r // 3, c - r // 3), max(2, r // 5))
    return surf


def build_touch_sprites():
    """Sensorli tugmalar bir marta chiziladi (har kadrda qayta chizilmaydi)."""
    turn, fire = {}, {}
    r = 100
    for left in (True, False):
        for on in (False, True):
            sf = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            pygame.draw.circle(sf, (90, 220, 255, 120 if on else 55), (r, r), r)
            pygame.draw.circle(sf, (150, 235, 255, 200), (r, r), r, 3)
            d = -1 if left else 1                  # dir=1 -> ekranda chapga
            pts = [(r + d * 46, r), (r - d * 22, r - 40), (r - d * 22, r + 40)]
            pygame.draw.polygon(sf, (200, 245, 255, 230), pts)
            turn[(left, on)] = sf
    for laser in (False, True):
        for on in (False, True):
            col = (255, 90, 90) if laser else (170, 175, 210)
            sf = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
            pygame.draw.circle(sf, col + ((120 if laser else 45) + (50 if on else 0),), (r, r), r)
            pygame.draw.circle(sf, col + (210,), (r, r), r, 3)
            pygame.draw.circle(sf, col + (230,), (r, r), 26 if laser else 14)
            fire[(laser, on)] = sf
    ps = pygame.Surface((56, 56), pygame.SRCALPHA)
    pygame.draw.circle(ps, (200, 200, 230, 90), (28, 28), 28, 2)
    pygame.draw.rect(ps, (200, 200, 230, 170), (19, 17, 6, 22))
    pygame.draw.rect(ps, (200, 200, 230, 170), (31, 17, 6, 22))
    SPR["tb_turn"], SPR["tb_fire"], SPR["tb_pause"] = turn, fire, ps


def build_sprites():
    SPR["bg_game"] = make_bg(True)
    SPR["bg_menu"] = make_bg(False)
    SPR["bg_menu_red"] = make_bg(False, True)

    ball = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(ball, (20, 110, 30), (16, 16), 14)
    pygame.draw.circle(ball, (70, 220, 70), (16, 16), 12)
    pygame.draw.circle(ball, (190, 255, 170), (12, 12), 4)
    SPR["poison"] = ball
    SPR["rock"] = make_rock(PROJ_R["rock"], (122, 122, 132), (48, 48, 56), 3)
    SPR["pebble"] = make_rock(PROJ_R["pebble"], (128, 128, 138), (52, 52, 60), 8)
    SPR["meteor"] = make_rock(PROJ_R["meteor"], (150, 96, 64), (80, 34, 20), 5, glow=(255, 120, 40))
    SPR["meteor_rot"] = [pygame.transform.rotate(SPR["meteor"], i * 22.5) for i in range(16)]   # aylanish kadrlari

    glow = pygame.Surface((HP_W + 2 * HP_PAD, HP_H + 2 * HP_PAD), pygame.SRCALPHA)
    for i in range(1, 8):
        a = max(0, 170 - i * 22)
        pygame.draw.rect(glow, (255, 255, 255, a),
                         (HP_PAD - i * 2, HP_PAD - i * 2, HP_W + i * 4, HP_H + i * 4), 2)
    SPR["glow"] = glow

    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 165))
    SPR["dim"] = dim
    soft = pygame.Surface((W, H), pygame.SRCALPHA)
    soft.fill((0, 0, 0, 55))
    SPR["dim_soft"] = soft
    bgd = SPR["bg_game"].copy()                  # fon + yengil qoraytirish (har kadrda alpha blit kerak emas)
    bgd.blit(soft, (0, 0))
    SPR["bg_game_dim"] = bgd
    SPR["bg_game_red"] = make_bg(True, True)     # LASTHIT: qizil fon
    rd = SPR["bg_game_red"].copy()
    rd.blit(soft, (0, 0))
    SPR["bg_game_red_dim"] = rd


def draw_ship(s, px, py, ux, uy, col, k=1.0, col2=None):
    """Kema: (ux, uy) - burun yo'nalishi. col2 berilsa qanotlari shu rangda (TOTEM: sariq + yashil)."""
    vx, vy = -uy, ux
    pts = [(px + ux * 15 * k, py + uy * 15 * k),
           (px - ux * 11 * k + vx * 11 * k, py - uy * 11 * k + vy * 11 * k),
           (px - ux * 6 * k, py - uy * 6 * k),
           (px - ux * 11 * k - vx * 11 * k, py - uy * 11 * k - vy * 11 * k)]
    pygame.draw.polygon(s, col, pts)
    if col2:
        nose, lt, notch, rt = pts
        pygame.draw.polygon(s, col2, [((nose[0] + lt[0]) / 2, (nose[1] + lt[1]) / 2), lt, notch])
        pygame.draw.polygon(s, col2, [((nose[0] + rt[0]) / 2, (nose[1] + rt[1]) / 2), rt, notch])
    pygame.draw.polygon(s, (255, 255, 255), pts, 2)


_HEART = [(16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
          for t in (i * TAU / 28 for i in range(28))]


def draw_heart(s, cx, cy, k, col, outline=(255, 220, 220)):
    """Yurakcha (LASTHIT). k=1.0 -> taxminan 32x30 px."""
    pts = [(cx + x * k, cy - y * k) for x, y in _HEART]
    pygame.draw.polygon(s, col, pts)
    pygame.draw.polygon(s, outline, pts, 2)
    pygame.draw.circle(s, (255, 235, 235), (int(cx - 8 * k), int(cy - 6 * k)), max(1, int(3 * k)))


def draw_eye(s, cx, cy, r, px, py, iris, glow, dark):
    if glow:
        pygame.draw.circle(s, iris, (cx, cy), r + 6, 3)
    pygame.draw.circle(s, (245, 245, 250), (cx, cy), r)
    d = math.hypot(px - cx, py - cy) or 1
    ox, oy = (px - cx) / d * r * 0.3, (py - cy) / d * r * 0.3
    pygame.draw.circle(s, iris, (cx + ox, cy + oy), int(r * 0.62))
    pygame.draw.circle(s, (15, 5, 25), (cx + ox, cy + oy), int(r * 0.3))
    pygame.draw.circle(s, dark, (cx, cy), r, 2)


# --------------------------------------------------------------------------- #
#  OVOZ (fayllarsiz, kod bilan sintez qilinadi; bir marta yaratilib qayta ishlatiladi)
# --------------------------------------------------------------------------- #
class Audio:
    def __init__(self):
        self.ok = False
        self.enabled = True
        self.snd = {}
        self.last = {}
        info = pygame.mixer.get_init()
        if not info or info[1] != -16:
            return
        self.rate, _, self.ch = info
        try:
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(2)          # 0: lazer gumburlashi, 1: zaryad
            self._build()
            self.ok = True
        except Exception:
            self.ok = False

    def _tone(self, dur, f0, f1=None, wave="sine", vol=0.4, decay=2.0, grit=0.0, loop=False):
        f1 = f0 if f1 is None else f1
        n = int(self.rate * dur)
        out = array.array("h")
        ph = 0.0
        rnd = random.uniform
        for i in range(n):
            t = i / n
            ph += (f0 + (f1 - f0) * t) / self.rate
            p = ph % 1.0
            if wave == "sine":
                v = math.sin(TAU * p)
            elif wave == "square":
                v = 1.0 if p < 0.5 else -1.0
            elif wave == "saw":
                v = 2 * p - 1
            else:
                v = rnd(-1, 1)
            if grit:
                v = v * (1 - grit) + rnd(-1, 1) * grit
            env = (1 - t) ** decay if decay else 1.0
            if not loop and i < 40:
                env *= i / 40
            out.append(int(32767 * vol * env * v))
        return out

    def _make(self, *parts):
        buf = array.array("h")
        for p in parts:
            buf.extend(p)
        if self.ch == 2:
            st = array.array("h", [0]) * (len(buf) * 2)
            st[0::2] = buf
            st[1::2] = buf
            buf = st
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        T, M = self._tone, self._make
        self.snd = {
            "shoot": M(T(0.07, 1100, 500, "square", 0.12, 2)),
            "hit": M(T(0.04, 300, 150, "noise", 0.18, 2)),
            "hurt": M(T(0.28, 260, 70, "saw", 0.42, 1.5, 0.2)),
            "light": M(T(0.07, 520, 250, "square", 0.16, 2)),
            "poison_shot": M(T(0.20, 180, 420, "sine", 0.40, 1.5)),
            "poison_hit": M(T(0.30, 420, 90, "sine", 0.50, 1.2, 0.1)),
            "blue": M(T(0.09, 1800, 700, "square", 0.10, 2)),
            "charge": M(T(BEAM_WARN, 120, 700, "saw", 0.20, 0.3)),
            "hum": M(T(0.5, 100, 100, "saw", 0.16, 0, loop=True)),
            "mouth": M(T(0.18, 260, 520, "sine", 0.30, 1)),
            "strike": M(T(0.12, 900, 120, "saw", 0.38, 1.5, 0.4)),
            "slow": M(T(0.30, 500, 140, "sine", 0.35, 1.2)),
            "heal": M(T(0.12, 700, 1100, "sine", 0.16, 1), T(0.14, 1100, 1400, "sine", 0.16, 1.5)),
            "tick": M(T(0.06, 250, 200, "sine", 0.25, 1.5)),
            "on": M(T(0.08, 500, 900, "sine", 0.28, 1)),
            "off": M(T(0.08, 900, 450, "sine", 0.28, 1)),
            "phase2": M(T(1.0, 140, 35, "saw", 0.45, 1.0, 0.35)),
            "win": M(T(0.12, 523, 523, "square", 0.18, 0.5), T(0.12, 659, 659, "square", 0.18, 0.5),
                     T(0.12, 784, 784, "square", 0.18, 0.5), T(0.40, 1047, 1047, "square", 0.18, 1.2)),
            "lose": M(T(1.0, 420, 50, "saw", 0.38, 1.0, 0.1)),
            "move": M(T(0.04, 650, 650, "square", 0.10, 1)),
            "select": M(T(0.10, 700, 1300, "square", 0.14, 1.5)),
            "rock": M(T(0.28, 140, 45, "sine", 0.55, 1.2, 0.25)),
            "pebble": M(T(0.05, 500, 200, "noise", 0.14, 2)),
            "meteor": M(T(0.4, 700, 120, "saw", 0.16, 1.5, 0.5)),
            "rift_warn": M(T(0.1, 420, 420, "square", 0.12, 1.5)),
            "rift": M(T(0.35, 110, 40, "saw", 0.5, 1.0, 0.5)),
            "violet": M(T(0.06, 1500, 900, "square", 0.09, 2)),
            "fire": M(T(0.14, 300, 900, "saw", 0.2, 1.5, 0.5)),
            "great": M(T(0.3, 200, 60, "saw", 0.4, 1.0, 0.3)),
            "squeak": M(T(0.06, 1500, 2700, "sine", 0.22, 1.0), T(0.09, 2700, 1800, "sine", 0.20, 1.5)),
            "squeak_hi": M(T(0.05, 1900, 3100, "sine", 0.20, 1.0), T(0.07, 3100, 2300, "sine", 0.18, 1.5)),
            "splat": M(T(0.14, 340, 90, "noise", 0.28, 1.8), T(0.12, 230, 70, "sine", 0.35, 1.5)),
            "goo_boom": M(T(0.30, 260, 50, "saw", 0.45, 1.2, 0.4), T(0.18, 600, 100, "noise", 0.30, 2.0)),
            "bubble": M(T(0.06, 520, 950, "sine", 0.14, 2.0)),
            "spit": M(T(0.18, 900, 220, "noise", 0.25, 1.5), T(0.10, 420, 200, "sine", 0.30, 1.5)),
            "mine": M(T(0.05, 900, 900, "square", 0.16, 0.5), T(0.03, 1, 1, "sine", 0.0, 1.0),
                      T(0.05, 1300, 1300, "square", 0.16, 0.5)),
            "totem": M(T(0.09, 523, 523, "sine", 0.28, 1.0), T(0.09, 659, 659, "sine", 0.28, 1.0),
                       T(0.28, 784, 1047, "sine", 0.32, 1.4)),
        }

    def play(self, name, cd=0.0):
        if not (self.ok and self.enabled):
            return
        if cd:
            now = pygame.time.get_ticks() / 1000
            if now - self.last.get(name, -9) < cd:
                return
            self.last[name] = now
        self.snd[name].play()

    def hum(self, on):
        if not self.ok:
            return
        ch = pygame.mixer.Channel(0)
        if on and self.enabled:
            if not ch.get_busy():
                ch.play(self.snd["hum"], loops=-1)
        else:
            ch.stop()

    def charge(self, on):
        if not self.ok:
            return
        ch = pygame.mixer.Channel(1)
        if on and self.enabled:
            ch.play(self.snd["charge"])
        else:
            ch.stop()

    def stop_all(self):
        if self.ok:
            pygame.mixer.stop()

    def pause(self, on):
        if self.ok:
            (pygame.mixer.pause if on else pygame.mixer.unpause)()


# --------------------------------------------------------------------------- #
#  SAQLASH: oddiy akkaunt (faqat ism) - progress, rang, yutuqlar
# --------------------------------------------------------------------------- #
class Save:
    def __init__(self):
        base = os.environ.get("ANDROID_PRIVATE")
        if not base:
            try:
                base = os.path.dirname(os.path.abspath(__file__))
            except NameError:
                base = os.getcwd()
        self.path = os.path.join(base, "decycle_save.json")
        self.data = {"last": None, "accounts": {}}
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("accounts"), dict):
                self.data = d
        except Exception:
            pass
        if self.data.get("last") not in self.data["accounts"]:
            self.data["last"] = next(iter(self.data["accounts"]), None)

    def flush(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    @property
    def name(self):
        return self.data["last"]

    @property
    def acc(self):
        a = self.data["accounts"].get(self.name)
        return a if a is not None else dict(color=0, unlocked=1, clears={})

    def names(self):
        return list(self.data["accounts"])

    def create(self, name):
        self.data["accounts"].setdefault(name, dict(color=0, unlocked=1, clears={}))
        self.data["last"] = name
        self.flush()

    def delete(self, name):
        """Akkauntni (progress bilan birga) o'chiradi."""
        if name in self.data["accounts"]:
            del self.data["accounts"][name]
            if self.data.get("last") == name:
                self.data["last"] = next(iter(self.data["accounts"]), None)
            self.flush()

    def switch(self, name):
        if name in self.data["accounts"]:
            self.data["last"] = name
            self.flush()

    def color(self):
        i = max(0, min(len(COLORS) - 1, int(self.acc.get("color", 0))))
        return 0 if (i == TOTEM_IDX and not self.totem_open()) else i

    def has_ach(self, key):
        return key in self.acc.get("ach", [])

    def totem_open(self):
        return self.has_ach("survivor")

    def record_lasthit(self, boss_name):
        """LASTHIT'da boss yengildi. Ilk 4 bossning hammasi yengilsa 'survivor' beriladi (TOTEM kemasi ochiladi).
        Yangi achivka olinsa True qaytaradi."""
        if not self.name:
            return False
        a = self.acc
        lh = a.setdefault("lasthit", [])
        if boss_name not in lh:
            lh.append(boss_name)
        ach = a.setdefault("ach", [])
        new = False
        if "survivor" not in ach and all(b.name in lh for b in BOSSES[:SURVIVOR_BOSSES]):
            ach.append("survivor")
            new = True
        self.flush()
        return new

    def set_color(self, i):
        if self.name:
            self.acc["color"] = i
            self.flush()

    def unlocked(self):
        return int(self.acc.get("unlocked", 1))

    def best(self, boss_name):
        return self.acc.get("clears", {}).get(boss_name, -1)

    def record_win(self, idx, boss_name, diff_idx, total):
        if not self.name:
            return
        a = self.acc
        a["unlocked"] = max(int(a.get("unlocked", 1)), min(total, idx + 2))
        a.setdefault("clears", {})[boss_name] = max(a["clears"].get(boss_name, -1), diff_idx)
        self.flush()


# --------------------------------------------------------------------------- #
#  PLAYER: har bir o'yinchining holati. Yakka o'yinda bitta, multiplayerda ikkita.
# --------------------------------------------------------------------------- #
class Player:
    def __init__(self, g, idx, color, ang, direction):
        self.g, self.idx, self.color = g, idx, color
        self.ang, self.dir, self.halt, self.w = ang, direction, False, 0.0
        self.laser = False
        self.fire_cd = 0.0
        self.inv = 0.0
        self.combat_t = 0.0
        self.healing = False
        self.hp_max = PLAYER_HP
        self.hp = float(PLAYER_HP)
        self.poison = self.poison_tick = 0.0
        self.burn = self.burn_tick = 0.0
        self.slow = 0.0
        # multiplayer
        self.down = False            # yiqilgan (HP 0): jamoadoshi tiriltirishini kutyapti
        self.rev = 0.0               # tiriltirish progressi (soniya)
        self.reviving = False        # hozir jamoadoshni tiriltiryapti
        self.flips = []              # oxirgi yo'nalish almashtirishlar vaqti
        self.color2 = None           # ikkinchi rang (TOTEM kemasi qanotlari)

    @property
    def pos(self):
        return CX + math.cos(self.ang) * ORBIT_R, CY + math.sin(self.ang) * ORBIT_R

    def predict_ang(self, T, d=None):
        """T soniyadan keyingi burchak. d: yo'nalishni majburan berish (1, -1, 0)."""
        if d is None:
            d = 0 if self.halt else self.dir
        a, w = self.ang, self.w
        target = d * PLAYER_SPEED * (SLOW_FACTOR if self.slow > 0 else 1.0)
        steps = max(1, int(T / 0.016))
        dt = T / steps
        k = min(1.0, dt * 9)
        for _ in range(steps):
            w += (target - w) * k
            a += w * dt
        return a

    def lead(self, T, factor):
        return self.ang + (self.predict_ang(T) - self.ang) * factor

    # ---- yo'nalish / tiriltirish uchun "tez-tez bosish" ----
    def set_dir(self, d):
        if d != self.dir:
            self.dir = d
            self.flips.append(self.g.t)
            del self.flips[:-4]

    def wiggling(self):
        f = self.flips
        return len(f) >= 2 and self.g.t - f[-2] < WIGGLE_WIN

    # ---- zarar / effektlar ----   
    def hurt(self, dmg, inv=0.5, snd="hurt"):
           
        g = self.g
        if self.inv > 0 or self.down or g.result:
            return False
        if g.lasthit:
            dmg = max(dmg, self.hp)          # LASTHIT: har qanday zarba o'ldiradi
        self.hp -= dmg
        self.inv = inv
        self.combat_t = 0.0
        g.shake = max(g.shake, 0.10 + dmg / 30)
        g.au.play(snd)
        return True

    def apply_status(self, kind, dur):
        if kind == "poison":
            self.poison = max(self.poison, dur)
        elif kind == "burn":
            self.burn = max(self.burn, dur)
        elif kind == "slow":
            if self.slow <= 0:
                self.g.au.play("slow")
            self.slow = max(self.slow, dur)

    def step(self, dt, halt):
        """Effektlar (zahar/yonish/sekinlik) + harakat."""
        au = self.g.au
        if self.slow > 0:
            self.slow = max(0, self.slow - dt)
        if self.poison > 0:
            self.poison = max(0, self.poison - dt)
            self.poison_tick += dt
            while self.poison_tick >= 1.0:
                self.poison_tick -= 1.0
                self.hp = max(1.0, self.hp - 1)       # zahar o'ldirmaydi
                self.combat_t = 0.0
                au.play("tick")
        else:
            self.poison_tick = 0.0
        if self.burn > 0:
            self.burn = max(0, self.burn - dt)
            self.burn_tick += dt
            while self.burn_tick >= 1.0:
                self.burn_tick -= 1.0
                self.hp -= BURN_DMG                   # yonish o'ldira oladi
                self.combat_t = 0.0
                au.play("tick")
        else:
            self.burn_tick = 0.0

        speed = PLAYER_SPEED * (SLOW_FACTOR if self.slow > 0 else 1.0)
        self.halt = halt
        self.w += ((0 if halt else self.dir) * speed - self.w) * min(1, dt * 9)
        self.ang = (self.ang + self.w * dt) % TAU

    def heal(self, dt):
        was = self.healing
        self.healing = False
        if not self.laser:
            self.combat_t += dt
            if self.combat_t >= HEAL_DELAY and self.hp < self.hp_max:
                self.hp = min(self.hp_max, self.hp + HEAL_RATE * dt)
                self.healing = True
        if self.healing and not was:
            self.g.au.play("heal")

    def fall(self):
        self.hp = 0.0
        self.down = True
        self.laser = False
        self.rev = 0.0
        self.reviving = False
        self.healing = False
        self.poison = self.burn = self.slow = 0.0
        self.poison_tick = self.burn_tick = 0.0
        self.w = 0.0
        self.flips = []

    def revive(self):
        self.down = False
        self.hp = self.hp_max if self.hp_max <= 1 else self.hp_max * REVIVE_HP
        self.inv = REVIVE_INV
        self.rev = 0.0
        self.combat_t = 0.0


# --------------------------------------------------------------------------- #
#  GAME (bitta jang). Boss logikasi bosslar klasslarida (pastda)
# --------------------------------------------------------------------------- #
class Game:
    def __init__(self, diff_name, au, boss_cls, color, mp=False, lasthit=False, totem=False):
        self.au = au
        self.mp = mp
        self.diff_name = diff_name
        self.d = DIFFS[diff_name]
        self.t = 0.0
        self.shake = 0.0
        self.result = None

        if mp:
            self.players = [Player(self, 0, COLORS[MP_COLORS[0]], math.pi / 2 + 0.7, 1),
                            Player(self, 1, COLORS[MP_COLORS[1]], math.pi / 2 - 0.7, -1)]
        else:
            self.players = [Player(self, 0, color, math.pi / 2, 1)]
        self.tp = self.players[0]            # bosslar hozir nishonga olgan o'yinchi
        self.pick_hist = []                  # oxirgi 2 ta nishon (adolat uchun)

        self.lasthit = lasthit               # hardcore: bitta zarba = o'lim (yurakcha)
        self.totem = bool(totem) and not mp  # TOTEM kemasi: bir o'yinda bir marta qo'shimcha jon
        self.totem_used = False
        self.totem_fx = 0.0
        self.totem_pos = (CX, CY)
        if lasthit:
            for p in self.players:
                p.hp_max, p.hp = 1, 1.0
        if self.totem:
            self.players[0].color2 = TOTEM_COL2

        self.boss = boss_cls(self)
        self.boss_max = int(self.d["boss_hp"] * self.boss.hp_mult * (MP_BOSS_HP if mp else 1.0))
        self.boss_hp = float(self.boss_max)

        self.phase = 1
        self.flash = 0.0
        self.boss_idle = 0.0
        self.boss_healing = False

        self.proj = Pool(Proj, 256)
        self.shots = Pool(Shot, 64)
        self.fx = Pool(Fx, 220)

        self.gen = None
        self.wait = 1.6
        self.last_attack = None
        self.result_t = 0.0
        self.rewarded = False
        self.paused = False
        self.touch = False           # sensorli tugmalar ko'rinadimi (App belgilaydi)
        self.tflash = {}

    # ---- yordamchi: bosslar shu orqali "hozirgi nishon"ni ko'radi ----
    @property
    def ang(self):
        return self.tp.ang

    @property
    def dir(self):
        return self.tp.dir

    @property
    def pos(self):
        return self.tp.pos

    def predict_ang(self, T, d=None):
        return self.tp.predict_ang(T, d)

    def lead(self, T, factor):
        return self.tp.lead(T, factor)

    def alive(self):
        return [p for p in self.players if not p.down]

    def pick_target(self):
        """Aralash nishon tanlash: o'q otayotgan va tiriltirayotgan o'yinchi ko'proq e'tibor
        tortadi, lekin bir o'yinchiga ketma-ket 2 martadan ortiq tushmaydi."""
        alive = self.alive()
        if not alive:
            return
        if len(alive) == 1:
            self.tp = alive[0]
            return
        h = self.pick_hist
        if len(h) >= 2 and h[-1] == h[-2]:
            for p in alive:
                if p.idx != h[-1]:
                    self.tp = p
                    break
        else:
            w = [1.0 + (0.8 if p.laser else 0.0) + (0.6 if p.reviving else 0.0) for p in alive]
            r = random.random() * sum(w)
            self.tp = alive[-1]
            for p, wt in zip(alive, w):
                r -= wt
                if r <= 0:
                    self.tp = p
                    break
        h.append(self.tp.idx)
        del h[:-2]

    def side_target(self, k):
        """Ko'p qismli hujumlar uchun: k-qism k-o'yinchiga (ikkalasi tirik bo'lsa bo'linadi)."""
        alive = self.alive()
        if alive:
            self.tp = alive[k % len(alive)]
        return self.tp

    @property
    def rate(self):
        return self.d["rate"] * (PHASE2_RATE if self.phase == 2 else 1.0)

    @property
    def proj_speed(self):
        return self.d["speed"] * (PHASE2_SPEED if self.phase == 2 else 1.0)

    def spawn_vel(self, x, y, vx, vy, kind):
        p = self.proj.get()
        p.x, p.y, p.vx, p.vy = x, y, vx, vy
        p.r = PROJ_R[kind]
        p.kind = kind

    def spawn_proj(self, sx, sy, tx, ty, speed, kind):
        d = math.hypot(tx - sx, ty - sy) or 1
        s = speed * self.proj_speed
        self.spawn_vel(sx, sy, (tx - sx) / d * s, (ty - sy) / d * s, kind)

    def emit(self, x, y, vx, vy, life, r, col):
        if len(self.fx.live) > (80 if ANDROID else 150):
            return
        f = self.fx.get()
        f.x, f.y, f.vx, f.vy = x, y, vx, vy
        f.t, f.life, f.r, f.col = 0.0, life, r, col

    def meteor_fx(self, b):
        """Meteor izi (cho'g' zarralari) va orbitani kesib o'tganda uchqun."""
        sp = math.hypot(b.vx, b.vy) or 1
        ux, uy = b.vx / sp, b.vy / sp
        rnd = random.uniform
        for _ in range(1 if random.random() < 0.5 else 0):
            k = rnd(0, 12)
            self.emit(b.x - ux * k + rnd(-4, 4), b.y - uy * k + rnd(-4, 4),
                      -ux * rnd(20, 70) + rnd(-30, 30), -uy * rnd(20, 70) + rnd(-30, 30),
                      rnd(0.25, 0.5), rnd(3, 6), (255, 150, 50))
        if abs(math.hypot(b.x - CX, b.y - CY) - ORBIT_R) < 9:
            for _ in range(3):
                a, v = rnd(0, TAU), rnd(80, 200)
                self.emit(b.x, b.y, math.cos(a) * v, math.sin(a) * v, rnd(0.15, 0.3), rnd(2, 3.5), (255, 235, 160))

    def pick_attack(self):
        opts = self.boss.attacks()
        if self.last_attack in opts and len(opts) > 1:
            opts.remove(self.last_attack)
        f = random.choice(opts)
        self.last_attack = f
        return f()

    # ---- boshqaruv ----
    def toggle_laser(self, p):
        p.laser = not p.laser
        self.au.play("on" if p.laser else "off")

    def key(self, k):
        if self.result:
            return
        if not self.mp:
            p = self.players[0]
            if k == pygame.K_LEFT:
                p.set_dir(1)          # ekranda: pastda chapga
            elif k == pygame.K_RIGHT:
                p.set_dir(-1)
            elif k == pygame.K_x:
                self.toggle_laser(p)
            return
        p1, p2 = self.players
        if k == pygame.K_z and not p1.down:
            p1.set_dir(-p1.dir)       # 1-o'yinchi: bitta tugma yo'nalishni almashtiradi
        elif k == pygame.K_x and not p1.down:
            self.toggle_laser(p1)
        elif k == pygame.K_LEFT and not p2.down:
            p2.set_dir(1)
        elif k == pygame.K_RIGHT and not p2.down:
            p2.set_dir(-1)
        elif k == pygame.K_DOWN and not p2.down:
            self.toggle_laser(p2)

    # ---- sensorli boshqaruv (faqat yakka o'yin) ----
    TB_TURN = (W - 140, H - 140, 100)     # (x, y, radius) o'ngda: yo'nalishni almashtirish
    TB_FIRE = (140, H - 140, 100)         # chapda: o'q otishni yoqish/o'chirish
    TB_PAUSE = (W - 44, 44, 26)           # yuqori o'ng burchak

    @staticmethod
    def _hit(c, x, y, pad=0):
        return (x - c[0]) ** 2 + (y - c[1]) ** 2 <= (c[2] + pad) ** 2

    def touch_press(self, x, y):
        """Teginish. 'pause' qaytarsa App pauza menyusini ochadi."""
        if self.result or self.paused or self.mp:
            return None
        p = self.players[0]
        if self._hit(self.TB_TURN, x, y):
            p.set_dir(-p.dir)
            self.tflash["turn"] = 0.15
        elif self._hit(self.TB_FIRE, x, y):
            self.toggle_laser(p)
            self.tflash["fire"] = 0.15
        elif self._hit(self.TB_PAUSE, x, y, 14):
            return "pause"
        return None

    def draw_touch(self, s):
        p = self.players[0]
        x, y, r = self.TB_TURN
        s.blit(SPR["tb_turn"][(p.dir == 1, "turn" in self.tflash)], (x - r, y - r))
        x, y, r = self.TB_FIRE
        s.blit(SPR["tb_fire"][(p.laser, "fire" in self.tflash)], (x - r, y - r))
        x, y, r = self.TB_PAUSE
        s.blit(SPR["tb_pause"], (x - 28, y - 28))

    # ---- yangilash ----
    def update(self, dt):
        for k in list(self.tflash):
            self.tflash[k] -= dt
            if self.tflash[k] <= 0:
                del self.tflash[k]
        if self.paused:
            return
        self.t += dt
        self.flash = max(0, self.flash - dt)
        self.shake = max(0, self.shake - dt)
        self.totem_fx = max(0, self.totem_fx - dt)
        for p in self.players:
            p.inv = max(0, p.inv - dt)

        if self.result:
            self.result_t += dt
            self.proj.clear()
            self.shots.clear()
            self.fx.clear()
            self.boss.clear()
            return

        # harakat + effektlar (yakka o'yinda Z ushlab turilsa to'xtaydi)
        halt = (not self.mp) and pygame.key.get_pressed()[pygame.K_z]
        for p in self.players:
            if p.down:
                p.w = 0.0
            else:
                p.step(dt, halt)

        # faza 2
        if self.phase == 1 and self.boss_hp < self.boss_max * 0.5:
            self.phase = 2
            self.shake = 0.6
            self.flash = 0.4
            self.gen = None
            self.boss.clear()
            self.wait = 1.2
            self.au.play("phase2")

        # boss hujumi (har bir qadamda nishon qaytadan tanlanadi -> ko'p qismli hujumlar bo'linadi)
        if self.tp.down:
            self.pick_target()
        self.wait -= dt
        if self.wait <= 0 and self.t > 1.5:
            self.pick_target()
            if self.gen is None:
                self.gen = self.pick_attack()
            try:
                self.wait = next(self.gen)
            except StopIteration:
                self.gen = None
                self.wait = self.boss.gap[self.phase - 1] / self.rate

        # bizning o'qlar
        shooting = False
        for p in self.players:
            if p.laser and not p.down:
                shooting = True
                p.combat_t = 0.0
                p.fire_cd -= dt
                while p.fire_cd <= 0:
                    sh = self.shots.get()
                    sh.r, sh.a, sh.c = ORBIT_R - 16, p.ang, p.idx
                    p.fire_cd += FIRE_INTERVAL
                    self.au.play("shoot")
            else:
                p.fire_cd = 0.0
        hit_r = self.boss.hit_r
        for sh in self.shots.live:
            sh.r -= SHOT_SPEED * dt
            if self.boss.absorb(sh):
                sh.dead = True
                continue
            if sh.r <= hit_r:
                sh.dead = True
                self.boss_hp -= SHOT_DMG
                self.flash = 0.06
                self.au.play("hit", cd=0.12)
        self.shots.sweep()

        # dushman o'qlari
        for b in self.proj.live:
            b.x += b.vx * dt
            b.y += b.vy * dt
            if b.kind == "meteor":
                self.meteor_fx(b)
            for p in self.players:
                if p.down:
                    continue
                px, py = p.pos
                if math.hypot(b.x - px, b.y - py) < b.r + PLAYER_R:
                    dmg, inv, snd, st = HITS[b.kind]
                    if p.hurt(dmg, inv, snd):
                        if st:
                            p.apply_status(st[0], st[1])
                        b.dead = True
                        break
            if not (-80 < b.x < W + 80 and -80 < b.y < H + 80):
                b.dead = True
        self.proj.sweep()
        for f in self.fx.live:
            f.t += dt
            f.x += f.vx * dt
            f.y += f.vy * dt
            if f.t >= f.life:
                f.dead = True
        self.fx.sweep()

        # boss o'zining narsalari (lazer, til, yorilish...)
        self.boss.update(dt)

        # boss heal: hech kim hujum qilmayotganda
        self.boss_healing = False
        if shooting or self.shots.live:
            self.boss_idle = 0.0
        else:
            self.boss_idle += dt
            if self.boss_idle >= BOSS_HEAL_DELAY and self.boss_hp < self.boss_max:
                self.boss_hp = min(self.boss_max, self.boss_hp + self.boss_max * BOSS_HEAL_PCT * dt)
                self.boss_healing = True

        # o'yinchilarning o'z-o'zini davolashi
        for p in self.players:
            if not p.down:
                p.heal(dt)

        # yiqilish
        for p in self.players:
            if not p.down and p.hp <= 0:
                if self.totem and not self.totem_used:
                    # TOTEM: o'lim o'rniga HP to'liq tiklanadi (bir o'yinda bir marta)
                    self.totem_used = True
                    p.hp = p.hp_max
                    p.inv = TOTEM_LIFE_INV
                    p.poison = p.burn = p.slow = 0.0
                    p.poison_tick = p.burn_tick = 0.0
                    p.combat_t = 0.0
                    self.totem_fx = 1.4
                    self.totem_pos = p.pos
                    self.shake = max(self.shake, 0.5)
                    self.au.play("totem")
                    for i in range(28):
                        a, v = random.uniform(0, TAU), random.uniform(80, 300)
                        self.emit(p.pos[0], p.pos[1], math.cos(a) * v, math.sin(a) * v,
                                  random.uniform(0.4, 0.8), random.uniform(3, 6),
                                  (250, 225, 60) if i % 2 else TOTEM_COL2)
                    continue
                p.fall()
                if self.mp and any(not q.down for q in self.players):
                    self.shake = max(self.shake, 0.5)
                    self.au.play("hurt")

        # tiriltirish: jamoadosh yonida turib yo'nalishni tez-tez almashtirsa
        if self.mp:
            for p in self.players:
                p.reviving = False
            for p in self.players:
                if not p.down:
                    continue
                helped = False
                for q in self.players:
                    if q is p or q.down:
                        continue
                    if angdiff(q.ang, p.ang) < REVIVE_NEAR and q.wiggling():
                        helped = True
                        q.reviving = True
                if helped:
                    p.rev += dt
                    if p.rev >= REVIVE_TIME:
                        p.revive()
                        self.au.play("heal")
                else:
                    p.rev = max(0.0, p.rev - dt * REVIVE_DECAY)

        if self.boss_hp <= 0:
            self.boss_hp = 0
            self.result = "win"
            self.shake = 0.8
            self.boss.clear()
            self.au.play("win")
        elif all(p.down for p in self.players):
            self.result = "lose"
            self.shake = 0.8
            self.boss.clear()
            self.au.play("lose")

    # ---- chizish ----
    def draw(self, s, fonts):
        s.blit(SPR["bg_game" + ("_red" if self.lasthit else "") + ("_dim" if getattr(self.boss, "dim", False) else "")], (0, 0))
        px, py = (self.players[0] if not self.players[0].down else self.tp).pos   # ko'zlar asosiy o'yinchiga qaraydi

        self.boss.draw_body(s, px, py)
        self.boss.draw_hazards(s)
        self.boss.draw_front(s, px, py)

        for f in self.fx.live:                 # zarrachalar (meteor izi, uchqun)
            k = f.t / f.life
            c = f.col
            col = (int(c[0] * (1 - k) + 60 * k), int(c[1] * (1 - k) + 50 * k), int(c[2] * (1 - k) + 50 * k))
            pygame.draw.circle(s, col, (int(f.x), int(f.y)), max(1, int(f.r * (1 - 0.7 * k))))

        # dushman o'qlari
        for b in self.proj.live:
            x, y = int(b.x), int(b.y)
            k = b.kind
            if k in ("poison", "rock", "pebble", "meteor"):
                spr = SPR[k]
                if k == "meteor":
                    sp = math.hypot(b.vx, b.vy) or 1
                    ux, uy = b.vx / sp, b.vy / sp
                    for ln, wd, col in METEOR_TRAIL:
                        pygame.draw.line(s, col, (x - ux * ln, y - uy * ln), (x, y), wd)    # so'nuvchi iz
                    frames = SPR["meteor_rot"]
                    spr = frames[int((b.x + b.y) / 9) % len(frames)]                         # aylanib uchadi
                s.blit(spr, (x - spr.get_width() // 2, y - spr.get_height() // 2))
            else:
                c1, c2, ln, wd = BOLT_STYLE[k]
                sp = math.hypot(b.vx, b.vy) or 1
                tx, ty = x - b.vx / sp * ln, y - b.vy / sp * ln
                pygame.draw.line(s, c1, (x, y), (tx, ty), wd)
                pygame.draw.line(s, c2, (x, y), (tx, ty), 2)
                if k == "fire":
                    pygame.draw.circle(s, (255, 200, 80), (x, y), 5)

        # bizning o'qlar (multiplayerda egasining rangida)
        for sh in self.shots.live:
            c, sn = math.cos(sh.a), math.sin(sh.a)
            a = (CX + c * sh.r, CY + sn * sh.r)
            b2 = (CX + c * (sh.r + 18), CY + sn * (sh.r + 18))
            col = self.players[sh.c].color if self.mp else (90, 210, 255)
            pygame.draw.line(s, col, a, b2, 5)
            pygame.draw.line(s, (255, 255, 255), a, b2, 2)

        # kemalar (rangi o'zgarmaydi) + effekt halqalari
        for p in self.players:
            if p.down and not self.mp:
                continue
            qx, qy = p.pos
            d = math.hypot(qx - CX, qy - CY) or 1
            ux, uy = -(qx - CX) / d, -(qy - CY) / d
            c = (int(qx), int(qy))
            if p.down:
                draw_ship(s, qx, qy, ux, uy, (70, 74, 92))
                pygame.draw.circle(s, (60, 64, 90), c, 24, 2)
                if p.rev > 0:
                    frac = min(1.0, p.rev / REVIVE_TIME)
                    rect = pygame.Rect(c[0] - 24, c[1] - 24, 48, 48)
                    pygame.draw.arc(s, p.color, rect, math.pi / 2, math.pi / 2 + TAU * frac, 5)
            else:
                if not (p.inv > 0 and int(self.t * 20) % 2 == 0):
                    draw_ship(s, qx, qy, ux, uy, p.color, 1.0, p.color2)
                r = 19
                if p.poison > 0:
                    pygame.draw.circle(s, (90, 230, 90), c, r, 2)
                    r += 4
                if p.slow > 0:
                    pygame.draw.circle(s, (150, 175, 235), c, r, 2)
                    r += 4
                if p.burn > 0:
                    pygame.draw.circle(s, (255, 140 + int(60 * ((self.t * 12) % 1)), 40), c, r, 2)
            if self.mp:
                lab = txt(fonts[0], "P%d" % (p.idx + 1), p.color)
                s.blit(lab, (qx + (qx - CX) / d * 36 - lab.get_width() // 2,
                             qy + (qy - CY) / d * 36 - lab.get_height() // 2))

        if self.totem_fx > 0:                                   # TOTEM ishladi
            k = 1 - self.totem_fx / 1.4
            tx, ty = int(self.totem_pos[0]), int(self.totem_pos[1])
            pygame.draw.circle(s, TOTEM_COL2, (tx, ty), int(20 + 90 * k), max(1, int(6 * (1 - k))))
            pygame.draw.circle(s, (250, 225, 60), (tx, ty), int(10 + 60 * k), max(1, int(4 * (1 - k))))
            lab = txt(fonts[1], "TOTEM!", (250, 225, 60))
            s.blit(lab, (tx - lab.get_width() // 2, ty - 60 - int(30 * k)))

        self.boss.draw_overlay(s)
        self.draw_hud(s, fonts)
        if self.touch and not self.result and not self.mp:
            self.draw_touch(s)

    # ---- HUD ----
    def draw_hud(self, s, fonts):
        f_s = fonts[0]
        if self.mp:
            for p in self.players:
                x = 24 if p.idx == 0 else W - 24 - HP_W
                self.draw_hp(s, p, x, 20)
                self.draw_mp_tag(s, f_s, p, x)
                self.draw_effects(s, f_s, p, 24 if p.idx == 0 else W - 24 - 52, 88)
        else:
            p = self.players[0]
            self.draw_hp(s, p, 24, 20)
            if self.lasthit:
                s.blit(txt(f_s, "LASTHIT", (255, 60, 70)), (64, 26))
            if self.totem:
                self.draw_totem_icon(s, 144 if self.lasthit else 24 + HP_W + 12, 18)
            self.draw_effects(s, f_s, p, W - 24 - 52 - (76 if self.touch else 0), 20)

        bw = 520
        x0 = CX - bw // 2
        pygame.draw.rect(s, (40, 30, 60), (x0, 24, bw, 16))
        fill = int(bw * self.boss_hp / self.boss_max)
        pygame.draw.rect(s, self.boss.bar[1 if self.phase == 2 else 0], (x0, 24, fill, 16))
        if self.boss_healing:
            pulse = (math.sin(self.t * 10) + 1) / 2
            pygame.draw.rect(s, (int(120 + 60 * pulse), 255, int(120 + 60 * pulse)), (x0, 24, bw, 16), 2)
        else:
            pygame.draw.rect(s, (200, 200, 230), (x0, 24, bw, 16), 2)
        t = txt(f_s, self.boss.name, (220, 220, 240))
        s.blit(t, (CX - t.get_width() // 2, 46))

    def draw_totem_icon(self, s, x, y):
        used = self.totem_used
        a, b = ((70, 74, 92), (50, 54, 70)) if used else ((250, 225, 60), TOTEM_COL2)
        pygame.draw.rect(s, a, (x, y, 16, 24))
        pygame.draw.rect(s, b, (x, y + 8, 16, 6))
        pygame.draw.rect(s, (110, 114, 140) if used else (255, 255, 255), (x, y, 16, 24), 2)

    def draw_mp_tag(self, s, f_s, p, x):
        """HP chizig'i tagida: P1/P2 yozuvi, holat va tiriltirish progressi."""
        label = "P%d" % (p.idx + 1)
        col = p.color
        if p.down:
            label += "  YIQILDI"
        elif p.reviving:
            label += "  tiriltiryapti..."
        lt = txt(f_s, label, col)
        if self.lasthit:                                        # yurakcha yonida
            s.blit(lt, (x + 40, 26) if p.idx == 0 else (x + HP_W - 40 - lt.get_width(), 26))
        else:
            s.blit(lt, (x, 40))
        if p.down:
            y = 66
            pygame.draw.rect(s, (30, 34, 60), (x, y, HP_W, 8))
            fw = int(HP_W * min(1.0, p.rev / REVIVE_TIME))
            if fw > 0:
                pygame.draw.rect(s, col, (x, y, fw, 8))
            pygame.draw.rect(s, (150, 160, 200), (x, y, HP_W, 8), 1)

    def draw_hp(self, s, p, x, y):
        if self.lasthit:                                        # LASTHIT: health bar o'rniga yurakcha
            hx = x + 17 if p.idx == 0 else x + HP_W - 17
            if p.down:
                draw_heart(s, hx, y + 14, 0.95, (70, 74, 92), (110, 114, 140))
            else:
                draw_heart(s, hx, y + 14, 0.95 * (1.0 + 0.06 * math.sin(self.t * 6)), (255, 25, 40))
            return
        w, h = HP_W, HP_H
        pygame.draw.rect(s, (60, 0, 6), (x, y, w, h))
        n = int(p.hp_max)
        fw = int(w * max(0, p.hp) / p.hp_max)
        if fw > 0:
            pygame.draw.rect(s, (255, 25, 40), (x, y, fw, h))
            pygame.draw.rect(s, (255, 130, 130), (x, y, fw, 3))
        for i in range(1, n):
            xx = x + i * w // n
            pygame.draw.line(s, (40, 0, 4), (xx, y), (xx, y + h - 1))
        if p.healing:
            pulse = (math.sin(self.t * 12) + 1) / 2
            g = SPR["glow"]
            g.set_alpha(int(70 + 185 * pulse))
            s.blit(g, (x - HP_PAD, y - HP_PAD))
            c = int(140 + 115 * pulse)
            pygame.draw.rect(s, (255, c, c), (x, y, w, h), 2)
        else:
            pygame.draw.rect(s, (255, 190, 190), (x, y, w, h), 2)

    def draw_effects(self, s, f_s, p, x, y):
        effects = []
        if p.poison > 0:
            effects.append(("poison", p.poison))
        if p.burn > 0:
            effects.append(("burn", p.burn))
        if p.slow > 0:
            effects.append(("slow", p.slow))
        for kind, rem in effects:
            if not (rem < 1.0 and int(self.t * 8) % 2 == 0):
                border = {"poison": (90, 220, 90), "burn": (255, 140, 40), "slow": (130, 160, 215)}[kind]
                pygame.draw.rect(s, (25, 28, 40), (x, y, 52, 52))
                pygame.draw.rect(s, border, (x, y, 52, 52), 2)
                if kind == "poison":
                    pygame.draw.polygon(s, (110, 255, 110), [(x + 26, y + 8), (x + 16, y + 28), (x + 36, y + 28)])
                    pygame.draw.circle(s, (110, 255, 110), (x + 26, y + 31), 11)
                    pygame.draw.circle(s, (210, 255, 200), (x + 22, y + 28), 3)
                elif kind == "burn":
                    pygame.draw.polygon(s, (255, 130, 30), [(x + 26, y + 6), (x + 39, y + 30), (x + 33, y + 45),
                                                            (x + 19, y + 45), (x + 13, y + 30), (x + 22, y + 22)])
                    pygame.draw.polygon(s, (255, 225, 110), [(x + 26, y + 26), (x + 32, y + 38),
                                                             (x + 29, y + 45), (x + 23, y + 45), (x + 20, y + 38)])
                else:
                    pygame.draw.rect(s, (170, 200, 255), (x + 21, y + 9, 10, 17))
                    pygame.draw.polygon(s, (170, 200, 255), [(x + 11, y + 25), (x + 41, y + 25), (x + 26, y + 43)])
                sec = int(math.ceil(rem))
                tt = txt(f_s, "%d:%02d" % (sec // 60, sec % 60), (235, 235, 245))
                s.blit(tt, (x + 26 - tt.get_width() // 2, y + 55))
            y += 82


# --------------------------------------------------------------------------- #
#  BOSSLAR
#  Yangi boss: pastdagi namunalardan biriga qarab @register_boss bilan klass qo'shing.
#  Boss uchun kerakli narsalar: name, hp_mult, bar, attacks(), update(dt), clear(),
#  draw_body(), draw_hazards(), draw_front(). Qolganini (HP, effektlar, heal, ovoz,
#  menyu, saqlash) o'yin o'zi qiladi.
# --------------------------------------------------------------------------- #
BOSSES = []


def register_boss(cls):
    BOSSES.append(cls)
    return cls


class Rift:
    __slots__ = ("a", "t", "warn", "burst", "fade", "hit", "snd", "dead")

    def __init__(self):
        self.dead = True


class MWarn:
    """KRATUS: meteor kirishidan oldingi ogohlantirish (pool uchun)."""
    __slots__ = ("x", "y", "tx", "ty", "t", "life", "dead")

    def __init__(self):
        self.dead = True


class Fx:
    """Zarracha (meteor izi, uchqun). Pool orqali qayta ishlatiladi."""
    __slots__ = ("x", "y", "vx", "vy", "t", "life", "r", "col", "dead")

    def __init__(self):
        self.dead = True


class Boss:
    name = "BOSS"
    hp_mult = 1.0
    hit_r = BOSS_R                                   # bizning o'qlar shu radiusda to'xtaydi
    bar = ((170, 90, 240), (230, 70, 110))           # HP bar rangi (1-faza, 2-faza)
    gap = (1.5, 0.9)                                 # hujumdan hujumga tanaffus (1-faza, 2-faza), soniya

    def __init__(self, g):
        self.g = g

    def attacks(self):
        return []

    def update(self, dt):
        pass

    def clear(self):
        pass

    def draw_body(self, s, px, py):
        pass

    def draw_hazards(self, s):
        pass

    def draw_front(self, s, px, py):
        pass

    def draw_overlay(self, s):
        """Hamma narsaning ustidan, HUD tagida chiziladi (masalan GOOSMO shilimshig'i)."""
        pass

    def absorb(self, sh):
        """True bo'lsa bizning o'q (sh) boss tanasiga yetmay yo'q bo'ladi."""
        return False


class BeamMixin:
    """Qizil lazer mexanikasi (ALDEMO va LASSER uchun umumiy)."""
    beam = None
    beam_thin = 0.75        # birinchi nurdan boshqalarining ingichkaligi
    beam_min = BEAM_MIN     # aylanish tezligi oralig'i (rad/s)
    beam_max = BEAM_MAX
    beam_turn = 3.0         # yo'nalish/tezlik o'zgarishining tezligi
    beam_cols = ((150, 0, 20), (255, 50, 50), (255, 230, 230))     # tashqi / o'rta / ichki rang
    beam_warn_col = (255, 70, 70)

    def beam_origin(self, k):
        raise NotImplementedError

    def beam_start(self, n, a):
        g = self.g
        self.beam = dict(
            n=n, a=a % TAU, w=0.0,
            tw=random.choice([-1, 1]) * random.uniform(self.beam_min, self.beam_max),
            t=0.0, warn=BEAM_WARN, dur=10.0 if g.phase == 2 else 8.0,
            flip=random.uniform(1.2, 2.4), on=False)
        g.au.charge(True)

    def beam_end(self):
        self.beam = None
        self.g.au.hum(False)
        self.g.au.charge(False)

    def beam_update(self, dt):
        b = self.beam
        if not b:
            return
        g = self.g
        b["t"] += dt
        if b["t"] < b["warn"]:
            return
        if not b["on"]:
            b["on"] = True
            g.au.hum(True)
        b["flip"] -= dt
        if b["flip"] <= 0:
            b["flip"] = random.uniform(1.0, 2.4)
            cur = 1 if b["tw"] > 0 else -1
            sgn = -cur if random.random() < 0.6 else cur
            b["tw"] = sgn * random.uniform(self.beam_min, self.beam_max)
        b["w"] += (b["tw"] - b["w"]) * min(1, dt * self.beam_turn)
        b["a"] = (b["a"] + b["w"] * dt) % TAU
        for q in g.players:
            if q.down:
                continue
            px, py = q.pos
            for k in range(b["n"]):
                ox, oy, a = self.beam_origin(k)
                if seg_dist(px, py, ox, oy, ox + math.cos(a) * BEAM_LEN, oy + math.sin(a) * BEAM_LEN) < BEAM_HALF + PLAYER_R:
                    q.hurt(DMG_BEAM, 0.3)
                    break
        if b["t"] >= b["warn"] + b["dur"]:
            self.beam_end()

    def beam_draw(self, s):
        b = self.beam
        if not b:
            return
        for k in range(b["n"]):
            ox, oy, a = self.beam_origin(k)
            end = (ox + math.cos(a) * BEAM_LEN, oy + math.sin(a) * BEAM_LEN)
            o = (int(ox), int(oy))
            if b["t"] < b["warn"]:
                if int(b["t"] * 12) % 2 == 0:
                    pygame.draw.line(s, self.beam_warn_col, o, end, 2)
            else:
                ws = 1.0 if k == 0 else self.beam_thin
                for wd, col in zip((34, 20, 7), self.beam_cols):
                    wd = max(2, int(wd * ws))
                    pygame.draw.line(s, col, o, end, wd)
                    pygame.draw.circle(s, col, o, wd // 2)       # yumaloq boshlanish


# =========================================================================== #
#  1) ALDEMO - 3 ko'zli siyohrang alien
# =========================================================================== #
@register_boss
class Aldemo(BeamMixin, Boss):
    name = "ALDEMO"
    hp_mult = 1.0

    def __init__(self, g):
        super().__init__(g)
        self.tongues = Pool(Tongue, 8)
        self.eye_glow = {"L": 0.0, "R": 0.0}
        self.mouth_t = 0.0

    def attacks(self):
        return [self.atk_poison, self.atk_blue, self.atk_red, self.atk_tongue]

    def beam_origin(self, k):
        dx, dy, _ = EYES[BEAM_EYES[k]]
        return CX + dx, CY + dy, self.beam["a"] + k * TAU / self.beam["n"]

    # ---- hujumlar ----
    def atk_poison(self):
        """Zahar: qochish yo'llariga (davom etsa / orqaga qaytsa / to'xtasa) otadi."""
        g = self.g
        volleys = 5 if g.phase == 2 else 4
        n = 3 if g.phase == 2 else 3
        spread = 0.22
        speed = 250
        travel = (ORBIT_R - 40) / (speed * g.proj_speed)
        for _ in range(volleys):
            for d in (None, -g.dir, 0):
                base = g.predict_ang(travel, d)
                for i in range(n):
                    a = base + (i - (n - 1) / 2) * spread
                    tx, ty = orbit_pt(a)
                    g.spawn_proj(MOUTH[0], MOUTH[1], tx, ty, speed, "poison")
            self.mouth_t = 0.3
            g.au.play("poison_shot")
            yield 0.95 / g.rate
        yield 0.5

    def atk_blue(self):
        g = self.g
        dur = 3.6 if g.phase == 2 else 3.0
        t, step, side = 0.0, 0.2 / g.rate, "L"
        speed = 470
        travel = (ORBIT_R - 30) / (speed * g.proj_speed)
        while t < dur:
            ex, ey, _ = EYES[side]
            g.side_target(0 if side == "L" else 1)
            a = g.lead(travel, 0.97) + random.uniform(-0.08, 0.08)
            tx, ty = orbit_pt(a)
            g.spawn_proj(CX + ex, CY + ey, tx, ty, speed, "blue")
            self.eye_glow[side] = 0.15
            g.au.play("blue")
            side = "R" if side == "L" else "L"
            t += step
            yield step
        yield 0.5

    def atk_red(self):
        g = self.g
        n = 3 if g.phase == 2 else 1
        if n == 1:
            a = g.ang + random.choice([-1, 1]) * random.uniform(1.6, 2.6)
        else:
            a = g.ang + TAU / 6 + random.uniform(-0.12, 0.12)
        self.beam_start(n, a)
        while self.beam is not None:
            yield 0.1
        yield 0.5

    def atk_tongue(self):
        g = self.g
        n = 4 if g.phase == 2 else 3
        for _ in range(n):
            tg = self.tongues.get()
            tg.p = g.tp
            tg.a = g.lead(0.5, TONGUE_FACTOR)
            tg.t = 0.0
            tg.warn = 0.62 / min(g.rate, 1.3)
            tg.ext, tg.hold, tg.ret = 0.08, 0.25, 0.2
            tg.hit = 0
            tg.struck = False
            tg.err = random.uniform(-TONGUE_ERR, TONGUE_ERR)
            g.au.play("mouth")
            yield 1.15 / min(g.rate, 1.3)
        yield 0.6

    # ---- til geometriyasi ----
    @staticmethod
    def tongue_prog(tg):
        t = tg.t
        if t < tg.warn:
            return 0.0
        t -= tg.warn
        if t < tg.ext:
            return t / tg.ext
        t -= tg.ext
        if t < tg.hold:
            return 1.0
        t -= tg.hold
        if t < tg.ret:
            return 1.0 - t / tg.ret
        return -1.0

    @staticmethod
    def tongue_tip(tg, p):
        tx, ty = orbit_pt(tg.a)
        return (MOUTH[0] + (tx - MOUTH[0]) * 1.08 * p,
                MOUTH[1] + (ty - MOUTH[1]) * 1.08 * p)

    # ---- yangilash ----
    def update(self, dt):
        g = self.g
        self.mouth_t = max(0, self.mouth_t - dt)
        for k in self.eye_glow:
            self.eye_glow[k] = max(0, self.eye_glow[k] - dt)
        self.beam_update(dt)

        for tg in self.tongues.live:
            tg.t += dt
            if tg.t < tg.warn - TONGUE_LOCK:
                tg.a = (tg.p.lead(tg.warn - tg.t + tg.ext * 0.93, TONGUE_FACTOR) + tg.err) % TAU
            if not tg.struck and tg.t >= tg.warn:
                tg.struck = True
                g.au.play("strike")
            p = self.tongue_prog(tg)
            if p < 0:
                tg.dead = True
                continue
            if p > 0.3:
                tx, ty = self.tongue_tip(tg, p)
                for q in g.players:
                    if q.down or (tg.hit >> q.idx) & 1:
                        continue
                    qx, qy = q.pos
                    if seg_dist(qx, qy, MOUTH[0], MOUTH[1], tx, ty) < 12 + PLAYER_R:
                        if q.hurt(DMG_TONGUE, 0.8):
                            tg.hit |= 1 << q.idx
                            q.apply_status("slow", 3.0)
        self.tongues.sweep()

    def clear(self):
        self.tongues.clear()
        if self.beam:
            self.beam_end()

    # ---- chizish ----
    def _colors(self):
        g = self.g
        base = (112, 48, 178) if g.phase == 1 else (152, 38, 150)
        if g.flash > 0:
            base = tuple(min(255, c + 60) for c in base)
        return base, tuple(c // 3 for c in base)

    def draw_body(self, s, px, py):
        g = self.g
        base, dark = self._colors()
        pts = []
        for k in range(32):
            a = TAU * k / 32
            r = BOSS_R + math.sin(a * 5 + g.t * 2.2) * 3 + (5 if k % 4 == 0 else 0)
            pts.append((CX + math.cos(a) * r, CY + math.sin(a) * r))
        pygame.draw.polygon(s, base, pts)
        pygame.draw.polygon(s, dark, pts, 4)
        if self.mouth_t > 0 or self.tongues.live:
            pygame.draw.ellipse(s, (35, 5, 30), (CX - 24, CY + 32, 48, 22))
            if self.mouth_t > 0:
                pygame.draw.ellipse(s, (90, 255, 90), (CX - 12, CY + 38, 24, 10))
        else:
            pygame.draw.ellipse(s, (35, 5, 30), (CX - 22, CY + 38, 44, 7))

    def draw_hazards(self, s):
        self.beam_draw(s)
        for tg in self.tongues.live:
            p = self.tongue_prog(tg)
            if p > 0:
                tip = self.tongue_tip(tg, p)
                pygame.draw.line(s, (170, 30, 85), MOUTH, tip, 16)
                pygame.draw.line(s, (240, 90, 140), MOUTH, tip, 10)
                pygame.draw.circle(s, (240, 90, 140), (int(tip[0]), int(tip[1])), 11)

    def draw_front(self, s, px, py):
        g = self.g
        _, dark = self._colors()
        idle = (255, 200, 60) if g.phase == 1 else (255, 130, 60)
        beam_on = self.beam is not None
        triple = beam_on and self.beam["n"] == 3
        for key in ("L", "R", "C"):
            dx, dy, r = EYES[key]
            if key == "C":
                glow = beam_on
                iris = (255, 40, 40) if glow else idle
            elif triple:
                glow, iris = True, (255, 40, 40)
            else:
                glow = self.eye_glow[key] > 0
                iris = (80, 180, 255) if glow else idle
            draw_eye(s, CX + dx, CY + dy, r, px, py, iris, glow, dark)


# =========================================================================== #
#  2) KRATUS - toshli kulrang 2 ko'zli alien (2-fazada faqat hujumlar tezlashadi)
# =========================================================================== #
@register_boss
class Kratus(Boss):
    name = "KRATUS"
    hp_mult = 1.5
    bar = ((150, 150, 165), (150, 150, 165))
    gap = (0.3, 0.15)                        # juda tez: nafas olishga vaqt yo'q
    EYES2 = ((-26, -14, 16), (26, -14, 16))

    def __init__(self, g):
        super().__init__(g)
        self.rifts = Pool(Rift, 16)
        self.warns = Pool(MWarn, 8)
        self.mouth_t = 0.0
        self.eyes_closed = False
        rng = random.Random(11)
        self.shape = [BOSS_R * (0.88 + 0.2 * rng.random()) for _ in range(18)]
        self.cracks = [(rng.uniform(-40, 40), rng.uniform(-50, 10), rng.uniform(-50, 50), rng.uniform(10, 55))
                       for _ in range(5)]

    @property
    def dim(self):                                 # meteor yomg'iri paytida fon biroz qorayadi
        return self.eyes_closed

    def attacks(self):
        return [self.atk_rock, self.atk_storm, self.atk_meteors, self.atk_rift]

    # 1) Katta tosh: og'izdan 4 marta, nishonga olib
    def atk_rock(self):
        g = self.g
        speed = 400
        travel = (ORBIT_R - 40) / (speed * g.proj_speed)
        for _ in range(10):
            a = g.lead(travel, 0.9) + random.uniform(-0.08, 0.08)
            tx, ty = orbit_pt(a)
            g.spawn_proj(MOUTH[0], MOUTH[1], tx, ty, speed, "rock")
            self.mouth_t = 0.35
            g.au.play("rock")
            yield 0.5 / g.rate
        yield 0.1

    # 2) Tosh bo'roni: tasodifiy tomonlarga mayda toshlar (Slowness 2 soniya)
    def atk_storm(self):
        g = self.g
        dur = 3.6 if g.phase == 2 else 3.2
        step = 0.13 / g.rate
        t = 0.0
        while t < dur:
            a = g.ang + random.uniform(-1.0, 1.0) if random.random() < 0.3 else random.uniform(0, TAU)
            tx, ty = orbit_pt(a)
            g.spawn_proj(MOUTH[0], MOUTH[1], tx, ty, 340, "pebble")
            self.mouth_t = 0.15
            g.au.play("pebble", cd=0.05)
            t += step
            yield step
        yield 0.1

    # 3) Meteor yomg'iri (bullet hell): ko'z yumiladi, meteorlar ko'p va tez-tez keladi
    def atk_meteors(self):
        g = self.g
        self.eyes_closed = True
        dur, step = 5.5, 0.13 / g.rate               # step kichik = ko'proq meteor
        t, side = 0.0, random.choice([-1, 1])
        while t < dur:
            if random.random() < 0.6:
                side = -side
            x = -40 if side < 0 else W + 40
            y = random.uniform(40, H - 40)
            tx = CX + random.uniform(-0.9, 0.9) * ORBIT_R
            ty = CY + random.uniform(-0.9, 0.9) * ORBIT_R
            d = math.hypot(tx - x, ty - y) or 1
            sp = 330 * g.proj_speed
            g.spawn_vel(x, y, (tx - x) / d * sp, (ty - y) / d * sp, "meteor")
            g.au.play("meteor", cd=0.15)
            g.shake = max(g.shake, 0.07)
            t += step
            yield step
        self.eyes_closed = False
        yield 0.2

    # 4) Yorilish: orbitada belgi chiqadi, keyin tosh kattalashib otilib chiqadi
    def atk_rift(self):
        g = self.g
        waves = 4 if g.phase == 2 else 3
        for _ in range(waves):
            angs = [q.predict_ang(0.9) for q in g.alive()][:3]
            while len(angs) < 3:
                angs.append(random.uniform(0, TAU))
            for a in angs:
                r = self.rifts.get()
                r.a = a % TAU
                r.t = 0.0
                r.warn = 1.0 / min(g.rate, 1.4)
                r.burst, r.fade = 0.3, 0.5
                r.hit = 0
                r.snd = False
            g.au.play("rift_warn")
            yield 1.0 / g.rate
        yield 0.1

    def update(self, dt):
        g = self.g
        self.mouth_t = max(0, self.mouth_t - dt)
        for w in self.warns.live:                  # ogohlantirish tugagach meteor uchib keladi
            w.t += dt
            if w.t >= w.life:
                d = math.hypot(w.tx - w.x, w.ty - w.y) or 1
                sp = 330 * g.proj_speed
                g.spawn_vel(w.x, w.y, (w.tx - w.x) / d * sp, (w.ty - w.y) / d * sp, "meteor")
                g.au.play("meteor")
                g.shake = max(g.shake, 0.07)
                w.dead = True
        self.warns.sweep()
        for r in self.rifts.live:
            r.t += dt
            if r.t >= r.warn and not r.snd:
                r.snd = True
                g.au.play("rift")
                g.shake = max(g.shake, 0.15)
            if r.warn <= r.t < r.warn + r.burst:
                cx, cy = orbit_pt(r.a)
                for q in g.players:
                    if q.down or (r.hit >> q.idx) & 1:
                        continue
                    qx, qy = q.pos
                    if math.hypot(qx - cx, qy - cy) < RIFT_R + PLAYER_R:
                        if q.hurt(DMG_RIFT, 0.6):
                            r.hit |= 1 << q.idx
            if r.t >= r.warn + r.burst + r.fade:
                r.dead = True
        self.rifts.sweep()

    def clear(self):
        self.rifts.clear()
        self.warns.clear()
        self.eyes_closed = False

    def draw_body(self, s, px, py):
        g = self.g
        n = len(self.shape)
        pts = [(CX + math.cos(TAU * k / n) * r, CY + math.sin(TAU * k / n) * r) for k, r in enumerate(self.shape)]
        base = (168, 168, 178) if g.flash > 0 else (118, 118, 128)
        dark = (52, 52, 60)
        pygame.draw.polygon(s, base, pts)
        pygame.draw.polygon(s, dark, pts, 4)
        for x1, y1, x2, y2 in self.cracks:
            pygame.draw.line(s, dark, (CX + x1, CY + y1), (CX + x2, CY + y2), 2)
        if self.mouth_t > 0:
            pygame.draw.ellipse(s, (30, 20, 24), (CX - 26, CY + 30, 52, 26))
            pygame.draw.ellipse(s, (120, 60, 40), (CX - 14, CY + 38, 28, 10))
        else:
            pygame.draw.ellipse(s, (30, 20, 24), (CX - 22, CY + 36, 44, 8))

    def draw_hazards(self, s):
        for w in self.warns.live:                  # meteor ogohlantirishi: punktir yo'l + belgi
            dx, dy = w.tx - w.x, w.ty - w.y
            d = math.hypot(dx, dy) or 1
            ux, uy = dx / d, dy / d
            pulse = 0.5 + 0.5 * math.sin(w.t * 18)
            col = (255, 150 + int(70 * pulse), 60)
            for i in range(0, 1100, 30):
                x1, y1 = w.x + ux * i, w.y + uy * i
                if -20 < x1 < W + 20 and -20 < y1 < H + 20:
                    pygame.draw.line(s, col, (x1, y1), (x1 + ux * 14, y1 + uy * 14), 2)
            mx = 24 if w.x < 0 else W - 24
            my = max(28, min(H - 28, w.y))
            sz = 14 + int(4 * pulse)
            tri = [(mx, my - sz), (mx - sz, my + sz * 0.8), (mx + sz, my + sz * 0.8)]
            pygame.draw.polygon(s, col, tri)
            pygame.draw.polygon(s, (60, 20, 10), tri, 2)
            pygame.draw.line(s, (60, 20, 10), (mx, my - sz * 0.35), (mx, my + sz * 0.15), 3)
            pygame.draw.circle(s, (60, 20, 10), (mx, int(my + sz * 0.45)), 2)
        for r in self.rifts.live:
            cx, cy = orbit_pt(r.a)
            if r.t < r.warn:
                prog = r.t / r.warn
                if int(r.t * 10) % 2 == 0 or prog > 0.7:
                    pygame.draw.circle(s, (255, 120, 60), (int(cx), int(cy)), RIFT_R, 3)
                    pygame.draw.circle(s, (255, 190, 90), (int(cx), int(cy)), max(3, int(RIFT_R * prog)), 2)
            else:
                e = r.t - r.warn
                if e < r.burst:
                    scale = 0.3 + 0.7 * min(1.0, e / 0.12)
                else:
                    scale = max(0.0, 1.0 - (e - r.burst) / r.fade)
                col = (135, 135, 146) if e < r.burst else (92, 92, 102)
                rad = RIFT_R * scale
                pts = []
                for k in range(12):
                    a = TAU * k / 12
                    rr = rad * (1.0 if k % 2 == 0 else 0.62)
                    pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
                if rad > 2:
                    pygame.draw.polygon(s, col, pts)
                    pygame.draw.polygon(s, (45, 45, 54), pts, 3)

    def draw_front(self, s, px, py):
        for dx, dy, r in self.EYES2:
            if self.eyes_closed:
                rect = pygame.Rect(CX + dx - r, CY + dy - r // 2, 2 * r, r)
                pygame.draw.arc(s, (40, 40, 48), rect, math.pi, TAU, 4)
            else:
                draw_eye(s, CX + dx, CY + dy, r, px, py, (255, 170, 50), False, (52, 52, 60))


# =========================================================================== #
#  3) LASSER - 1 ko'zli uchburchak lazer boss
# =========================================================================== #
@register_boss
class Lasser(BeamMixin, Boss):
    """LASSER: aylanuvchi uchburchak. 2-fazada 3 ta kichik uchburchakka bo'linadi.
    Uchlari (1-faza) / yo'ldoshlari (2-faza) lazer va o'qlarni otadi."""
    name = "LASSER"
    hp_mult = 1.3
    bar = ((80, 170, 230), (80, 170, 230))
    gap = (0.9, 0.5)
    VR = 84                      # 1-faza: katta uchburchak uchlarining masofasi
    SAT_R = 140                  # 2-faza: yo'ldoshlar aylanadigan halqa radiusi
    IDLE_SPIN = 0.35             # tinch holatdagi aylanish tezligi (rad/s)
    beam_thin = 0.85
    beam_min = 1.4                                   # qizil lazer o'rniga KO'K lazer, tezroq
    beam_max = 1.8                                   # PLAYER_SPEED (1.9) dan oshmasin!
    beam_turn = 4.5
    beam_cols = ((10, 40, 130), (60, 140, 255), (225, 240, 255))
    beam_warn_col = (90, 160, 255)
    GREAT_WARN_BASE = 1.2        # katta nur: belgi vaqti = BASE + kerakli masofa / (tezlik * SPEED)
    GREAT_WARN_SPEED = 0.7       # (kichikroq = belgi uzunroq = osonroq)
    EMBER_R = 26                 # cho'g' radiusi
    EMBER_MAX = 6                # bir vaqtda ko'pi bilan nechta cho'g'

    def __init__(self, g):
        super().__init__(g)
        self.hit_r = 60                      # 2-fazada yadro kichrayadi
        self.great = None
        self.embers = Pool(Rift, 16)
        self.eye_glow = 0.0                  # olovli hujum
        self.vglow = 0.0                     # siyohrang hujum
        self.pod_flash = [0.0, 0.0, 0.0]
        self.rot = -math.pi / 2              # 0-uchning burchagi
        self.spin = self.IDLE_SPIN
        self.spin_v = self.IDLE_SPIN
        self.sp = 0.0                        # bo'linish progressi (0 -> 1)

    def attacks(self):
        return [self.atk_red, self.atk_tri, self.atk_great, self.atk_fire]

    # ---- geometriya ----
    @property
    def sat_r(self):
        return self.VR + (self.SAT_R - self.VR) * self.sp

    def pod_ang(self, k):
        return self.rot + k * TAU / 3

    def pod(self, k):
        a, r = self.pod_ang(k), self.sat_r
        return CX + math.cos(a) * r, CY + math.sin(a) * r

    def beam_origin(self, k):
        b = self.beam
        if b["n"] == 1:
            return CX, CY, b["a"]
        a = b["a"] + k * TAU / 3
        r = self.sat_r
        return CX + math.cos(a) * r, CY + math.sin(a) * r, a

    def tgt(self, k):
        """k-manba uchun nishon. 0-manba DOIM asosiy (1-) o'yinchiga, qolganlari bo'linadi."""
        g = self.g
        al = g.alive()
        if not al or (k == 0 and not g.players[0].down):
            return g.players[0]
        return al[k % len(al)]

    def spd(self, v):
        """O'q tezligi: orbitaga yetguncha kamida ~0.5 soniya ko'rinsin (adolat uchun)."""
        cap = max(150.0, (ORBIT_R - self.sat_r - 10) / 0.5)
        return min(v * self.g.proj_speed, cap)

    def shoot(self, x, y, tx, ty, speed, kind):
        d = math.hypot(tx - x, ty - y) or 1
        v = self.spd(speed)
        self.g.spawn_vel(x, y, (tx - x) / d * v, (ty - y) / d * v, kind)

    # 1) Qizil lazer: 1-fazada ko'zdan, 2-fazada 3 yo'ldoshdan. Tana nur bilan aylanadi
    def atk_red(self):
        g = self.g
        n = 3 if g.phase == 2 else 1
        al = g.alive() or g.players
        best, best_gap = 0.0, -1.0
        for _ in range(60):                       # hech bir o'yinchiga yaqin bo'lmagan boshlang'ich burchak
            a = random.uniform(0, TAU)
            gap = min(angdiff(a + k * TAU / n, q.ang) for k in range(n) for q in al)
            if gap > best_gap:
                best, best_gap = a, gap
        self.beam_start(n, best)
        q = self.tgt(0)                               # nur asosiy o'yinchi tomon aylanib boshlaydi
        near = min((best + k * TAU / n for k in range(n)), key=lambda a: angdiff(a, q.ang))
        diff = (q.ang - near + math.pi) % TAU - math.pi
        self.beam["tw"] = math.copysign(abs(self.beam["tw"]), diff or 1)
        while self.beam is not None:
            yield 0.1
        yield 0.2

    # 2) Trilaser: tana aylanib o'q yog'diradi, keyin uchburchak to'r (3 tomondan bir nuqtaga)
    def atk_tri(self):
        g = self.g
        sign = random.choice([-1, 1])
        self.spin = sign * 1.5
        t, step = 0.0, (0.17 if g.phase == 2 else 0.12) / g.rate
        offs = (-0.09, 0.09) if g.phase == 2 else (0.0,)
        while t < 2.6:                            # A) aylanuvchi yomg'ir
            for k in range(3):
                x, y = self.pod(k)
                va = self.pod_ang(k)
                for o in offs:
                    self.shoot(x, y, x + math.cos(va + o), y + math.sin(va + o), 380, "violet")
            self.vglow = 0.1
            g.au.play("violet", cd=0.06)
            if int(t / step) % 3 == 0:                # har 3-qadamda asosiy o'yinchiga nishonli o'q
                tx, ty = orbit_pt(self.tgt(0).lead(0.6, 0.95))
                self.shoot(CX, CY, tx, ty, 380, "violet")
            t += step
            yield step
        self.spin = -sign * 1.1                   # B) uchburchak to'r: uch uchdan bir vaqtda yetib keladi
        T = 0.95 / min(g.proj_speed, 1.4)
        for i in range(3):
            base = self.tgt(i).predict_ang(T)
            for off in (-0.17, 0.0, 0.17):
                tx, ty = orbit_pt(base + off)
                for k in range(3):
                    x, y = self.pod(k)
                    d = math.hypot(tx - x, ty - y) or 1
                    g.spawn_vel(x, y, (tx - x) / d * d / T, (ty - y) / d * d / T, "violet")
            self.vglow = 0.3
            g.au.play("rift_warn")
            yield 0.9 / g.rate
        self.spin = self.IDLE_SPIN
        yield 0.2

    # 3) Katta nur: yo'ldan "ov" (nishondagi yoy) yoki "xavfsiz yoy" (qolgan hammasi yonadi)
    def atk_great(self):
        g = self.g
        al = g.alive() or g.players
        if random.random() < 0.65:                                 # ov: turgan joyimizni egallaydi
            span = random.choice(GREAT_HUNT) * TAU
            c = self.tgt(0).lead(0.35, 0.7) % TAU
        else:                                                      # xavfsiz yoy: o'yinchilar unga sig'ishi kerak
            safe = random.choice(GREAT_SAFE) * TAU
            if len(al) > 1:
                sep = angdiff(al[0].ang, al[1].ang)
                safe = max(safe, sep + 0.7)
                mid = al[0].ang + ((al[1].ang - al[0].ang + math.pi) % TAU - math.pi) / 2
                sc = mid + random.uniform(-0.4, 0.4)
            else:
                sc = al[0].ang + random.choice([-1, 1]) * random.uniform(safe / 2 + 0.2, safe / 2 + 1.0)
            safe = min(safe, TAU * 0.7)
            span = TAU - safe
            c = (sc + math.pi) % TAU
        need = 0.0                                                 # qochish uchun kerakli masofa (rad)
        for q in al:
            d = angdiff(q.ang, c)
            if d < span / 2:
                need = max(need, span / 2 - d + 0.2)
        warn = self.GREAT_WARN_BASE + need / (PLAYER_SPEED * self.GREAT_WARN_SPEED)
        drift = random.choice([-1, 1]) * 0.3 if g.phase == 2 else 0.0
        self.great = dict(c=c, span=span, t=0.0, warn=warn, on=False, w=drift, ch2=False)
        g.au.charge(True)
        while self.great is not None:
            yield 0.1
        yield 0.3

    # 4) Olovli hujum: nishonli olovli lazerlar + orbitada yonib turadigan cho'g'lar
    def atk_fire(self):
        g = self.g
        waves = 4 if g.phase == 2 else 3
        for _ in range(waves):
            if len(self.embers.live) < self.EMBER_MAX:
                angs = [q.predict_ang(0.9) for q in g.alive()][:2] + [random.uniform(0, TAU)]
                for a in angs:
                    e = self.embers.get()
                    e.a, e.t = a % TAU, 0.0
                    e.warn, e.burst, e.fade = 0.8, 3.2, 0.5
                    e.hit, e.snd = 0, False
            self.fire_volley()
            yield 1.1 / g.rate
        yield 0.2

    def fire_volley(self):
        g = self.g
        if g.phase == 2:                          # har bir yo'ldosh o'z nishoniga
            for k in range(3):
                x, y = self.pod(k)
                v = self.spd(420)
                travel = max(0.3, (ORBIT_R - self.sat_r) / v)
                base = self.tgt(k).lead(travel, 0.95)
                for off in (-0.1, 0.1):
                    tx, ty = orbit_pt(base + off + random.uniform(-0.03, 0.03))
                    self.shoot(x, y, tx, ty, 420, "fire")
        else:
            travel = (ORBIT_R - 20) / self.spd(420)
            base = self.tgt(0).lead(travel, 0.95)
            for off in (-0.2, 0.0, 0.2):
                tx, ty = orbit_pt(base + off + random.uniform(-0.03, 0.03))
                self.shoot(CX, CY, tx, ty, 420, "fire")
        self.eye_glow = 0.2
        g.au.play("fire")

    # ---- yo'ldoshlar bizning o'qlarni to'sadi (faqat bo'lingandan keyin) ----
    def absorb(self, sh):
        if self.sp < 0.6:
            return False
        sr = self.sat_r
        if not (sr - 30 < sh.r <= sr + 8):
            return False
        w = 22 / sr
        for k in range(3):
            if angdiff(sh.a, self.pod_ang(k)) < w:
                self.pod_flash[k] = 0.1
                self.g.au.play("hit", cd=0.12)
                return True
        return False

    def end_great(self):
        self.great = None
        self.g.au.hum(False)
        self.g.au.charge(False)

    def update(self, dt):
        g = self.g
        self.eye_glow = max(0, self.eye_glow - dt)
        self.vglow = max(0, self.vglow - dt)
        for k in range(3):
            self.pod_flash[k] = max(0, self.pod_flash[k] - dt)

        if g.phase == 2 and self.sp < 1.0:                       # uchburchak 3 ga bo'linadi
            if self.sp == 0.0:
                g.au.play("rift")
                g.shake = max(g.shake, 0.4)
            self.sp = min(1.0, self.sp + dt / 1.2)
            self.hit_r = 60 - 22 * self.sp

        self.beam_update(dt)
        b = self.beam                                            # tana: lazer bilan yoki o'z tezligida aylanadi
        if b:
            if b["t"] < b["warn"]:
                d = (b["a"] - self.rot + math.pi) % TAU - math.pi
                self.rot += d * min(1, dt * 6)
            else:
                self.rot = b["a"]
            self.spin_v = 0.0
        else:
            tgt = 2.4 if (g.phase == 2 and self.sp < 1.0) else self.spin
            self.spin_v += (tgt - self.spin_v) * min(1, dt * 3)
            self.rot = (self.rot + self.spin_v * dt) % TAU

        gr = self.great
        if gr:
            gr["t"] += dt
            if not gr["ch2"] and gr["t"] >= gr["warn"] - 0.8:
                gr["ch2"] = True
                g.au.charge(True)                                # otishdan oldin yana zaryad ovozi
            if gr["t"] >= gr["warn"]:
                if not gr["on"]:
                    gr["on"] = True
                    g.au.hum(True)
                    g.au.play("great")
                    g.shake = max(g.shake, 0.25)
                gr["c"] = (gr["c"] + gr["w"] * dt) % TAU
                for q in g.players:
                    if not q.down and angdiff(q.ang, gr["c"]) < gr["span"] / 2:
                        q.hurt(DMG_GREAT, 0.6)
                if gr["t"] >= gr["warn"] + GREAT_TIME:
                    self.end_great()

        for e in self.embers.live:                               # cho'g'lar
            e.t += dt
            if e.t >= e.warn:
                if not e.snd:
                    e.snd = True
                    g.au.play("fire")
                if e.t < e.warn + e.burst:
                    cx, cy = orbit_pt(e.a)
                    for q in g.players:
                        if not q.down:
                            qx, qy = q.pos
                            if math.hypot(qx - cx, qy - cy) < self.EMBER_R + PLAYER_R:
                                q.apply_status("burn", 2.5)
            if e.t >= e.warn + e.burst + e.fade:
                e.dead = True
        self.embers.sweep()

    def clear(self):
        self.spin = self.IDLE_SPIN
        if self.beam:
            self.beam_end()
        if self.great:
            self.end_great()
        self.embers.clear()

    # ---- chizish ----
    def draw_body(self, s, px, py):
        g = self.g
        sp = self.sp
        base = (60, 110, 160) if g.flash > 0 else (36, 78, 120)
        if sp < 1.0:                                             # katta uchburchak (bo'linganda kichrayadi)
            kk = self.VR * (1.0 - 0.85 * sp)
            pts = [(CX + math.cos(self.pod_ang(i)) * kk, CY + math.sin(self.pod_ang(i)) * kk) for i in range(3)]
            pygame.draw.polygon(s, base, pts)
            pygame.draw.polygon(s, (14, 30, 50), pts, 5)
            inner = [(CX - (x - CX) * 0.5, CY - (y - CY) * 0.5) for x, y in pts]
            pygame.draw.polygon(s, (24, 52, 84), inner)
            pygame.draw.polygon(s, (14, 30, 50), inner, 3)
        if sp > 0:
            for k in range(3):
                pygame.draw.line(s, (28, 60, 96), (CX, CY), self.pod(k), 3)
            pygame.draw.circle(s, base, (CX, CY), int(14 + 22 * sp))
            pygame.draw.circle(s, (14, 30, 50), (CX, CY), int(14 + 22 * sp), 4)

    def draw_hazards(self, s):
        self.beam_draw(s)
        gr = self.great
        if gr:
            R, Ri = ORBIT_R + 45, 48
            c, half = gr["c"], gr["span"] / 2
            steps = max(8, int(gr["span"] / 0.08))
            ang = [c - half + gr["span"] * i / steps for i in range(steps + 1)]
            inner = [(CX + math.cos(a) * Ri, CY + math.sin(a) * Ri) for a in reversed(ang)]
            poly = [(CX + math.cos(a) * R, CY + math.sin(a) * R) for a in ang] + inner
            if gr["t"] < gr["warn"]:
                late = gr["warn"] - gr["t"] < 0.6                # otishga oz qoldi: yorqin miltillaydi
                blink = int(gr["t"] * 10) % 2 == 0
                fill = ((150, 30, 30) if blink else (90, 18, 20)) if late else (70, 12, 16)
                pygame.draw.polygon(s, fill, poly)
                pygame.draw.polygon(s, (255, 90, 70) if (blink or not late) else (170, 50, 40), poly, 3)
            else:
                pygame.draw.polygon(s, (210, 40, 40), poly)
                poly2 = [(CX + math.cos(a) * R * 0.85, CY + math.sin(a) * R * 0.85) for a in ang] + inner
                pygame.draw.polygon(s, (255, 150, 120), poly2)
                pygame.draw.polygon(s, (255, 235, 220), poly, 3)
            if gr["span"] > math.pi:                             # xavfsiz yoy yorqin ko'rsatiladi
                sc, sh = c + math.pi, (TAU - gr["span"]) / 2
                n2 = max(6, int(2 * sh / 0.08))
                pts = [(CX + math.cos(sc - sh + 2 * sh * i / n2) * (ORBIT_R + 30),
                        CY + math.sin(sc - sh + 2 * sh * i / n2) * (ORBIT_R + 30)) for i in range(n2 + 1)]
                pygame.draw.lines(s, (120, 255, 220), False, pts, 6)

        for e in self.embers.live:
            cx, cy = orbit_pt(e.a)
            if e.t < e.warn:
                if int(e.t * 12) % 2 == 0:
                    pygame.draw.circle(s, (255, 120, 40), (int(cx), int(cy)), self.EMBER_R, 2)
            else:
                k = e.t - e.warn
                scale = 1.0 if k < e.burst else max(0.0, 1.0 - (k - e.burst) / e.fade)
                r = self.EMBER_R * scale * (1 + 0.12 * math.sin(self.g.t * 14 + e.a * 5))
                if r > 2:
                    c = (int(cx), int(cy))
                    pygame.draw.circle(s, (190, 50, 10), c, int(r))
                    pygame.draw.circle(s, (255, 150, 40), c, int(r * 0.62))
                    pygame.draw.circle(s, (255, 230, 130), c, max(2, int(r * 0.28)))

    def draw_front(self, s, px, py):
        triple = self.beam is not None and self.beam["n"] == 3
        size = 14 + 12 * self.sp
        for k in range(3):                                       # uchlar / yo'ldoshlar
            x, y = self.pod(k)
            a = self.pod_ang(k)
            ux, uy = math.cos(a), math.sin(a)
            vx, vy = -uy, ux
            pts = [(x + ux * size, y + uy * size),
                   (x - ux * size * 0.7 + vx * size * 0.85, y - uy * size * 0.7 + vy * size * 0.85),
                   (x - ux * size * 0.7 - vx * size * 0.85, y - uy * size * 0.7 - vy * size * 0.85)]
            pygame.draw.polygon(s, (70, 120, 170) if self.pod_flash[k] > 0 else (36, 78, 120), pts)
            pygame.draw.polygon(s, (14, 30, 50), pts, 3)
            col = (90, 160, 255) if triple else ((190, 90, 255) if self.vglow > 0 else
                                                ((255, 150, 40) if self.eye_glow > 0 else (90, 190, 240)))
            pygame.draw.circle(s, col, (int(x + ux * size * 0.5), int(y + uy * size * 0.5)), 5)
        if self.great is not None:
            iris, glow = (255, 40, 40), True
        elif self.beam is not None:
            iris, glow = (70, 150, 255), True
        elif self.vglow > 0:
            iris, glow = (190, 90, 255), True
        elif self.eye_glow > 0:
            iris, glow = (255, 150, 40), True
        else:
            iris, glow = (110, 200, 255), False
        draw_eye(s, CX, CY + 4, 24, px, py, iris, glow, (14, 30, 50))


# =========================================================================== #
#  4) GOOSMO - yashil yopishqoq shilimshiq (bitta qop-qora ko'z, chiyillaydi)
#     1 SQUEK   - yopishqoq bomba (o'yinchiga yoki orbitaga yopishadi, 3 soniyada portlaydi)
#     2 STICKY  - turli tomonga shilliq oqimi (ko'lmak qoldiradi, sekinlashtiradi)
#     3 GOO     - ko'p sekin pufakchalar (tegsa ekranni shilimshiq bosadi)
#     4 POSTICK - tupuradi: orbitada dumalab quvlaydigan shilliq (yetay desa qochadi)
#     5 TIL     - yashil til (nishon aniqligi past)
# =========================================================================== #
class Goo:
    """GOOSMO snaryadi: squeak / sticky / bubble / spit. Pool uchun."""
    __slots__ = ("x", "y", "vx", "vy", "r", "kind", "t", "dead")

    def __init__(self):
        self.dead = True


class Bomb:
    """GOOSMO: yopishgan shilliq. p=None: orbitada turibdi; p=Player: o'yinchiga yopishgan."""
    __slots__ = ("x", "y", "t", "fuse", "p", "armed", "dead")

    def __init__(self):
        self.dead = True


class Puddle:
    """GOOSMO: orbitadagi shilliq ko'lmak (ustidan yursa sekinlashadi)."""
    __slots__ = ("x", "y", "t", "life", "dead")

    def __init__(self):
        self.dead = True


class Boom:
    """GOOSMO: portlash / yo'qolish effekti."""
    __slots__ = ("x", "y", "t", "big", "dead")

    def __init__(self):
        self.dead = True


GOO_KEY = (255, 0, 255)


def make_goo_screen(seed, scale=1.0):
    """Ekranga to'kilgan shilliq: ekranni to'liq yopmaydi, orasida shaffof joylar qoladi.
    Telefonda: shaffoflik o'rniga colorkey (juda tez chiziladi); scale - yo'qolish bosqichlari uchun."""
    rng = random.Random(seed)
    if ANDROID:
        sf = pygame.Surface((W, H))
        sf.fill(GOO_KEY)
    else:
        sf = pygame.Surface((W, H), pygame.SRCALPHA)

    def organic(cx, cy, rx, ry, n=16):
        return [(cx + math.cos(TAU * k / n) * rx * (0.78 + 0.34 * rng.random()),
                 cy + math.sin(TAU * k / n) * ry * (0.78 + 0.34 * rng.random())) for k in range(n)]

    for _ in range(9):
        cx, cy = rng.uniform(40, W - 40), rng.uniform(40, H - 40)
        rx, ry = rng.uniform(80, 210) * scale, rng.uniform(60, 150) * scale
        pygame.draw.polygon(sf, (36, 120, 38, 215), organic(cx, cy, rx, ry))
        pygame.draw.polygon(sf, (70, 185, 58, 205), organic(cx - rx * 0.06, cy - ry * 0.08, rx * 0.84, ry * 0.82))
        dl = rng.uniform(50, 150) * scale                           # oqib tushayotgan tomchi
        dx = cx + rng.uniform(-rx * 0.5, rx * 0.5)
        pygame.draw.line(sf, (70, 185, 58, 205), (dx, cy + ry * 0.4), (dx, cy + ry * 0.4 + dl), rng.randint(8, 16))
        pygame.draw.circle(sf, (70, 185, 58, 205), (int(dx), int(cy + ry * 0.4 + dl)), rng.randint(8, 14))
        pygame.draw.ellipse(sf, (190, 255, 170, 150),
                            (int(cx - rx * 0.5), int(cy - ry * 0.55), int(rx * 0.5), int(ry * 0.22)))
    for _ in range(40):                                              # sachragan tomchilar
        r = max(2, int(rng.randint(3, 11) * scale))
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        pygame.draw.circle(sf, (60, 170, 50, 210), (int(x), int(y)), r)
        pygame.draw.circle(sf, (200, 255, 180, 190), (int(x - r * 0.3), int(y - r * 0.3)), max(1, r // 3))
    if ANDROID:
        sf.set_colorkey(GOO_KEY, pygame.RLEACCEL)
    return sf


def build_goo_sprites():
    """GOOSMO sprite'lari: birinchi marta kerak bo'lganda bir marta yaratiladi."""
    S, A = pygame.Surface, pygame.SRCALPHA

    def blob(r, base, dark, hi):
        sf = S((2 * r + 4, 2 * r + 4), A)
        c = (r + 2, r + 2)
        pygame.draw.circle(sf, dark, c, r)
        pygame.draw.circle(sf, base, c, r - 2)
        pygame.draw.circle(sf, hi, (c[0] - r // 3, c[1] - r // 3), max(2, r // 3))
        return sf

    SPR["goo_blob"] = blob(14, (90, 215, 70), (25, 100, 30), (205, 255, 180))     # squek
    SPR["goo_spit"] = blob(18, (70, 190, 60), (20, 85, 28), (190, 255, 160))      # tupuruk
    bubbles = []
    for r in (9, 12, 15):                                                         # pufakchalar
        sf = S((2 * r + 4, 2 * r + 4), A)
        c = (r + 2, r + 2)
        pygame.draw.circle(sf, (90, 220, 80, 150), c, r)
        pygame.draw.circle(sf, (190, 255, 170, 230), c, r, 2)
        pygame.draw.circle(sf, (255, 255, 255, 220), (c[0] - r // 3, c[1] - r // 3), max(2, r // 4))
        bubbles.append(sf)
    SPR["goo_bubbles"] = bubbles
    R = CH_R                                                                      # dumalovchi shar
    frames = []
    for i in range(16):
        sf = S((2 * R + 4, 2 * R + 4), A)
        c = (R + 2, R + 2)
        pygame.draw.circle(sf, (22, 95, 30), c, R)
        pygame.draw.circle(sf, (80, 205, 65), c, R - 2)
        for k, (rho, sr) in enumerate(((0.55, 4), (0.50, 3), (0.60, 3), (0.45, 4))):
            a = i * TAU / 16 + k * TAU / 4
            pygame.draw.circle(sf, (40, 140, 45), (int(c[0] + math.cos(a) * R * rho), int(c[1] + math.sin(a) * R * rho)), sr)
        pygame.draw.circle(sf, (200, 255, 175), (c[0] - R // 3, c[1] - R // 3), max(2, R // 4))
        frames.append(sf)
    SPR["goo_roll"] = frames
    z = S((2 * GOO_BOMB_R + 4, 2 * GOO_BOMB_R + 4), A)                            # portlash zonasi
    pygame.draw.circle(z, (110, 230, 90, 70), (GOO_BOMB_R + 2, GOO_BOMB_R + 2), GOO_BOMB_R)
    SPR["goo_zone"] = z
    zones = {}                                                                    # rang bosqichi x miltillash (halqa ichiga chizilgan)
    for ci, col in enumerate(((120, 235, 70), (190, 205, 60), (255, 140, 50), (255, 60, 40))):
        for bright in (0, 1):
            zs = S((2 * GOO_BOMB_R + 4, 2 * GOO_BOMB_R + 4), A)
            pygame.draw.circle(zs, col + (140 if bright else 70,), (GOO_BOMB_R + 2, GOO_BOMB_R + 2), GOO_BOMB_R)
            pygame.draw.circle(zs, col + (255,), (GOO_BOMB_R + 2, GOO_BOMB_R + 2), GOO_BOMB_R, 3)
            zones[(ci, bright)] = zs
    SPR["goo_zone_set"] = zones
    fade = []                                                                     # portlash diski so'nishi (4 bosqich)
    for al in (200, 140, 80, 35):
        zf = S((2 * GOO_BOMB_R + 4, 2 * GOO_BOMB_R + 4), A)
        pygame.draw.circle(zf, (110, 230, 90, al), (GOO_BOMB_R + 2, GOO_BOMB_R + 2), GOO_BOMB_R)
        fade.append(zf)
    SPR["goo_zone_fade"] = fade
    seeds = (3, 17) if ANDROID else (3, 17, 29)
    SPR["goo_screen"] = [make_goo_screen(sd) for sd in seeds]                     # ekran shilimshig'i
    if ANDROID:                                                                   # yo'qolish bosqichlari (alpha o'rniga kichrayadi)
        SPR["goo_screen_fade"] = [[make_goo_screen(sd, 0.72), make_goo_screen(sd, 0.45)] for sd in seeds]


@register_boss
class Goosmo(Boss):
    name = "GOOSMO"
    hp_mult = 1.4
    bar = ((90, 210, 60), (190, 235, 40))
    gap = (1.1, 0.7)
    MOUTH_W = (28, 105, 36), (100, 225, 80)       # til: tashqi / ichki rang

    def __init__(self, g):
        super().__init__(g)
        if "goo_blob" not in SPR:
            build_goo_sprites()
        self.goo = Pool(Goo, 160)
        self.bombs = Pool(Bomb, 16)
        self.puddles = Pool(Puddle, 48)
        self.booms = Pool(Boom, 16)
        self.tongues = Pool(Tongue, 8)
        self.mouth_t = 0.0
        self.chase = None                 # POSTICK: dumalab quvlayotgan shilliq (dict) yoki None
        self.chase_pending = False        # tupuruk havoda
        self.trail_t = 0.0
        self.splat_t = 0.0                # ekran shilimshig'ining qolgan vaqti
        self.splat_age = 0.0
        self.splat_v = 0
        r7 = random.Random(7)             # portlashdagi sachragan tomchilar: (cos, sin, tezlik, o'lcham)
        self.burst = []
        for i in range(18):
            a = TAU * i / 18 + r7.uniform(-0.12, 0.12)
            self.burst.append((math.cos(a), math.sin(a), r7.uniform(0.65, 1.1), r7.randint(3, 7)))
        rng = random.Random(21)
        self.spots = []                   # tana ustidagi to'q dog'lar
        for _ in range(8):
            a, d = rng.uniform(0, TAU), rng.uniform(8, 48)
            self.spots.append((math.cos(a) * d, math.sin(a) * d, rng.randint(4, 9)))

    def attacks(self):
        opts = [self.atk_squeak, self.atk_sticky, self.atk_goo]
        if self.chase is None and not self.chase_pending:      # bir vaqtda faqat bitta quvlovchi
            opts.append(self.atk_postick)
        opts.append(self.atk_tongue)
        return opts

    # ---- yordamchi ----
    def shoot(self, tx, ty, speed, kind, r):
        """Og'izdan (tx, ty) tomon snaryad."""
        o = self.goo.get()
        d = math.hypot(tx - MOUTH[0], ty - MOUTH[1]) or 1
        v = speed * self.g.proj_speed
        o.x, o.y = MOUTH
        o.vx, o.vy = (tx - MOUTH[0]) / d * v, (ty - MOUTH[1]) / d * v
        o.r, o.kind, o.t = r, kind, 0.0

    def carrying(self, q):
        for b in self.bombs.live:
            if b.p is q:
                return True
        return False

    # ---- hujumlar ----
    def atk_squeak(self):
        """1) SQUEK: 4-5 ta tez-tez yopishqoq shilliq: juft raqamlilari nishonga, qolganlari tasodifiy."""
        g = self.g
        n = 5 if g.phase == 2 else 4
        speed = 360
        travel = (ORBIT_R - 30) / (speed * g.proj_speed)
        for i in range(n):
            if i % 2 == 0:
                a = g.lead(travel, 0.95) + random.uniform(-0.1, 0.1)
            else:
                a = random.uniform(0, TAU)
            tx, ty = orbit_pt(a)
            self.shoot(tx, ty, speed, "squeak", 10)
            self.mouth_t = 0.25
            g.au.play("squeak" if i % 2 == 0 else "squeak_hi")
            yield 0.32 / g.rate
        yield 0.6

    def atk_sticky(self):
        """2) STICKY: turli tomonlarga shilliq oqimi (+ bittasi o'yinchiga)."""
        g = self.g
        waves = 5 if g.phase == 2 else 4
        speed = 300
        travel = (ORBIT_R - 30) / (speed * g.proj_speed)
        for _ in range(waves):
            n = 7
            base = random.uniform(0, TAU)
            for i in range(n):
                tx, ty = orbit_pt(base + i * TAU / n + random.uniform(-0.12, 0.12))
                self.shoot(tx, ty, speed, "sticky", 7)
            tx, ty = orbit_pt(g.lead(travel, 0.9))
            self.shoot(tx, ty, speed, "sticky", 7)
            self.mouth_t = 0.3
            g.au.play("squeak_hi")
            yield 0.95 / g.rate
        yield 0.5

    def atk_goo(self):
        """3) GOO: atrofidan tasodifiy, ko'p va sekin pufakchalar (pattern yo'q)."""
        g = self.g
        dur = 5.0 if g.phase == 2 else 4.0
        step = 0.11 / g.rate
        t = 0.0
        while t < dur:
            for _ in range(2 if random.random() < 0.4 else 1):
                a = random.uniform(0, TAU)
                v = random.uniform(95, 170) * g.proj_speed
                o = self.goo.get()
                o.x, o.y = CX + math.cos(a) * (BOSS_R + 4), CY + math.sin(a) * (BOSS_R + 4)
                o.vx, o.vy = math.cos(a) * v, math.sin(a) * v
                o.r, o.kind, o.t = random.choice((9, 12, 15)), "bubble", 0.0
            g.au.play("bubble", cd=0.08)
            t += step
            yield step
        yield 0.6

    def atk_postick(self):
        """4) POSTICK: tupuradi. Tupuk orbitaga tushsa, 8 soniya quvlaydigan dumalab yuruvchi shilliqqa aylanadi."""
        g = self.g
        self.chase_pending = True
        speed = 420
        travel = (ORBIT_R - 30) / (speed * g.proj_speed)
        tx, ty = orbit_pt(g.lead(travel, 0.9))
        self.shoot(tx, ty, speed, "spit", 16)
        self.mouth_t = 0.45
        g.au.play("spit")
        yield 0.5

    def atk_tongue(self):
        """5) TIL: ALDEMOnikiga o'xshaydi, lekin yashil va nishoni noaniqroq."""
        g = self.g
        n = 4 if g.phase == 2 else 3
        for _ in range(n):
            tg = self.tongues.get()
            tg.p = g.tp
            tg.a = g.lead(0.5, GOO_TONGUE_FACTOR)
            tg.t = 0.0
            tg.warn = 0.62 / min(g.rate, 1.3)
            tg.ext, tg.hold, tg.ret = 0.08, 0.25, 0.2
            tg.hit = 0
            tg.struck = False
            tg.err = random.uniform(-GOO_TONGUE_ERR, GOO_TONGUE_ERR)
            g.au.play("mouth")
            yield 1.15 / min(g.rate, 1.3)
        yield 0.6

    tongue_prog = staticmethod(Aldemo.tongue_prog)
    tongue_tip = staticmethod(Aldemo.tongue_tip)

    def home(self, o, dt):
        """Squek o'qi: yo'lidagi (to'g'risidagi) o'yinchiga biroz magnit kabi buriladi.
        O'yinchi harakatda bo'lgani uchun uning hozirgi joyiga emas, yetib borish vaqtidagi joyiga buriladi."""
        sp = math.hypot(o.vx, o.vy)
        if sp < 1e-6:
            return
        ux, uy = o.vx / sp, o.vy / sp
        best, bl = None, 0.0
        for q in self.g.players:
            if q.down or self.carrying(q):
                continue
            qx, qy = q.pos
            fwd = (qx - o.x) * ux + (qy - o.y) * uy
            if fwd <= 0:                                     # orqada qoldi
                continue
            tx, ty = orbit_pt(q.predict_ang(fwd / sp))       # o'q yetganda o'yinchi turadigan joy
            ex, ey = tx - o.x, ty - o.y
            if ex * ux + ey * uy <= 0:
                continue
            lat = abs(ex * uy - ey * ux)                     # yo'ldan yon tomonga farq
            if lat < GOO_HOME_RANGE and (best is None or lat < bl):
                best, bl = (ex, ey), lat
        if best:
            av = math.atan2(o.vy, o.vx)
            diff = (math.atan2(best[1], best[0]) - av + math.pi) % TAU - math.pi
            av += max(-GOO_HOME_TURN * dt, min(GOO_HOME_TURN * dt, diff))
            o.vx, o.vy = math.cos(av) * sp, math.sin(av) * sp

    # ---- holatlar (yopishish, portlash, ko'lmak, ekran) ----
    def stick(self, q):
        """Squek o'yinchiga yopishdi."""
        b = self.bombs.get()
        b.p = q
        b.armed = False
        b.x, b.y = q.pos
        b.t, b.fuse = 0.0, GOO_BOMB_FUSE
        self.g.au.play("splat")

    def land(self, o):
        """Squek orbitaga yopishdi."""
        b = self.bombs.get()
        b.p = None
        b.armed = False
        b.x, b.y = orbit_pt(math.atan2(o.y - CY, o.x - CX))
        b.t, b.fuse = 0.0, GOO_BOMB_FUSE
        self.g.au.play("splat", cd=0.05)

    def puddle(self, o):
        pd = self.puddles.get()
        pd.x, pd.y = orbit_pt(math.atan2(o.y - CY, o.x - CX))
        pd.t, pd.life = 0.0, random.uniform(*GOO_PUDDLE_LIFE)

    def splat(self, o):
        """Pufakcha o'yinchiga tegdi: ekranni shilimshiq bosadi (2-3 soniya)."""
        if self.splat_t <= 0:
            self.splat_age = 0.0
            self.splat_v = random.randrange(len(SPR["goo_screen"]))
        self.splat_t = max(self.splat_t, random.uniform(2.0, 3.0))
        self.g.au.play("splat", cd=0.1)
        for _ in range(6):
            a, v = random.uniform(0, TAU), random.uniform(60, 150)
            self.g.emit(o.x, o.y, math.cos(a) * v, math.sin(a) * v, random.uniform(0.2, 0.4),
                        random.uniform(2, 4), (120, 235, 90))

    def explode(self, b):
        g = self.g
        carried = b.p is not None
        hit_any = False
        for q in g.players:
            if q.down:
                continue
            qx, qy = q.pos
            if math.hypot(qx - b.x, qy - b.y) < GOO_BOMB_R:
                hit_any = True
                if q.hurt(DMG_SQUEAK, 0.6, "hurt"):
                    q.apply_status("poison", 2.0)
        bm = self.booms.get()
        bm.x, bm.y, bm.t = b.x, b.y, 0.0
        bm.big = carried or hit_any
        if bm.big:
            g.au.play("goo_boom")
            g.shake = max(g.shake, 0.35)
            for i in range(24):
                a, v = random.uniform(0, TAU), random.uniform(90, 320)
                g.emit(b.x, b.y, math.cos(a) * v, math.sin(a) * v, random.uniform(0.3, 0.6),
                       random.uniform(3, 7), (120, 235, 90) if i % 3 else (210, 255, 170))
        else:
            g.au.play("bubble")
        b.dead = True

    def start_chase(self, o):
        """Tupuruk orbitaga tushdi: quvlovchi shilliq tug'iladi."""
        self.chase_pending = False
        self.chase = dict(a=math.atan2(o.y - CY, o.x - CX) % TAU, w=0.0, t=0.0, arm=0.7,
                          mode=0, ft=0.0, fd=1.0, rot=0.0)
        self.g.au.play("splat")

    def update_chase(self, dt):
        g = self.g
        c = self.chase
        c["t"] += dt
        c["arm"] = max(0.0, c["arm"] - dt)
        if c["t"] >= CH_TIME:
            self.end_chase(True)
            return
        al = g.alive()
        if al:
            q = min(al, key=lambda p: angdiff(p.ang, c["a"]))
            d = (q.ang - c["a"] + math.pi) % TAU - math.pi        # + : o'yinchi oldinda
            sgn = 1.0 if d >= 0 else -1.0
            k = 1.1 if g.phase == 2 else 1.0
            if c["mode"] == 0:                                    # quvlash
                tw = sgn * CH_SPEED * k
                closing = max(0.0, sgn * (c["w"] - q.w))          # yaqinlashish tezligi (rad/s)
                if abs(d) < CH_FLEE_DIST + CH_FLEE_LEAD * closing:    # yetay dedi: qarama-qarshi tomonga qochadi
                    c["mode"], c["ft"], c["fd"] = 1, CH_FLEE_TIME, -sgn
            else:                                                 # qochish
                if abs(d) < CH_FLEE_DIST * 1.6:
                    c["fd"] = -sgn
                tw = c["fd"] * CH_FLEE_SPEED
                c["ft"] -= dt
                if c["ft"] <= 0:
                    c["mode"] = 0
        else:
            tw = 0.0
        c["w"] += (tw - c["w"]) * min(1.0, dt * 7)
        c["a"] = (c["a"] + c["w"] * dt) % TAU
        c["rot"] = (c["rot"] + c["w"] * dt * ORBIT_R / CH_R) % TAU
        cx, cy = orbit_pt(c["a"])
        if c["arm"] <= 0:
            for q in g.players:
                if q.down:
                    continue
                qx, qy = q.pos
                if math.hypot(qx - cx, qy - cy) < CH_R + PLAYER_R - 2:
                    q.hurt(DMG_CHASE, 0.7, "hurt")
        self.trail_t -= dt
        if self.trail_t <= 0 and abs(c["w"]) > 0.8:
            self.trail_t = 0.05
            g.emit(cx, cy, random.uniform(-25, 25), random.uniform(-25, 25), 0.3, random.uniform(3, 5), (110, 230, 80))

    def end_chase(self, pop):
        c = self.chase
        if pop and c:
            cx, cy = orbit_pt(c["a"])
            for _ in range(10):
                a, v = random.uniform(0, TAU), random.uniform(60, 180)
                self.g.emit(cx, cy, math.cos(a) * v, math.sin(a) * v, random.uniform(0.2, 0.4),
                            random.uniform(3, 5), (110, 230, 80))
            self.g.au.play("bubble")
        self.chase = None

    # ---- yangilash ----
    def update(self, dt):
        g = self.g
        self.mouth_t = max(0, self.mouth_t - dt)
        if self.splat_t > 0:
            self.splat_t = max(0.0, self.splat_t - dt)
            self.splat_age += dt

        for o in self.goo.live:
            o.t += dt
            o.x += o.vx * dt
            o.y += o.vy * dt
            if not (-80 < o.x < W + 80 and -80 < o.y < H + 80):
                o.dead = True
                continue
            if o.kind == "bubble" and math.hypot(o.x - CX, o.y - CY) > ORBIT_R + 55:
                g.emit(o.x, o.y, random.uniform(-40, 40), random.uniform(-40, 40), 0.2, 2.5, (150, 240, 130))
                o.dead = True                  # orbitadan o'tgan pufakcha endi tegolmaydi: yengil "paq" bilan yo'qoladi
                continue
            k = o.kind
            if k == "bubble":
                if (o.x - CX) ** 2 + (o.y - CY) ** 2 > (ORBIT_R + 60) ** 2:    # orbitadan uzoqda hech kimga tegmaydi: yorilib yo'qoladi
                    for _ in range(2):
                        a, v = random.uniform(0, TAU), random.uniform(30, 90)
                        g.emit(o.x, o.y, math.cos(a) * v, math.sin(a) * v, 0.25, 2.5, (150, 240, 130))
                    o.dead = True
                    continue
                for q in g.players:
                    if q.down:
                        continue
                    qx, qy = q.pos
                    if math.hypot(o.x - qx, o.y - qy) < o.r + PLAYER_R:
                        if DMG_BUBBLE:
                            q.hurt(DMG_BUBBLE, 0.3, "light")
                        self.splat(o)
                        o.dead = True
                        break
            elif k == "squeak":
                self.home(o, dt)
                for q in g.players:
                    if q.down or self.carrying(q):
                        continue
                    qx, qy = q.pos
                    if math.hypot(o.x - qx, o.y - qy) < o.r + PLAYER_R + GOO_STICK_PAD:
                        self.stick(q)
                        o.dead = True
                        break
                if not o.dead and math.hypot(o.x - CX, o.y - CY) >= ORBIT_R:
                    self.land(o)
                    o.dead = True
            elif k == "sticky":
                for q in g.players:
                    if q.down:
                        continue
                    qx, qy = q.pos
                    if math.hypot(o.x - qx, o.y - qy) < o.r + PLAYER_R:
                        if q.hurt(DMG_STICKY, 0.4, "light"):
                            q.apply_status("slow", GOO_SLOW)
                        o.dead = True
                        break
                if not o.dead and math.hypot(o.x - CX, o.y - CY) >= ORBIT_R:
                    self.puddle(o)
                    o.dead = True
            elif k == "spit":
                if math.hypot(o.x - CX, o.y - CY) >= ORBIT_R:
                    self.start_chase(o)
                    o.dead = True
        self.goo.sweep()

        for b in self.bombs.live:
            b.t += dt
            if b.p is not None:
                b.x, b.y = b.p.pos
            elif not b.armed:                                  # orbitadagi squek: ustidan o'tsa mina kabi ishga tushadi
                for q in g.players:
                    if q.down:
                        continue
                    qx, qy = q.pos
                    if math.hypot(qx - b.x, qy - b.y) < GOO_MINE_R:
                        b.armed = True
                        b.fuse = min(b.fuse, b.t + GOO_MINE_FUSE)     # qochish uchun 0.5 soniya
                        g.au.play("mine")
                        break
            if b.t >= b.fuse:
                self.explode(b)
        self.bombs.sweep()

        for pd in self.puddles.live:
            pd.t += dt
            if pd.t >= pd.life:
                pd.dead = True
                continue
            for q in g.players:
                if q.down:
                    continue
                qx, qy = q.pos
                if math.hypot(qx - pd.x, qy - pd.y) < GOO_PUDDLE_R + PLAYER_R * 0.6:
                    q.apply_status("slow", GOO_SLOW)
        self.puddles.sweep()

        for bm in self.booms.live:
            bm.t += dt
            if bm.t >= GOO_BOOM_T:
                bm.dead = True
        self.booms.sweep()

        if self.chase:
            self.update_chase(dt)

        for tg in self.tongues.live:
            tg.t += dt
            if tg.t < tg.warn - TONGUE_LOCK:
                tg.a = (tg.p.lead(tg.warn - tg.t + tg.ext * 0.93, GOO_TONGUE_FACTOR) + tg.err) % TAU
            if not tg.struck and tg.t >= tg.warn:
                tg.struck = True
                g.au.play("strike")
            p = self.tongue_prog(tg)
            if p < 0:
                tg.dead = True
                continue
            if p > 0.3:
                tx, ty = self.tongue_tip(tg, p)
                for q in g.players:
                    if q.down or (tg.hit >> q.idx) & 1:
                        continue
                    qx, qy = q.pos
                    if seg_dist(qx, qy, MOUTH[0], MOUTH[1], tx, ty) < 12 + PLAYER_R:
                        if q.hurt(DMG_TONGUE, 0.8):
                            tg.hit |= 1 << q.idx
                            q.apply_status("slow", 3.0)
        self.tongues.sweep()

    def clear(self):
        self.goo.clear()
        self.bombs.clear()
        self.puddles.clear()
        self.booms.clear()
        self.tongues.clear()
        self.chase = None
        self.chase_pending = False
        self.splat_t = 0.0

    # ---- chizish ----
    def _colors(self):
        g = self.g
        base = (86, 196, 70) if g.phase == 1 else (136, 206, 48)
        if g.flash > 0:
            base = tuple(min(255, c + 55) for c in base)
        return base, (base[0] // 3, base[1] // 2, base[2] // 3)

    def draw_body(self, s, px, py):
        g = self.g
        base, dark = self._colors()
        pts = []
        for k in range(40):
            a = TAU * k / 40
            r = BOSS_R + math.sin(a * 5 + g.t * 2.6) * 3 + math.sin(a * 3 - g.t * 1.7) * 2.5
            pts.append((CX + math.cos(a) * r, CY + math.sin(a) * r))
        pygame.draw.polygon(s, base, pts)
        pygame.draw.polygon(s, dark, pts, 4)
        light = tuple(min(255, c + 22) for c in base)
        pygame.draw.polygon(s, light, [(CX - 3 + (x - CX) * 0.86, CY - 5 + (y - CY) * 0.86) for x, y in pts])
        spot = tuple(max(0, c - 28) for c in base)
        for dx, dy, r in self.spots:
            pygame.draw.circle(s, spot, (int(CX + dx), int(CY + dy)), r)
        pygame.draw.ellipse(s, (205, 255, 180), (CX - 48, CY - 54, 30, 14))            # yaltiroq
        for k, dx in enumerate((-34, 2, 36)):                                           # tomayotgan shilliq
            ln = 12 + 8 * math.sin(g.t * 1.6 + k * 2.1)
            y0 = CY + BOSS_R - 6
            pygame.draw.line(s, base, (CX + dx, y0), (CX + dx, y0 + ln), 7)
            pygame.draw.circle(s, base, (CX + dx, int(y0 + ln)), 5)
        if g.phase == 2:                                                                # 2-faza: qaynayotgan pufakchalar
            for k in range(5):
                a = k * 1.3 + g.t * 0.8
                pygame.draw.circle(s, (210, 255, 150), (int(CX + math.cos(a) * 36), int(CY + math.sin(a * 1.3) * 28)),
                                   int(4 + 2 * math.sin(g.t * 5 + k)), 2)
        mouth_dark = (14, 50, 18)
        if self.mouth_t > 0 or self.tongues.live:
            pygame.draw.ellipse(s, mouth_dark, (CX - 24, CY + 32, 48, 22))
            if self.mouth_t > 0:
                pygame.draw.ellipse(s, (130, 240, 100), (CX - 12, CY + 38, 24, 10))
        else:
            pygame.draw.ellipse(s, mouth_dark, (CX - 22, CY + 38, 44, 7))

    def draw_hazards(self, s):
        g = self.g
        for pd in self.puddles.live:                                  # ko'lmaklar
            k = pd.t / pd.life
            fade = 1.0 if k < 0.75 else max(0.0, (1.0 - k) / 0.25)
            r = int(GOO_PUDDLE_R * (0.55 + 0.45 * min(1.0, pd.t / 0.15)) * (0.4 + 0.6 * fade))
            c = (int(pd.x), int(pd.y))
            pygame.draw.circle(s, (30, 110, 36), c, r + 2)
            pygame.draw.circle(s, (88, 205, 72), c, r)
            pygame.draw.circle(s, (88, 205, 72), (c[0] + int(r * 0.8), c[1] - int(r * 0.2)), max(2, r // 3))
            pygame.draw.circle(s, (88, 205, 72), (c[0] - int(r * 0.7), c[1] + int(r * 0.3)), max(2, r // 4))
            pygame.draw.circle(s, (170, 250, 150), (c[0] - int(r * 0.3), c[1] - int(r * 0.3)), max(2, r // 4))

        for b in self.bombs.live:                                     # bombalar + portlash radiusi
            if b.armed:                                           # mina ishga tushdi: qizarib tez yonadi
                prog = 1.0 - max(0.0, b.fuse - b.t) / GOO_MINE_FUSE
                col = (255, int(120 - 90 * prog), 50)
            else:
                prog = min(1.0, b.t / b.fuse)
                col = (int(120 + 130 * prog), int(235 - 150 * prog), 70)
            c = (int(b.x), int(b.y))
            ci = (3 if prog > 0.5 else 2) if b.armed else min(2, int(prog * 3))
            z = SPR["goo_zone_set"][(ci, 1 if math.sin(b.t * (6 + 24 * prog)) > 0 else 0)]
            s.blit(z, (c[0] - GOO_BOMB_R - 2, c[1] - GOO_BOMB_R - 2))
            pygame.draw.circle(s, (200, 255, 160), c, max(3, int(GOO_BOMB_R * prog)), 1)
            ox = oy = 0
            if b.p is not None:                                       # kema ustida emas, tashqarisida ko'rinsin
                d = math.hypot(b.x - CX, b.y - CY) or 1
                ox, oy = (b.x - CX) / d * 12, (b.y - CY) / d * 12
            spr = SPR["goo_blob"]
            s.blit(spr, (int(c[0] + ox) - spr.get_width() // 2, int(c[1] + oy) - spr.get_height() // 2))
            pygame.draw.circle(s, col, (int(c[0] + ox), int(c[1] + oy)), 15 + int(3 * prog), 2)

        o_col, i_col = self.MOUTH_W
        for tg in self.tongues.live:                                  # yashil til
            p = self.tongue_prog(tg)
            if p > 0:
                tip = self.tongue_tip(tg, p)
                pygame.draw.line(s, o_col, MOUTH, tip, 18)
                pygame.draw.line(s, i_col, MOUTH, tip, 11)
                for f in (0.3, 0.55, 0.8):
                    pygame.draw.circle(s, (170, 250, 150), (int(MOUTH[0] + (tip[0] - MOUTH[0]) * f),
                                                            int(MOUTH[1] + (tip[1] - MOUTH[1]) * f)), 3)
                pygame.draw.circle(s, o_col, (int(tip[0]), int(tip[1])), 13)
                pygame.draw.circle(s, i_col, (int(tip[0]), int(tip[1])), 10)

        c = self.chase                                                # dumalovchi shilliq
        if c and not (c["arm"] > 0 and int(g.t * 16) % 2 == 0):
            x, y = orbit_pt(c["a"])
            fr = SPR["goo_roll"][int(c["rot"] / TAU * 16) % 16]
            s.blit(fr, (int(x) - fr.get_width() // 2, int(y) - fr.get_height() // 2))

        for o in self.goo.live:                                       # snaryadlar
            x, y = int(o.x), int(o.y)
            k = o.kind
            if k == "bubble":
                spr = SPR["goo_bubbles"][0 if o.r < 11 else (1 if o.r < 14 else 2)]
                s.blit(spr, (x - spr.get_width() // 2 + int(2 * math.sin(o.t * 6 + o.x * 0.05)),
                             y - spr.get_height() // 2))
                continue
            sp = math.hypot(o.vx, o.vy) or 1
            ux, uy = o.vx / sp, o.vy / sp
            if k == "sticky":
                pygame.draw.line(s, (28, 105, 36), (x, y), (x - ux * 22, y - uy * 22), 10)
                pygame.draw.line(s, (140, 245, 110), (x, y), (x - ux * 22, y - uy * 22), 4)
                pygame.draw.circle(s, (100, 225, 80), (x, y), 6)
            else:                                                     # squeak / spit
                pygame.draw.line(s, (60, 160, 50), (x, y), (x - ux * 20, y - uy * 20), 8)
                spr = SPR["goo_spit" if k == "spit" else "goo_blob"]
                s.blit(spr, (x - spr.get_width() // 2, y - spr.get_height() // 2))

        for bm in self.booms.live:                                    # portlash effekti
            k = bm.t / GOO_BOOM_T
            c0 = (int(bm.x), int(bm.y))
            if bm.big:
                e = 1.0 - (1.0 - min(1.0, k * 1.8)) ** 2          # tez ochilib, sekinlashadi
                rad = int(GOO_BOMB_R * (0.25 + 0.75 * e))
                z = SPR["goo_zone_fade"][min(3, int(k * 4))]      # yashil disk asta so'nadi
                s.blit(z, (c0[0] - GOO_BOMB_R - 2, c0[1] - GOO_BOMB_R - 2))
                if k < 0.2:                                       # yarqin yadro
                    pygame.draw.circle(s, (235, 255, 210), c0, int(GOO_BOMB_R * 0.5 * (1 - k / 0.2)) + 8)
                star = []                                         # tikanli shilliq "splat"
                for i in range(18):
                    a = i * TAU / 18 + bm.x * 0.013
                    r = rad * (1.0 if i % 2 == 0 else 0.7)
                    star.append((c0[0] + math.cos(a) * r, c0[1] + math.sin(a) * r))
                pygame.draw.polygon(s, (150, 255, 110), star, max(1, int(6 * (1 - k))))
                pygame.draw.circle(s, (230, 255, 200), c0, int(rad * 0.7), max(1, int(3 * (1 - k))))
                for dx, dy, sp, sz in self.burst:                 # sachragan tomchilar
                    d = GOO_BOMB_R * 1.25 * sp * e
                    qx, qy = c0[0] + dx * d, c0[1] + dy * d
                    rr = max(1, int(sz * (1 - 0.8 * k)))
                    pygame.draw.line(s, (60, 170, 50), (qx - dx * 12, qy - dy * 12), (qx, qy), rr)
                    pygame.draw.circle(s, (110, 235, 90), (int(qx), int(qy)), rr)
            else:
                pygame.draw.circle(s, (150, 230, 120), c0, max(2, int(22 * (1 - k))), 2)

    def draw_front(self, s, px, py):
        ex, ey, r = CX, CY - 12, 25                                   # bitta qop-qora ko'z
        _, dark = self._colors()
        d = math.hypot(px - ex, py - ey) or 1
        gx, gy = (px - ex) / d * r * 0.32, (py - ey) / d * r * 0.32   # yaltiroq nishonga qaraydi
        pygame.draw.circle(s, dark, (ex, ey), r + 4)
        pygame.draw.circle(s, (6, 8, 6), (ex, ey), r)
        pygame.draw.circle(s, (235, 255, 235), (int(ex + gx - 6), int(ey + gy - 7)), 6)
        pygame.draw.circle(s, (200, 245, 200), (int(ex + gx + 7), int(ey + gy + 6)), 3)

    def draw_overlay(self, s):
        """Ekranga to'kilgan shilimshiq (pufakcha tekkanda): HUD tagida, hamma narsaning ustida."""
        if self.splat_t <= 0:
            return
        if ANDROID:                       # telefonda: alpha yo'q, yo'qolayotganda dog'lar kichrayadi
            if self.splat_t < 0.35:
                sf = SPR["goo_screen_fade"][self.splat_v][1]
            elif self.splat_t < 0.7:
                sf = SPR["goo_screen_fade"][self.splat_v][0]
            else:
                sf = SPR["goo_screen"][self.splat_v]
            s.blit(sf, (0, 0))
            return
        a = min(1.0, self.splat_age / 0.12, self.splat_t / 0.7)
        sf = SPR["goo_screen"][self.splat_v]
        sf.set_alpha(int(255 * a))
        s.blit(sf, (0, 0))


# --------------------------------------------------------------------------- #
#  APP (menyular, akkaunt, rang, pauza)
# --------------------------------------------------------------------------- #
BACK = {"delete": "accounts", "confirm": "accounts", "profile": "menu", "accounts": "profile", "colors": "profile",
        "levels": "menu", "difficulty": "levels", "settings": "menu", "mp": "menu", "ach": "profile"}
COLS = {"levels": 5, "colors": 6}


def level_names():
    return [b.name for b in BOSSES] + ["???"] * max(0, NUM_LEVELS - len(BOSSES))


class App:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("DeCycle Mobile 2.0")
        flags = pygame.SCALED | (pygame.FULLSCREEN if ANDROID else pygame.RESIZABLE)
        self.screen = pygame.display.set_mode((W, H), flags)
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        names = "consolas,dejavusansmono,arial"
        self.fonts = (pygame.font.SysFont(names, 20),
                      pygame.font.SysFont(names, 30),
                      pygame.font.SysFont(names, 76, bold=True))
        self.f_title = pygame.font.SysFont(names, 110, bold=True)
        t = self.fonts[1].render("Loading...", True, (150, 230, 255))     # ovoz yaratilguncha
        self.screen.fill((8, 6, 20))
        self.screen.blit(t, t.get_rect(center=(CX, CY)))
        pygame.display.flip()
        build_sprites()
        build_touch_sprites()
        self.au = Audio()
        self.save = Save()
        self.state = "menu" if self.save.name else "name"
        self.sel = 0
        self.rects = []
        self.shake_on = not ANDROID
        self.touch_mode = 0          # 0=AUTO, 1=ON, 2=OFF
        self.finger_seen = False
        self.show_fps = False
        self.kb_on = False
        self.name_rects = None
        self.game = None
        self.overlay = None          # None / "pause" / "result"
        self.osel = 0
        self.orects = []
        self.level_idx = 0
        self.diff = "Easy"
        self.mp = False              # multiplayer (same device) rejimi
        self.lasthit = False         # LASTHIT (hardcore) rejimi
        self.new_ach = False         # yangi achivka olindi (natija oynasida ko'rsatiladi)
        self.name_buf = ""
        self.del_name = ""
        self.t = 0.0
        gc.collect()

    def touch_on(self):
        """Telefon bo'lsa (yoki sensorli ekran bosilgan bo'lsa) sensorli boshqaruv."""
        if self.touch_mode == 1:
            return True
        if self.touch_mode == 2:
            return False
        return ANDROID or self.finger_seen

    # ------------------------------------------------------------------ menyular
    def items(self):
        st = self.state
        if st == "menu":
            return ["Play", "Multiplayer", "Profile", "Settings", "Quit"]
        if st == "mp":
            return ["Same device (PC only)" if self.touch_on() else "Same device (2 players)", "Connect (soon)", "Back"]
        if st == "profile":
            return ["Account: %s" % self.save.name, "Ship color", "Achievements", "Back"]
        if st == "ach":
            return ["Back"]
        if st == "accounts":
            n = self.save.names()
            return n + ["+ New account"] + (["Delete account"] if n else []) + ["Back"]
        if st == "delete":
            return self.save.names() + ["Back"]
        if st == "confirm":
            return ["Yes, delete %s" % self.del_name, "No"]
        if st == "colors":
            return [str(i) for i in range(len(COLORS) if self.save.totem_open() else len(COLORS) - 1)]
        if st == "levels":
            return level_names() + ["Back"]
        if st == "difficulty":
            return ["Easy", "Mid", "Hard", "Back", "LASTHIT"]
        if st == "settings":
            return ["Sound: %s" % ("ON" if self.au.enabled else "OFF"),
                    "Screen shake: %s" % ("ON" if self.shake_on else "OFF"),
                    "Touch controls: %s" % ("AUTO", "ON", "OFF")[self.touch_mode],
                    "FPS counter: %s" % ("ON" if self.show_fps else "OFF"),
                    "Fullscreen (toggle)", "Back"]
        return []

    def go(self, state):
        if self.state == "game":
            self.end_game()
        if state in ("levels", "menu"):
            self.lasthit = False                               # LASTHIT har safar qayta yoqiladi
        self.state, self.sel = state, 0
        if state == "accounts" and self.save.name in self.save.names():
            self.sel = self.save.names().index(self.save.name)
        elif state == "colors":
            self.sel = self.save.color()
        elif state == "levels":
            self.sel = min(self.level_idx, NUM_LEVELS - 1)

    def start_game(self, idx, diff, lasthit=None):
        self.level_idx, self.diff = idx, diff
        lh = self.lasthit if lasthit is None else lasthit      # Retry: o'sha rejim; yangi jang: menyudagi tanlov
        self.lasthit = False                                   # keyingi safar yana qo'lda yoqiladi
        self.game = Game(diff, self.au, BOSSES[idx], COLORS[self.save.color()], self.mp, lh,
                         (not self.mp) and self.save.color() == TOTEM_IDX)
        self.new_ach = False
        self.state = "game"
        self.overlay = None
        gc.collect()
        gc.disable()          # jang paytida GC to'xtatilgan: pool'lar tufayli xotira o'smaydi

    def end_game(self):
        self.au.stop_all()
        self.overlay = None
        gc.enable()
        gc.collect()

    def level_open(self, i):
        return i < len(BOSSES) and (self.mp or i < self.save.unlocked()
                                    or (i > 0 and self.save.best(BOSSES[i - 1].name) >= 0))

    def activate(self, i):
        it = self.items()[i]
        self.au.play("select")
        st = self.state
        if st == "menu":
            if it == "Play":
                self.mp = False
                self.go("levels")
            elif it == "Multiplayer":
                self.go("mp")
            elif it == "Profile":
                self.go("profile")
            elif it == "Settings":
                self.go("settings")
            else:
                pygame.quit()
                sys.exit()
        elif st == "mp":
            if i == 0:
                if self.touch_on():
                    self.au.play("hurt")          # same device: faqat kompyuterda
                else:
                    self.mp = True
                    self.go("levels")
            elif i == 1:
                self.au.play("hurt")          # online rejim keyingi versiyada
            else:
                self.go("menu")
        elif st == "profile":
            if i == 0:
                self.go("accounts")
            elif i == 1:
                self.go("colors")
            elif i == 2:
                self.go("ach")
            else:
                self.go("menu")
        elif st == "ach":
            self.go("profile")
        elif st == "accounts":
            names = self.save.names()
            if i < len(names):
                self.save.switch(names[i])
                self.go("profile")
            elif it == "+ New account":
                if len(names) >= MAX_ACCOUNTS:
                    self.au.play("hurt")
                else:
                    self.name_buf = ""
                    self.state = "name"
            elif it == "Delete account":
                self.go("delete")
            else:
                self.go("profile")
        elif st == "delete":
            names = self.save.names()
            if i < len(names):
                self.del_name = names[i]
                self.go("confirm")
            else:
                self.go("accounts")
        elif st == "confirm":
            if i == 0:
                self.save.delete(self.del_name)
                if self.save.names():
                    self.go("accounts")
                else:                                  # akkaunt qolmadi: yangisini yaratish kerak
                    self.name_buf = ""
                    self.state = "name"
            else:
                self.go("accounts")
        elif st == "colors":
            self.save.set_color(i)
            self.go("profile")
        elif st == "levels":
            if it == "Back":
                self.go("mp" if self.mp else "menu")
            elif self.level_open(i):
                self.level_idx = i
                self.go("difficulty")
            else:
                self.au.play("hurt")
        elif st == "difficulty":
            if it == "Back":
                self.go("levels")
            elif it == "LASTHIT":
                self.lasthit = not self.lasthit
            else:
                self.start_game(self.level_idx, it)
        elif st == "settings":
            if i == 0:
                self.au.enabled = not self.au.enabled
                if not self.au.enabled:
                    self.au.stop_all()
                else:
                    self.au.play("select")
            elif i == 1:
                self.shake_on = not self.shake_on
            elif i == 2:
                self.touch_mode = (self.touch_mode + 1) % 3
            elif i == 3:
                self.show_fps = not self.show_fps
            elif i == 4:
                pygame.display.toggle_fullscreen()
            else:
                self.go("menu")

    # ------------------------------------------------------------------ pauza / natija
    def ov_items(self):
        if self.overlay == "pause":
            return ["Resume", "Restart", "Level select", "Main menu"]
        items = []
        if self.game.result == "win" and self.level_idx + 1 < len(BOSSES):
            items.append("Next boss")
        return items + ["Retry", "Level select", "Main menu"]

    def open_overlay(self, kind):
        self.overlay, self.osel = kind, 0
        if kind == "pause":
            self.game.paused = True
            self.au.pause(True)

    def ov_activate(self, i):
        it = self.ov_items()[i]
        self.au.play("select")
        if it == "Resume":
            self.game.paused = False
            self.au.pause(False)
            self.overlay = None
        elif it in ("Restart", "Retry"):
            lh = self.game.lasthit
            self.end_game()
            self.start_game(self.level_idx, self.diff, lh)
        elif it == "Next boss":
            self.end_game()
            self.start_game(self.level_idx + 1, self.diff)
        elif it == "Level select":
            self.go("levels")
        else:
            self.go("menu")

    # ------------------------------------------------------------------ hodisalar
    def handle(self, e):
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        back = getattr(pygame, "K_AC_BACK", None)           # Android "orqaga" tugmasi = Esc
        if e.type == pygame.KEYDOWN and back is not None and e.key == back:
            e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="", mod=0)
        if e.type == pygame.FINGERDOWN or (e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "touch", False)):
            self.finger_seen = True
        elif e.type == pygame.KEYDOWN and not ANDROID:
            self.finger_seen = False
        if (ANDROID and e.type == getattr(pygame, "WINDOWFOCUSLOST", -1) and self.state == "game"
                and not self.overlay and not self.game.result):
            self.open_overlay("pause")                      # ilova fonga o'tsa - pauza
        if self.state == "name":
            self.handle_name(e)
        elif self.state == "game":
            self.handle_game(e)
        else:
            self.handle_menu(e)

    def confirm_name(self):
        name = self.name_buf.strip()
        if not name:
            return
        if name not in self.save.names() and len(self.save.names()) >= MAX_ACCOUNTS:
            self.au.play("hurt")
            return
        self.save.create(name)
        self.au.play("select")
        self.go("menu")

    def handle_name(self, e):
        if e.type == pygame.TEXTINPUT and ANDROID:          # ekran klaviaturasi matni
            for ch in e.text:
                if len(self.name_buf) < 12 and ch.isprintable() and (ch.isalnum() or ch in " _-"):
                    self.name_buf += ch
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.name_rects:
            box, ok, back = self.name_rects
            if ok.collidepoint(e.pos):
                self.confirm_name()
            elif back is not None and back.collidepoint(e.pos):
                self.go("accounts")
            elif box.collidepoint(e.pos) and ANDROID:
                pygame.key.start_text_input()                 # klaviatura yopilgan bo'lsa qayta ochish
            return
        if e.type != pygame.KEYDOWN:
            return
        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.confirm_name()
        elif e.key == pygame.K_BACKSPACE:
            self.name_buf = self.name_buf[:-1]
        elif e.key == pygame.K_ESCAPE:
            if self.save.names():
                self.go("accounts")
        elif not ANDROID:
            ch = e.unicode
            if ch and len(self.name_buf) < 12 and ch.isprintable() and (ch.isalnum() or ch in " _-"):
                self.name_buf += ch

    def nav(self, key):
        n = len(self.items())
        cols = COLS.get(self.state, 1)
        if key == pygame.K_LEFT:
            self.sel = (self.sel - 1) % n
        elif key == pygame.K_RIGHT:
            self.sel = (self.sel + 1) % n
        elif cols == 1:
            self.sel = (self.sel + (-1 if key == pygame.K_UP else 1)) % n
        else:
            grid = n - 1 if self.state == "levels" else n      # levels: oxirgisi Back
            if key == pygame.K_UP:
                if self.state == "levels" and self.sel == n - 1:
                    self.sel = grid - 3
                elif self.sel >= cols:
                    self.sel -= cols
                elif self.state == "colors":
                    self.sel += cols
            else:
                if self.sel + cols < grid:
                    self.sel += cols
                elif self.state == "levels":
                    self.sel = n - 1
                else:
                    self.sel = (self.sel + cols) % grid
        self.au.play("move")

    def handle_menu(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self.nav(e.key)
            elif e.key == pygame.K_x:
                self.activate(self.sel)
            elif e.key == pygame.K_ESCAPE and self.state in BACK:
                self.go("mp" if (self.mp and self.state == "levels") else BACK[self.state])
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos) and self.sel != i:
                    self.sel = i
                    self.au.play("move")
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.sel = i
                    self.activate(i)
                    break

    def handle_game(self, e):
        g = self.game
        if self.overlay:
            n = len(self.ov_items())
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_UP):
                    self.osel = (self.osel - 1) % n
                    self.au.play("move")
                elif e.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self.osel = (self.osel + 1) % n
                    self.au.play("move")
                elif e.key == pygame.K_x:
                    self.ov_activate(self.osel)
                elif e.key in (pygame.K_ESCAPE, pygame.K_p):
                    if self.overlay == "pause":
                        self.osel = 0
                        self.ov_activate(0)               # Resume
                    elif e.key == pygame.K_ESCAPE:
                        self.go("levels")
            elif e.type == pygame.MOUSEMOTION:
                for i, r in enumerate(self.orects):
                    if r.collidepoint(e.pos) and self.osel != i:
                        self.osel = i
                        self.au.play("move")
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self.orects):
                    if r.collidepoint(e.pos):
                        self.osel = i
                        self.ov_activate(i)
                        break
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_p) and not g.result:
                self.open_overlay("pause")
            else:
                g.key(e.key)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.touch_on():
            if g.touch_press(*e.pos) == "pause":
                self.open_overlay("pause")

    # ------------------------------------------------------------------ chizish
    def draw_title(self, s, sub):
        title = txt(self.f_title, "DeCycle", (150, 230, 255))
        s.blit(title, (CX - title.get_width() // 2, 70))
        t = txt(self.fonts[0], sub, (140, 150, 190))
        s.blit(t, (CX - t.get_width() // 2, 195))

    def draw_list(self, s, sub, extra=None):
        self.draw_title(s, sub)
        items = self.items()
        gap = 64 if len(items) <= 5 else (48 if len(items) <= 8 else 40)
        y0 = 300
        self.rects = []
        for i, it in enumerate(items):
            sel = i == self.sel
            col = (255, 255, 255) if sel else (140, 150, 190)
            if self.state in ("accounts", "delete") and i < len(self.save.names()) and it == self.save.name and not sel:
                col = (170, 235, 190)
            t = txt(self.fonts[1], ("> %s <" if sel else "%s") % it, col)
            r = t.get_rect(center=(CX, y0 + i * gap))
            self.rects.append(r.inflate(60, 16))
            s.blit(t, r)
        if extra:
            t = txt(self.fonts[0], extra, (170, 180, 220))
            s.blit(t, (CX - t.get_width() // 2, y0 + len(items) * gap + 6))

    def draw_levels(self, s):
        cw, ch, gap = 180, 120, 24
        x0 = (W - (5 * cw + 4 * gap)) // 2
        y0 = 170
        head = txt(self.fonts[1], "Level tanlang" + ("  -  2 players" if self.mp else ""), (150, 230, 255))
        s.blit(head, (CX - head.get_width() // 2, 100))
        self.rects = []
        names = level_names()
        for i, name in enumerate(names):
            r = pygame.Rect(x0 + (i % 5) * (cw + gap), y0 + (i // 5) * (ch + gap), cw, ch)
            self.rects.append(r)
            sel = i == self.sel
            op = self.level_open(i)
            pygame.draw.rect(s, (30, 34, 70) if op else (18, 18, 34), r)
            border = (255, 255, 255) if sel else ((120, 140, 220) if op else (60, 60, 90))
            pygame.draw.rect(s, border, r, 3 if sel else 2)
            num = txt(self.fonts[0], str(i + 1), (170, 180, 220) if op else (90, 90, 120))
            s.blit(num, (r.x + 10, r.y + 8))
            label = name if op else ("LOCKED" if i < len(BOSSES) else "???")
            t = txt(self.fonts[1], label, (255, 255, 255) if op else (90, 90, 120))
            s.blit(t, t.get_rect(center=r.center))
            if i < len(BOSSES) and not self.mp:
                best = self.save.best(name)
                for k in range(3):
                    col = (255, 215, 70) if k <= best else (50, 52, 80)
                    pygame.draw.rect(s, col, (r.right - 16 - k * 16, r.bottom - 16, 10, 10))
                if name in self.save.acc.get("lasthit", []):
                    draw_heart(s, r.x + 22, r.bottom - 18, 0.45, (255, 25, 40))
        sel = self.sel == len(names)
        back = txt(self.fonts[1], "> Back <" if sel else "Back", (255, 255, 255) if sel else (140, 150, 190))
        br = back.get_rect(center=(CX, y0 + 3 * (ch + gap) + 20))
        self.rects.append(br.inflate(60, 20))
        s.blit(back, br)
        hint = txt(self.fonts[0], ("Tanlash uchun bosing" if self.touch_on() else "Left/Right/Up/Down - tanlash,  X - tasdiqlash,  Esc - orqaga"), (100, 110, 150))
        s.blit(hint, (CX - hint.get_width() // 2, H - 40))

    def draw_difficulty(self, s):
        self.draw_title(s, "Qiyinchilikni tanlang")
        items = self.items()                                  # Easy, Mid, Hard, Back, LASTHIT
        self.rects = []
        for i, it in enumerate(items[:4]):
            sel = i == self.sel
            t = txt(self.fonts[1], ("> %s <" if sel else "%s") % it, (255, 255, 255) if sel else (140, 150, 190))
            r = t.get_rect(center=(CX, 300 + i * 64))
            self.rects.append(r.inflate(60, 16))
            s.blit(t, r)
        sel = self.sel == 4                                   # LASTHIT: o'ng pastki burchakda, qizil
        on = self.lasthit
        r = pygame.Rect(W - 330, H - 104, 306, 52)
        self.rects.append(r)
        pygame.draw.rect(s, (70, 10, 18) if on else (26, 12, 24), r)
        pygame.draw.rect(s, (255, 255, 255) if sel else ((255, 60, 70) if on else (150, 40, 55)), r, 3 if (sel or on) else 2)
        draw_heart(s, r.x + 30, r.y + 25, 0.8, (255, 25, 40) if on else (120, 30, 45))
        t = txt(self.fonts[1], "LASTHIT: %s" % ("ON" if on else "OFF"), (255, 70, 80) if (on or sel) else (190, 60, 75))
        s.blit(t, (r.x + 60, r.centery - t.get_height() // 2))
        extra = None
        if self.sel < 3:
            d, b = DIFFS[items[self.sel]], BOSSES[self.level_idx]
            extra = "%s   |   Boss HP %d   |   Sizning HP %s" % (
                b.name, int(d["boss_hp"] * b.hp_mult * (MP_BOSS_HP if self.mp else 1.0)),
                "1 (LASTHIT)" if self.lasthit else PLAYER_HP)
        elif self.sel == 4:
            extra = "Hardcore: bitta zarbada o'lasiz (health bar o'rniga yurakcha)"
        if extra:
            t = txt(self.fonts[0], extra, (255, 120, 130) if self.sel == 4 else (170, 180, 220))
            s.blit(t, (CX - t.get_width() // 2, 300 + 4 * 64 + 6))

    def draw_ach(self, s):
        self.draw_title(s, "Achievements")
        got = self.save.has_ach("survivor")
        box = pygame.Rect(CX - 320, 290, 640, 110)
        pygame.draw.rect(s, (24, 26, 52), box)
        pygame.draw.rect(s, (255, 215, 70) if got else (70, 80, 130), box, 3)
        if got:
            draw_heart(s, box.x + 56, box.y + 56, 1.5, (255, 25, 40))
            t1 = txt(self.fonts[1], "I'M SURVIVOR", (255, 215, 70))
            t2 = txt(self.fonts[0], "Ilk 4 ta bossni LASTHIT'da yengdingiz.  Mukofot: TOTEM kemasi", (190, 200, 235))
        else:
            draw_heart(s, box.x + 56, box.y + 56, 1.5, (50, 52, 80), (90, 90, 120))
            t1 = txt(self.fonts[1], "???", (110, 110, 140))
            t2 = txt(self.fonts[0], "Sirli achivka", (110, 110, 140))
        s.blit(t1, (box.x + 120, box.y + 24))
        s.blit(t2, (box.x + 120, box.y + 66))
        self.rects = []
        back = txt(self.fonts[1], "> Back <", (255, 255, 255))
        br = back.get_rect(center=(CX, 480))
        self.rects.append(br.inflate(60, 20))
        s.blit(back, br)

    def draw_colors(self, s):
        head = txt(self.fonts[1], "Kema rangini tanlang", (150, 230, 255))
        s.blit(head, (CX - head.get_width() // 2, 120))
        cw, gap = 110, 20
        x0 = (W - (6 * cw + 5 * gap)) // 2
        y0 = 230
        self.rects = []
        cur = self.save.color()
        for i, col in enumerate(COLORS[:len(self.items())]):
            r = pygame.Rect(x0 + (i % 6) * (cw + gap), y0 + (i // 6) * (cw + gap), cw, cw)
            self.rects.append(r)
            pygame.draw.rect(s, (24, 26, 52), r)
            sel = i == self.sel
            pygame.draw.rect(s, (255, 255, 255) if sel else (70, 80, 130), r, 3 if sel else 2)
            draw_ship(s, r.centerx, r.centery, 0, -1, col, 2.0, TOTEM_COL2 if i == TOTEM_IDX else None)
            if i == TOTEM_IDX:
                lab = txt(self.fonts[0], "TOTEM", (250, 225, 60))
                s.blit(lab, (r.centerx - lab.get_width() // 2, r.y + 8))
            if i == cur:
                pygame.draw.rect(s, (170, 235, 190), (r.x + 8, r.bottom - 12, r.w - 16, 4))
        hint = txt(self.fonts[0], ("Tanlash uchun bosing" if self.touch_on() else "Left/Right/Up/Down - tanlash,  X - tasdiqlash,  Esc - orqaga"), (100, 110, 150))
        s.blit(hint, (CX - hint.get_width() // 2, H - 40))

    def draw_name(self, s):
        self.draw_title(s, "Akkaunt")
        tl = self.touch_on()
        y = 265 if tl else 360            # sensorli: ekran klaviaturasi ostida qolmasligi uchun yuqoriroq
        t = txt(self.fonts[1], "Ismingizni kiriting", (200, 210, 240))
        s.blit(t, (CX - t.get_width() // 2, y - 60))
        box = pygame.Rect(CX - 200, y, 400, 56)
        pygame.draw.rect(s, (24, 26, 52), box)
        pygame.draw.rect(s, (150, 230, 255), box, 2)
        shown = self.name_buf + ("_" if int(self.t * 2) % 2 == 0 else " ")
        t = txt(self.fonts[1], shown, (255, 255, 255))
        s.blit(t, (box.x + 14, box.y + 12))
        ok = pygame.Rect(CX + 220, y, 120, 56)
        back = pygame.Rect(CX - 340, y, 120, 56) if self.save.names() else None
        self.name_rects = (box, ok, back) if tl else None
        if tl:
            for r, label in ((ok, "OK"), (back, "Back")):
                if r is None:
                    continue
                pygame.draw.rect(s, (30, 36, 70), r, border_radius=10)
                pygame.draw.rect(s, (150, 235, 255), r, 2, border_radius=10)
                lt = txt(self.fonts[1], label, (240, 245, 255))
                s.blit(lt, lt.get_rect(center=r.center))
            hint = "Yozish uchun maydonni bosing"
        else:
            hint = "Enter - tasdiqlash" + ("   Esc - orqaga" if self.save.names() else "")
        t = txt(self.fonts[0], hint, (100, 110, 150))
        s.blit(t, (CX - t.get_width() // 2, y + 80))

    def draw_menu(self, s):
        s.blit(SPR["bg_menu_red" if (self.state == "difficulty" and self.lasthit) else "bg_menu"], (0, 0))
        pygame.draw.circle(s, (35, 40, 80), (CX, CY + 30), 330, 2)
        a = self.t * 1.2
        pygame.draw.circle(s, COLORS[self.save.color()], (CX + math.cos(a) * 330, CY + 30 + math.sin(a) * 330), 9)
        st = self.state
        if st == "levels":
            self.draw_levels(s)
        elif st == "colors":
            self.draw_colors(s)
        elif st == "name":
            self.draw_name(s)
        elif st == "difficulty":
            self.draw_difficulty(s)
        elif st == "ach":
            self.draw_ach(s)
        elif st == "menu":
            self.draw_list(s, "orbital boss fight   |   Player: %s" % self.save.name)
        elif st == "profile":
            self.draw_list(s, "Profil")
        elif st == "accounts":
            self.draw_list(s, "Akkauntni tanlang")
        elif st == "delete":
            self.draw_list(s, "Qaysi akkauntni o'chirasiz?")
        elif st == "confirm":
            self.draw_list(s, "'%s' progress bilan birga o'chiriladi" % self.del_name)
        elif st == "mp":
            self.draw_list(s, "Multiplayer   |   test 0.1",
                           "Same device: faqat kompyuterda (2 ta klaviatura boshqaruvi)" if self.touch_on()
                           else "1-o'yinchi: Z, X     |     2-o'yinchi: Left/Right, Down")
        else:
            self.draw_list(s, "Sozlamalar")
        if st in ("menu", "profile", "accounts", "delete", "confirm", "difficulty", "settings", "mp", "ach"):
            hint = txt(self.fonts[0], ("Tanlash uchun bosing" if self.touch_on() else "Left/Right - tanlash,  X - tasdiqlash,  Esc - orqaga"), (100, 110, 150))
            s.blit(hint, (CX - hint.get_width() // 2, H - 40))

    def draw_overlay(self, s):
        s.blit(SPR["dim"], (0, 0))
        g = self.game
        if self.overlay == "pause":
            title, col = "PAUZA", (255, 255, 255)
        elif g.result == "win":
            title, col = "G'ALABA!", (120, 255, 170)
        else:
            title, col = "YUTQAZDINGIZ", (255, 100, 100)
        t = txt(self.fonts[2], title, col)
        s.blit(t, (CX - t.get_width() // 2, 150))
        if self.overlay == "result" and self.new_ach:
            box = pygame.Rect(CX - 300, 24, 600, 92)
            pygame.draw.rect(s, (30, 24, 8), box)
            pygame.draw.rect(s, (255, 215, 70), box, 3)
            draw_heart(s, box.x + 48, box.y + 46, 1.3, (255, 25, 40))
            s.blit(txt(self.fonts[0], "ACHIEVEMENT UNLOCKED", (255, 215, 70)), (box.x + 96, box.y + 10))
            s.blit(txt(self.fonts[1], "I'M SURVIVOR", (255, 255, 255)), (box.x + 96, box.y + 30))
            s.blit(txt(self.fonts[0], "TOTEM kemasi ochildi:  Profile > Ship color", (120, 255, 170)), (box.x + 96, box.y + 66))
        self.orects = []
        for i, it in enumerate(self.ov_items()):
            sel = i == self.osel
            tt = txt(self.fonts[1], ("> %s <" if sel else "%s") % it, (255, 255, 255) if sel else (150, 160, 200))
            r = tt.get_rect(center=(CX, 320 + i * 62))
            self.orects.append(r.inflate(60, 16))
            s.blit(tt, r)

    # ------------------------------------------------------------------ asosiy sikl
    def run(self):
        while True:
            dt = min(self.clock.tick(60) / 1000, 0.05)
            self.t += dt
            for e in pygame.event.get():
                self.handle(e)

            want_kb = ANDROID and self.state == "name"             # ekran klaviaturasi faqat yozish joyida
            if want_kb != self.kb_on:
                self.kb_on = want_kb
                (pygame.key.start_text_input if want_kb else pygame.key.stop_text_input)()

            if self.state == "game":
                g = self.game
                g.touch = self.touch_on()
                g.update(dt)
                if g.result == "win" and not g.rewarded:
                    g.rewarded = True
                    if not g.mp:          # multiplayer test: akkauntga yozilmaydi
                        self.save.record_win(self.level_idx, BOSSES[self.level_idx].name,
                                             DIFF_ORDER.index(self.diff), len(BOSSES))
                        if g.lasthit and self.save.record_lasthit(BOSSES[self.level_idx].name):
                            self.new_ach = True
                            self.au.play("totem")
                if g.result and self.overlay is None and g.result_t > 1.0:
                    self.open_overlay("result")
                m = int(10 * g.shake) if (self.shake_on and g.shake > 0 and not self.overlay) else 0
                if m > 0:                                          # silkinish: faqat shu paytda nusxa
                    g.draw(self.canvas, self.fonts)
                    self.screen.fill((0, 0, 0))
                    self.screen.blit(self.canvas, (random.randint(-m, m), random.randint(-m, m)))
                else:
                    g.draw(self.screen, self.fonts)                # to'g'ridan-to'g'ri ekranga (tez)
                    if self.overlay:
                        self.draw_overlay(self.screen)
            else:
                self.draw_menu(self.screen)

            if self.show_fps:
                f = self.fonts[0].render("FPS %d" % self.clock.get_fps(), True, (120, 255, 120), (0, 0, 0))
                self.screen.blit(f, (24, 44))
            pygame.display.flip()


if __name__ == "__main__":
    App().run()