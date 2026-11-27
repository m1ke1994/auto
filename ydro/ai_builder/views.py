import io
import zipfile
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project, Revision, BlockEdit
from .block_jobs import BLOCKS, state as edit_state, block_edit_data, active_for_owner, queue_edit, run_dist
from .design import STYLES, preview, source_files
from .jobs import project_dist, queue_project, refresh_project, visual_result, progress_event
from .provider import generate, mode, GenerationError
from .versions import archive_for, ensure_history, history_data, record as record_version

class ContactInput(serializers.Serializer):
    phone=serializers.RegexField(r"^\+?[0-9 ()-]{5,32}$",required=False,allow_blank=True,max_length=32)
    email=serializers.EmailField(required=False,allow_blank=True,max_length=180)
    address=serializers.CharField(required=False,allow_blank=True,max_length=250)
    telegram=serializers.URLField(required=False,allow_blank=True,max_length=250)
    vk=serializers.URLField(required=False,allow_blank=True,max_length=250)
    whatsapp=serializers.URLField(required=False,allow_blank=True,max_length=250)
    website=serializers.URLField(required=False,allow_blank=True,max_length=250)

    def validate(self, attrs):
        from urllib.parse import urlsplit
        import re
        attrs={k:v for k,v in attrs.items() if v}
        for key,value in attrs.items():
            if any(ord(c)<32 or ord(c)==127 for c in value):
                raise serializers.ValidationError({key:"Недопустимый символ."})
        if attrs.get("email") and not re.fullmatch(r"[^\s@<>\x22\x27:;,?&#%]+@[^\s@<>\x22\x27:;,?&#%]+\.[^\s@<>\x22\x27:;,?&#%]+",attrs["email"]):
            raise serializers.ValidationError({"email":"Укажите обычный публичный email."})
        phone=attrs.get("phone","")
        if phone and not 5<=sum(c.isdigit() for c in phone)<=15:
            raise serializers.ValidationError({"phone":"Укажите действительный формат номера."})
        for key in ("telegram","vk","whatsapp","website"):
            if key in attrs:
                url=urlsplit(attrs[key])
                if url.scheme not in ("http","https") or not url.hostname or url.username or url.password or "\\" in attrs[key] or any(c.isspace() for c in attrs[key]):
                    raise serializers.ValidationError({key:"Укажите публичную ссылку http:// или https://."})
        return attrs

class ProjectInput(serializers.Serializer):
    name=serializers.CharField(max_length=120)
    prompt=serializers.CharField(max_length=8000)
    contacts=ContactInput(required=False,default=dict)
    style=serializers.ChoiceField(choices=STYLES,default="auto")
    engine=serializers.ChoiceField(choices=("quick","cinematic"),default="cinematic")
    asset_style=serializers.ChoiceField(choices=("realistic","stylized"),default="realistic",write_only=True)
    hero_mode=serializers.ChoiceField(choices=("auto","immersive","product","split","cinematic","editorial","environment"),default="auto",write_only=True)
    require_model=serializers.BooleanField(default=False,write_only=True)

class EditInput(serializers.Serializer):
    instruction=serializers.CharField(max_length=8000)
    revision=serializers.IntegerField(required=False,min_value=1)

def revision_data(r):
    return {"id":r.id,"instruction":r.instruction,"html":r.html,"created_at":r.created_at,"provider":r.provider,"design":bool(r.design)}

def project_data(p,detail=False):
    p=refresh_project(p)
    dist=project_dist(p)
    data={
        "id":str(p.id),"name":p.name,"prompt":p.prompt,"style":p.style, "contacts":p.contacts,
        "created_at":p.created_at,"updated_at":p.updated_at,
        "published_revision":p.published_revision_id,"mode":mode(),"engine":p.engine,
        "generation_status":p.generation_status,"generation_stage":p.generation_stage,
        "generation_error":p.generation_error,
        "generation_event_at":progress_event(p),
        "preview_path":f"/studio-preview/{p.preview_token}/" if dist else "",
        "visual_review":visual_result(p,dist),
        "source_archive_available":bool(dist and (dist.parent/"tracknode-agent-site.zip").is_file()),
        "preview_version":p.run_directory,
        "block_edit":block_edit_data(latest) if (latest:=p.block_edits.first()) else None,
    }
    if detail:
        data["revisions"]=[revision_data(r) for r in p.revisions.all()[:30]]
        data["block_edits"]=[block_edit_data(e) for e in p.block_edits.all()[:30]]
        data["versions"]=history_data(p)
    return data

class StudioView(APIView):
    permission_classes=[IsAuthenticated]
    def initial(self,*args,**kwargs):
        if not getattr(settings,"STUDIO_DEMO_ENABLED",False):
            raise Http404
        super().initial(*args,**kwargs)
    def project(self,request,pk):
        return get_object_or_404(Project,pk=pk,owner=request.user)

class Config(StudioView):
    def get(self,request):
        provider=mode()
        configured=provider=="demo" or (provider in ("yandex","deepseek") and bool(settings.STUDIO_AI_KEY and settings.STUDIO_AI_MODEL and (provider!="yandex" or settings.STUDIO_AI_FOLDER)))
        return Response({
            "provider":provider,"configured":configured,"styles":STYLES,
            "cinematic_enabled":bool(getattr(settings,"STUDIO_CINEMATIC_ENABLED",False)),
            "cinematic_max_cost_usd":float(getattr(settings,"STUDIO_CINEMATIC_MAX_COST_USD",2.50)),
        })

class Projects(StudioView):
    def get(self,request):
        return Response([project_data(p) for p in Project.objects.filter(owner=request.user)[:100]])
    def post(self,request):
        s=ProjectInput(data=request.data)
        s.is_valid(raise_exception=True)
        if Project.objects.filter(owner=request.user).count()>=20:
            return Response({"detail":"Локальный лимит: 20 проектов."},status=400)
        values=dict(s.validated_data)
        asset_style=values.pop("asset_style")
        hero_mode=values.pop("hero_mode")
        require_model=values.pop("require_model")
        engine=values["engine"]
        if engine=="cinematic":
            if not getattr(settings,"STUDIO_CINEMATIC_ENABLED",False):
                return Response({"detail":"Кинематографический движок не запущен локально."},status=503)
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                for active in Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")):
                    refresh_project(active)
                if active_for_owner(request.user) or Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")).exists():
                    return Response({"detail":"Дождитесь завершения текущей кинематографической генерации. Платные параллельные повторы отключены."},status=409)
                profile="cinema" if values["style"] in ("auto","cinema","3d") else ("premium" if values["style"]=="premium" else "standard")
                with transaction.atomic():
                    p=Project.objects.create(owner=request.user,generation_status="queued",generation_stage="queued",**values)
                    transaction.on_commit(lambda: queue_project(p,profile=profile,asset_style=asset_style,hero_mode=hero_mode,require_model=require_model))
                return Response(project_data(p,True),status=202)
        values.pop("engine",None)
        contacts=values.pop("contacts",{})
        if contacts:
            return Response({"detail":"Контактная группа доступна в Cinematic Engine."},status=400)
        try:
            spec=generate(**values)
        except GenerationError as exc:
            return Response({"detail":str(exc)},status=502)
        with transaction.atomic():
            p=Project.objects.create(owner=request.user,engine="quick",**values)
            Revision.objects.create(project=p,instruction=p.prompt,html=preview(spec),design=spec,provider=mode())
        return Response(project_data(p,True),status=201)

class Detail(StudioView):
    def get(self,request,pk):
        return Response(project_data(self.project(request,pk),True))

class Edit(StudioView):
    def post(self,request,pk):
        p=self.project(request,pk)
        if p.engine=="cinematic":
            return Response({"detail":"Для кинематографического проекта создайте новое контролируемое задание; автоматические платные repair-циклы отключены."},status=400)
        s=EditInput(data=request.data)
        s.is_valid(raise_exception=True)
        if p.revisions.count()>=30:
            return Response({"detail":"Локальный лимит: 30 версий."},status=400)
        latest=p.revisions.first()
        base=get_object_or_404(p.revisions,pk=s.validated_data["revision"]) if "revision" in s.validated_data else latest
        instruction=s.validated_data["instruction"]
        try:
            spec=generate(p.name,p.prompt,p.style,instruction,base.design if base and base.design else None)
        except GenerationError as exc:
            return Response({"detail":str(exc)},status=502)
        with transaction.atomic():
            p=get_object_or_404(Project.objects.select_for_update(),pk=pk,owner=request.user)
            if p.revisions.count()>=30 or p.revisions.first().id!=latest.id:
                return Response({"detail":"Проект уже изменён. Откройте его заново."},status=409)
            Revision.objects.create(project=p,instruction=instruction,html=preview(spec),design=spec,provider=mode())
        return Response(project_data(p,True))

class Publish(StudioView):
    @transaction.atomic
    def post(self,request,pk,revision):
        p=get_object_or_404(Project.objects.select_for_update(),pk=pk,owner=request.user)
        if p.engine=="cinematic":
            return Response({"detail":"Кинематографический результат уже сохранён локально и не публикуется автоматически."},status=400)
        p.published_revision=get_object_or_404(p.revisions,pk=revision)
        p.save(update_fields=["published_revision"])
        return Response(project_data(p,True))

class Export(StudioView):
    def get(self,request,pk,revision):
        p=self.project(request,pk)
        r=get_object_or_404(p.revisions,pk=revision)
        output=io.BytesIO()
        with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as z:
            files=source_files(r.design) if r.design else {"index.html":r.html,"README.txt":"Legacy static demo."}
            for path,content in files.items():
                z.writestr(path,content)
        response=HttpResponse(output.getvalue(),content_type="application/zip")
        response["Content-Disposition"]='attachment; filename="tracknode-site.zip"'
        return response

class CinematicExport(StudioView):
    def get(self,request,pk):
        p=refresh_project(self.project(request,pk))
        dist=project_dist(p)
        archive=(Path(settings.STUDIO_OUTPUT_ROOT)/p.run_directory/"tracknode-agent-site.zip") if dist else None
        if not archive or not archive.is_file():
            raise Http404
        response=FileResponse(archive.open("rb"),content_type="application/zip")
        response["Content-Disposition"]='attachment; filename="tracknode-cinematic-site.zip"'
        return response

class HeroOptions(serializers.Serializer):
    direction=serializers.ChoiceField(("auto","large-static","large-dynamic","compact-product","organic","abstract","human-scale","universal"),required=False)
    motion=serializers.ChoiceField(("directed","still"),required=False)
    speed=serializers.ChoiceField(("focused","balanced","calm"),required=False)
    lighting=serializers.ChoiceField(("auto","softbox","dramatic"),required=False)
    captions=serializers.ListField(child=serializers.CharField(min_length=2,max_length=145),min_length=1,max_length=5,required=False)

    def validate_captions(self, captions):
        if len(set(captions))!=len(captions) or any("{" in text for text in captions):
            raise serializers.ValidationError("Use distinct plain-text captions.")
        return captions


class BlockInput(serializers.Serializer):
    instruction=serializers.CharField(max_length=4000)
    upgrade_motion=serializers.BooleanField(default=False)
    local_hero_film=serializers.BooleanField(default=False)
    hero_options=HeroOptions(required=False)

class Blocks(StudioView):
    def get(self,request,pk):
        p=refresh_project(self.project(request,pk))
        dist=project_dist(p)
        available=bool(dist and (dist.parent/"tracknode-agent-site.zip").is_file())
        return Response({"available":available,"blocks":[{"id":k,"label":v} for k,v in BLOCKS.items()] if available else []})

class RegenerateBlock(StudioView):
    @transaction.atomic
    def post(self,request,pk,block):
        # Serialize requests for this owner/project. One outstanding edit at a time.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        p=refresh_project(get_object_or_404(Project.objects.select_for_update(),pk=pk,owner=request.user))
        if not getattr(settings,"STUDIO_CINEMATIC_ENABLED",False):
            return Response({"detail":"Cinematic Engine недоступен."},status=503)
        if block not in BLOCKS:
            raise Http404
        dist=project_dist(p)
        if not dist or not (dist.parent/"tracknode-agent-site.zip").is_file():
            return Response({"detail":"Для правки необходим исходный ZIP готового Cinema-сайта."},status=400)
        for active in Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")):
            refresh_project(active)
        if active_for_owner(request.user) or Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")).exists():
            return Response({"detail":"Дождитесь завершения активного задания."},status=409)
        if any(edit_state(e)["status"]=="complete" for e in p.block_edits.filter(decision="pending")):
            return Response({"detail":"Сначала примите или отклоните готовый вариант блока."},status=409)
        if p.block_edits.count()>=30:
            return Response({"detail":"Локальный лимит: 30 правок проекта."},status=400)
        s=BlockInput(data=request.data)
        s.is_valid(raise_exception=True)
        local_film=s.validated_data["local_hero_film"]
        if local_film and block!="home":
            return Response({"detail":"Полноэкранная сцена доступна только для Hero."},status=400)
        edit=BlockEdit.objects.create(project=p,block=block,base_run=p.run_directory,base_stage=p.generation_stage,
            instruction="Full-screen two-act Hero film (local, no AI)" if local_film else s.validated_data["instruction"],upgrade_motion=block=="home" and (local_film or s.validated_data["upgrade_motion"]))
        transaction.on_commit(lambda:queue_edit(edit,local_hero_film=local_film,hero_options=s.validated_data.get("hero_options")))
        return Response(project_data(p,True),status=202)

class BlockDecision(StudioView):
    @transaction.atomic
    def post(self,request,pk,edit_id,action):
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        p=get_object_or_404(Project.objects.select_for_update(),pk=pk,owner=request.user)
        e=get_object_or_404(p.block_edits.select_for_update(),pk=edit_id)
        s=edit_state(e)
        if s["status"]!="complete":
            return Response({"detail":"Вариант ещё не прошёл техническую проверку."},status=409)
        if action=="accept" and e.decision=="pending" and p.run_directory==e.base_run:
            ensure_history(p)
            p.run_directory=s["run_directory"]
            p.generation_stage="technical-preview"
            e.decision="accepted"
        elif action=="discard" and e.decision=="pending":
            e.decision="discarded"
        elif action=="rollback" and e.decision=="accepted" and p.run_directory==s["run_directory"] and run_dist(e.base_run):
            if active_for_owner(request.user) or any(edit_state(x)["status"]=="complete" for x in p.block_edits.filter(decision="pending")):
                return Response({"detail":"Сначала завершите, примите или отклоните текущую правку."},status=409)
            ensure_history(p)
            p.run_directory=e.base_run
            p.generation_stage=e.base_stage
            e.decision="rolled_back"
        else:
            return Response({"detail":"Версия уже изменена или действие недоступно."},status=409)
        p.save(update_fields=["run_directory","generation_stage","updated_at"])
        e.save(update_fields=["decision"])
        if action=="accept":
            record_version(p,kind="accepted",instruction=e.instruction,edit=e)
        elif action=="rollback":
            previous=p.versions.filter(run_directory=e.base_run).first()
            record_version(p,kind="restored",restored_from=previous)
        return Response(project_data(p,True))


class RestoreVersionInput(serializers.Serializer):
    expected_version = serializers.UUIDField()


class ProjectVersions(StudioView):
    def get(self, request, pk):
        return Response(history_data(refresh_project(self.project(request, pk))))


class VersionRestore(StudioView):
    @transaction.atomic
    def post(self, request, pk, version_id):
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        p = get_object_or_404(Project.objects.select_for_update(), pk=pk, owner=request.user)
        if p.engine != "cinematic" or p.generation_status != "complete":
            return Response({"detail": "Восстановление доступно для готового сайта."}, status=409)
        data = RestoreVersionInput(data=request.data)
        data.is_valid(raise_exception=True)
        active = ensure_history(p)
        target = get_object_or_404(p.versions, pk=version_id)
        if not active or active.id != data.validated_data["expected_version"]:
            return Response({"detail": "Версия сайта уже изменилась. Обновите проект."}, status=409)
        if target.id == active.id:
            return Response(project_data(p, True))
        for pending in Project.objects.filter(owner=request.user, engine="cinematic",
                                               generation_status__in=("queued", "running")):
            refresh_project(pending)
        if (active_for_owner(request.user)
                or Project.objects.filter(owner=request.user, engine="cinematic",
                                          generation_status__in=("queued", "running")).exists()
                or any(edit_state(e)["status"] == "complete"
                       for e in p.block_edits.filter(decision="pending"))):
            return Response({"detail": "Сначала завершите, примите или отклоните активную правку."}, status=409)
        if not archive_for(target):
            return Response({"detail": "Сборка или исходный архив версии недоступны."}, status=409)
        p.run_directory = target.run_directory
        p.generation_stage = target.generation_stage
        p.save(update_fields=["run_directory", "generation_stage", "updated_at"])
        record_version(p, kind="restored", restored_from=target)
        return Response(project_data(p, True))


class VersionExport(StudioView):
    def get(self, request, pk, version_id):
        p = self.project(request, pk)
        version = get_object_or_404(p.versions, pk=version_id)
        archive = archive_for(version)
        if not archive:
            raise Http404
        response = FileResponse(archive.open("rb"), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="tracknode-version-{version.number}.zip"'
        return response
