"""Iconic 3D landmarks along the Las Vegas Strip (30 October 2022).

Replaces 2D satellite orthophoto street textures with authentic 3D features:
1. Elevated Strip Pedestrian Skyways (Tropicana & Flamingo intersections)
2. New York-New York Big Apple Roller Coaster (tubular red steel track & support pylons)
3. Welcome to Fabulous Las Vegas Sign (median south of Mandalay Bay)
4. The High Roller Observation Wheel (167.6 m white rim & spherical cabins)
5. Paris Las Vegas Montgolfier Balloon & Arc de Triomphe
6. The Mirage Volcano & Tropical Lagoon
7. The Venetian St. Mark's Campanile & Rialto Bridge
"""
import math
from mathutils import Vector

TAU = math.tau


def build_all(mb):
    """Add all Strip landmarks into the batched builders."""
    build_skyways(mb)
    build_roller_coaster(mb)
    build_welcome_sign(mb)
    build_high_roller(mb)
    build_paris_landmarks(mb)
    build_mirage_volcano(mb)
    build_venetian_landmarks(mb)


def build_skyways(mb):
    """Elevated pedestrian walkway bridges crossing Las Vegas Blvd and cross streets.
    Floor deck clearance is Z = 6.8 m (walkable in first-person camera mode!).
    """
    steel = mb.get('steel', mb.get('block'))
    glass = mb.get('glass', mb.get('block'))
    block = mb.get('block')

    # A. Tropicana Ave & Las Vegas Blvd (X ~ 255, Y ~ -1560)
    # Corners: NW=NY-NY (214, -1525), NE=MGM Grand (296, -1525),
    #          SW=Excalibur (214, -1595), SE=Tropicana (296, -1595)
    corners_trop = [
        (214.0, -1525.0),  # NW (NY-NY)
        (296.0, -1525.0),  # NE (MGM)
        (296.0, -1595.0),  # SE (Tropicana)
        (214.0, -1595.0),  # SW (Excalibur)
    ]
    _build_intersection_skyway(steel, glass, block, corners_trop)

    # B. Flamingo Rd & Las Vegas Blvd (X ~ 195, Y ~ 20)
    # Corners: NW=Caesars Palace (165, 55), NE=The Cromwell (235, 55),
    #          SE=Bally's (235, -15), SW=Bellagio (165, -15)
    corners_flam = [
        (165.0, 55.0),   # NW (Caesars)
        (235.0, 55.0),   # NE (Cromwell)
        (235.0, -15.0),  # SE (Bally's)
        (165.0, -15.0),  # SW (Bellagio)
    ]
    _build_intersection_skyway(steel, glass, block, corners_flam)


def _build_intersection_skyway(steel, glass, block, corners):
    """Build 4 elevated skybridge spans and 4 corner escalator/elevator towers."""
    Z_DECK = 6.8
    W_DECK = 5.4

    # 4 Bridge spans connecting adjacent corners
    for i in range(4):
        p0 = corners[i]
        p1 = corners[(i + 1) % 4]
        v0 = Vector((p0[0], p0[1], Z_DECK))
        v1 = Vector((p1[0], p1[1], Z_DECK))

        # Main floor slab
        steel.box_between(v0, v1, W_DECK, 0.4)

        # Balustrades / glass railings along each side (height 1.3 m)
        d = (v1 - v0).normalized()
        up = Vector((0, 0, 1))
        side = d.cross(up).normalized() * (W_DECK * 0.48)
        glass.box_between(v0 + side + Vector((0, 0, 0.7)), v1 + side + Vector((0, 0, 0.7)), 0.15, 1.2)
        glass.box_between(v0 - side + Vector((0, 0, 0.7)), v1 - side + Vector((0, 0, 0.7)), 0.15, 1.2)

        # Overhead arch canopy
        mid = (v0 + v1) * 0.5 + Vector((0, 0, 2.8))
        steel.box_between(v0 + Vector((0, 0, 2.2)), mid, 1.8, 0.3)
        steel.box_between(mid, v1 + Vector((0, 0, 2.2)), 1.8, 0.3)

        # Mid-span median support column down to street
        mp = (v0 + v1) * 0.5
        steel.cylinder((mp.x, mp.y, 0.0), 0.7, Z_DECK, n=10)

    # 4 Corner entrance pavilions / escalator shafts
    for c in corners:
        # Glass shaft
        glass.box((c[0], c[1], 4.5), (6.2, 6.2, 9.0))
        # Structural steel framing
        steel.box((c[0], c[1], 4.5), (6.6, 6.6, 9.2))
        # Street-level foundation
        block.box((c[0], c[1], 0.4), (7.2, 7.2, 0.8))


def build_roller_coaster(mb):
    """The Big Apple Coaster at New York-New York: bright red tubular steel track
    weaving past the skyscrapers, over the casino roof, and swooping towards the Strip.
    """
    coaster = mb.get('coaster', mb.get('block'))
    steel = mb.get('steel', mb.get('block'))

    # Waypoints through the resort
    pts = [
        Vector((180.0, -1460.0, 16.0)),  # Station dispatch
        Vector((182.0, -1485.0, 32.0)),  # Lift hill climb
        Vector((185.0, -1515.0, 54.0)),  # Lift hill crest (54 m)
        Vector((195.0, -1535.0, 34.0)),  # First steep drop
        Vector((212.0, -1550.0, 18.0)),  # Swoop along Tropicana Ave
        Vector((230.0, -1555.0, 14.0)),  # Banked turn
        Vector((242.0, -1530.0, 24.0)),  # Rise along Las Vegas Blvd
        Vector((240.0, -1495.0, 42.0)),  # Camelback hill
        Vector((234.0, -1465.0, 26.0)),  # Dive past Chrysler tower
        Vector((215.0, -1450.0, 32.0)),  # Heartline roll / twist
        Vector((198.0, -1468.0, 22.0)),  # Loop return
        Vector((190.0, -1495.0, 18.0)),  # Downward helix
        Vector((180.0, -1480.0, 16.0)),  # Brake run
        Vector((180.0, -1460.0, 16.0)),  # Station return
    ]

    # Track segments
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        # Main track box beam
        coaster.box_between(p0, p1, 1.4, 0.5)

        # Rails
        d = (p1 - p0).normalized()
        up = Vector((0, 0, 1))
        side = d.cross(up).normalized() * 0.55
        coaster.box_between(p0 + side + Vector((0, 0, 0.2)), p1 + side + Vector((0, 0, 0.2)), 0.22, 0.22)
        coaster.box_between(p0 - side + Vector((0, 0, 0.2)), p1 - side + Vector((0, 0, 0.2)), 0.22, 0.22)

        # Support columns down to ground/roof every node
        steel.cylinder((p0.x, p0.y, 0.0), 0.55, p0.z, n=8)


def build_welcome_sign(mb):
    """The iconic 'Welcome to Fabulous Las Vegas' neon sign on the median island south of Mandalay Bay."""
    steel = mb.get('steel', mb.get('block'))
    neon = mb.get('neon', mb.get('gold', mb.get('block')))
    block = mb.get('block')

    cx, cy = 328.2, -3430.3  # GPS: 36.08206° N, 115.17278° W

    # Paved median island
    block.cylinder((cx, cy, 0.0), 6.5, 0.4, n=16)
    block.cylinder((cx, cy, 0.0), 7.2, 0.25, n=16)

    # Two turquoise/blue support columns
    steel.cylinder((cx - 2.2, cy, 0.0), 0.25, 8.5, n=8)
    steel.cylinder((cx + 2.2, cy, 0.0), 0.25, 8.5, n=8)

    # Stretched Googie diamond sign board (width 7.6 m, height 4.4 m, centered at Z = 7.2 m)
    # Diamond 4 vertices in X-Z plane
    pts = [
        Vector((cx, cy, 7.2 + 2.2)),   # Top point
        Vector((cx + 3.8, cy, 7.2)),   # East point
        Vector((cx, cy, 7.2 - 2.2)),   # Bottom point
        Vector((cx - 3.8, cy, 7.2)),   # West point
    ]
    # Sign body
    for i in range(4):
        p0, p1 = pts[i], pts[(i + 1) % 4]
        steel.box_between(p0, p1, 0.35, 0.35)
    # Sign face in neon
    neon.box((cx, cy, 7.2), (6.4, 0.25, 3.6))

    # Yellow 8-pointed neon star on top of sign (Z = 9.8 m)
    neon.box((cx, cy, 9.8), (2.2, 0.2, 0.45))
    neon.box((cx, cy, 9.8), (0.45, 0.2, 2.2))
    neon.box((cx, cy, 9.8), (1.5, 0.2, 1.5), rot=math.pi / 4)


def build_high_roller(mb):
    """The High Roller Observation Wheel (167.6 m / 550 ft) at The LINQ / Flamingo area."""
    steel = mb.get('steel', mb.get('block'))
    glass = mb.get('glass', mb.get('block'))
    block = mb.get('block')

    cx, cy = 730.0, 488.0
    R = 79.0        # Wheel radius (158 m diameter, apex at Z = 167 m)
    Z_HUB = 88.0    # Center hub height

    # 4 Giant white tubular A-frame legs
    leg_coords = [
        (cx - 18.0, cy - 16.0),
        (cx - 18.0, cy + 16.0),
        (cx + 18.0, cy - 16.0),
        (cx + 18.0, cy + 16.0),
    ]
    hub_pos = Vector((cx, cy, Z_HUB))
    for lx, ly in leg_coords:
        steel.box_between(Vector((lx, ly, 0.0)), hub_pos, 2.2, 2.2)

    # Spindle hub cylinder
    steel.cylinder((cx, cy - 6.0, Z_HUB), 3.2, 12.0, n=12)

    # Outer wheel rim (32 chord segments)
    N_SEG = 32
    rim_pts = []
    for i in range(N_SEG):
        a = i * TAU / N_SEG
        # Wheel plane roughly along X-Z (rotated slightly to match LINQ promenade)
        px = cx + R * math.cos(a)
        pz = Z_HUB + R * math.sin(a)
        rim_pts.append(Vector((px, cy, pz)))

    for i in range(N_SEG):
        p0 = rim_pts[i]
        p1 = rim_pts[(i + 1) % N_SEG]
        steel.box_between(p0, p1, 1.6, 1.6)

        # Spoke cables radiating from hub to every second rim joint
        if i % 2 == 0:
            steel.box_between(hub_pos, p0, 0.25, 0.25)

    # 28 Spherical glass passenger observation cabins
    N_CAB = 28
    for i in range(N_CAB):
        a = i * TAU / N_CAB
        cpx = cx + R * math.cos(a)
        cpz = Z_HUB + R * math.sin(a)
        # Spherical cabin
        glass.cylinder((cpx, cy, cpz - 2.2), 2.4, 4.4, n=10, r_top=2.0)
        # Steel cabin ring
        steel.cylinder((cpx, cy, cpz - 0.2), 2.5, 0.4, n=10)

    # Boarding terminal building
    block.box((cx, cy, 4.5), (32.0, 24.0, 9.0))


def build_paris_landmarks(mb):
    """Paris Las Vegas Montgolfier Balloon marquee and Arc de Triomphe replica."""
    steel = mb.get('steel', mb.get('block'))
    gold = mb.get('gold', mb.get('block'))
    block = mb.get('block')

    # 1. Montgolfier Balloon (X ~ 315, Y ~ -115)
    bx, by = 315.0, -115.0
    # Marquee pedestal base
    block.cylinder((bx, by, 0.0), 6.5, 12.0, n=8)
    # Balloon gondola / basket
    gold.cylinder((bx, by, 12.0), 3.2, 3.2, n=8)
    # Hot air balloon envelope (reaching Z = 35 m)
    gold.cylinder((bx, by, 15.2), 3.2, 8.0, n=12, r_top=8.5)
    steel.cylinder((bx, by, 23.2), 8.5, 6.0, n=12, r_top=7.0)
    gold.cylinder((bx, by, 29.2), 7.0, 5.0, n=12, r_top=1.0)

    # 2. Arc de Triomphe replica (X ~ 325, Y ~ -75)
    ax, ay = 325.0, -75.0
    # Two massive monumental stone piers
    block.box((ax - 5.5, ay, 6.5), (4.5, 9.0, 13.0))
    block.box((ax + 5.5, ay, 6.5), (4.5, 9.0, 13.0))
    # Vaulted arch span and entablature
    block.box((ax, ay, 15.5), (16.0, 9.4, 5.0))
    # Attic cornice crown
    block.box((ax, ay, 18.8), (17.0, 9.8, 1.6))


def build_mirage_volcano(mb):
    """The Mirage Volcano & Tropical Lagoon (in operation October 2022)."""
    block = mb.get('block')
    neon = mb.get('neon', mb.get('gold', mb.get('block')))

    vx, vy = 240.0, 915.0  # In front of The Mirage

    # Tropical lagoon pool basin
    block.cylinder((vx, vy, 0.0), 22.0, 0.5, n=16)

    # Volcanic rock caldera tiers (reaching Z = 14 m)
    block.cylinder((vx, vy, 0.5), 15.0, 4.0, n=12, r_top=12.0)
    block.cylinder((vx, vy, 4.5), 12.0, 4.5, n=12, r_top=9.0)
    block.cylinder((vx, vy, 9.0), 9.0, 5.0, n=10, r_top=6.0)

    # Crater fire vent at peak
    neon.cylinder((vx, vy, 13.8), 3.5, 0.6, n=8)


def build_venetian_landmarks(mb):
    """The Venetian St. Mark's Campanile (96 m) and Rialto Bridge."""
    castle = mb.get('castle', mb.get('block'))
    gold = mb.get('gold', mb.get('block'))
    block = mb.get('block')

    cx, cy = 457.6, 944.4  # The Campanile

    # Square red-brick tower shaft (Z = 0 to 72 m)
    castle.box((cx, cy, 36.0), (12.0, 12.0, 72.0))

    # Open arched belfry (Z = 72 to 82 m)
    block.box((cx, cy, 77.0), (11.6, 11.6, 10.0))

    # Attic story (Z = 82 to 86 m)
    block.box((cx, cy, 84.0), (11.0, 11.0, 4.0))

    # Pyramidal copper spire (Z = 86 to 96 m)
    castle.cylinder((cx, cy, 86.0), 5.5, 10.0, n=4, r_top=0.1)

    # Golden angel weathervane atop spire
    gold.box((cx, cy, 97.2), (1.2, 1.2, 2.4))

    # Rialto Bridge arch across the canal
    rx, ry = 415.0, 930.0
    block.box((rx, ry, 2.2), (24.0, 8.0, 4.4))
