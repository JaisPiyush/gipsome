# Generated by Django 3.0.1 on 2019-12-22 11:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0010_auto_20191222_1007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='time_left',
            field=models.TimeField(default=datetime.datetime(2019, 12, 22, 11, 0, 33, 390873)),
        ),
        migrations.AlterField(
            model_name='servei',
            name='date_join',
            field=models.DateField(default=datetime.datetime(2019, 12, 22, 11, 0, 33, 376952)),
        ),
    ]
