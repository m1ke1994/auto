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

Worker feature negotiation prevents older running watchers from accepting
manual edit jobs. Update with start-studio.ps1 -RestartWatcher -Test while
the queue is empty. The startup script stops only the local backend before
replacing the idle watcher, so it cannot enqueue a job during the restart;
the supervisor automatically launches the new watcher. It then starts the
backend/frontend normally. No database or project artifacts are deleted.

## Local style controls

Static text leaves without existing custom/dynamic inline styles support color,
background color, bounded font sizes/weights, alignment, spacing and padding.
Only explicit allowed values enter source. A marked inline style is owned by
the editor; subsequent edits can update or remove it. Existing author styles
and cinematic captions remain protected. The UI previews styling through the
same isolated preview bridge. Styles are saved through the offline candidate
pipeline. Image replacement, layout rearrangement, dynamic content editing
and global themes remain outside this increment.

## Vue transport regression

The iframe bridge must receive plain data, never Vue reactive proxies. The
Studio component serializes the permitted style fields before postMessage;
transport failures show a local warning without discarding the draft. CI
also mounts the actual StudioView component in Vite, drives its text/style
controls in Chromium, checks the iframe and validates the mocked save request.
This complements (does not replace) end-to-end Docker/project acceptance.
