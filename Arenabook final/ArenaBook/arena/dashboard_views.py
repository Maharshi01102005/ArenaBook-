"""
ArenaBook admin panel.

A custom, fully themed management area for staff users at /dashboard/.
(The standard Django admin is still available at /django-admin/.)
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AdminUserForm,
    BookingStatusForm,
    CategoryForm,
    TurfForm,
    TurfImageForm,
)
from .models import (
    Booking,
    City,
    ContactUs,
    Country,
    Payment,
    Review,
    SportCategory,
    State,
    Turf,
    TurfImage,
)

User = get_user_model()


def staff_required(view):
    """Only active staff members may enter the admin panel."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff and u.is_active,
        login_url="login",
    )(view)
    return login_required(decorated, login_url="login")


# ===========================================================================
#  Dashboard home
# ===========================================================================
@staff_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    bookings = Booking.objects.all()
    payments = Payment.objects.filter(status=Payment.COMPLETED)

    revenue_rows = (
        payments.annotate(month=TruncMonth("payment_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")[:12]
    )
    chart_labels = [r["month"].strftime("%b %Y") for r in revenue_rows if r["month"]]
    chart_values = [float(r["total"]) for r in revenue_rows if r["month"]]

    status_counts = {
        s: bookings.filter(status=s).count() for s, _ in Booking.STATUS_CHOICES
    }

    top_turfs = (
        Turf.objects.annotate(
            total_bookings=Count("bookings"),
            revenue=Sum("bookings__total_amount",
                        filter=Q(bookings__status=Booking.CONFIRMED)),
        )
        .order_by("-total_bookings")[:5]
    )

    context = {
        "cards": {
            "users": User.objects.filter(is_superuser=False).count(),
            "turfs": Turf.objects.count(),
            "bookings": bookings.count(),
            "revenue": payments.aggregate(t=Sum("amount"))["t"] or 0,
            "month_revenue": payments.filter(payment_date__date__gte=month_start)
            .aggregate(t=Sum("amount"))["t"] or 0,
            "today_bookings": bookings.filter(booking_date=today).count(),
            "pending": status_counts.get(Booking.PENDING, 0),
            "reviews": Review.objects.count(),
            "unread": ContactUs.objects.filter(is_read=False).count(),
        },
        "status_counts": status_counts,
        "chart_labels": json.dumps(chart_labels),
        "chart_values": json.dumps(chart_values),
        "status_json": json.dumps(
            [status_counts.get(s, 0) for s, _ in Booking.STATUS_CHOICES]
        ),
        "recent_bookings": bookings.select_related("user", "turf")[:8],
        "recent_payments": Payment.objects.select_related("user", "booking")[:6],
        "recent_reviews": Review.objects.select_related("user", "turf")[:5],
        "top_turfs": top_turfs,
        "avg_rating": round(
            Review.objects.aggregate(a=Avg("rating"))["a"] or 0, 1
        ),
    }
    return render(request, "dashboard/index.html", context)


# ===========================================================================
#  Sport categories
# ===========================================================================
@staff_required
def admin_categories(request):
    categories = SportCategory.objects.annotate(total=Count("turfs"))
    return render(
        request, "dashboard/categories.html", {"categories": categories}
    )


@staff_required
def admin_category_form(request, pk=None):
    category = get_object_or_404(SportCategory, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, request.FILES or None, instance=category)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f'Category "{obj.category_name}" saved.')
        return redirect("admin_categories")
    return render(
        request,
        "dashboard/category_form.html",
        {"form": form, "category": category},
    )


@staff_required
@require_POST
def admin_category_delete(request, pk):
    category = get_object_or_404(SportCategory, pk=pk)
    name = category.category_name
    category.delete()
    messages.success(request, f'Category "{name}" deleted.')
    return redirect("admin_categories")


# ===========================================================================
#  Turfs
# ===========================================================================
@staff_required
def admin_turfs(request):
    turfs = Turf.objects.select_related("category", "city").annotate(
        total_bookings=Count("bookings"), rating=Avg("reviews__rating")
    )
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    if q:
        turfs = turfs.filter(Q(turf_name__icontains=q) | Q(address__icontains=q))
    if category.isdigit():
        turfs = turfs.filter(category_id=int(category))

    page_obj = Paginator(turfs, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/turfs.html",
        {
            "page_obj": page_obj,
            "turfs": page_obj.object_list,
            "categories": SportCategory.objects.all(),
            "q": q,
            "selected_category": category,
        },
    )


@staff_required
def admin_turf_form(request, pk=None):
    turf = get_object_or_404(Turf, pk=pk) if pk else None
    form = TurfForm(request.POST or None, request.FILES or None, instance=turf)
    image_form = TurfImageForm()

    if request.method == "POST" and form.is_valid():
        obj = form.save()
        for extra in request.FILES.getlist("gallery"):
            TurfImage.objects.create(turf=obj, image=extra)
        messages.success(request, f'Venue "{obj.turf_name}" saved successfully.')
        return redirect("admin_turfs")

    return render(
        request,
        "dashboard/turf_form.html",
        {
            "form": form,
            "turf": turf,
            "image_form": image_form,
            "countries": Country.objects.all(),
            "states": State.objects.all(),
            "cities": City.objects.all(),
        },
    )


@staff_required
@require_POST
def admin_turf_delete(request, pk):
    turf = get_object_or_404(Turf, pk=pk)
    name = turf.turf_name
    turf.delete()
    messages.success(request, f'Venue "{name}" deleted.')
    return redirect("admin_turfs")


@staff_required
@require_POST
def admin_turf_toggle(request, pk):
    turf = get_object_or_404(Turf, pk=pk)
    turf.is_active = not turf.is_active
    turf.save(update_fields=["is_active"])
    messages.info(
        request,
        f'"{turf.turf_name}" is now {"active" if turf.is_active else "hidden"}.',
    )
    return redirect("admin_turfs")


@staff_required
@require_POST
def admin_turf_image_delete(request, pk):
    image = get_object_or_404(TurfImage, pk=pk)
    turf_id = image.turf_id
    image.delete()
    messages.info(request, "Gallery image removed.")
    return redirect("admin_turf_edit", pk=turf_id)


# ===========================================================================
#  Bookings
# ===========================================================================
@staff_required
def admin_bookings(request):
    bookings = Booking.objects.select_related("user", "turf").prefetch_related(
        "payments"
    )
    status = request.GET.get("status", "")
    q = request.GET.get("q", "").strip()
    if status in dict(Booking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)
    if q:
        bookings = bookings.filter(
            Q(turf__turf_name__icontains=q)
            | Q(user__email__icontains=q)
            | Q(user__first_name__icontains=q)
        )

    page_obj = Paginator(bookings, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/bookings.html",
        {
            "page_obj": page_obj,
            "bookings": page_obj.object_list,
            "status": status,
            "q": q,
            "status_choices": Booking.STATUS_CHOICES,
            "totals": {
                "all": Booking.objects.count(),
                "pending": Booking.objects.filter(status=Booking.PENDING).count(),
                "confirmed": Booking.objects.filter(status=Booking.CONFIRMED).count(),
                "cancelled": Booking.objects.filter(status=Booking.CANCELLED).count(),
            },
        },
    )


@staff_required
def admin_booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("user", "turf"), pk=pk
    )
    form = BookingStatusForm(request.POST or None, instance=booking)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, f"Booking {booking.reference} marked as {booking.get_status_display()}."
        )
        return redirect("admin_booking_detail", pk=booking.pk)
    return render(
        request,
        "dashboard/booking_detail.html",
        {
            "booking": booking,
            "form": form,
            "payments": booking.payments.all(),
        },
    )


@staff_required
@require_POST
def admin_booking_status(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    status = request.POST.get("status")
    if status in dict(Booking.STATUS_CHOICES):
        booking.status = status
        booking.save(update_fields=["status"])
        messages.success(
            request,
            f"Booking {booking.reference} is now {booking.get_status_display()}.",
        )
    return redirect(request.META.get("HTTP_REFERER", "admin_bookings"))


@staff_required
@require_POST
def admin_booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    ref = booking.reference
    booking.delete()
    messages.success(request, f"Booking {ref} deleted.")
    return redirect("admin_bookings")


# ===========================================================================
#  Payments
# ===========================================================================
@staff_required
def admin_payments(request):
    payments = Payment.objects.select_related("user", "booking", "booking__turf")
    status = request.GET.get("status", "")
    if status in dict(Payment.STATUS_CHOICES):
        payments = payments.filter(status=status)

    page_obj = Paginator(payments, 12).get_page(request.GET.get("page"))
    completed = Payment.objects.filter(status=Payment.COMPLETED)
    return render(
        request,
        "dashboard/payments.html",
        {
            "page_obj": page_obj,
            "payments": page_obj.object_list,
            "status": status,
            "status_choices": Payment.STATUS_CHOICES,
            "total_revenue": completed.aggregate(t=Sum("amount"))["t"] or 0,
            "completed_count": completed.count(),
            "failed_count": Payment.objects.filter(status=Payment.FAILED).count(),
            "method_rows": Payment.objects.values("payment_method")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total"),
        },
    )


@staff_required
@require_POST
def admin_payment_status(request, pk):
    pay = get_object_or_404(Payment, pk=pk)
    status = request.POST.get("status")
    if status in dict(Payment.STATUS_CHOICES):
        pay.status = status
        pay.save(update_fields=["status"])
        if status == Payment.COMPLETED:
            pay.booking.status = Booking.CONFIRMED
            pay.booking.save(update_fields=["status"])
        messages.success(request, "Payment status updated.")
    return redirect("admin_payments")


# ===========================================================================
#  Reviews / users / messages / locations
# ===========================================================================
@staff_required
def admin_reviews(request):
    reviews = Review.objects.select_related("user", "turf")
    rating = request.GET.get("rating", "")
    if rating.isdigit():
        reviews = reviews.filter(rating=int(rating))
    page_obj = Paginator(reviews, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/reviews.html",
        {
            "page_obj": page_obj,
            "reviews": page_obj.object_list,
            "rating": rating,
            "average": round(Review.objects.aggregate(a=Avg("rating"))["a"] or 0, 1),
            "breakdown": [
                {"stars": i, "count": Review.objects.filter(rating=i).count()}
                for i in range(5, 0, -1)
            ],
            "total": Review.objects.count(),
        },
    )


@staff_required
@require_POST
def admin_review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.delete()
    messages.success(request, "Review deleted.")
    return redirect("admin_reviews")


@staff_required
def admin_users(request):
    users = User.objects.annotate(
        total_bookings=Count("bookings"),
        spent=Sum("payments__amount",
                  filter=Q(payments__status=Payment.COMPLETED)),
    ).select_related("profile")
    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(
            Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )
    page_obj = Paginator(users, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/users.html",
        {
            "page_obj": page_obj,
            "users": page_obj.object_list,
            "q": q,
            "active_count": User.objects.filter(is_active=True).count(),
            "staff_count": User.objects.filter(is_staff=True).count(),
            "new_count": User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=30)
            ).count(),
        },
    )


@staff_required
def admin_user_edit(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    form = AdminUserForm(request.POST or None, instance=user_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{user_obj.full_name} updated.")
        return redirect("admin_users")
    return render(
        request,
        "dashboard/user_form.html",
        {
            "form": form,
            "user_obj": user_obj,
            "bookings": user_obj.bookings.select_related("turf")[:10],
        },
    )


@staff_required
@require_POST
def admin_user_toggle(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.warning(request, "You cannot deactivate your own account.")
    else:
        user_obj.is_active = not user_obj.is_active
        user_obj.save(update_fields=["is_active"])
        messages.info(
            request,
            f'{user_obj.full_name} is now '
            f'{"active" if user_obj.is_active else "blocked"}.',
        )
    return redirect("admin_users")


@staff_required
def admin_messages(request):
    items = ContactUs.objects.all()
    page_obj = Paginator(items, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/messages.html",
        {
            "page_obj": page_obj,
            "items": page_obj.object_list,
            "unread": ContactUs.objects.filter(is_read=False).count(),
        },
    )


@staff_required
@require_POST
def admin_message_read(request, pk):
    item = get_object_or_404(ContactUs, pk=pk)
    item.is_read = not item.is_read
    item.save(update_fields=["is_read"])
    return redirect("admin_messages")


@staff_required
@require_POST
def admin_message_delete(request, pk):
    get_object_or_404(ContactUs, pk=pk).delete()
    messages.success(request, "Message deleted.")
    return redirect("admin_messages")


@staff_required
def admin_locations(request):
    if request.method == "POST":
        kind = request.POST.get("kind")
        name = (request.POST.get("name") or "").strip()
        parent = request.POST.get("parent")
        try:
            if kind == "country" and name:
                Country.objects.get_or_create(name=name)
            elif kind == "state" and name and parent:
                State.objects.get_or_create(name=name, country_id=parent)
            elif kind == "city" and name and parent:
                City.objects.get_or_create(name=name, state_id=parent)
            else:
                raise ValueError("Missing information.")
            messages.success(request, f"{name} added.")
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Could not save: {exc}")
        return redirect("admin_locations")

    return render(
        request,
        "dashboard/locations.html",
        {
            "countries": Country.objects.annotate(total=Count("states")),
            "states": State.objects.select_related("country").annotate(
                total=Count("cities")
            ),
            "cities": City.objects.select_related("state", "state__country"),
        },
    )


@staff_required
@require_POST
def admin_location_delete(request, kind, pk):
    model = {"country": Country, "state": State, "city": City}.get(kind)
    if model:
        get_object_or_404(model, pk=pk).delete()
        messages.success(request, f"{kind.title()} deleted.")
    return redirect("admin_locations")
