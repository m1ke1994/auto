from rest_framework import serializers

from competitor_analysis.models import CompetitorAnalysis
from competitor_analysis.security import DomainValidationError, normalize_competitor_domains


class CompetitorAnalysisCreateSerializer(serializers.Serializer):
    competitors = serializers.ListField(
        child=serializers.CharField(allow_blank=True, max_length=255),
        allow_empty=True,
        required=True,
    )

    def validate_competitors(self, value):
        try:
            return normalize_competitor_domains(value, max_count=2)
        except DomainValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class CompetitorAnalysisSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(read_only=True)
    pdf_available = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = CompetitorAnalysis
        fields = (
            "id",
            "site_id",
            "competitors",
            "status",
            "pdf_available",
            "can_cancel",
            "errors",
            "created_at",
            "updated_at",
            "finished_at",
        )

    def get_pdf_available(self, obj):
        return bool(obj.pdf_file)

    def get_can_cancel(self, obj):
        return str(obj.status or "").lower() in {"pending", "running", "processing"}
