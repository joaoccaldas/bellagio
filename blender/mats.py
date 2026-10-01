"""Blender materials (Cycles). Colours are linear; tuned against day photos of the tower."""
import bpy

M = {}


def principled(name, color, rough=.6, metal=0.0, emit=None, strength=0.0, coat=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Transmission Weight'].default_value = trans
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    M[name] = m
    return m


def noisy(name, color, var=.08, scale=.35, rough=.8):
    """Stucco-like: base colour modulated by low-frequency noise in object space."""
    m = principled(name, color, rough)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*[c * (1 - var) for c in color], 1)
    mix.inputs['B'].default_value = (*[c * (1 + var) for c in color], 1)
    nt.links.new(nz.outputs['Fac'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def diamonds(name, c1, c2, size=1.2):
    """Diamond lozenge frieze (cream / terracotta) using the box-projected UVs (metres/4)."""
    m = principled(name, c1, .7)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    uv = nt.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    k = 4 / size

    def expr(a, b_, op):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = op
        if isinstance(a, float):
            n.inputs[0].default_value = a
        else:
            nt.links.new(a, n.inputs[0])
        if isinstance(b_, float):
            n.inputs[1].default_value = b_
        else:
            nt.links.new(b_, n.inputs[1])
        return n.outputs[0]
    u = expr(sep.outputs['X'], k, 'MULTIPLY')
    v = expr(sep.outputs['Y'], k * 2, 'MULTIPLY')
    fu = expr(expr(expr(u, 1.0, 'FRACT') if False else expr(u, 1.0, 'MODULO'), .5, 'SUBTRACT'), 0.0, 'ABSOLUTE')
    fv = expr(expr(expr(v, 1.0, 'MODULO'), .5, 'SUBTRACT'), 0.0, 'ABSOLUTE')
    d = expr(expr(fu, fv, 'ADD'), .42, 'LESS_THAN')
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*c1, 1)
    mix.inputs['B'].default_value = (*c2, 1)
    nt.links.new(d, mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def build():
    noisy('stucco', (.62, .47, .33), var=.05)
    noisy('trim', (.74, .63, .49), var=.04)
    principled('sill', (.74, .66, .54), .7)
    diamonds('frieze', (.80, .71, .58), (.52, .25, .15))
    principled('dark', (.03, .03, .03), .6)
    principled('bronze', (.09, .075, .06), .38, metal=.8)
    room_glass('glass')
    principled('roof', (.30, .34, .35), .45, metal=.6)
    principled('copper', (.10, .30, .24), .45, metal=.4)
    principled('uplight', (1, .8, .6), 1, emit=(1.0, .72, .42), strength=0.0)
    principled('lantern_in', (.9, .8, .3), .6, emit=(1.0, .78, .25), strength=0.0)
    water()
    noisy('ground', (.30, .27, .23), var=.15, scale=.05, rough=.9)
    noisy('asphalt', (.06, .06, .06), var=.2, scale=.2, rough=.85)
    noisy('grass', (.07, .13, .04), var=.25, scale=.3, rough=.9)
    noisy('terracotta', (.42, .14, .07), var=.12, scale=.8, rough=.7)
    noisy('villa_a', (.72, .58, .40), .06)
    noisy('villa_b', (.66, .45, .30), .06)
    noisy('villa_c', (.78, .66, .50), .06)
    noisy('villa_d', (.62, .50, .38), .06)
    principled('podium_roof', (.55, .48, .40), .85)
    principled('context', (.25, .26, .28), .5, metal=.2)
    principled('desert', (.34, .28, .21), .95)
    principled('lakebed', (.03, .07, .06), .9)
    noisy('coping', (.62, .55, .45), .06, 1.0, .75)
    principled('basin', (.25, .24, .2), .9)
    principled('balustrade', (.78, .72, .62), .7)
    principled('iron', (.02, .02, .02), .45, metal=.8)
    principled('lamp', (1, .95, .8), .3, emit=(1.0, .85, .6), strength=0.0)
    noisy('rock', (.55, .45, .33), .12, 1.2, .85)
    principled('shutter', (.10, .16, .10), .6)
    principled('lead', (.22, .25, .26), .5, metal=.5)
    stripes('awning_red', (.55, .04, .03), (.8, .75, .65))
    stripes('awning_blue', (.03, .08, .30), (.8, .75, .65))
    principled('verdigris', (.10, .20, .16), .5, metal=.6)
    shadow_clear(principled('skylight', (.92, .97, .96), .0, trans=1.0))
    principled('dome_white', (.80, .76, .68), .5)
    noisy('concrete', (.40, .38, .35), .08, .5, .9)
    windows_grid('context_lit', (.20, .19, .17), (.015, .025, .035))
    principled('eiffel', (.22, .15, .10), .6, metal=.3)
    principled('pool_tile', (.25, .55, .65), .3)
    noisy('pool_deck', (.70, .64, .55), .05, 1.0, .8)
    principled('pool_water', (.05, .35, .45), .02)
    principled('bark', (.12, .09, .07), .9)
    noisy('leaf', (.05, .10, .03), .3, 3.0, .8)
    noisy('leaf_dark', (.025, .06, .025), .25, 3.0, .8)
    principled('palm_bark', (.20, .16, .11), .9)
    noisy('int_plaster', (.78, .68, .52), .04, .6, .6)
    principled('int_ceiling', (.82, .75, .62), .7)
    principled('marble_dark', (.10, .08, .06), .12, coat=.4)
    principled('wood', (.18, .08, .035), .45, coat=.3)
    principled('gold', (.83, .62, .28), .28, metal=1.0)
    principled('lightbox', (1, 1, 1), .5, emit=(1.0, .96, .88), strength=6.0)
    chihuly_glass()
    for n, c in (('flower_pink', (.85, .12, .35)), ('flower_white', (.85, .85, .80)), ('flower_yellow', (.9, .65, .03)),
                 ('flower_red', (.70, .02, .02)), ('flower_purple', (.30, .08, .55))):
        blooms(n, c)
    blooms('blossom', (.95, .55, .65), leaf=(.25, .12, .12), scale=9.0, cover=.8)
    noisy('topiary', (.03, .09, .02), .3, 5.0, .85)
    return M


def chihuly_glass():
    """Hand-blown glass: colour from the per-piece attribute, thin-walled transmission, a little glow
    from the light box above (the ceiling is backlit)."""
    m = principled('chihuly', (1, 1, 1), .08, trans=.85)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeVertexColor')
    at.layer_name = 'Col'
    nt.links.new(at.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(at.outputs['Color'], b.inputs['Emission Color'])
    b.inputs['Emission Strength'].default_value = 1.4
    b.inputs['Transmission Weight'].default_value = .45
    b.inputs['IOR'].default_value = 1.5
    b.inputs['Thin Film Thickness'].default_value = 0.0
    return m


def stripes(name, c1, c2, n=8.0):
    m = principled(name, c1, .8)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = n
    nt.links.new(sep.outputs['X'], mul.inputs[0])
    md = nt.nodes.new('ShaderNodeMath'); md.operation = 'PINGPONG'; md.inputs[1].default_value = .5
    nt.links.new(mul.outputs[0], md.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = .25
    nt.links.new(md.outputs[0], gt.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*c1, 1); mix.inputs['B'].default_value = (*c2, 1)
    nt.links.new(gt.outputs[0], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m


def windows_grid(name, wall, win):
    """Context towers: a brick texture reads as a window grid at distance."""
    m = principled(name, wall, .6)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Scale'].default_value = .28
    br.inputs['Mortar Size'].default_value = .35
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = .9
    br.inputs['Color1'].default_value = (*win, 1)
    br.inputs['Color2'].default_value = (*[c * 1.3 for c in win], 1)
    br.inputs['Mortar'].default_value = (*wall, 1)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    nt.links.new(sep.outputs['X'], add.inputs[0]); nt.links.new(sep.outputs['Y'], add.inputs[1])
    nt.links.new(add.outputs[0], comb.inputs['X']); nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
    nt.links.new(comb.outputs['Vector'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    return m


def water():
    """Lake: teal, lightly wind-rippled (bump from two noise octaves)."""
    m = principled('water', (.012, .05, .045), .04)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 2.2, 1.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = .9
    nz.inputs['Detail'].default_value = 8
    nz.inputs['Roughness'].default_value = .6
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .25
    bump.inputs['Distance'].default_value = .05
    nt.links.new(nz.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def blooms(name, color, leaf=(.02, .07, .015), scale=14.0, cover=.62):
    """Flower beds: Voronoi cells = individual blooms (hue-jittered), gaps = foliage."""
    m = principled(name, color, .75)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.feature = 'F1'
    vo.inputs['Scale'].default_value = scale
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = cover * .55
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = cover * .55 + .08
    ramp.color_ramp.elements[1].color = (0, 0, 0, 1)
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac'])
    hue = nt.nodes.new('ShaderNodeHueSaturation')
    hue.inputs['Color'].default_value = (*color, 1)
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'MULTIPLY_ADD'
    sub.inputs[1].default_value = .06; sub.inputs[2].default_value = .47
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(vo.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs[0], sub.inputs[0])
    nt.links.new(sub.outputs[0], hue.inputs['Hue'])
    val = nt.nodes.new('ShaderNodeMath'); val.operation = 'MULTIPLY_ADD'
    val.inputs[1].default_value = .5; val.inputs[2].default_value = .75
    nt.links.new(sep.outputs[1], val.inputs[0])
    nt.links.new(val.outputs[0], hue.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*leaf, 1)
    nt.links.new(ramp.outputs['Color'], mix.inputs['Factor'])
    nt.links.new(hue.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .6
    nt.links.new(ramp.outputs['Color'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


NIGHT = {'on': False}


def room_glass(name):
    """Hotel glass: dark reflective by day; at night ~55% of rooms glow warm behind curtains.
    Room choice comes from the per-window random in the WIN uv layer (x), quadrant-split into 4 rooms."""
    m = principled(name, (.006, .010, .010), .03)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = .9
    uvw = nt.nodes.new('ShaderNodeUVMap'); uvw.uv_map = 'WIN'
    uv0 = nt.nodes.new('ShaderNodeUVMap'); uv0.uv_map = 'UVMap'
    s0 = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uv0.outputs['UV'], s0.inputs['Vector'])
    sw = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(uvw.outputs['UV'], sw.inputs['Vector'])
    # quadrant index q = floor(u*2) + 2*floor(v*2); per-room random = fract(r * 7.13 + q * .37)
    def op(o, a, bb=None, v=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = o
        for k, x in enumerate((a, bb)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[k].default_value = x
            else:
                nt.links.new(x, n.inputs[k])
        return n.outputs[0]
    qu = op('FLOOR', op('MULTIPLY', s0.outputs['X'], 2.0))
    qv = op('FLOOR', op('MULTIPLY', s0.outputs['Y'], 2.0))
    q = op('ADD', qu, op('MULTIPLY', qv, 2.0))
    r = op('FRACT', op('ADD', op('MULTIPLY', sw.outputs['X'], 7.13), op('MULTIPLY', q, .37)))
    lit = op('MULTIPLY', op('LESS_THAN', r, .30), op('ADD', .35, op('MULTIPLY', op('FRACT', op('MULTIPLY', r, 31.0)), .9)))
    warm = nt.nodes.new('ShaderNodeMix'); warm.data_type = 'RGBA'
    warm.inputs['A'].default_value = (1.0, .62, .30, 1)
    warm.inputs['B'].default_value = (1.0, .82, .55, 1)
    nt.links.new(op('FRACT', op('MULTIPLY', r, 13.0)), warm.inputs['Factor'])
    nt.links.new(warm.outputs['Result'], b.inputs['Emission Color'])
    k = nt.nodes.new('ShaderNodeValue'); k.name = 'NIGHT_GAIN'; k.outputs[0].default_value = 0.0
    nt.links.new(op('MULTIPLY', lit, k.outputs[0]), b.inputs['Emission Strength'])
    # seen from inside (back faces) the pane is clear glass with a faint reflection
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = .02
    inner = nt.nodes.new('ShaderNodeMixShader'); inner.inputs['Fac'].default_value = .08
    nt.links.new(tr.outputs[0], inner.inputs[1]); nt.links.new(gl.outputs[0], inner.inputs[2])
    mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(geo.outputs['Backfacing'], mx.inputs['Fac'])
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(inner.outputs[0], mx.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath')
    mx2 = nt.nodes.new('ShaderNodeMixShader')       # let sun through for interiors behind the facade
    nt.links.new(lp.outputs['Is Shadow Ray'], mx2.inputs['Fac'])
    nt.links.new(mx.outputs[0], mx2.inputs[1]); nt.links.new(tr.outputs[0], mx2.inputs[2])
    nt.links.new(mx2.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m


def shadow_clear(m):
    """Glass that lets direct light through (Cycles has no caustics by default)."""
    nt = m.node_tree
    out = nt.nodes['Material Output']
    b = nt.nodes['Principled BSDF']
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], mix.inputs['Fac'])
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    return m


def set_night(on, glass_gain=1.6):
    """Switch emissive materials between day and night."""
    NIGHT['on'] = on
    for name, s in (('uplight', 55.0), ('lamp', 30.0), ('lantern_in', 18.0)):
        if name in M:
            M[name].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = s if on else 0.0
    for m in M.values():
        n = m.node_tree.nodes.get('NIGHT_GAIN') if m.node_tree else None
        if n:
            n.outputs[0].default_value = (glass_gain if m.name != 'spray' else .35) if on else 0.0
