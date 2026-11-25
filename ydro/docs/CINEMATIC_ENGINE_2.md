# Cinematic Engine 2 — phase 1

The existing preflight approval thresholds, required business sections, source gate, and offline audit stay active. Existing exported sites are unchanged. New exports include the trusted runtime src/cinematic-motion.js.

The preflight mode remains backward compatible. The generation runner derives a deterministic composition/motion/lighting recommendation from the brief and selected model, printed as STUDIO_CINEMATIC_DIRECTION. It is guidance, not a rigid template or a guarantee of cross-project uniqueness. Explicit edge-accent requests may use a compact model. Conditional assets avoid close detail emphasis and vehicles avoid floating.

Composition vocabulary: immersive_xl, museum_focus, editorial_split, asymmetric_split, floating_edges, detail_editorial, environment_stage, chapter_transformation, layered_depth. A photo-led fallback is available with no approved asset. OpenHands implements CSS layouts itself. No global carousel, automatic scene compositor or historical diversity database is introduced in this phase.

CinemaModel props: motion-preset, opening-yaw, motion-strength, lighting, model-role, and existing shots/ground/exposure/accent. Ten named scroll presets and five lighting schemes. Custom shots override presets and can independently animate modelYaw, lift (ground=false only), and light (key azimuth). Default custom behavior is retained. The motion system is scroll-driven; no autonomous idle loop. Chapter transitions/edge travel are authored in generated GSAP/CSS, not a shared cross-page renderer. Detail focus retains safe bounds, not an intentional extreme crop. Reduced motion uses the opening shot. A primary hero keeps original framing minimums; an accent has its own minimum host size and the same projected coverage and clipping checks. The audit accepts actual object/light movement for new presets rather than requiring camera movement only.

Local regression: Docker agent build runs existing Python tests including the recommendation and trusted-file tests. Run the standalone motion math tests from ydro with Node 22:
  node --experimental-default-type=module --test docker/studio-agent/cinematic-motion.test.mjs

Then run studio-quality.ps1 with a matching, existing preflight to test full browser output. Inspect desktop/mobile screenshots; technical checks are not artistic acceptance. No deployment is implied.
