from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import approver_required

from .forms import BookingForm, WaitlistForm
from .models import Booking, Room, Waitlist


def notify_waitlist(room):
    for entry in Waitlist.objects.filter(room=room, notified=False):
        if not Booking.find_conflicts(room, entry.start_time, entry.end_time).exists():
            entry.notified = True
            entry.save(update_fields=["notified"])


@login_required
def dashboard(request):
    my_bookings = (
        Booking.objects.filter(user=request.user)
        .select_related("room")
        .order_by("-start_time")
    )
    waitlist = list(
        Waitlist.objects.filter(user=request.user)
        .select_related("room")
        .order_by("start_time")
    )
    for entry in waitlist:
        # Kiểm tra trực tiếp: khung giờ này còn trống không?
        entry.available = not Booking.find_conflicts(
            entry.room, entry.start_time, entry.end_time
        ).exists()

    return render(request, "bookings/dashboard.html", {
        "bookings": my_bookings,
        "waitlist": waitlist,
    })


@login_required
def room_list(request):
    rooms = Room.objects.filter(is_active=True)
    return render(request, "bookings/room_list.html", {"rooms": rooms})


@login_required
def booking_create(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            messages.success(request, "Đã gửi yêu cầu đặt phòng, vui lòng chờ duyệt.")
            return redirect("dashboard")
    else:
        initial = {}
        for key in ("room", "purpose", "start_time", "end_time"):
            value = request.GET.get(key)
            if value:
                initial[key] = value
        form = BookingForm(initial=initial)

    return render(request, "bookings/booking_form.html", {"form": form})


@login_required
@require_POST
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if booking.status in Booking.ACTIVE_STATUSES:
        booking.status = Booking.Status.CANCELLED
        booking.save()
        notify_waitlist(booking.room)
        messages.success(request, "Đã hủy lượt đặt phòng.")
    return redirect("dashboard")



@login_required
@require_POST
def waitlist_join(request):
    form = WaitlistForm(request.POST)
    if form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()
        messages.success(request, "Đã đăng ký vào hàng chờ. Khi phòng trống, bạn sẽ thấy thông báo ở trang chủ.")
        return redirect("dashboard")
    return render(request, "bookings/booking_form.html", {"form": form})


@login_required
@require_POST
def waitlist_leave(request, pk):
    entry = get_object_or_404(Waitlist, pk=pk, user=request.user)
    entry.delete()
    messages.success(request, "Đã rời khỏi hàng chờ.")
    return redirect("dashboard")



@approver_required
def approval_list(request):
    pending = (
        Booking.objects.filter(status=Booking.Status.PENDING)
        .select_related("room", "user")
        .order_by("start_time")
    )
    return render(request, "bookings/approval_list.html", {"bookings": pending})


@approver_required
@require_POST
def booking_approve(request, pk):
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=pk)

        if booking.status != Booking.Status.PENDING:
            messages.error(request, "Lượt đặt này đã được xử lý trước đó.")
            return redirect("approval_list")

        conflicts = Booking.find_conflicts(
            booking.room, booking.start_time, booking.end_time, exclude_pk=booking.pk
        ).filter(status=Booking.Status.APPROVED)
        if conflicts.exists():
            messages.error(request, "Không thể duyệt: phòng đã có lượt được duyệt trong khung giờ này.")
            return redirect("approval_list")

        booking.status = Booking.Status.APPROVED
        booking.approver = request.user
        booking.save()

    messages.success(request, "Đã duyệt lượt đặt phòng.")
    return redirect("approval_list")


@approver_required
@require_POST
def booking_reject(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    if booking.status != Booking.Status.PENDING:
        messages.error(request, "Lượt đặt này đã được xử lý trước đó.")
        return redirect("approval_list")

    reason = request.POST.get("reason", "").strip()
    if not reason:
        messages.error(request, "Vui lòng nhập lý do từ chối.")
        return redirect("approval_list")

    booking.status = Booking.Status.REJECTED
    booking.reject_reason = reason
    booking.approver = request.user
    booking.save()
    notify_waitlist(booking.room)

    messages.success(request, "Đã từ chối lượt đặt phòng.")
    return redirect("approval_list")