# Shared carousel runtime v2

The trusted SceneCarousel hides its own horizontal scrollbar chrome without
disabling scroll. Previous/next, dots, keyboard, native horizontal trackpad
and touch are retained. Vertical wheel on the track advances one slide per
420 ms (no global wheel listener); at either edge it releases vertical page
scroll. Reduced motion uses immediate transitions. New exports include
tn-carousel-contract.json for all profiles. The browser audit records
carousel stage/reason and visible horizontal scroll containers, and rejects
new builds that violate the contract. Legacy artifacts without the contract
keep the old acceptance rules; existing accepted ZIP/dist files are not mutated.
The generator and audit Docker images must be rebuilt before new generation.
CI exercises the actual Vue component at desktop/tablet/mobile widths across
all six modes. Real touch hardware and existing project migration are separate
acceptance tasks.

Boundary release uses the selected first/last slide as well as physical scroll limits, because full-width slides can be centered before the last spacer gap. Browser failure artifacts contain active slide, position, page/track limits and a screenshot.
