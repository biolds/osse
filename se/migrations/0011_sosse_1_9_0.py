# Copyright 2022-2024 Laurent Defert
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

# Generated by Django 3.2.19 on 2024-01-22 11:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('se', '0010_sosse_1_8_0'),
    ]

    operations = [
        migrations.RenameField(
            model_name='crawlpolicy',
            old_name='condition',
            new_name='recursion',
        ),
        migrations.RenameField(
            model_name='crawlpolicy',
            old_name='crawl_depth',
            new_name='recursion_depth',
        ),
    ]
