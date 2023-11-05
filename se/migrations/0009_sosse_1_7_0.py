# Copyright 2022-2023 Laurent Defert
#
#  This file is part of SOSSE.
#
# SOSSE is free software: you can redistribute it and/or modify it under the terms of the GNU Affero
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# SOSSE is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with SOSSE.
# If not, see <https://www.gnu.org/licenses/>.

# Generated by Django 3.2.19 on 2023-11-05 10:40

from django.db import migrations, models


def forward_default_remove_nav(apps, schema_editor):
    CrawlPolicy = apps.get_model('se', 'CrawlPolicy')
    CrawlPolicy.objects.filter(remove_nav_elements='yes').update(remove_nav_elements='idx')


def reverse_default_remove_nav(apps, schema_editor):
    CrawlPolicy = apps.get_model('se', 'CrawlPolicy')
    CrawlPolicy.objects.filter(remove_nav_elements='idx').update(remove_nav_elements='yes')


class Migration(migrations.Migration):

    dependencies = [
        ('se', '0008_sosse_1_6_0'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crawlpolicy',
            name='remove_nav_elements',
            field=models.CharField(choices=[('idx', 'From index'), ('scr', 'From index and screenshots'), ('yes', 'From index, screens and HTML snaps'), ('no', 'No')], default='idx', help_text='Remove navigation related elements', max_length=4),
        ),
        migrations.RunPython(forward_default_remove_nav, reverse_default_remove_nav),
    ]
