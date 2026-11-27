"""Separate candidate revisions; original project remains readable until acceptance."""
import json
from django.utils import timezone
from .jobs import RUN_NAME, job_root, output_root, _atomic_json
from .models import BlockEdit

BLOCKS={"home":"Hero / Главная","about":"О компании","services":"Услуги","benefits":"Преимущества","contacts":"Контакты","header":"Header","footer":"Footer"}

def run_dist(name):
    if not isinstance(name,str) or not RUN_NAME.fullmatch(name):
        return None
    root=output_root().resolve()
    run=root/name
    raw_dist=run/"dist"
    if run.is_symlink() or raw_dist.is_symlink():
        return None
    dist=raw_dist.resolve()
    try:
        dist.relative_to(root)
    except ValueError:
        return None
    return dist if (dist/"index.html").is_file() else None

def state(edit):
    default={"status":"queued","stage":"queued","error":"","run_directory":"","updated_at":None}
    if edit.decision=="queue_failed":
        return {**default,"status":"failed","stage":"failed","error":"Unable to write local job queue"}
    try:
        path=job_root()/"status"/f"{edit.id}.json"
        data=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data,dict) or data.get("project_id")!=str(edit.id) or data.get("status") not in ("queued","running","failed","complete"):
            return default
        if data["status"]=="complete":
            name=data.get("run_directory")
            dist=run_dist(name)
            if not dist or name==edit.base_run or not name.startswith("block-edit-"):
                return {**default,"status":"failed","error":"Candidate build missing"}
            try:
                meta=json.loads((dist.parent/"studio-result.json").read_text(encoding="utf-8"))
            except (OSError,ValueError,TypeError):
                return {**default,"status":"failed","error":"Candidate audit metadata missing or invalid"}
            if not isinstance(meta,dict) or meta.get("technical_passed") is not True:
                return {**default,"status":"failed","error":"Candidate audit not passed"}
        return {key:data.get(key,value) for key,value in default.items()}
    except (OSError,ValueError,TypeError,AttributeError):
        return default

def block_edit_data(edit):
    s=state(edit)
    return {"id":str(edit.id),"block":edit.block,"instruction":edit.instruction,
            "decision":edit.decision,"created_at":edit.created_at,
            "base_run":edit.base_run,"status":s["status"],"stage":s["stage"],
            "error":s["error"],"updated_at":s["updated_at"],
            "candidate_run":s["run_directory"] if s["status"]=="complete" else "",
            "preview_path":f"/studio-preview/{edit.id}/" if s["status"]=="complete" else ""}

def active_for_owner(owner):
    return any(state(e)["status"] in ("queued","running") for e in BlockEdit.objects.filter(project__owner=owner,decision="pending"))

def queue_edit(edit, *, local_hero_film=False, hero_options=None):
    p=edit.project
    profile="cinema" if p.style in ("auto","cinema","3d") else "premium" if p.style=="premium" else "standard"
    payload={
        "version":1,"kind":"block_edit","project_id":str(edit.id),
        "name":p.name,"prompt":p.prompt,"profile":profile,
        "asset_style":"realistic","hero_mode":"auto","require_model":False,
        "base_run":edit.base_run,"block":edit.block,"instruction":edit.instruction,
        "upgrade_motion":edit.upgrade_motion,"created_at":timezone.now().isoformat()
    }
    if local_hero_film:
        payload["local_hero_film"]=True
        if hero_options:
            payload["hero_options"]=hero_options
    try:
        _atomic_json(job_root()/"pending"/f"{edit.id}.json",payload)
    except OSError:
        # Never leave an unqueued revision blocking the owner's future work.
        edit.decision="queue_failed"
        edit.save(update_fields=["decision"])
        raise
