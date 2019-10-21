# Generated by Django 2.2.6 on 2019-10-13 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0002_auto_20191013_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='catId',
            field=models.CharField(db_index=True, default=True, max_length=30, unique=True),
        ),
        migrations.AddField(
            model_name='item',
            name='fatherCat',
            field=models.CharField(default=True, max_length=30),
        ),
        migrations.AddField(
            model_name='item',
            name='prevCat',
            field=models.CharField(default=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='item',
            name='heading',
            field=models.CharField(default='None', max_length=30),
        ),
    ]
