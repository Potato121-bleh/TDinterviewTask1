# Generated by Django 5.1.5 on 2025-01-27 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apiApp', '0002_rename_cat_id_producttb_cat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttb',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
