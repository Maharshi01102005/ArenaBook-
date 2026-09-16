"""URL routes for the ArenaBook website and admin panel."""

from django.urls import path

from . import dashboard_views as dash
from . import views

urlpatterns = [
    # ---------------- public site ----------------
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("categories/", views.category_list, name="category_list"),
    path("venues/", views.turf_list, name="turf_list"),
    path("venues/<int:pk>/", views.turf_detail, name="turf_detail"),
    path("venues/<int:pk>/slots/", views.slot_availability, name="slot_availability"),

    # ---------------- accounts ----------------
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("ajax/states/", views.load_states, name="load_states"),
    path("ajax/cities/", views.load_cities, name="load_cities"),

    # ---------------- bookings & payments ----------------
    path("venues/<int:pk>/book/", views.booking_create, name="booking_create"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="booking_cancel"),
    path("bookings/<int:pk>/payment/", views.payment, name="payment"),
    path("bookings/<int:pk>/success/", views.booking_success, name="booking_success"),
    path("bookings/<int:pk>/invoice/", views.invoice, name="invoice"),

    # ---------------- reviews ----------------
    path("venues/<int:pk>/review/", views.review_submit, name="review_submit"),
    path("reviews/<int:pk>/delete/", views.review_delete, name="review_delete"),

    # ---------------- admin panel ----------------
    path("dashboard/", dash.dashboard, name="dashboard"),

    path("dashboard/categories/", dash.admin_categories, name="admin_categories"),
    path("dashboard/categories/add/", dash.admin_category_form,
         name="admin_category_add"),
    path("dashboard/categories/<int:pk>/edit/", dash.admin_category_form,
         name="admin_category_edit"),
    path("dashboard/categories/<int:pk>/delete/", dash.admin_category_delete,
         name="admin_category_delete"),

    path("dashboard/venues/", dash.admin_turfs, name="admin_turfs"),
    path("dashboard/venues/add/", dash.admin_turf_form, name="admin_turf_add"),
    path("dashboard/venues/<int:pk>/edit/", dash.admin_turf_form,
         name="admin_turf_edit"),
    path("dashboard/venues/<int:pk>/delete/", dash.admin_turf_delete,
         name="admin_turf_delete"),
    path("dashboard/venues/<int:pk>/toggle/", dash.admin_turf_toggle,
         name="admin_turf_toggle"),
    path("dashboard/venue-images/<int:pk>/delete/", dash.admin_turf_image_delete,
         name="admin_turf_image_delete"),

    path("dashboard/bookings/", dash.admin_bookings, name="admin_bookings"),
    path("dashboard/bookings/<int:pk>/", dash.admin_booking_detail,
         name="admin_booking_detail"),
    path("dashboard/bookings/<int:pk>/status/", dash.admin_booking_status,
         name="admin_booking_status"),
    path("dashboard/bookings/<int:pk>/delete/", dash.admin_booking_delete,
         name="admin_booking_delete"),

    path("dashboard/payments/", dash.admin_payments, name="admin_payments"),
    path("dashboard/payments/<int:pk>/status/", dash.admin_payment_status,
         name="admin_payment_status"),

    path("dashboard/reviews/", dash.admin_reviews, name="admin_reviews"),
    path("dashboard/reviews/<int:pk>/delete/", dash.admin_review_delete,
         name="admin_review_delete"),

    path("dashboard/users/", dash.admin_users, name="admin_users"),
    path("dashboard/users/<int:pk>/edit/", dash.admin_user_edit,
         name="admin_user_edit"),
    path("dashboard/users/<int:pk>/toggle/", dash.admin_user_toggle,
         name="admin_user_toggle"),

    path("dashboard/messages/", dash.admin_messages, name="admin_messages"),
    path("dashboard/messages/<int:pk>/read/", dash.admin_message_read,
         name="admin_message_read"),
    path("dashboard/messages/<int:pk>/delete/", dash.admin_message_delete,
         name="admin_message_delete"),

    path("dashboard/locations/", dash.admin_locations, name="admin_locations"),
    path("dashboard/locations/<str:kind>/<int:pk>/delete/",
         dash.admin_location_delete, name="admin_location_delete"),
]
