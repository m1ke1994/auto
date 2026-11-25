"""Local OpenHands SDK integration; no terminal and no general file access."""
import argparse
import logging
import os
import signal
import tempfile
from collections.abc import Sequence

from pydantic import Field, SecretStr
from openhands.sdk import Action, Agent, Conversation, LLM, Observation, TextContent, ToolDefinition
from openhands.sdk.tool import Tool, ToolExecutor, register_tool
from site_store import SiteStore

STORE = SiteStore()

class SiteFileAction(Action):
    operation: str = Field(description="write, read, or list")
    path: str = Field(default="", description="Relative project path, e.g. src/App.vue")
    content: str = Field(default="", description="Full UTF-8 source for write")

class SiteFileObservation(Observation):
    message: str

    @property
    def to_llm_content(self) -> Sequence[TextContent]:
        return [TextContent(text=self.message)]

class SiteFileExecutor(ToolExecutor[SiteFileAction, SiteFileObservation]):
    def __call__(self, action, conversation=None):
        try:
            if action.operation == "write":
                STORE.write(action.path, action.content)
                message = "Saved " + action.path
            elif action.operation == "read":
                message = STORE.read(action.path)
            elif action.operation == "list":
                message = "\n".join(sorted(STORE.files)) or "Empty project."
            else:
                message = "Invalid operation."
        except ValueError as exc:
            message = str(exc)
        return SiteFileObservation(message=message)

class SiteFileTool(ToolDefinition[SiteFileAction, SiteFileObservation]):
    @classmethod
    def create(cls, conv_state, **params):
        return [cls(
            description="Read/list/write project source only. Write complete files under src/. Required: src/App.vue and src/style.css. No shell or filesystem access.",
            action_type=SiteFileAction,
            observation_type=SiteFileObservation,
            executor=SiteFileExecutor(),
        )]

register_tool(SiteFileTool.name, SiteFileTool)

def make_agent(key, model):
    llm = LLM(
        model="openai/" + model,
        base_url="https://api.deepseek.com/v1",
        api_key=SecretStr(key),
        usage_id="tracknode-agent",
        max_output_tokens=8192,
        litellm_extra_body={"thinking":{"type":"disabled"}},
        caching_prompt=False,
        log_completions_to_file=False,
    )
    return Agent(llm=llm, tools=[Tool(name=SiteFileTool.name)])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--prompt")
    args=parser.parse_args()
    if args.check:
        # No LLM request, no key required.
        result=SiteFileExecutor()(SiteFileAction(operation="list"))
        assert result.message == "Empty project."
        print("OpenHands SDK and bounded tool import OK")
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
    signal.alarm(600)
    try:
        agent=make_agent(key,model)
        with tempfile.TemporaryDirectory(prefix="studio-") as workspace:
            conversation=Conversation(agent=agent,workspace=workspace,
                max_iteration_per_run=12,max_budget_per_run=0.30,visualizer=None)
            conversation.send_message(
                "Build a polished, original Vue 3 website in Russian. Use SiteFileTool to actually save "
                "src/App.vue, src/style.css, and at least one meaningful Vue component. "
                "Only Vue and browser APIs are available; no external dependencies, fetches or remote assets. "
                "The entrypoint and Vite config are supplied separately. Use relative imports. "
                "Create a distinctive responsive layout with accessible navigation, editorial typography, "
                "CSS or inline SVG artwork and purposeful animations respecting reduced motion. "
                "No false client claims, testimonials, or invented contact details; clearly label examples. "
                "Do not collect real personal data or use external forms. Do not claim to have built or tested. "
                "Keep file sizes compact, save essential files early, and finish within 12 steps. "
                "User brief:\n" + args.prompt
            )
            conversation.run()
            STORE.export("/output/tracknode-agent-site.zip",model)
        print("OPENHANDS_SOURCE_READY: /output/tracknode-agent-site.zip (build not verified)")
    except Exception as exc:
        # Avoid dumping credentials or untrusted prompts in exception logs.
        print("OpenHands generation failed: "+type(exc).__name__,flush=True)
        raise SystemExit(1) from None
    finally:
        signal.alarm(0)

if __name__=="__main__":
    main()
