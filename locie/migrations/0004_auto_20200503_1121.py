# Generated by Django 3.0.1 on 2020-05-03 11:21

import datetime
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('locie', '0003_auto_20200428_1438'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerReviewModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_id', models.CharField(default='', max_length=50)),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('servei_ids', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('store_keys', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('item_ids', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('order_ids', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('pilot_ids', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('review_type', models.CharField(default='COMMENT', max_length=15)),
                ('date_time', models.DateTimeField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 500986, tzinfo=utc))),
            ],
        ),
        migrations.CreateModel(
            name='Publytics',
            fields=[
                ('pub_id', models.CharField(default='', max_length=50, primary_key=True, serialize=False)),
                ('reference_id', models.CharField(default='', max_length=70)),
                ('site_uname', models.CharField(default='', max_length=70)),
                ('views_log', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('revenue_log', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('start_dates', models.DateField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 499126, tzinfo=utc))),
            ],
        ),
        migrations.RemoveField(
            model_name='lociestoresite',
            name='last_settlement_date',
        ),
        migrations.RemoveField(
            model_name='lociestoresite',
            name='settlement_log',
        ),
        migrations.RemoveField(
            model_name='lociestoresite',
            name='views_site',
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_required',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='date_joined',
            field=models.DateField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 452839, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=models.DateField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 486432, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='lociestoresite',
            name='date_of_creation',
            field=models.DateField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 496238, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='order',
            name='date_time_creation',
            field=models.DateTimeField(default=datetime.datetime(2020, 5, 3, 11, 21, 55, 474196, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='pickdroporder',
            name='cost',
            field=models.DecimalField(decimal_places=4, default=40.0, max_digits=7),
        ),
        migrations.AlterField(
            model_name='servei',
            name='date_join',
            field=models.DateField(default=datetime.date(2020, 5, 3)),
        ),
        migrations.AlterField(
            model_name='store',
            name='closing_time',
            field=models.TimeField(default=datetime.time(11, 21, 55, 470286)),
        ),
        migrations.AlterField(
            model_name='store',
            name='opening_time',
            field=models.TimeField(default=datetime.time(11, 21, 55, 470191)),
        ),
    ]
