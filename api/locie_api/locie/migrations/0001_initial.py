# Generated by Django 2.2.6 on 2019-10-12 20:56

import django.contrib.gis.db.models.fields
import django.contrib.gis.geos.point
import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, default='', max_length=30)),
                ('prevCat', models.CharField(default='', max_length=20)),
                ('image', models.TextField(default='')),
                ('nextCat', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('fatherCat', models.CharField(default='', max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('name', models.CharField(db_index=True, default='', max_length=70)),
                ('itemId', models.CharField(db_index=True, default='', max_length=20, primary_key=True, serialize=False)),
                ('serveiId', models.CharField(db_index=True, default='', max_length=20)),
                ('city', models.CharField(default='', max_length=20)),
                ('cityCode', models.CharField(db_index=True, default='', max_length=5)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('effectivePrice', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('images', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), default=list, size=4)),
                ('description', models.TextField(default='')),
                ('measureParam', models.CharField(default='', max_length=10)),
                ('position', django.contrib.gis.db.models.fields.PointField(default=django.contrib.gis.geos.point.Point(0.0, 0.0, srid=4326), srid=4326)),
            ],
        ),
    ]
