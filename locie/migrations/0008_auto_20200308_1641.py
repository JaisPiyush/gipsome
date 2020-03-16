# Generated by Django 3.0.1 on 2020-03-08 16:41

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0007_auto_20200221_2109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='data_joined',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
        migrations.AlterField(
            model_name='officialrequest',
            name='date_applied',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
        migrations.AlterField(
            model_name='officialrequest',
            name='date_requested',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
        migrations.AlterField(
            model_name='ontonotfication',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2020, 3, 8, 16, 41, 41, 25751, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_of_creation',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
        migrations.AlterField(
            model_name='order',
            name='time_left',
            field=models.TimeField(default=datetime.time(16, 41, 41, 15134)),
        ),
        migrations.AlterField(
            model_name='order',
            name='time_of_creation',
            field=models.TimeField(default=datetime.time(16, 41, 41, 15068)),
        ),
        migrations.AlterField(
            model_name='phonetoken',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 3, 8, 16, 41, 41, 23455, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='servei',
            name='date_join',
            field=models.DateField(default=datetime.datetime(2020, 3, 8, 16, 41, 41, 4115)),
        ),
        migrations.AlterField(
            model_name='servei',
            name='dob',
            field=models.DateField(default=datetime.date(2020, 3, 8)),
        ),
    ]
