# Generated by Django 4.0.4 on 2022-04-21 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot_app', '0002_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='step',
            field=models.PositiveIntegerField(default=0, verbose_name='Счетчик'),
        ),
    ]
