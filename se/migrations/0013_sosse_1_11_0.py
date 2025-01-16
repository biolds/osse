# Copyright 2022-2025 Laurent Defert
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

# Generated by Django 3.2.19 on 2024-08-07 14:50

from django.db import migrations, models

import se.models


def migrate_thumbnail(apps, schema_editor):
    CrawlPolicy = apps.get_model("se", "CrawlPolicy")
    CrawlPolicy.objects.filter(create_thumbnails=False).update(thumbnail_mode="none")


def reverse_thumbnail(apps, schema_editor):
    CrawlPolicy = apps.get_model("se", "CrawlPolicy")
    CrawlPolicy.objects.filter(thumbnail_mode="none").update(create_thumbnails=False)


def url_regex_pg(apps, schema_editor):
    CrawlPolicy = apps.get_model("se", "CrawlPolicy")
    CrawlPolicy.objects.update(url_regex_pg=models.F("url_regex"))
    policy = CrawlPolicy.objects.filter(url_regex=".*").first()
    if policy:
        policy.url_regex = "(default)"
        policy.url_regex_pg = ".*"
        policy.save()


def reverse_url_regex_pg(apps, schema_editor):
    CrawlPolicy = apps.get_model("se", "CrawlPolicy")
    for policy in CrawlPolicy.objects.all():
        if policy.url_regex == "(default)":
            policy.url_regex = ".*"
        else:
            regexs = policy.url_regex.splitlines()
            regexs = [regex for regex in regexs if regex and not regex.startsiwth("#")]
            policy.url_regex = regexs[0]

        policy.save()


class Migration(migrations.Migration):
    dependencies = [
        ("se", "0012_sosse_1_10_0"),
    ]

    operations = [
        # Linkpreview based thumbnails
        migrations.AddField(
            model_name="crawlpolicy",
            name="thumbnail_mode",
            field=models.CharField(
                choices=[
                    ("preview", "Page preview from metadata"),
                    ("prevscreen", "Preview from meta, screenshot as fallback"),
                    ("screenshot", "Take a screenshot"),
                    ("none", "No thumbnail"),
                ],
                default="prevscreen",
                help_text="Save thumbnails to display in search results",
                max_length=10,
            ),
        ),
        migrations.RunPython(migrate_thumbnail, reverse_thumbnail),
        migrations.RemoveField(
            model_name="crawlpolicy",
            name="create_thumbnails",
        ),
        # Multiline crawl policy regexp
        migrations.AddField(
            model_name="crawlpolicy",
            name="url_regex_pg",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="crawlpolicy",
            name="url_regex",
            field=models.TextField(
                help_text="URL regular expressions for this policy. (one by line, lines starting with # are ignored)",
                validators=[se.crawl_policy.validate_url_regexp],
            ),
        ),
        migrations.RunPython(url_regex_pg, reverse_url_regex_pg),
        migrations.RunSQL(
            "CREATE INDEX home_idx ON se_document (show_on_homepage, title ASC) WHERE show_on_homepage",
            "DROP INDEX home_idx",
        ),
    ]
