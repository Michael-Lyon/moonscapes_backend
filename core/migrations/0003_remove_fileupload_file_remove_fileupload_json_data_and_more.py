# Generated by Django 5.0.7 on 2024-10-10 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_fileupload'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileupload',
            name='file',
        ),
        migrations.RemoveField(
            model_name='fileupload',
            name='json_data',
        ),
        migrations.AddField(
            model_name='fileupload',
            name='glb_file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/glb/'),
        ),
        migrations.AddField(
            model_name='fileupload',
            name='json_file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/json/'),
        ),
        migrations.AddField(
            model_name='fileupload',
            name='usdz_file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/usdz/'),
        ),
        migrations.AlterField(
            model_name='fileupload',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/thumbnails/'),
        ),
    ]
