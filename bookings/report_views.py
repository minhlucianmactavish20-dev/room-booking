from datetime import datetime, time, timedelta

from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import approver_required

from .models import Booking, Room

OPEN_HOUR = 7
CLOSE_HOUR = 22
MAX_DAYS = 366


def _parse(value, default):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return default


def _aware(day, hour=0):
    return timezone.make_aware(datetime.combine(day, time(hour)))


def _booked_hours(booking, date_from, date_to):
    start = timezone.localtime(booking.start_time)
    end = timezone.localtime(booking.end_time)

    day = max(start.date(), date_from)
    last_day = min(end.date(), date_to)

    total = 0.0
    while day <= last_day:
        window_start = _aware(day, OPEN_HOUR)
        window_end = _aware(day, CLOSE_HOUR)
        s = max(start, window_start)
        e = min(end, window_end)
        if e > s:
            total += (e - s).total_seconds() / 3600
        day += timedelta(days=1)
    return total


@approver_required
def report(request):
    today = timezone.localdate()
    first_of_month = today.replace(day=1)
    next_month = (first_of_month + timedelta(days=32)).replace(day=1)
    last_of_month = next_month - timedelta(days=1)

    date_from = _parse(request.GET.get("from"), first_of_month)
    date_to = _parse(request.GET.get("to"), last_of_month)
    if date_to < date_from:
        date_from, date_to = date_to, date_from
    if (date_to - date_from).days + 1 > MAX_DAYS:
        date_to = date_from + timedelta(days=MAX_DAYS - 1)

    num_days = (date_to - date_from).days + 1
    available_hours = num_days * (CLOSE_HOUR - OPEN_HOUR)

    range_start = _aware(date_from)
    range_end = _aware(date_to + timedelta(days=1))
    now = timezone.now()

    rooms = list(Room.objects.filter(is_active=True))
    stats = {
        r.pk: {
            "room": r,
            "total": 0,
            "approved": 0,
            "pending": 0,
            "rejected": 0,
            "cancelled": 0,
            "checked_in": 0,
            "no_show": 0,
            "hours": 0.0,
        }
        for r in rooms
    }

    bookings = Booking.objects.filter(
        start_time__lt=range_end, end_time__gt=range_start
    )
    for b in bookings:
        s = stats.get(b.room_id)
        if s is None:
            continue
        s["total"] += 1
        s[b.status] += 1
        if b.status == Booking.Status.APPROVED:
            s["hours"] += _booked_hours(b, date_from, date_to)
            if b.checked_in_at:
                s["checked_in"] += 1
            elif b.end_time < now:
                s["no_show"] += 1

    rows = []
    total_hours = 0.0
    for s in stats.values():
        s["hours"] = round(s["hours"], 1)
        s["rate"] = round(s["hours"] / available_hours * 100, 1) if available_hours else 0
        total_hours += s["hours"]
        rows.append(s)
    rows.sort(key=lambda x: x["rate"], reverse=True)

    overall_rate = 0
    if rooms and available_hours:
        overall_rate = round(total_hours / (available_hours * len(rooms)) * 100, 1)

    return render(request, "bookings/report.html", {
        "rows": rows,
        "date_from": date_from,
        "date_to": date_to,
        "num_days": num_days,
        "available_hours": available_hours,
        "total_hours": round(total_hours, 1),
        "overall_rate": overall_rate,
        "open_hour": OPEN_HOUR,
        "close_hour": CLOSE_HOUR,
    })