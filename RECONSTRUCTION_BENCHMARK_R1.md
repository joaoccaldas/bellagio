# Bellagio Reconstruction Benchmark R1

Status: research-only branch.

## Question
For real-world venue/digital-twin capture, when should the unified 3D system use:
1. optimized mesh,
2. Gaussian splat,
3. hybrid mesh + splat?

## One-scene rule
Choose one bounded Bellagio scene and use the same camera path for all representations.

## Measure
- visual fidelity from canonical cameras;
- file/network size;
- time to first useful frame;
- frame time p50/p95/p99;
- memory pressure;
- mobile feasibility;
- collision/interaction suitability;
- editability;
- material/light controllability;
- compatibility with product placement;
- LOD/streaming behavior.

## Decision framework
Meshes win where editability, collision, semantic parts and relighting matter.
Splats may win where capture fidelity and time-to-reconstruction dominate.
Hybrid wins only if the extra pipeline complexity produces a measurable advantage.

## Rule
Do not promote neural reconstruction because it looks impressive in a demo. Promotion requires measurable benefit on our target devices and workflows.