"""Static fountain 'moment' for hero renders (the browser animates the full show).

Heights are the published maxima (Wikipedia, Fountains of Bellagio): oarsmen 77 ft, mini-shooters 100 ft,
super-shooters 240 ft, extreme-shooters 460 ft. Positions: survey.fountain_nozzles() (satellite pipe layout)."""
import math, random, json, os
import bpy
from mathutils import Vector
import survey as S
from geo import MB

FT = .3048
G = 9.81
MAXH = {'oar': 77 * FT, 'mini': 100 * FT, 'super': 240 * FT, 'extreme': 460 * FT}
rnd = random.Random(5)


def spray_material(name='spray'):
    """Water spray as a scattering volume inside each jet tube (surface fully transparent).
    Density is broken up by noise so jets read as streaming, aerated water; night emission is
    added at the base (the underwater lamps light the columns from below)."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    nt.links.new(tr.outputs[0], out.inputs['Surface'])
    vol = nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (.95, .97, 1.0, 1)
    vol.inputs['Anisotropy'].default_value = .6
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.2, 1.2, .25)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = .38; mr.inputs['From Max'].default_value = .75
    mr.inputs['To Min'].default_value = 0.02; mr.inputs['To Max'].default_value = .7
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs[0], vol.inputs['Density'])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.inputs[1].default_value = -1 / 25
    nt.links.new(sep.outputs['Z'], k.inputs[0])
    ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'EXPONENT'
    nt.links.new(k.outputs[0], ex.inputs[0])
    gain = nt.nodes.new('ShaderNodeValue'); gain.name = 'NIGHT_GAIN'; gain.outputs[0].default_value = 0.0
    es = nt.nodes.new('ShaderNodeMath'); es.operation = 'MULTIPLY'
    nt.links.new(ex.outputs[0], es.inputs[0]); nt.links.new(gain.outputs[0], es.inputs[1])
    es2 = nt.nodes.new('ShaderNodeMath'); es2.operation = 'MULTIPLY'
    nt.links.new(es.outputs[0], es2.inputs[0]); nt.links.new(mr.outputs[0], es2.inputs[1])
    nt.links.new(es2.outputs[0], vol.inputs['Emission Strength'])
    vol.inputs['Emission Color'].default_value = (1.0, .96, .88, 1)
    nt.links.new(vol.outputs[0], out.inputs['Volume'])
    return m


def jet(mb, p0, v, t_end, r0, r1, sides=8, segs=22):
    """Tube along a ballistic path, radius growing as the stream breaks up."""
    rings = []
    prev_n = None
    for i in range(segs + 1):
        t = t_end * i / segs
        p = p0 + v * t + Vector((0, 0, -.5 * G * t * t))
        d = (v + Vector((0, 0, -G * t))).normalized()
        n = d.orthogonal().normalized() if prev_n is None else (prev_n - d * prev_n.dot(d)).normalized()
        prev_n = n
        b = d.cross(n)
        u = i / segs
        r = (r0 + (r1 - r0) * u ** 1.3) * min(1.0, (1 - u) * 6 + .15)
        rings.append([p + (n * math.cos(a) + b * math.sin(a)) * r for a in [k / sides * math.tau for k in range(sides)]])
    for i in range(segs):
        for k in range(sides):
            k2 = (k + 1) % sides
            mb.quad(rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k], 0)


def moment(name='finale'):
    """One frozen instant of a show: which nozzles fire, how high, which tilt."""
    out = []
    for nz in S.fountain_nozzles():
        k, g, u = nz['k'], nz['g'], nz['u']
        h, tilt, az = 0.0, 0.0, 0.0
        if name == 'finale':
            if g == 'front':
                continue
            if k == 'extreme':
                h = MAXH[k] * (.85 + .15 * rnd.random())
            elif k == 'super':
                h = MAXH[k] * (.45 + .2 * math.sin(u * 20) ** 2)
            elif k == 'oar':
                h, tilt = MAXH[k] * .8, math.radians(28)
            elif g in ('ring_in', 'ring_n', 'ring_s'):
                h, tilt = MAXH[k] * .45, math.radians(18)
            elif g == 'arc':
                continue
        elif name == 'arcs':
            if k == 'oar' or g.startswith('ring'):
                h, tilt = MAXH['oar'] * .75, math.radians(35)
        if h <= 0:
            continue
        # oarsmen / ring jets lean outward from their ring centre, arc jets sway along the curve
        if g.startswith('ring'):
            c = {'ring_in': S.RING_BIG[0], 'ring_out': S.RING_BIG[0], 'ring_n': S.RING_N[0], 'ring_s': S.RING_S[0]}[g]
            az = math.atan2(nz['y'] - c[1], nz['x'] - c[0])
        else:
            az = math.sin(u * 31) * math.pi
            tilt = tilt or math.radians(6) * math.sin(u * 17)
        out.append((nz['x'], nz['y'], h, tilt, az, k))
    return out


def build(coll, mat, name='finale'):
    mb = MB('FOUNTAIN_jets', [mat])
    mist = MB('FOUNTAIN_mist', [mat])
    z0 = S.LAKE_LEVEL
    for x, y, h, tilt, az, k in moment(name):
        vz = math.sqrt(2 * G * h)
        vh = vz * math.tan(tilt)
        v = Vector((math.cos(az) * vh, math.sin(az) * vh, vz))
        t_up = vz / G
        t_end = t_up * 2.0
        r0 = {'oar': .06, 'mini': .07, 'super': .11, 'extreme': .16}[k]
        r1 = .35 + h * .035
        jet(mb, Vector((x, y, z0)), v, t_end, r0, r1)
        if k == 'extreme':
            mist.dome((x, y, 0), 3.0, 2.5, n=10, rings=4, m=0, z0=z0)
    return [mb.build(coll, smooth=True), mist.build(coll, smooth=True)]
