#!/usr/bin/env python3
import io, json, math, sys, urllib.request
from pathlib import Path
from PIL import Image

UA={"User-Agent":"caldas-world-builder/1.0"}

def fetch(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read()

def lon2x(lon,z): return (lon+180.0)/360.0*(2**z)
def lat2y(lat,z):
    latr=math.radians(lat)
    return (1-math.asinh(math.tan(latr))/math.pi)/2*(2**z)
def x2lon(x,z): return x/(2**z)*360.0-180.0
def y2lat(y,z): return math.degrees(math.atan(math.sinh(math.pi*(1-2*y/(2**z)))))

def terrarium_elev(rgb):
    r,g,b=rgb
    return r*256.0+g+b/256.0-32768.0

def main(cfg_path):
    cfg=json.load(open(cfg_path))
    z=int(cfg.get("zoom",12)); grid=int(cfg.get("grid",129))
    b=cfg["bbox"]
    x0=math.floor(lon2x(b["west"],z)); x1=math.floor(lon2x(b["east"],z))
    y0=math.floor(lat2y(b["north"],z)); y1=math.floor(lat2y(b["south"],z))
    wtiles=x1-x0+1; htiles=y1-y0+1
    img=Image.new("RGB",(wtiles*256,htiles*256))
    elev_tiles={}
    for ty in range(y0,y1+1):
      for tx in range(x0,x1+1):
        iy=(ty-y0)*256; ix=(tx-x0)*256
        imagery=Image.open(io.BytesIO(fetch(f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{ty}/{tx}"))).convert("RGB")
        img.paste(imagery,(ix,iy))
        eim=Image.open(io.BytesIO(fetch(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png"))).convert("RGB")
        elev_tiles[(tx,ty)]=eim

    full_bounds={
      "west":x2lon(x0,z),"east":x2lon(x1+1,z),
      "north":y2lat(y0,z),"south":y2lat(y1+1,z)
    }
    # Crop exactly to configured bbox for imagery.
    px0=(lon2x(b["west"],z)-x0)*256
    px1=(lon2x(b["east"],z)-x0)*256
    py0=(lat2y(b["north"],z)-y0)*256
    py1=(lat2y(b["south"],z)-y0)*256
    crop=img.crop((int(px0),int(py0),int(px1),int(py1)))
    if crop.width>1600:
        nh=round(crop.height*1600/crop.width); crop=crop.resize((1600,nh),Image.LANCZOS)

    def sample(lat,lon):
        xf=lon2x(lon,z); yf=lat2y(lat,z)
        tx=min(x1,max(x0,math.floor(xf))); ty=min(y1,max(y0,math.floor(yf)))
        px=min(255,max(0,int((xf-tx)*256))); py=min(255,max(0,int((yf-ty)*256)))
        return terrarium_elev(elev_tiles[(tx,ty)].getpixel((px,py)))

    elev=[]
    emin=1e9; emax=-1e9
    for gy in range(grid):
        lat=b["north"]+(b["south"]-b["north"])*gy/(grid-1)
        row=[]
        for gx in range(grid):
            lon=b["west"]+(b["east"]-b["west"])*gx/(grid-1)
            h=round(sample(lat,lon),2)
            emin=min(emin,h); emax=max(emax,h); row.append(h)
        elev.append(row)

    out=Path(cfg_path).parent/"geo"; out.mkdir(parents=True,exist_ok=True)
    crop.save(out/"terrain.jpg",quality=88,optimize=True,progressive=True)
    meta={
      "schema":"caldas.geo-terrain/v1",
      "id":cfg["id"],"center":cfg["center"],"bbox":b,
      "grid":grid,"min_elevation_m":round(emin,2),"max_elevation_m":round(emax,2),
      "vertical_scale":cfg.get("vertical_scale",1.0),
      "attribution":cfg.get("attribution",""),
      "elevations":elev
    }
    (out/"terrain.json").write_text(json.dumps(meta,separators=(",",":")))
    print(cfg["id"],crop.size,grid,round(emin,1),round(emax,1),out)

if __name__=="__main__":
    for p in sys.argv[1:]:
        main(p)
