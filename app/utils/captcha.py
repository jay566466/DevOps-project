"""
Visual Grid CAPTCHA — "Select all images containing a [CATEGORY]"
High-quality Pillow illustrations for each category.
"""

import io, base64, random, math, secrets
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from flask import session

CAPTCHA_SESSION_KEY = "captcha_grid"
GRID_SIZE  = 9
TILE_SIZE  = 96

VEHICLE_CATEGORIES    = ["car", "bus", "bicycle", "motorcycle", "truck"]
DISTRACTOR_CATEGORIES = ["tree", "building", "flower", "cat", "traffic_light"]

CATEGORY_LABELS = {
    "car":          "cars",
    "bus":          "buses",
    "bicycle":      "bicycles",
    "motorcycle":   "motorcycles",
    "truck":        "trucks",
}

# ═══════════════════════════════════════════════════════════
#  SHARED HELPERS
# ═══════════════════════════════════════════════════════════

def _sky_ground(img, draw, w, h,
                sky1=(135,195,235), sky2=(180,220,250),
                gnd=(85,130,70)):
    """Gradient sky + solid ground."""
    # vertical gradient sky
    for y in range(int(h * 0.55)):
        t = y / (h * 0.55)
        r = int(sky1[0] + t*(sky2[0]-sky1[0]))
        g = int(sky1[1] + t*(sky2[1]-sky1[1]))
        b = int(sky1[2] + t*(sky2[2]-sky1[2]))
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    # ground
    gy = int(h * 0.55)
    draw.rectangle([0, gy, w, h], fill=gnd)
    # ground highlight strip
    draw.rectangle([0, gy, w, gy+3], fill=(100,150,85))

def _road_bg(img, draw, w, h):
    """Road scene background."""
    # sky gradient
    for y in range(int(h*0.45)):
        t = y / (h*0.45)
        r = int(120 + t*40); g = int(175 + t*30); b = int(220 + t*20)
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    # road
    ry = int(h*0.45)
    draw.rectangle([0, ry, w, h], fill=(75,75,82))
    # kerb line
    draw.rectangle([0, ry, w, ry+3], fill=(200,200,190))
    # dashed centre line
    for x in range(0, w, 16):
        draw.rectangle([x, ry+(h-ry)//2-2, x+9, ry+(h-ry)//2+2], fill=(240,230,100))
    # pavement sheen
    draw.rectangle([0, ry+3, w, ry+6], fill=(90,90,98))

def _add_shadow(draw, x1,y1,x2,y2, blur_r=3):
    """Fake drop shadow under a rect."""
    draw.ellipse([x1+4,y2-2, x2+4,y2+blur_r*2], fill=(0,0,0,60))

def _light_spot(draw, cx, cy, r, col):
    for i in range(r, 0, -1):
        alpha = int(180 * (1 - i/r))
        draw.ellipse([cx-i,cy-i,cx+i,cy+i], fill=(*col[:3], alpha))

def _wheel(draw, cx, cy, r, col=(30,30,30)):
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=col, outline=(15,15,15), width=2)
    draw.ellipse([cx-r//3,cy-r//3,cx+r//3,cy+r//3], fill=(80,80,90))
    for a in range(0,360,60):
        sx=cx+int((r-4)*math.cos(math.radians(a)))
        sy=cy+int((r-4)*math.sin(math.radians(a)))
        draw.line([(cx,cy),(sx,sy)], fill=(60,60,65), width=1)

def _rounded_rect(draw, x1,y1,x2,y2, radius=6, fill=None, outline=None, width=1):
    draw.rounded_rectangle([x1,y1,x2,y2], radius=radius, fill=fill, outline=outline, width=width)

def _window(draw, x1,y1,x2,y2, tint=(190,225,255,200), radius=3):
    """Glossy window."""
    draw.rounded_rectangle([x1,y1,x2,y2], radius=radius,
                            fill=(160,205,240), outline=(120,170,210), width=1)
    # glare
    mid = (x1+x2)//2
    draw.polygon([(x1+2,y1+2),(mid,y1+2),(x1+2,(y1+y2)//2)], fill=(220,240,255,100))

def _cloud(draw, cx, cy, scale=1.0):
    """Draw a fluffy cloud."""
    for dx,dy,r in [
        (0,0,int(14*scale)), (int(16*scale),-int(6*scale),int(10*scale)),
        (-int(14*scale),-int(4*scale),int(9*scale)), (int(6*scale),-int(12*scale),int(8*scale))
    ]:
        draw.ellipse([cx+dx-r,cy+dy-r,cx+dx+r,cy+dy+r], fill=(245,248,255))


# ═══════════════════════════════════════════════════════════
#  VEHICLES
# ═══════════════════════════════════════════════════════════

CAR_PALETTES = [
    ((210,40,40),(160,20,20)),   # red
    ((50,100,200),(30,65,150)),  # blue
    ((240,200,30),(190,150,20)), # yellow
    ((50,160,70),(30,110,45)),   # green
    ((220,220,225),(160,160,165)),# silver
    ((30,30,35),(15,15,18)),     # black
    ((230,120,30),(175,80,15)),  # orange
]

def _draw_car(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img, "RGBA")
    _road_bg(img,draw,w,h)
    _cloud(draw, 20, 18, 0.7)
    _cloud(draw, 68, 14, 0.55)

    body, dark = random.choice(CAR_PALETTES)
    hl = tuple(min(255,c+45) for c in body)
    gnd = int(h*0.45)
    # ground shadow
    draw.ellipse([10,gnd+28,86,gnd+38], fill=(0,0,0,50))

    # body lower
    _rounded_rect(draw, 6,gnd+10, 90,gnd+30, radius=6, fill=body, outline=dark, width=2)
    # body upper / cabin
    _rounded_rect(draw, 18,gnd-4, 76,gnd+14, radius=7, fill=body, outline=dark, width=2)
    # cabin highlight
    _rounded_rect(draw, 20,gnd-2, 74,gnd+5, radius=5, fill=hl)

    # windows
    _window(draw, 21,gnd-3, 45,gnd+10)
    _window(draw, 48,gnd-3, 72,gnd+10)

    # bonnet slope
    draw.polygon([(75,gnd-4),(88,gnd+10),(75,gnd+10)], fill=body, outline=dark)

    # wheels
    _wheel(draw, 23, gnd+30, 11)
    _wheel(draw, 73, gnd+30, 11)

    # headlight
    draw.rounded_rectangle([82,gnd+13,92,gnd+20], radius=2, fill=(255,255,200), outline=(220,210,100))
    # tail light
    draw.rounded_rectangle([4,gnd+13,12,gnd+20], radius=2, fill=(255,80,80), outline=(200,40,40))
    # door crease
    draw.line([(47,gnd+11),(47,gnd+28)], fill=dark, width=1)
    # door handle
    draw.rounded_rectangle([55,gnd+18,62,gnd+21], radius=1, fill=(200,200,200))

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


BUS_PALETTES = [
    ((240,210,30),(190,160,20)),  # yellow school bus
    ((220,45,40),(170,25,20)),    # red London
    ((255,255,255),(200,200,200)),# white
    ((30,100,200),(20,70,155)),   # blue
]

def _draw_bus(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _road_bg(img,draw,w,h)
    _cloud(draw,72,16,0.6)

    body,dark = random.choice(BUS_PALETTES)
    hl = tuple(min(255,c+40) for c in body)
    gnd = int(h*0.45)
    # shadow
    draw.ellipse([4,gnd+32,92,gnd+42], fill=(0,0,0,55))

    # main body — tall box
    _rounded_rect(draw, 4,gnd-16, 92,gnd+32, radius=4, fill=body, outline=dark, width=2)
    # roof band
    _rounded_rect(draw, 4,gnd-16, 92,gnd-9, radius=4, fill=dark)
    # body highlight strip
    draw.rectangle([5,gnd-8,91,gnd-4], fill=hl)

    # windows row
    for wx in [9,25,41,57]:
        _window(draw, wx,gnd-14, wx+13,gnd-1)

    # windshield  (front right)
    _window(draw, 75,gnd-14, 90,gnd+4, radius=2)
    # door
    _rounded_rect(draw, 8,gnd+2, 22,gnd+32, radius=3,
                  fill=tuple(min(255,c+20) for c in body), outline=dark, width=1)
    draw.line([(15,gnd+2),(15,gnd+32)], fill=dark, width=1)

    # destination board
    draw.rounded_rectangle([26,gnd-13,62,gnd-6], radius=2, fill=(0,0,60))
    for bx in range(29,60,6):
        draw.rectangle([bx,gnd-12,bx+3,gnd-8], fill=(200,200,255))

    # headlight
    draw.rounded_rectangle([82,gnd+8,92,gnd+17], radius=2, fill=(255,255,210))
    draw.rounded_rectangle([82,gnd+18,92,gnd+26], radius=2, fill=(255,100,100))

    # wheels
    _wheel(draw, 20, gnd+33, 11)
    _wheel(draw, 70, gnd+33, 11)
    _wheel(draw, 55, gnd+33, 10)

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


BIKE_PALETTES = [
    (200,40,40),(50,120,200),(50,160,70),(180,100,20),(80,80,160)
]

def _draw_bicycle(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _sky_ground(img,draw,w,h,
                sky1=(140,200,240),sky2=(200,230,255),gnd=(80,140,70))
    _cloud(draw,30,20,0.85)

    col  = random.choice(BIKE_PALETTES)
    dark = tuple(max(0,c-60) for c in col)
    gnd  = int(h*0.55)
    r    = 20
    lw, rw = 18, 74
    cy   = gnd + r

    # shadow
    draw.ellipse([lw-r,cy+r-2,lw+r,cy+r+4],fill=(0,0,0,40))
    draw.ellipse([rw-r,cy+r-2,rw+r,cy+r+4],fill=(0,0,0,40))

    # tyres
    for cx_ in [lw,rw]:
        draw.ellipse([cx_-r,cy-r,cx_+r,cy+r], fill=(25,25,25), outline=(10,10,10),width=3)
        # inner rim
        draw.ellipse([cx_-r+4,cy-r+4,cx_+r-4,cy+r-4],
                     outline=(80,80,90), width=2)
        # hub
        draw.ellipse([cx_-4,cy-4,cx_+4,cy+4], fill=(90,90,100))
        # spokes
        for a in range(0,360,45):
            sx=cx_+int((r-6)*math.cos(math.radians(a)))
            sy=cy+int((r-6)*math.sin(math.radians(a)))
            draw.line([(cx_,cy),(sx,sy)], fill=(70,70,80), width=1)

    # FRAME  diamond
    mid_x = (lw+rw)//2 + 2
    # top tube
    draw.line([(lw+r,cy-8),(mid_x,cy-22)], fill=col, width=4)
    # down tube
    draw.line([(mid_x,cy-22),(rw-r-2,cy)], fill=col, width=4)
    # seat tube
    draw.line([(mid_x,cy-22),(mid_x+2,cy)], fill=col, width=4)
    # chain stay
    draw.line([(lw+r,cy),(mid_x+2,cy)], fill=dark, width=3)
    # seat stay
    draw.line([(lw+r,cy),(mid_x,cy-22)], fill=dark, width=2)

    # fork
    draw.line([(rw-r,cy),(rw-4,cy-20)], fill=dark, width=3)

    # saddle
    draw.rounded_rectangle([mid_x-8,cy-26,mid_x+6,cy-22],
                            radius=3, fill=(40,25,15))
    draw.line([(mid_x-2,cy-22),(mid_x-2,cy-18)], fill=(60,40,20), width=2)

    # handlebar stem + bars
    draw.line([(rw-4,cy-20),(rw-4,cy-28)], fill=(60,60,65), width=3)
    draw.line([(rw-10,cy-28),(rw+4,cy-28)], fill=(50,50,55), width=3)
    draw.ellipse([rw-11,cy-30,rw-8,cy-26], fill=(20,20,20))
    draw.ellipse([rw+3,cy-30,rw+6,cy-26], fill=(20,20,20))

    # pedal
    draw.ellipse([mid_x-4,cy-4,mid_x+4,cy+4], fill=(50,50,55))
    draw.rectangle([mid_x+3,cy-2,mid_x+10,cy+2], fill=(40,40,45))

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


MOTO_PALETTES = [
    ((25,25,28),(200,45,30)),
    ((30,30,32),(220,120,20)),
    ((28,28,32),(50,110,200)),
    ((200,50,35),(180,35,20)),
    ((60,60,65),(240,240,245)),
]

def _draw_motorcycle(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _road_bg(img,draw,w,h)
    _cloud(draw,20,15,0.65)

    frame_col, accent = random.choice(MOTO_PALETTES)
    gnd = int(h*0.45)
    lw, rw = 18, 76
    r = 17
    cy = gnd + r

    # shadow
    draw.ellipse([8,cy+r-1,88,cy+r+7], fill=(0,0,0,55))

    # wheels
    for cx_ in [lw,rw]:
        draw.ellipse([cx_-r,cy-r,cx_+r,cy+r], fill=(22,22,22), outline=(10,10,10),width=4)
        draw.ellipse([cx_-r+5,cy-r+5,cx_+r-5,cy+r-5], outline=(65,65,70),width=2)
        draw.ellipse([cx_-4,cy-4,cx_+4,cy+4], fill=(75,75,80))
        for a in range(0,360,60):
            sx=cx_+int((r-7)*math.cos(math.radians(a)))
            sy=cy+int((r-7)*math.sin(math.radians(a)))
            draw.line([(cx_,cy),(sx,sy)], fill=(60,60,65),width=1)

    # swingarm
    draw.line([(lw+r,cy),(lw+r+16,cy-4)], fill=(55,55,60), width=4)

    # frame / engine block
    draw.polygon([
        (lw+r+4,cy-4),(rw-r-6,cy-2),
        (rw-r,cy-10),(rw-r-4,cy-20),
        (lw+r+10,cy-22),(lw+r+4,cy-12)
    ], fill=frame_col, outline=(10,10,12))

    # fuel tank
    draw.rounded_rectangle([36,cy-30,72,cy-12], radius=7, fill=accent, outline=(10,10,12),width=2)
    # tank highlight
    draw.rounded_rectangle([39,cy-29,65,cy-22], radius=5, fill=tuple(min(255,c+50) for c in accent))

    # seat
    draw.rounded_rectangle([30,cy-14,62,cy-8], radius=4, fill=(28,20,14))

    # fairing / front cowl
    draw.polygon([
        (rw-r+2,cy-10),(rw+2,cy-20),
        (rw+6,cy-12),(rw+4,cy-4),(rw-r,cy-2)
    ], fill=accent, outline=(10,10,12))
    # headlight
    draw.ellipse([rw+2,cy-20,rw+12,cy-12], fill=(255,255,220), outline=(200,200,100),width=1)
    # headlight glare
    draw.arc([rw+4,cy-18,rw+10,cy-15], 200, 320, fill=(255,255,255), width=1)

    # handlebar
    draw.line([(rw-2,cy-22),(rw+8,cy-28)], fill=(50,50,55), width=3)
    draw.line([(rw+6,cy-30),(rw+10,cy-25)], fill=(22,22,22), width=3)

    # rider silhouette
    draw.ellipse([40,cy-46,56,cy-32], fill=(30,30,35))     # helmet
    # visor
    draw.arc([42,cy-44,54,cy-33], 30, 150, fill=(80,130,180), width=3)
    draw.rounded_rectangle([38,cy-34,60,cy-14], radius=5, fill=(35,35,40))  # body
    draw.line([(38,cy-28),(28,cy-18)], fill=(35,35,40), width=4)  # arm

    # exhaust
    draw.rounded_rectangle([lw+r,cy-2,lw+r+20,cy+3], radius=2, fill=(140,130,120))
    draw.ellipse([lw+r+17,cy-3,lw+r+24,cy+4], fill=(120,110,105))

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


TRUCK_BODY_COLS = [(230,230,235),(220,55,45),(50,105,185),(80,80,82),(200,165,40)]
TRAILER_COLS    = [(160,155,150),(140,135,130),(120,115,112),(180,175,170)]

def _draw_truck(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _road_bg(img,draw,w,h)
    _cloud(draw,70,14,0.6)

    cab   = random.choice(TRUCK_BODY_COLS)
    cab_d = tuple(max(0,c-55) for c in cab)
    cargo = random.choice(TRAILER_COLS)
    cargo_d = tuple(max(0,c-35) for c in cargo)
    gnd   = int(h*0.45)

    # shadow
    draw.ellipse([2,gnd+30,94,gnd+42], fill=(0,0,0,55))

    # TRAILER
    _rounded_rect(draw, 2,gnd-12, 68,gnd+30, radius=3, fill=cargo, outline=cargo_d, width=2)
    # trailer ribs
    for rx in range(8, 66, 10):
        draw.line([(rx,gnd-11),(rx,gnd+29)], fill=cargo_d, width=1)
    # trailer roof lip
    draw.rectangle([2,gnd-12,68,gnd-8], fill=cargo_d)

    # CAB
    _rounded_rect(draw, 62,gnd-18, 94,gnd+30, radius=5, fill=cab, outline=cab_d, width=2)
    # cab roof deflector
    draw.polygon([(64,gnd-18),(94,gnd-18),(92,gnd-26),(70,gnd-28)],
                 fill=tuple(max(0,c-30) for c in cab), outline=cab_d)

    # windshield
    _window(draw, 65,gnd-16, 91,gnd-2)

    # cab side window
    _window(draw, 65,gnd+2, 80,gnd+14, radius=2)

    # headlights
    draw.rounded_rectangle([84,gnd+4,94,gnd+13], radius=2, fill=(255,255,215))
    draw.rounded_rectangle([84,gnd+14,94,gnd+21], radius=2, fill=(255,90,90))

    # chrome bumper
    _rounded_rect(draw, 62,gnd+24,94,gnd+30, radius=3, fill=(195,195,195), outline=(150,150,150))
    # grill
    draw.rounded_rectangle([63,gnd+6,70,gnd+23], radius=2, fill=(40,40,45))
    for gy2 in range(gnd+8,gnd+22,4):
        draw.line([(64,gy2),(69,gy2)], fill=(80,80,85),width=1)

    # trailer wheels (3)
    for cx_ in [15, 35, 55]:
        _wheel(draw, cx_, gnd+32, 11)
    # cab wheels (2)
    for cx_ in [70, 83]:
        _wheel(draw, cx_, gnd+32, 10)

    # exhaust stacks
    for ex in [62, 67]:
        draw.rounded_rectangle([ex,gnd-30,ex+4,gnd-18], radius=2, fill=(100,95,90))
        draw.ellipse([ex-1,gnd-33,ex+5,gnd-28], fill=(80,75,70))

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


# ═══════════════════════════════════════════════════════════
#  DISTRACTORS
# ═══════════════════════════════════════════════════════════

TREE_STYLES = ["pine","round","palm"]

def _draw_tree(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _sky_ground(img,draw,w,h,
                sky1=(130,195,240),sky2=(195,230,255),gnd=(65,130,55))
    _cloud(draw,72,18,0.7)
    _cloud(draw,20,24,0.5)

    style = random.choice(TREE_STYLES)
    gnd   = int(h*0.55)
    cx    = w//2 + random.randint(-6,6)

    if style == "pine":
        trunk_col = (110,70,30)
        draw.rectangle([cx-4,gnd-6,cx+4,gnd+8], fill=trunk_col)
        greens = [(34,120,40),(42,145,48),(28,100,34)]
        for i,(ty,tw) in enumerate([(gnd-10,28),(gnd-22,22),(gnd-34,16),(gnd-44,10)]):
            g = greens[i%len(greens)]
            draw.polygon([(cx-tw,ty),(cx+tw,ty),(cx,ty-16)], fill=g, outline=(20,80,25))

    elif style == "round":
        trunk_col = (100,65,25)
        draw.rounded_rectangle([cx-5,gnd-8,cx+5,gnd+10], radius=3, fill=trunk_col)
        greens = [(40,150,50),(50,170,60),(30,125,40),(55,160,55)]
        for g in greens:
            for dx,dy,r in [
                (0,-28,20),(12,-20,16),(-12,-20,16),(0,-42,14),(14,-34,12),(-14,-34,12)
            ]:
                draw.ellipse([cx+dx-r,gnd+dy-r,cx+dx+r,gnd+dy+r], fill=g)

    else:  # palm
        trunk_col = (160,120,60)
        # curved trunk
        for i in range(20):
            px = cx + int(i*0.4)
            py = gnd + 10 - i*3
            draw.ellipse([px-3,py-3,px+3,py+3], fill=trunk_col)
        # fronds
        for angle in range(0,360,45):
            r = 22; a = math.radians(angle)
            ex = cx + int(r*math.cos(a))
            ey = (gnd-50) + int(r*0.5*math.sin(a))
            # feathered frond
            steps = 10
            for s in range(steps):
                t  = s/steps
                fx = int(cx + t*(ex-cx))
                fy = int((gnd-50) + t*(ey-(gnd-50)))
                fw = max(1, int(3*(1-t)))
                draw.ellipse([fx-fw,fy-fw,fx+fw,fy+fw], fill=(40,150,40))

    # ground grass tufts
    for gx in range(4, w-4, 9):
        gh = random.randint(4,8)
        draw.line([(gx, gnd),(gx-2,gnd-gh)], fill=(50,110,40), width=1)
        draw.line([(gx, gnd),(gx+2,gnd-gh)], fill=(45,100,35), width=1)

    img = img.filter(ImageFilter.GaussianBlur(0.35))
    return img


BUILDING_PALETTES = [
    ((200,195,190),(160,155,150)),
    ((180,200,220),(140,160,180)),
    ((220,210,190),(180,170,150)),
    ((190,185,200),(150,145,160)),
]

def _draw_building(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    # Sky
    for y in range(h):
        t = y/h
        r = int(100+t*60); g = int(145+t*55); b = int(195+t*45)
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    # ground
    draw.rectangle([0,int(h*0.75),w,h], fill=(80,80,85))

    wall, dark = random.choice(BUILDING_PALETTES)
    hl = tuple(min(255,c+25) for c in wall)

    # background building
    bx1,bx2 = random.randint(0,10), random.randint(w-10,w)
    by = random.randint(int(h*0.12),int(h*0.25))
    bg_col = tuple(max(0,c-30) for c in wall)
    draw.rectangle([bx1,by,bx2,int(h*0.75)], fill=bg_col, outline=tuple(max(0,c-50) for c in wall))
    for wy in range(by+8, int(h*0.72), 10):
        for wx in range(bx1+6,bx2-4,10):
            if random.random()>0.3:
                wc = (255,255,160) if random.random()>0.4 else (100,130,170)
                draw.rectangle([wx,wy,wx+6,wy+7], fill=wc, outline=(60,60,65),width=1)

    # main foreground building
    mx1,mx2 = 12, w-12
    my = random.randint(int(h*0.05),int(h*0.18))
    draw.rectangle([mx1,my,mx2,int(h*0.75)], fill=wall, outline=dark, width=2)
    # facade highlight strip
    draw.rectangle([mx1,my,mx2,my+4], fill=hl)

    # windows grid
    for wy in range(my+10, int(h*0.72), 12):
        for wx in range(mx1+8, mx2-6, 13):
            lit = random.random() > 0.35
            wc  = (255,252,160) if lit else (80,105,145)
            draw.rounded_rectangle([wx,wy,wx+8,wy+8], radius=1, fill=wc, outline=(55,55,60),width=1)
            if lit:
                # window glow
                draw.rectangle([wx-1,wy-1,wx+9,wy+9], outline=(255,240,100,40))

    # roof details
    draw.rectangle([mx1,my-6,mx2,my], fill=dark)
    for rx in range(mx1+8, mx2-4, 12):
        draw.rectangle([rx,my-14,rx+6,my-6], fill=dark)

    # entrance
    ecx = (mx1+mx2)//2
    draw.rounded_rectangle([ecx-10,int(h*0.55),ecx+10,int(h*0.75)], radius=3,
                            fill=(30,30,35), outline=dark)

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


FLOWER_COLS = [
    (220,60,100),(240,130,30),(240,210,30),(80,160,220),(160,80,200),(255,120,150)
]

def _draw_flower(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _sky_ground(img,draw,w,h,
                sky1=(155,215,245),sky2=(210,240,255),gnd=(70,145,65))

    n_flowers = random.randint(2,3)
    positions = [(w//2+random.randint(-20,20), int(h*0.55)) for _ in range(n_flowers)]

    for (fx, gy) in positions:
        col   = random.choice(FLOWER_COLS)
        dark  = tuple(max(0,c-60) for c in col)
        n_pet = random.choice([5,6,7,8])
        pr    = random.randint(10,14)    # petal reach
        ps    = random.randint(5,7)      # petal size
        stem_h = random.randint(18,28)

        # stem
        draw.line([(fx,gy),(fx+random.randint(-4,4),gy-stem_h)], fill=(50,130,40), width=3)
        # leaves
        for sign in [-1,1]:
            lx = fx + sign*10
            ly = gy - stem_h//2
            draw.ellipse([lx-8,ly-4,lx+8,ly+4], fill=(45,120,35))

        # petals
        for i in range(n_pet):
            a  = math.radians(i*(360/n_pet))
            px = fx + int(pr*math.cos(a))
            py = (gy-stem_h) + int(pr*math.sin(a))
            draw.ellipse([px-ps,py-ps,px+ps,py+ps], fill=col, outline=dark, width=1)
            # petal highlight
            hpx = fx + int((pr-3)*math.cos(a))
            hpy = (gy-stem_h) + int((pr-3)*math.sin(a))
            draw.ellipse([hpx-2,hpy-2,hpx+2,hpy+2], fill=tuple(min(255,c+60) for c in col))

        # centre
        draw.ellipse([fx-6,gy-stem_h-6,fx+6,gy-stem_h+6], fill=(255,220,30), outline=(200,160,20),width=1)
        draw.ellipse([fx-3,gy-stem_h-3,fx+3,gy-stem_h+3], fill=(220,160,20))

    # grass tufts
    for gx in range(2,w-2,7):
        gh = random.randint(3,7)
        draw.line([(gx,int(h*0.55)),(gx-2,int(h*0.55)-gh)], fill=(50,115,40),width=1)

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


CAT_COLS = [
    (200,180,150),(90,75,65),(220,210,200),(50,50,55),(180,140,100)
]

def _draw_cat(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _sky_ground(img,draw,w,h,
                sky1=(145,205,240),sky2=(200,230,250),gnd=(85,145,75))

    col   = random.choice(CAT_COLS)
    dark  = tuple(max(0,c-55) for c in col)
    light = tuple(min(255,c+55) for c in col)
    gnd   = int(h*0.55)
    cx    = w//2

    # shadow
    draw.ellipse([cx-18,gnd+2,cx+18,gnd+8], fill=(0,0,0,40))

    # BODY
    draw.ellipse([cx-18,gnd-26,cx+18,gnd+4], fill=col)
    # belly highlight
    draw.ellipse([cx-10,gnd-20,cx+10,gnd+2], fill=light)

    # HEAD
    draw.ellipse([cx-15,gnd-50,cx+15,gnd-22], fill=col)
    # face highlight
    draw.ellipse([cx-9,gnd-46,cx+9,gnd-26], fill=light)

    # EARS
    for sign in [-1,1]:
        ex = cx + sign*12
        draw.polygon([(ex,gnd-48),(ex+sign*10,gnd-58),(ex+sign*4,gnd-36)],
                     fill=col, outline=dark)
        # inner ear
        draw.polygon([(ex,gnd-46),(ex+sign*6,gnd-54),(ex+sign*3,gnd-38)],
                     fill=(220,150,150))

    # EYES
    for sign in [-1,1]:
        ex = cx + sign*6
        ey = gnd-40
        draw.ellipse([ex-5,ey-4,ex+5,ey+4], fill=(50,200,80))
        draw.ellipse([ex-2,ey-4,ex+2,ey+4], fill=(20,20,20))
        draw.ellipse([ex-1,ey-3,ex+1,ey-1], fill=(255,255,255))

    # NOSE
    draw.polygon([(cx,gnd-32),(cx-3,gnd-29),(cx+3,gnd-29)], fill=(220,120,130))
    # mouth
    draw.arc([cx-5,gnd-30,cx,gnd-26], 180,360, fill=dark, width=1)
    draw.arc([cx,gnd-30,cx+5,gnd-26], 180,360, fill=dark, width=1)

    # WHISKERS
    for sign in [-1,1]:
        for wy in [-31,-29,-27]:
            draw.line([(cx,gnd+wy),(cx+sign*16,gnd+wy+sign*1)], fill=(200,200,200),width=1)

    # TAIL
    pts = []
    for i in range(15):
        t  = i/14
        tx = cx+18 + int(20*t)
        ty = gnd - int(5*math.sin(t*math.pi*2)) + int(t*12)
        pts.append((tx,ty))
    for i in range(len(pts)-1):
        draw.line([pts[i],pts[i+1]], fill=col, width=5)
    # tail tip
    draw.ellipse([pts[-1][0]-4,pts[-1][1]-4,pts[-1][0]+4,pts[-1][1]+4], fill=dark)

    # LEGS
    for sign in [-1,1]:
        lx = cx + sign*12
        draw.rounded_rectangle([lx-4,gnd-6,lx+4,gnd+12], radius=4, fill=col)
        # paw
        draw.ellipse([lx-5,gnd+9,lx+5,gnd+15], fill=light)

    img = img.filter(ImageFilter.GaussianBlur(0.35))
    return img


def _draw_traffic_light(w, h):
    img  = Image.new("RGBA",(w,h),(0,0,0,0))
    draw = ImageDraw.Draw(img,"RGBA")
    _road_bg(img,draw,w,h)

    gnd  = int(h*0.45)
    cx   = w//2 + random.randint(-12,12)
    pole_h = random.randint(24,32)

    # POLE
    draw.rounded_rectangle([cx-3,gnd-pole_h,cx+3,gnd+6],
                            radius=2, fill=(55,55,60), outline=(40,40,45))

    # HOUSING
    hx1,hx2 = cx-12, cx+12
    hy1,hy2 = gnd-pole_h-38, gnd-pole_h+2
    draw.rounded_rectangle([hx1,hy1,hx2,hy2], radius=6,
                            fill=(25,25,28), outline=(15,15,18), width=2)
    # housing highlight
    draw.rounded_rectangle([hx1+1,hy1+1,hx2-1,hy1+8], radius=4, fill=(40,40,44))

    # LIGHTS
    light_state = random.choice(["red","amber","green"])
    mid = (hx1+hx2)//2
    configs = [
        ("red",   mid, hy1+8,  (200,30,30),  (255,60,60),  True ),
        ("amber", mid, hy1+19, (200,130,20),  (255,185,30), False),
        ("green", mid, hy1+30, (20,160,50),   (50,220,80),  False),
    ]
    for name,lx,ly,off_col,on_col,_ in configs:
        active = (name == light_state)
        col = on_col if active else tuple(c//3 for c in on_col)
        draw.ellipse([lx-7,ly-7,lx+7,ly+7], fill=col, outline=(10,10,10),width=1)
        if active:
            # glow
            for gr in range(10,3,-1):
                ga = int(60*(1-gr/10))
                draw.ellipse([lx-gr,ly-gr,lx+gr,ly+gr],
                             fill=(*on_col[:3],ga))

    # visor shades
    for ly in [hy1+8, hy1+19, hy1+30]:
        draw.rounded_rectangle([hx1+1,ly-8,hx2-1,ly-5], radius=1, fill=(15,15,18))

    # BASE box
    draw.rounded_rectangle([cx-6,gnd-2,cx+6,gnd+6], radius=2, fill=(45,45,50))

    # Background elements
    _cloud(draw, 25, 18, 0.6)
    # second light in background (smaller)
    bcx = cx + random.choice([-30,32])
    if 8 < bcx < w-8:
        bhy = gnd - random.randint(18,26)
        draw.rounded_rectangle([bcx-7,bhy-22,bcx+7,bhy],
                               radius=4, fill=(22,22,25), outline=(15,15,18))
        for i,lc in enumerate([(180,20,20),(160,110,15),(15,140,40)]):
            lly = bhy-19+i*7
            ac = lc if i==1 else tuple(c//4 for c in lc)
            draw.ellipse([bcx-4,lly-4,bcx+4,lly+4], fill=ac)

    img = img.filter(ImageFilter.GaussianBlur(0.3))
    return img


# ═══════════════════════════════════════════════════════════
#  CATEGORY → FUNCTION MAP
# ═══════════════════════════════════════════════════════════

DRAW_FUNCTIONS = {
    "car":           _draw_car,
    "bus":           _draw_bus,
    "bicycle":       _draw_bicycle,
    "motorcycle":    _draw_motorcycle,
    "truck":         _draw_truck,
    "tree":          _draw_tree,
    "building":      _draw_building,
    "flower":        _draw_flower,
    "cat":           _draw_cat,
    "traffic_light": _draw_traffic_light,
}


def _img_to_b64(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def generate_captcha_grid() -> dict:
    target_cat = random.choice(VEHICLE_CATEGORIES)
    n_correct  = random.randint(2, 4)
    n_distract = GRID_SIZE - n_correct

    tile_cats  = [target_cat] * n_correct
    tile_cats += random.choices(DISTRACTOR_CATEGORIES, k=n_distract)
    random.shuffle(tile_cats)

    correct_indices = [i for i,c in enumerate(tile_cats) if c == target_cat]

    images = []
    for cat in tile_cats:
        img = DRAW_FUNCTIONS[cat](TILE_SIZE, TILE_SIZE)
        images.append(_img_to_b64(img))

    session[CAPTCHA_SESSION_KEY] = {
        "target":          target_cat,
        "correct_indices": correct_indices,
    }
    try:
        session.modified = True
    except AttributeError:
        pass

    return {
        "images": images,
        "prompt": f"Select all images containing <strong>{CATEGORY_LABELS[target_cat]}</strong>",
        "count":  n_correct,
    }


def validate_captcha(selected_str: str) -> bool:
    data = session.pop(CAPTCHA_SESSION_KEY, None)
    try:
        session.modified = True
    except AttributeError:
        pass
    if not data:
        return False
    correct = set(data.get("correct_indices", []))
    if not correct:
        return False
    try:
        submitted = set(int(x) for x in selected_str.split(",") if x.strip().isdigit())
    except (ValueError, AttributeError):
        return False
    return submitted == correct
