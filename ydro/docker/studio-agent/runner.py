"""Local OpenHands SDK integration; no terminal and no general file access."""
import argparse
import json
import logging
import os
import signal
import tempfile
from collections.abc import Sequence

from pydantic import Field, SecretStr
from openhands.sdk import Action, Agent, Conversation, LLM, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import Tool, ToolExecutor, register_tool
from site_store import SiteStore
from media import MediaLibrary
from models3d import ModelLibrary
from sketchfab_models import SketchfabLibrary
from art_direction import PROFILES, build_prompt
from quality import quality_issues

MEDIA = MediaLibrary(os.environ.get("PEXELS_API_KEY",""))
MODELS = ModelLibrary()
SKETCHFAB = SketchfabLibrary(os.environ.get("SKETCHFAB_API_TOKEN",""),MODELS)
STORE = SiteStore(MEDIA, MODELS)

class SiteFileAction(Action):
    operation: str = Field(description="plan, write, read, list, quality_check, review, photo_search, photo_save, model_search, model_save, sketchfab_search, or sketchfab_save")
    path: str = Field(default="", description="Relative project path, e.g. src/App.vue")
    content: str = Field(default="", description="Full source, plan/review, or English search query for photo_search/model_search; model ID for model_save/sketchfab_save; English query for sketchfab_search")
    orientation: str = Field(default="landscape", description="Photo orientation: landscape, portrait, square")
    photo_id: int = Field(default=0, description="Photo id from search for photo_save")

class SiteFileObservation(Observation):
    message: str

    @property
    def to_llm_content(self) -> Sequence[TextContent]:
        return [TextContent(text=self.message)]

class SiteFileExecutor(ToolExecutor[SiteFileAction, SiteFileObservation]):
    def __call__(self, action, conversation=None):
        try:
            if action.operation == "plan":
                STORE.set_plan(action.content)
                print("STUDIO_STAGE: art direction ready",flush=True)
                message = "Art direction saved."
            elif action.operation == "quality_check":
                print("STUDIO_STAGE: source quality check",flush=True)
                issues=quality_issues(STORE.files,STORE.profile or "premium")
                message="Source structural checks passed (not browser or visual verification)." if not issues else "\n".join(issues)
            elif action.operation == "review":
                STORE.set_review(action.content)
                message = "Source self-review saved (not a build or visual check)."
            elif action.operation == "sketchfab_search":
                message = json.dumps(SKETCHFAB.search(action.content),ensure_ascii=False)
            elif action.operation == "sketchfab_save":
                message = json.dumps(SKETCHFAB.save(action.content.strip()),ensure_ascii=False)
                STORE.self_review = ""
            elif action.operation == "model_search":
                message = json.dumps(MODELS.search(action.content),ensure_ascii=False)
            elif action.operation == "model_save":
                message = json.dumps(MODELS.save(action.content.strip()),ensure_ascii=False)
                STORE.self_review = ""
            elif action.operation == "photo_search":
                message = json.dumps(MEDIA.search(action.content,action.orientation),ensure_ascii=False)
            elif action.operation == "photo_save":
                message = json.dumps(MEDIA.save(action.photo_id),ensure_ascii=False)
                STORE.self_review = ""
            elif action.operation == "write":
                if not STORE.design_brief:
                    raise ValueError("Save art direction first using plan.")
                STORE.write(action.path, action.content)
                print("STUDIO_SOURCE: "+action.path,flush=True)
                message = "Saved " + action.path
            elif action.operation == "read":
                message = STORE.read(action.path)
            elif action.operation == "list":
                message = "\n".join(sorted([*STORE.files,*MEDIA.assets,*MODELS.assets])) or "Empty project."
            else:
                message = "Invalid operation."
        except ValueError as exc:
            message = str(exc)
        return SiteFileObservation(message=message)

class SiteFileTool(ToolDefinition[SiteFileAction, SiteFileObservation]):
    @classmethod
    def create(cls, conv_state, **params):
        return [cls(
            description="Plan art direction, read/list/write project source, and record final source review. Save plan before writing. Write complete files under src/. Required: src/App.vue, src/style.css, and at least one Vue component. Run quality_check and fix the reported issues, then review after last write. photo_search searches Pexels by query and orientation; photo_save downloads a returned photo id as a local WebP, max six downloads. model_search searches Poly Haven CC0 models by English keywords; model_save saves a returned ID and all required glTF files locally. sketchfab_search searches licensed CC0/CC BY models for the authenticated local user; sketchfab_save imports a returned ID. Two model downloads total across providers. No shell or filesystem access.",
            action_type=SiteFileAction,
            observation_type=SiteFileObservation,
            executor=SiteFileExecutor(),
        )]

register_tool(SiteFileTool.name, SiteFileTool)

def make_agent(key, model):
    # Conservative peak/cache-miss USD rates per token (official pricing 2026-11-25).
    # SDK accounting is an estimate; a single completion may overshoot.
    input_rate, output_rate = {"deepseek-v4-pro": (1.32, 3.96), "deepseek-flash": (0.30, 1.20)}[model]
    llm = LLM(
        model="openai/" + model,
        base_url="https://api.deepseek.com/v1",
        api_key=SecretStr(key),
        usage_id="tracknode-agent",
        max_output_tokens=8192,
        input_cost_per_token=input_rate / 1_000_000,
        output_cost_per_token=output_rate / 1_000_000,
        litellm_extra_body={"thinking":{"type":"disabled"}},
        caching_prompt=False,
        log_completions_to_file=False,
    )
    return Agent(llm=llm, tools=[Tool(name=SiteFileTool.name)])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--check-media",action="store_true")
    parser.add_argument("--check-models",action="store_true")
    parser.add_argument("--check-sketchfab",action="store_true")
    parser.add_argument("--check-sketchfab-import",action="store_true")
    parser.add_argument("--prompt")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="premium")
    args=parser.parse_args()
    if args.check:
        # No LLM request, no key required.
        result=SiteFileExecutor()(SiteFileAction(operation="list"))
        assert result.message == "Empty project."
        make_agent("offline-check-only","deepseek-v4-pro")
        print("OpenHands SDK and bounded tool import OK; premium profiles initialized")
        return
    if args.check_sketchfab_import:
        try:
            matches=SKETCHFAB.search("chair")
            if not matches:
                raise ValueError("No matching model with verified license and geometry metadata.")
            errors=[]
            for item in matches[:2]:
                try:
                    asset=SKETCHFAB.save(item["id"])
                    print("SKETCHFAB_IMPORT_OK: "+asset["id"]+"; "+str(asset["bytes"])+" bytes; "+asset["license"],flush=True)
                    break
                except ValueError as exc:
                    errors.append(str(exc))
            else:
                raise ValueError(" | ".join(errors))
        except ValueError as exc:
            print(str(exc),flush=True)
            raise SystemExit(1) from None
        return
    if args.check_sketchfab:
        from sketchfab_probe import probe
        try:
            probe(os.environ.get("SKETCHFAB_API_TOKEN","").strip())
        except ValueError as exc:
            print(str(exc),flush=True)
            raise SystemExit(1) from None
        return
    if args.check_models:
        try:
            models=MODELS.search("chair")
            if not models:
                raise ValueError("No models found.")
            asset=MODELS.save(models[0]["id"])
            print("POLYHAVEN_OK: "+asset["id"]+" ("+str(asset["bytes"])+" bytes)")
        except ValueError as exc:
            print(str(exc))
            raise SystemExit(1) from None
        return
    if args.check_media:
        try:
            photos=MEDIA.search("misty forest","landscape")
            if not photos:
                raise ValueError("No photos returned.")
            photo=MEDIA.save(photos[0]["id"])
            print("PEXELS_OK: photo downloaded and optimized, id="+str(photo["id"]))
        except ValueError as exc:
            print(str(exc))
            raise SystemExit(1) from None
        return
    if not args.prompt or not 1 <= len(args.prompt.strip()) <= 8000:
        parser.error("--prompt is required, maximum 8000 characters")
    key=os.environ.get("STUDIO_AI_KEY","").strip()
    model=os.environ.get("STUDIO_AI_MODEL","deepseek-v4-pro").strip()
    if not key or model not in {"deepseek-v4-pro","deepseek-flash"}:
        parser.error("Configure a DeepSeek key and supported model in .env.studio.local")
    if not os.path.isdir("/output"):
        parser.error("Mount a new empty output directory at /output")
    if os.path.lexists("/output/tracknode-agent-site.zip"):
        parser.error("Use a fresh output directory; ZIP already exists")
    logging.disable(logging.INFO)
    # Independent wall-clock stop even if the model stalls. Container is disposable.
    signal.signal(signal.SIGALRM, lambda *_: os._exit(124))
    signal.alarm(900)
    try:
        STORE.profile=args.profile
        agent=make_agent(key,model)
        with tempfile.TemporaryDirectory(prefix="studio-") as workspace:
            conversation=Conversation(agent=agent,workspace=workspace,
                max_iteration_per_run=30,max_budget_per_run=0.60,visualizer=None)
            print("OPENHANDS_PROFILE: "+args.profile+" (art direction, source, self-review)",flush=True)
            conversation.send_message(build_prompt(args.prompt,args.profile,MEDIA.enabled,SKETCHFAB.enabled))
            conversation.run()
            STORE.export("/output/tracknode-agent-site.zip",model,args.profile)
        print("OPENHANDS_SOURCE_READY: /output/tracknode-agent-site.zip (build not verified)")
    except Exception as exc:
        # Avoid dumping credentials or untrusted prompts in exception logs.
        print("OpenHands generation failed: "+type(exc).__name__,flush=True)
        if isinstance(exc,ValueError):
            print("Source checks: "+" | ".join(quality_issues(STORE.files,args.profile)),flush=True)
        raise SystemExit(1) from None
    finally:
        signal.alarm(0)

if __name__=="__main__":
    main()
