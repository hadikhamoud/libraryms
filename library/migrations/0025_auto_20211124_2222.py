# Generated by Django 3.2.9 on 2021-11-24 20:22

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0024_auto_20211124_2221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrower',
            name='book',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='library.book'),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='return_date',
            field=models.DateTimeField(default=datetime.datetime(2021, 11, 25, 22, 22, 18, 358059)),
        ),
        migrations.AlterField(
            model_name='borrower',
            name='student',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='library.studentextra'),
        ),
    ]
