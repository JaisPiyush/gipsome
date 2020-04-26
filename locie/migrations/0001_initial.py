# Generated by Django 3.0.1 on 2020-04-26 10:37

import datetime
from django.conf import settings
import django.contrib.gis.db.models.fields
import django.contrib.gis.geos.point
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import locie.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('account_id', models.CharField(default='account_id', max_length=30, unique=True)),
                ('date_joined', models.DateField(default=datetime.datetime(2020, 4, 26, 10, 37, 32, 741647, tzinfo=utc))),
                ('phone_number', models.CharField(db_index=True, default='', max_length=15)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('relation', models.CharField(db_index=True, default='', max_length=4)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'account',
                'verbose_name_plural': 'accounts',
            },
            managers=[
                ('objects', locie.models.AccountManager()),
            ],
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('cart_id', models.CharField(default='', max_length=75, primary_key=True, serialize=False)),
                ('clusters', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('net_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('quantity', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('customer_id', models.CharField(db_index=True, default='', max_length=70)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat_id', models.CharField(db_index=True, default='', max_length=50, unique=True)),
                ('name', models.CharField(db_index=True, default='', max_length=50)),
                ('prev_cat', models.CharField(blank=True, default='', max_length=50)),
                ('image', models.TextField(blank=True, default='')),
                ('next_cat', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None)),
                ('father_cat', models.CharField(blank=True, default='', max_length=50)),
                ('cat_type', models.CharField(blank=True, db_index=True, default='', max_length=2)),
                ('city_site', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=5), blank=True, default=list, size=None)),
                ('required_desc', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=50), blank=True, default=list, size=None)),
                ('delivery_type', models.CharField(blank=True, default='', max_length=3)),
                ('pick_type', models.CharField(blank=True, default='OP', max_length=2)),
                ('radiod', models.BooleanField(blank=True, default=False)),
                ('returnable', models.BooleanField(blank=True, default=True)),
                ('inspection', models.BooleanField(blank=True, default=False)),
                ('default_items', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='CityCode',
            fields=[
                ('city', models.CharField(db_index=True, default='', max_length=40)),
                ('cityCode', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('state', models.CharField(db_index=True, default='', max_length=20)),
                ('pin_codes', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=10), default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Coordinates',
            fields=[
                ('coordinates_id', models.CharField(default='', max_length=50, primary_key=True, serialize=False)),
                ('relation', models.CharField(db_index=True, default='', max_length=10)),
                ('position', django.contrib.gis.db.models.fields.PointField(default=django.contrib.gis.geos.point.Point(0.0, 0.0, srid=4326), srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='DefaultItems',
            fields=[
                ('item_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('cat_id', models.CharField(db_index=True, default='', max_length=50)),
                ('measure_param', models.CharField(default='', max_length=30)),
                ('unit', models.CharField(default='', max_length=4)),
                ('image', models.TextField(blank=True, default='')),
                ('pick_type', models.CharField(default='SP', max_length=2)),
                ('delivery_type', models.CharField(default='', max_length=3)),
                ('father_cat', models.CharField(db_index=True, default='', max_length=50)),
                ('name', models.CharField(default='', max_length=50)),
                ('inspection', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, default='')),
                ('required_desc', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), blank=True, default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='ExtraCharges',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation', models.CharField(default='009', max_length=4)),
                ('categories', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('extra_charges', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('name', models.CharField(db_index=True, default='', max_length=30)),
                ('item_id', models.CharField(db_index=True, default='', max_length=50, primary_key=True, serialize=False)),
                ('store_key', models.CharField(db_index=True, default='', max_length=50)),
                ('servei_id', models.CharField(db_index=True, default='', max_length=50)),
                ('city', models.CharField(default='', max_length=20)),
                ('cityCode', models.CharField(db_index=True, default='', max_length=5)),
                ('allowed', models.BooleanField(default=True)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('effective_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=7)),
                ('images', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), default=list, size=4)),
                ('description', models.TextField(default='')),
                ('heading', models.CharField(default='None', max_length=30)),
                ('measure_param', models.CharField(default='', max_length=10)),
                ('unit', models.DecimalField(decimal_places=2, default=0.0, max_digits=6)),
                ('inspection', models.BooleanField(default=False)),
                ('delivery_type', models.CharField(default='', max_length=3)),
                ('prev_cat', models.CharField(default=True, max_length=30)),
                ('father_cat', models.CharField(default=True, max_length=30)),
                ('required_desc', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=80), blank=True, default=list, size=None)),
                ('ratings', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('default_item_id', models.CharField(default='none', max_length=70)),
            ],
        ),
        migrations.CreateModel(
            name='LocieStoreSite',
            fields=[
                ('uname', models.CharField(default='', max_length=120, primary_key=True, serialize=False)),
                ('store_link', models.CharField(db_index=True, default='', max_length=255)),
                ('site', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('site_context', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('views_site', models.IntegerField(default=0)),
                ('monetized', models.BooleanField(default=True)),
                ('settlement_log', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('last_settlement_date', models.DateTimeField(default=datetime.datetime(2020, 4, 26, 10, 37, 32, 779945, tzinfo=utc))),
                ('online', models.BooleanField(default=True)),
                ('date_of_creation', models.DateField(default=datetime.datetime(2020, 4, 26, 10, 37, 32, 780059, tzinfo=utc))),
            ],
        ),
        migrations.CreateModel(
            name='MeasureParam',
            fields=[
                ('measure_id', models.CharField(default='krispiforever@103904tilltheendoftheinfinity', max_length=50, primary_key=True, serialize=False)),
                ('units', django.contrib.postgres.fields.ArrayField(base_field=models.DecimalField(decimal_places=2, default=0.0, max_digits=4), default=list, size=None)),
                ('measure_params', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(db_index=True, decimal_places=2, default=0.0, max_digits=4)),
                ('categories', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('city_site', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=5), default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('store_name', models.CharField(default='', max_length=50)),
                ('creator', models.CharField(db_index=True, default=True, max_length=30)),
                ('store_category', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('father_categories', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('store_key', models.CharField(db_index=True, default='', max_length=50, primary_key=True, serialize=False)),
                ('owners', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=30), default=list, size=None)),
                ('product_line', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, max_length=20), default=list, size=None)),
                ('creators_profession', models.CharField(default='', max_length=30)),
                ('official_support', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('contacts', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('address', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('cityCode', models.CharField(db_index=True, default='', max_length=6)),
                ('coordinates_id', models.CharField(db_index=True, default='', max_length=50)),
                ('opening_time', models.TimeField(default=datetime.time(10, 37, 32, 759392))),
                ('closing_time', models.TimeField(default=datetime.time(10, 37, 32, 759501))),
                ('online', models.BooleanField(default=True)),
                ('headings', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=70), default=list, size=None)),
                ('allowed', models.BooleanField(default=True)),
                ('store_link', models.CharField(default='', max_length=255)),
                ('store_site_online', models.BooleanField(default=False)),
                ('store_images', django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=list, size=None)),
                ('store_unmae', models.CharField(db_index=True, default='', max_length=70)),
                ('image', models.TextField(default='')),
                ('descriptions', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Servei',
            fields=[
                ('servei_id', models.CharField(db_index=True, default='', max_length=50, primary_key=True, serialize=False)),
                ('cityCode', models.CharField(db_index=True, default='', max_length=5)),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('phone_number', models.CharField(default='', max_length=10, unique=True)),
                ('email', models.EmailField(default='', max_length=254)),
                ('gender', models.CharField(default='', max_length=20)),
                ('profession', models.CharField(default='', max_length=30)),
                ('image', models.TextField(default='')),
                ('coordinates_id', models.CharField(db_index=True, default='', max_length=50)),
                ('aadhar', models.CharField(db_index=True, default='', max_length=30, unique=True)),
                ('aadhar_image', models.TextField(default='')),
                ('pan', models.CharField(db_index=True, default='', max_length=30, unique=True)),
                ('pan_image', models.TextField(default='')),
                ('store', models.CharField(db_index=True, default='', max_length=50)),
                ('date_join', models.DateField(default=datetime.date(2020, 4, 26))),
                ('allowed', models.BooleanField(default=True)),
                ('online', models.BooleanField(default=True)),
                ('address', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('pin_code', models.CharField(default='', max_length=6)),
                ('country', models.CharField(default='INDIA', max_length=20)),
                ('country_code', models.CharField(default='+91', max_length=4)),
                ('account', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pilot',
            fields=[
                ('pilot_id', models.CharField(default='', max_length=50, primary_key=True, serialize=False)),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('address', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('cityCode', models.CharField(db_index=True, default='', max_length=6)),
                ('image', models.TextField(default='')),
                ('phone_number', models.CharField(db_index=True, default='', max_length=12)),
                ('email', models.EmailField(blank=True, db_index=True, max_length=254, null=True)),
                ('aadhar', models.CharField(db_index=True, default='', max_length=30, unique=True)),
                ('aadhar_image', models.TextField(default='')),
                ('vehicle', models.CharField(default='', max_length=10)),
                ('vehicle_id', models.CharField(db_index=True, default='', max_length=20, unique=True)),
                ('driving_license', models.CharField(db_index=True, default='', max_length=30)),
                ('dl_image', models.TextField(default='')),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('coordinates_id', models.CharField(db_index=True, default='', max_length=50)),
                ('weight', models.IntegerField(db_index=True, default=0)),
                ('account', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MobileDevice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name')),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation date')),
                ('device_id', models.CharField(blank=True, db_index=True, help_text='Unique device identifier', max_length=150, null=True, verbose_name='Device ID')),
                ('registration_id', models.TextField(verbose_name='Registration token')),
                ('type', models.CharField(choices=[('ios', 'ios'), ('android', 'android'), ('web', 'web')], max_length=10)),
                ('locie_partner', models.CharField(db_index=True, default='', max_length=50)),
                ('partnership', models.CharField(db_index=True, default='', max_length=10)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FCM device',
                'verbose_name_plural': 'FCM devices',
            },
        ),
        migrations.CreateModel(
            name='CustomerDevice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Name')),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation date')),
                ('device_id', models.CharField(blank=True, db_index=True, help_text='Unique device identifier', max_length=150, null=True, verbose_name='Device ID')),
                ('registration_id', models.TextField(verbose_name='Registration token')),
                ('type', models.CharField(choices=[('ios', 'ios'), ('android', 'android'), ('web', 'web')], max_length=10)),
                ('customer_id', models.CharField(db_index=True, default='', max_length=50)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FCM device',
                'abstract': False,
            },
        ),
    ]
