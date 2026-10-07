from django.urls import path

from . import calendar_views, checkin_views, report_views, views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/<int:pk>/calendar/", calendar_views.room_calendar, name="room_calendar"),
    path("book/", views.booking_create, name="booking_create"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="booking_cancel"),
    path("bookings/<int:pk>/qr/", checkin_views.booking_qr, name="booking_qr"),
    path("checkin/<uuid:token>/", checkin_views.checkin, name="checkin"),
    path("waitlist/join/", views.waitlist_join, name="waitlist_join"),
    path("waitlist/<int:pk>/leave/", views.waitlist_leave, name="waitlist_leave"),
    path("approvals/", views.approval_list, name="approval_list"),
    path("approvals/<int:pk>/approve/", views.booking_approve, name="booking_approve"),
    path("approvals/<int:pk>/reject/", views.booking_reject, name="booking_reject"),
    path("report/", report_views.report, name="report"),
]