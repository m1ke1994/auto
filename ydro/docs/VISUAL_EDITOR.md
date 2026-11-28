# Visual Editor — stage 9, first increment

The Visual tab lists conservative static text leaves from the accepted Vue
source archive. A preview-only message bridge allows selecting a uniquely
matching rendered text node, showing a draft immediately, and resetting it.
The bridge is restricted to the existing localhost Studio parent origins and
is never written into source archives or exported builds.

Save submits a batch of up to 12 plain-text changes tied to the active
ProjectVersion and a fingerprint of all source files. Server and offline
container validate the exact fields again. The original source ZIP and
dist are read-only; the existing candidate workflow rebuilds and audits
the new source with no paid repair, then the user accepts or discards it.
Accepted changes enter version history. No new database migration.

Supported: literal leaf headings, labels, links, buttons, paragraphs and
similar visible text. Not supported: dynamic Vue expressions, generated
lists, 3D captions, actual contact links, component props, image replacement,
layout dragging or CSS editing. Ambiguous text cannot be reliably previewed
live; use the field list and review the built candidate. This is a conservative
first increment, not a full WYSIWYG editor.

Local: update backend/frontend via start-studio.ps1 after queued jobs finish.
The offline patch script is mounted from the checkout into the existing agent
image; no agent image rebuild is required. A live old watcher must be migrated
or restarted safely while idle to recognize the new manual edit dispatch.
