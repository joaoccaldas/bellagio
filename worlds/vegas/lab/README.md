# Bellagio · Caldas 3D Lab Wing

This is a cross-world integration adapter, not a copy of KONA room code.

## Rooms

- NOR // 3 → canonical KONA review runtime
- Beast Cave → canonical KONA world runtime
- Breitling × KONA → canonical KONA brand-room runtime

## Why this pattern

This is the integration model we want to prove first:

Bellagio owns navigation and the host world.
KONA owns the room/runtime source of truth.
The integration layer points to stable semantic room IDs/URLs.
No room geometry, product identity or renderer implementation is copied into Bellagio.

## What this proves

- cross-world navigation;
- canonical room identity;
- shared experience composition without repository forks;
- a path toward a future shared runtime/WorldSpec adapter.

## What it does not prove yet

- seamless GPU/runtime sharing;
- same-scene portals;
- shared physics state;
- shared avatar/equipment state;
- zero-load transitions.

Those require later experiments after the shared contracts are stable.
