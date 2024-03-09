# Generated by Django 5.0.3 on 2024-03-09 06:14

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arts", "0002_alter_artcomment_options_alter_artlike_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="artcomment",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="Дата создания",
            ),
            preserve_default=False,
        ),
    ]
