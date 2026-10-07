from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Booking, Room

FIRST_HOUR = 7    # lịch bắt đầu từ 07:00
LAST_HOUR = 21    # ô cuối cùng là 21:00 - 22:00


def _aware(day, hour=0):
    """Ghép ngày + giờ thành datetime có múi giờ (Asia/Ho_Chi_Minh)."""
    return timezone.make_aware(datetime.combine(day, time(hour)))


@login_required
def room_calendar(request, pk):
    room = get_object_or_404(Room, pk=pk, is_active=True)

    # Tuần cần xem: ?week=YYYY-MM-DD, mặc định là tuần hiện tại
    try:
        ref = datetime.strptime(request.GET.get("week", ""), "%Y-%m-%d").date()
    except ValueError:
        ref = timezone.localdate()

    monday = ref - timedelta(days=ref.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    week_start = _aware(monday)
    week_end = _aware(monday + timedelta(days=7))

    bookings = list(
        Booking.objects.filter(
            room=room,
            status__in=Booking.ACTIVE_STATUSES,
            start_time__lt=week_end,
            end_time__gt=week_start,
        ).select_related("user")
    )

    rows = []
    for hour in range(FIRST_HOUR, LAST_HOUR + 1):
        cells = []
        for day in days:
            slot_start = _aware(day, hour)
            slot_end = slot_start + timedelta(hours=1)
            found = next(
                (b for b in bookings if b.start_time < slot_end and b.end_time > slot_start),
                None,
            )
            cells.append(found)
        rows.append({"label": f"{hour:02d}:00", "cells": cells})

    return render(request, "bookings/calendar.html", {
        "room": room,
        "days": days,
        "rows": rows,
        "prev_week": monday - timedelta(days=7),
        "next_week": monday + timedelta(days=7),
        "this_week": timezone.localdate(),
    })