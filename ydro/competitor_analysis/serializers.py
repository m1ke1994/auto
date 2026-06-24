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
            return normalize_competitor_domains(value, max_count=3)
        except DomainValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class CompetitorAnalysisSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(read_only=True)
    pdf_available = serializers.SerializerMethodField()

    class Meta:
        model = CompetitorAnalysis
        fields = (
            "id",
            "site_id",
            "competitors",
            "status",
            "pdf_available",
            "errors",
            "created_at",
            "updated_at",
            "finished_at",
        )

    def get_pdf_available(self, obj):
        return bool(obj.pdf_file)
