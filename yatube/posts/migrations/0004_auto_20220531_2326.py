# Generated by Django 2.2.9 on 2022-05-31 16:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20220531_1210'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date'], 'verbose_name': 'Публикация', 'verbose_name_plural': 'Публикации'},
        ),
    ]
