from datetime import timedelta
import os

from django.conf import settings
from django.db import connection, models
from django.shortcuts import render
from django.utils.timezone import now
from langdetect.detector_factory import PROFILES_DIRECTORY
import pygal

from .models import CrawlerStats, Document
from .views import get_context


def get_unit(n):
    units = ['', 'k', 'M', 'G', 'T', 'P']
    unit_no = 0
    while n >= 1000:
        unit_no += 1
        n /= 1000
    return 10 ** (unit_no * 3), units[unit_no]


def filesizeformat(n):
    factor, unit = get_unit(n)
    return '%0.1f%sB' % (n / factor, unit)


def datetime_graph(pygal_style, data, col):
    t = now() - timedelta(hours=23)
    t = t.replace(minute=0, second=0, microsecond=0)
    x_labels = [t]
    dt = timedelta(hours=24)
    while dt.total_seconds() > 0:
        t += timedelta(hours=6)
        dt -= timedelta(hours=6)
        x_labels.append(t)


    g = pygal.DateTimeLine(style=pygal_style, disable_xml_declaration=True,
                                     truncate_label=-1, show_legend=False, fill=True,
                                     x_value_formatter=lambda dt: dt.strftime('%I:%M'),
                                     x_title='UTC time')
    g.x_labels = x_labels
    stats_max = data.aggregate(m=models.Max(col)).get('m', 0) or 0
    factor, unit = get_unit(stats_max)

    entries = []
    for entry in data:
        val = getattr(entry, col)
        if val is not None:
            entries.append((entry.t, val / factor))

    g.add('', entries)
    return g


def crawler_stats(pygal_style, freq):
    data = CrawlerStats.objects.filter(freq=freq).order_by('t')

    if data.count() < 2:
        return {}

    if freq == CrawlerStats.MINUTELY:
        period = '24h'
    else:
        period = 'year'

    # Doc count minutely
    doc_count = datetime_graph(pygal_style, data, 'doc_count')
    factor, unit = get_unit(data.aggregate(m=models.Max('doc_count')).get('m', 0) or 0)
    doc_count.title = 'Doc count last %s' % period
    if unit:
        doc_count.title += ' (%s)' % unit
    doc_count = doc_count.render()

    # Indexing speed minutely
    idx_speed_data = data.annotate(speed=models.F('indexing_speed') / 60)
    idx_speed = datetime_graph(pygal_style, idx_speed_data, 'speed')
    factor, unit = get_unit(data.aggregate(m=models.Max('indexing_speed')).get('m', 0) or 0 / 60.0)
    if not unit:
        unit = 'doc'
    idx_speed.title = 'Indexing speed last %s (%s/s)' % (period, unit)
    idx_speed = idx_speed.render()

    # Url queued minutely
    url_queue = datetime_graph(pygal_style, data, 'url_queued_count')
    factor, unit = get_unit(data.aggregate(m=models.Max('url_queued_count')).get('m', 1))
    url_queue.title = 'URL queue size last %s' % period
    if unit:
        url_queue.title += ' (%s)' % unit
    url_queue = url_queue.render()
    freq = freq.lower()
    return {
        '%s_doc_count' % freq: doc_count,
        '%s_idx_speed' % freq: idx_speed,
        '%s_url_queue' % freq: url_queue,
    }


def stats(request):
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_database_size(%s)', [settings.DATABASES['default']['NAME']])
        db_size = cursor.fetchall()[0][0]

    doc_count = Document.objects.count()

    indexed_langs = Document.objects.exclude(lang_iso_639_1__isnull=True).values('lang_iso_639_1').annotate(count=models.Count('lang_iso_639_1')).order_by('-count')

    # Language chart
    pygal_style = pygal.style.Style(
        background='transparent',
        plot_background='transparent',
        title_font_size=40,
        legend_font_size=40,
        label_font_size=40,
        major_label_font_size=40,
    )
    lang_chart = pygal.Bar(style=pygal_style, disable_xml_declaration=True)
    lang_chart.title = 'Language repartition'

    factor, unit = get_unit(indexed_langs[0]['count'])
    if unit:
        lang_chart.title += ' (%s)' % unit

    for lang in indexed_langs[:8]:
        lang_iso = lang['lang_iso_639_1']
        title = settings.MYSE_LANGDETECT_TO_POSTGRES.get(lang_iso, {}).get('name', 'unknown').title()
        percent = lang['count'] / factor
        lang_chart.add(title, percent)

    # HDD chart
    statvfs = os.statvfs('/var/lib')
    hdd_size = statvfs.f_frsize * statvfs.f_blocks
    hdd_free = statvfs.f_frsize * statvfs.f_bavail
    hdd_other = hdd_size - hdd_free - db_size
    factor, unit = get_unit(hdd_size)

    hdd_pie = pygal.Pie(style=pygal_style, disable_xml_declaration=True)
    hdd_pie.title = 'HDD size (total %s)' % filesizeformat(hdd_size)
    hdd_pie.add('DB(%s)' % filesizeformat(db_size), db_size)
    hdd_pie.add('Other(%s)' % filesizeformat(hdd_other), hdd_other)
    hdd_pie.add('Free(%s)' % filesizeformat(hdd_free), hdd_free)

    # Crawler stats
    context = get_context({
        'title': 'Statistics',

        # index
        'doc_count': doc_count,
        'lang_count': len(indexed_langs),
        'db_size': filesizeformat(db_size),
        'doc_size': filesizeformat(db_size / doc_count),
        'lang_recognizable': len(os.listdir(PROFILES_DIRECTORY)),
        'lang_parsable': [l.title() for l in sorted(Document.get_supported_langs())],
        'lang_chart': lang_chart.render(),
        'hdd_pie': hdd_pie.render(),
    })

    context.update(crawler_stats(pygal_style, CrawlerStats.MINUTELY))
    context.update(crawler_stats(pygal_style, CrawlerStats.DAILY))
    return render(request, 'se/stats.html', context)

