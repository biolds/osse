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

# Generated by Django 3.2.19 on 2023-11-11 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('se', '0009_sosse_1_7_0'),
    ]

    operations = [
        migrations.AddField(
            model_name='excludedurl',
            name='starting_with',
            field=models.BooleanField(default=False, help_text='Exclude all urls starting with the url pattern'),
        ),
    ]
