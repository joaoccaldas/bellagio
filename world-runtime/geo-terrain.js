export function localMeters(lat,lon,center){
  const kx=111320*Math.cos(center.lat*Math.PI/180);
  return [(lon-center.lon)*kx,(lat-center.lat)*110574];
}

export async function loadGeoTerrain(THREE,scene,{base='./geo/',segments=128,verticalScale=1,materialOptions={}}={}){
  const meta=await fetch(base+'terrain.json').then(r=>{if(!r.ok)throw new Error('terrain.json '+r.status);return r.json()});
  const tex=await new THREE.TextureLoader().loadAsync(base+'terrain.jpg');
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.anisotropy=4;
  const center=meta.center,b=meta.bbox,grid=meta.grid;
  const [xw,ys]=localMeters(b.south,b.west,center);
  const [xe,yn]=localMeters(b.north,b.east,center);
  const width=Math.abs(xe-xw),depth=Math.abs(yn-ys);
  const sx=Math.min(segments,grid-1),sz=Math.min(segments,grid-1);
  const g=new THREE.PlaneGeometry(width,depth,sx,sz);
  g.rotateX(-Math.PI/2);
  const p=g.attributes.position;
  const datum=meta.min_elevation_m;
  function sampleGrid(u,v){
    const gx=Math.max(0,Math.min(grid-1,u*(grid-1)));
    const gy=Math.max(0,Math.min(grid-1,(1-v)*(grid-1)));
    const ix=Math.min(grid-2,Math.floor(gx)),iy=Math.min(grid-2,Math.floor(gy));
    const ax=gx-ix,ay=gy-iy;
    const a=meta.elevations[iy][ix],b0=meta.elevations[iy][ix+1],c=meta.elevations[iy+1][ix],d=meta.elevations[iy+1][ix+1];
    return (a*(1-ax)+b0*ax)*(1-ay)+(c*(1-ax)+d*ax)*ay;
  }
  const uv=g.attributes.uv;
  for(let i=0;i<p.count;i++){
    const u=uv.getX(i),v=uv.getY(i);
    p.setY(i,(sampleGrid(u,v)-datum)*verticalScale);
  }
  g.computeVertexNormals();
  const m=new THREE.MeshStandardMaterial({map:tex,roughness:.96,metalness:.01,...materialOptions});
  const mesh=new THREE.Mesh(g,m);mesh.name='GEO_TERRAIN';scene.add(mesh);

  const heightAt=(lat,lon)=>{
    const u=(lon-meta.bbox.west)/(meta.bbox.east-meta.bbox.west);
    const v=(lat-meta.bbox.south)/(meta.bbox.north-meta.bbox.south);
    return (sampleGrid(u,v)-datum)*verticalScale;
  };
  const toWorld=(lat,lon,yOffset=0)=>{
    const [x,zNorth]=localMeters(lat,lon,center);
    return new THREE.Vector3(x,heightAt(lat,lon)+yOffset,-zNorth);
  };
  return {mesh,meta,heightAt,toWorld,center,width,depth,datum};
}
