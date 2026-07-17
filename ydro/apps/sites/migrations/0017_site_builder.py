from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0016_site_ai_generation_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(max_length=100, unique=True, verbose_name="Template key")),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                ("category", models.CharField(blank=True, default="", max_length=100, verbose_name="Category")),
                ("description", models.TextField(blank=True, default="", verbose_name="Description")),
                ("preview_image", models.CharField(blank=True, default="", max_length=500, verbose_name="Preview image")),
                ("component_key", models.CharField(blank=True, default="", max_length=100, verbose_name="Component key")),
                ("schema", models.JSONField(blank=True, default=dict, verbose_name="Schema")),
                ("default_config", models.JSONField(blank=True, default=dict, verbose_name="Default config")),
                ("is_active", models.BooleanField(default=True, verbose_name="Is active")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Updated at")),
            ],
            options={
                "verbose_name": "Site template",
                "verbose_name_plural": "Site templates",
                "ordering": ["category", "title"],
            },
        ),
    ]
