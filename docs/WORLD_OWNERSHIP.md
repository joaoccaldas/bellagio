# One canonical source per world
As of 2026-10-23. This document clarifies the existing `worlds/registry.json` rather than creating a new ownership registry.

| World ID | Route host / portal | Existing canonical source | Status of ownership claim |
| --- | --- | --- | --- |
| vegas | bellagio/worlds/vegas/ | joaoccaldas/bellagio | declared in current registry |
| nice | bellagio/worlds/nice/ | joaoccaldas/bellagio | declared in current registry |
| kona | bellagio/worlds/kona/ | joaoccaldas/studio-kona | declared in current registry |
| st-george | bellagio/worlds/st-george/ | joaoccaldas/canyonmuseum | declared in current registry |

A portal route is **not** a second owner of the underlying scene. The `source` field describes existing declared provenance, not a guarantee that route bytes always derive from the source HEAD, nor a license grant.

## Rules
- Bellagio's `worlds/registry.json` owns **portal routing and declared source mapping** only.
- Kona.m's consumer app owns its own UI, progression, room identities, asset manifests and release pipeline. It must not acquire authority over the Studio Kona geographic world by proxy.
- Each referenced source repository owns its source code/assets subject to its existing authority docs. Do not transfer ownership by changing the portal registry alone.
- World IDs and routes must be unique. Run `node tools/validate-world-ownership.mjs` and `node --test tests/world-ownership.test.mjs`.
- Changes of `source` require dedicated migration review: pinned before/after commit, file/asset provenance, licensing, regression tests, deployment verification, and reversible redirect.
- Do not delete a source or fork after updating a `source` value. Historical commits and source manifests remain evidence.
- Distinguish duplicate source implementations from intentional different consumers, cinematics, studios or derivatives.

## Unresolved
- `luxor` is not presently defined as a distinct entry in the inspected portal registry; its actual canonical package is unverified.
- A cross-project canonical **platform library** is not yet approved. Shared contracts should be extracted only after proven adoption by two consumers.
- Registry validation cannot prove actual scene equivalence, art rights, CI success, mobile performance or Greatlinq compatibility.
- Routes may be assembled or proxied; provenance must be verified against pinned build artifacts before commercial use.

## Safe convergence pathway
1. Audit the existing source and deployment SHA for each route.
2. Compare exact asset fingerprints and rendering/behavior traces, preserving variants.
3. Classify each implementation: canonical, derivative, experiment, historical, or unresolved.
4. Migrate one supported consumer at a time behind a reversible adapter.
5. Re-run content, license, visual, accessibility, mobile, performance and security gates at the exact release SHA.
6. Share lessons through source-linked ADRs and knowledge records, not speculative copying of private material into public repos.
