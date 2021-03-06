# Generated by Django 3.0.1 on 2020-05-09 19:21

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0008_auto_20200508_2057'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='biding_bared',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='date_joined',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 547141, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 580588, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customerreviewmodel',
            name='date_time',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 595667, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='lociestoresite',
            name='date_of_creation',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 590654, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_time_creation',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 567600, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='publytics',
            name='start_dates',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 21, 31, 593824, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='servei',
            name='date_join',
            field=models.DateField(default=datetime.date(2020, 5, 9)),
        ),
        migrations.AlterField(
            model_name='store',
            name='closing_time',
            field=models.TimeField(default=datetime.time(19, 21, 31, 563461)),
        ),
        migrations.AlterField(
            model_name='store',
            name='opening_time',
            field=models.TimeField(default=datetime.time(19, 21, 31, 563357)),
        ),
    ]
