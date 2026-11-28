# TrackNode 2.0 Studio roadmap

This is a development roadmap, not a claim that every stage is production-ready.

| Stage | Module | Current scope |
|---|---|---|
| 1 | AI Architect | Existing source and design planning |
| 2 | OpenHands Developer | Existing controlled source generation |
| 3 | Asset Engine | Existing asset preflight and 3D selection |
| 4 | Quality Control | Existing build and browser gate |
| 5 | Studio Interface | Existing project and preview UI |
| 6 | AI Block Editor | Existing candidate workflow |
| 7 | Cinematic Engine 2.0 | Existing runtime and hero direction controls |
| 8 | Project Version Engine | History, restoration, integrity and explicit backup |
| 9 | Visual Editor | Static text, bounded styles, draft preview, candidate build; advanced image/layout/section editing pending |
| 10 | AI Block Editor 2.0 | Real semantic scopes, source/version checks, protected contract; broader dynamic/multi-section editing pending |
| 11 | GitHub Engine | Next: project repository lifecycle and export/sync, no automatic publication |
| 12 | Deployment Engine | Next: isolated staging, custom domains, publish/rollback and server security |
| 13 | TrackNode Integration | Next: analytics, SEO, leads, reports and subscription limits |

Each stage is reviewed independently. A green CI run is evidence of the
covered tests only; actual Windows Docker, browser UI and real projects require
local acceptance. Stage 9/10 are functional increments, not a claim of full
WYSIWYG/AI editing parity with other platforms.

Local after the queue is empty: pull, validate scripts, then
start-studio.ps1 -RestartWatcher -Test. Preserve local artifacts and DB.
