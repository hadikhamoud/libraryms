# Generated by Django 3.0.1 on 2021-11-26 20:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0030_auto_20211126_1755'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrower',
            name='Fine',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='return_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 11, 27, 20, 46, 29, 316787)),
        ),
    ]