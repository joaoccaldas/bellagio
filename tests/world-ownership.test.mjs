import test from 'node:test';
import assert from 'node:assert/strict';
import {validate} from '../tools/validate-world-ownership.mjs';
const base={schema:'caldas.world-registry/v1',worlds:[{id:'nice',route:'worlds/nice/',source:'joaoccaldas/bellagio',lat:43.7,lon:7.2}]};
test('unique valid source ownership',()=>assert.deepEqual(validate(base),[]));
test('duplicate id and route rejected',()=>{
 const data=structuredClone(base);data.worlds.push({...data.worlds[0]});
 assert.match(validate(data).join('; '),/duplicate id/);
 assert.match(validate(data).join('; '),/duplicate route/);
});
test('invalid source, path and coordinates rejected',()=>{
 const data=structuredClone(base);Object.assign(data.worlds[0],{source:'../bad',route:'../../secrets/',lat:92});
 assert.match(validate(data).join('; '),/invalid canonical source/);
 assert.match(validate(data).join('; '),/invalid or duplicate route/);
 assert.match(validate(data).join('; '),/invalid latitude/);
});
test('missing deployed local route reported',()=>assert.match(validate(base,{exists:()=>false}).join(' '),/local route missing/));
