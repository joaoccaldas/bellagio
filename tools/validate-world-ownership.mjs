#!/usr/bin/env node
// Validates the existing world registry. Does not edit sources or resolve rights.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export function validate(registry,{exists=()=>true}={}){
 const errors=[];
 if(registry?.schema!=='caldas.world-registry/v1')errors.push('unsupported registry schema');
 if(!Array.isArray(registry?.worlds)||!registry.worlds.length)return [...errors,'worlds must be nonempty'];
 const ids=new Set(),routes=new Set();
 for(const [i,w] of registry.worlds.entries()){
  const tag='worlds['+i+']';
  if(!w||typeof w!=='object'){errors.push(tag+': not an object');continue}
  if(typeof w.id!=='string'||! /^[a-z][a-z0-9-]*$/.test(w.id)||ids.has(w.id))errors.push(tag+': invalid or duplicate id');
  else ids.add(w.id);
  if(typeof w.route!=='string'||! /^worlds\/[a-z0-9-]+\/$/.test(w.route)||routes.has(w.route))errors.push(tag+': invalid or duplicate route');
  else {routes.add(w.route);if(!exists(w.route))errors.push(tag+': local route missing')}
  if(typeof w.source!=='string'||! /^[-\w]+\/[-\w.]+$/.test(w.source))errors.push(tag+': invalid canonical source repository');
  if(typeof w.lat!=='number'||!Number.isFinite(w.lat)||Math.abs(w.lat)>90)errors.push(tag+': invalid latitude');
  if(typeof w.lon!=='number'||!Number.isFinite(w.lon)||Math.abs(w.lon)>180)errors.push(tag+': invalid longitude');
 }
 return errors;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const registry=JSON.parse(fs.readFileSync(path.join(root,'worlds/registry.json'),'utf8'));
 const errors=validate(registry,{exists:p=>fs.existsSync(path.join(root,p,'index.html'))});
 if(errors.length){console.error(errors.join('\n'));process.exitCode=1}
 else console.log('World ownership registry passed: '+registry.worlds.length+' unique worlds');
}
