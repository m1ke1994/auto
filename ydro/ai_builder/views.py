import io
import zipfile
from pathlib import Path
from django.conf import settings
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Project, Revision
from .design import STYLES, preview, source_files
from .jobs import project_dist, queue_project, refresh_project, visual_result, progress_event
from .provider import generate, mode, GenerationError

class ProjectInput(serializers.Serializer):
    name=serializers.CharField(max_length=120)
    prompt=serializers.CharField(max_length=8000)
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
        "id":str(p.id),"name":p.name,"prompt":p.prompt,"style":p.style,
        "created_at":p.created_at,"updated_at":p.updated_at,
        "published_revision":p.published_revision_id,"mode":mode(),"engine":p.engine,
        "generation_status":p.generation_status,"generation_stage":p.generation_stage,
        "generation_error":p.generation_error,
        "generation_event_at":progress_event(p),
        "preview_path":f"/studio-preview/{p.preview_token}/" if dist else "",
        "visual_review":visual_result(p,dist),
        "source_archive_available":bool(dist and (dist.parent/"tracknode-agent-site.zip").is_file()),
    }
    if detail:
        data["revisions"]=[revision_data(r) for r in p.revisions.all()[:30]]
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
            for active in Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")):
                refresh_project(active)
            if Project.objects.filter(owner=request.user,engine="cinematic",generation_status__in=("queued","running")).exists():
                return Response({"detail":"Дождитесь завершения текущей кинематографической генерации. Платные параллельные повторы отключены."},status=409)
            profile="cinema" if values["style"] in ("auto","cinema","3d") else ("premium" if values["style"]=="premium" else "standard")
            with transaction.atomic():
                p=Project.objects.create(owner=request.user,generation_status="queued",generation_stage="queued",**values)
                transaction.on_commit(lambda: queue_project(p,profile=profile,asset_style=asset_style,hero_mode=hero_mode,require_model=require_model))
            return Response(project_data(p,True),status=202)
        values.pop("engine",None)
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
