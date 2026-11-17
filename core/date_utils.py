"""Форматы даты и времени.

В хранилище (stickers.json) дата-время всегда хранится в ISO-формате
"%Y-%m-%d %H:%M". Все преобразования выполняются только на уровне UI.
"""

from datetime import datetime

from core import settings
from core.i18n import _

ISO_FORMAT = "%Y-%m-%d %H:%M"

DEFAULT_DATE_FORMAT = "YYYY-MM-DD"
DEFAULT_TIME_FORMAT = "24h"

# Код настройки -> (формат strptime/strftime, исходная подпись-подсказка)
DATE_FORMATS = {
    "YYYY-MM-DD": ("%Y-%m-%d", "ГГГГ-ММ-ДД"),
    "DD-MM-YYYY": ("%d-%m-%Y", "ДД-ММ-ГГГГ"),
    "MM-DD-YYYY": ("%m-%d-%Y", "ММ-ДД-ГГГГ"),
}

TIME_FORMATS = {
    "24h": ("%H:%M", "ЧЧ:ММ"),
    "12h": ("%I:%M %p", "ЧЧ:ММ AM/PM"),
}

DATE_OPTIONS = list(DATE_FORMATS.keys())
TIME_OPTIONS = list(TIME_FORMATS.keys())


def get_date_format():
    value = settings.get("date_format", DEFAULT_DATE_FORMAT)
    return value if value in DATE_FORMATS else DEFAULT_DATE_FORMAT


def get_time_format():
    value = settings.get("time_format", DEFAULT_TIME_FORMAT)
    return value if value in TIME_FORMATS else DEFAULT_TIME_FORMAT


def date_pattern():
    return DATE_FORMATS[get_date_format()][0]


def time_pattern():
    return TIME_FORMATS[get_time_format()][0]


def date_hint():
    return _(DATE_FORMATS[get_date_format()][1])


def time_hint():
    return _(TIME_FORMATS[get_time_format()][1])


def input_hint():
    """Подсказка формата ввода, например «ГГГГ-ММ-ДД и ЧЧ:ММ»."""
    return _("{} и {}").format(date_hint(), time_hint())


def parse_iso(value):
    """ISO-строка (или datetime) -> datetime либо None."""
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value), ISO_FORMAT)
    except (ValueError, TypeError):
        return None


def format_date(moment):
    if isinstance(moment, str):
        moment = parse_iso(moment)
    if moment is None:
        return ""
    return moment.strftime(date_pattern())


def format_time(moment):
    if isinstance(moment, str):
        moment = parse_iso(moment)
    if moment is None:
        return ""
    return moment.strftime(time_pattern())


def format_datetime(value):
    """ISO-строка/datetime -> (дата, время) согласно настройкам."""
    moment = parse_iso(value) if not isinstance(value, datetime) else value
    if moment is None:
        # Не удалось разобрать — отдаём как есть, разделив на дату и время
        date_part, _, time_part = str(value or "").partition(" ")
        return date_part.strip(), time_part.strip()
    return format_date(moment), format_time(moment)


def parse_input(date_str, time_str):
    """Строки из полей ввода -> datetime (или исключение ValueError)."""
    date_str = (date_str or "").strip()
    time_str = (time_str or "").strip()
    full = "{} {}".format(date_str, time_str)
    pattern = "{} {}".format(date_pattern(), time_pattern())
    return datetime.strptime(full, pattern)


def to_iso(moment):
    """datetime -> ISO-строка для хранения."""
    return moment.strftime(ISO_FORMAT)
