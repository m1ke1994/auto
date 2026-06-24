from rest_framework import serializers

from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.security import DomainValidationError, normalize_competitor_domains, normalize_public_domain


class CompetitorAnalysisCreateSerializer(serializers.Serializer):
    user_domain = serializers.CharField(allow_blank=True, max_length=255, required=False)
    competitor_domain = serializers.CharField(allow_blank=True, max_length=255, required=False)
    competitors = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=255),
        allow_empty=True,
        required=False,
    )

    def validate(self, attrs):
        site = self.context.get("site")
        raw_user_domain = str(attrs.get("user_domain") or "").strip()
        raw_competitor_domain = str(attrs.get("competitor_domain") or "").strip()

        try:
            if raw_user_domain or raw_competitor_domain:
                if not raw_user_domain:
                    raise DomainValidationError("Укажите домен вашего сайта.")
                if not raw_competitor_domain:
                    raise DomainValidationError("Укажите домен конкурента.")
                user_domain = normalize_public_domain(raw_user_domain, resolve_dns=False)
                competitor_domain = normalize_public_domain(raw_competitor_domain, resolve_dns=False)
            else:
                competitors = normalize_competitor_domains(attrs.get("competitors"), max_count=1)
                user_domain = normalize_public_domain(getattr(site, "domain", ""), resolve_dns=False)
                competitor_domain = competitors[0]
        except DomainValidationError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        if user_domain == competitor_domain:
            raise serializers.ValidationError({"detail": "Домен конкурента должен отличаться от вашего сайта."})

        attrs["user_domain"] = user_domain
        attrs["competitor_domain"] = competitor_domain
        attrs["competitors"] = [competitor_domain]
        return attrs


class CompetitorAnalysisSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(read_only=True)
    user_domain = serializers.SerializerMethodField()
    competitor_domain = serializers.SerializerMethodField()
    pdf_available = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = CompetitorAnalysis
        fields = (
            "id",
            "site_id",
            "user_domain",
            "competitor_domain",
            "competitors",
            "status",
            "pdf_available",
            "can_cancel",
            "errors",
            "created_at",
            "updated_at",
            "finished_at",
        )

    def get_user_domain(self, obj):
        return str(obj.user_domain or getattr(obj.site, "domain", "") or "").strip()

    def get_competitor_domain(self, obj):
        if obj.competitor_domain:
            return obj.competitor_domain
        competitors = obj.competitors if isinstance(obj.competitors, list) else []
        return str(competitors[0] if competitors else "").strip()

    def get_pdf_available(self, obj):
        return bool(obj.pdf_file)

    def get_can_cancel(self, obj):
        return str(obj.status or "").lower() in {"pending", "running", "processing"}
