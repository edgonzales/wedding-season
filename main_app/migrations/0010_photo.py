# Generated by Django 5.0 on 2023-12-21 02:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0009_event_guests'),
    ]

    operations = [
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=250)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main_app.event')),
            ],
        ),
    ]