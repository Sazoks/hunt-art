# Generated by Django 5.0.3 on 2024-04-27 12:37

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arts", "0003_artcomment_created_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="art",
            name="tags",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=100),
                blank=True,
                default=list,
                size=None,
                verbose_name="Тэги",
            ),
        ),
    ]
