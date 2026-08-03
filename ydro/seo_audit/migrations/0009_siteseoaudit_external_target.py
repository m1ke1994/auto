# Generated manually for safe additive external SEO audit support.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("seo_audit", "0008_alter_seoissue_severity_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteseoaudit",
            name="requested_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="requested_seo_audits",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="siteseoaudit",
            name="target_url",
            field=models.URLField(blank=True, max_length=2048, null=True),
        ),
    ]
