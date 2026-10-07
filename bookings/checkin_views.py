import io
from datetime import timedelta

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import approver_required

from .models import Booking


CHECKIN_EARLY_MINUTES = 15


def can_check_in(booking):
    now = timezone.now()
    return (
        booking.status == Booking.Status.APPROVED
        and booking.checked_in_at is None
        and booking.start_time - timedelta(minutes=CHECKIN_EARLY_MINUTES) <= now <= booking.end_time
    )


@login_required
def booking_qr(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("room"),
        pk=pk,
        user=request.user,
        status=Booking.Status.APPROVED,
    )
    url = request.build_absolute_uri(reverse("checkin", args=[booking.qr_token]))

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=20)
    buffer = io.BytesIO()
    img.save(buffer)
    svg = buffer.getvalue().decode("utf-8")
    if svg.startswith("<?xml"):
        svg = svg.split("?>", 1)[1]

    return render(request, "bookings/qr.html", {"booking": booking, "svg": svg, "url": url})


@approver_required
def checkin(request, token):
    booking = get_object_or_404(
        Booking.objects.select_related("room", "user"),
        qr_token=token,
    )

    if request.method == "POST":
        if can_check_in(booking):
            booking.checked_in_at = timezone.now()
            booking.save(update_fields=["checked_in_at"])
            messages.success(request, "Check-in thành công.")
        else:
            messages.error(
                request,
                "Không thể check-in: lượt đặt chưa được duyệt, đã check-in rồi, hoặc chưa tới/đã quá giờ.",
            )
        return redirect("checkin", token=token)

    return render(request, "bookings/checkin.html", {
        "booking": booking,
        "can_check_in": can_check_in(booking),
        "early_minutes": CHECKIN_EARLY_MINUTES,
    })