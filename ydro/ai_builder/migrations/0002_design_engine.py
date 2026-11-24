from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("ai_builder","0001_initial")]
    operations=[
        migrations.AddField(model_name="project",name="style",field=models.CharField(default="auto",max_length=20)),
        migrations.AddField(model_name="revision",name="design",field=models.JSONField(default=dict,blank=True)),
        migrations.AddField(model_name="revision",name="provider",field=models.CharField(default="demo",max_length=20)),
    ]
