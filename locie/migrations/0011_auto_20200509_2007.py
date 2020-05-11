# Generated by Django 3.0.1 on 2020-05-09 20:07

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0010_auto_20200509_1925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='date_joined',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 543068, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 599461, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customerreviewmodel',
            name='date_time',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 624378, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='lociestoresite',
            name='date_of_creation',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 617290, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_time_creation',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 574940, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='publytics',
            name='start_dates',
            field=models.DateField(default=datetime.datetime(2020, 5, 9, 20, 7, 14, 621704, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='store',
            name='closing_time',
            field=models.TimeField(default=datetime.time(20, 7, 14, 569175)),
        ),
        migrations.AlterField(
            model_name='store',
            name='opening_time',
            field=models.TimeField(default=datetime.time(20, 7, 14, 568916)),
        ),
    ]
