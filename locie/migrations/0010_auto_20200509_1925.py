# Generated by Django 3.0.1 on 2020-05-09 19:25

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0009_auto_20200509_1921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='date_joined',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 724055, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 758434, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customerreviewmodel',
            name='date_time',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 773788, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='lociestoresite',
            name='date_of_creation',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 768707, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='biding_bared',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_time_creation',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 744951, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='publytics',
            name='start_dates',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 19, 25, 44, 771996, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='store',
            name='closing_time',
            field=models.TimeField(default=datetime.time(19, 25, 44, 740823)),
        ),
        migrations.AlterField(
            model_name='store',
            name='opening_time',
            field=models.TimeField(default=datetime.time(19, 25, 44, 740721)),
        ),
    ]
