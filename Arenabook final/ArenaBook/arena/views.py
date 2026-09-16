"""Public facing views for the ArenaBook website."""

import uuid
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    BookingForm,
    ContactForm,
    LoginForm,
    PaymentForm,
    ProfileForm,
    RegisterForm,
    ReviewForm,
    UserUpdateForm,
)
from .models import (
    Booking,
    City,
    Payment,
    Review,
    SportCategory,
    State,
    Turf,
    UserProfile,
)


# ===========================================================================
#  Static / marketing pages
# ===========================================================================
def home(request):
    turfs = Turf.objects.filter(is_active=True).select_related("category", "city")
    context = {
        "categories": SportCategory.objects.annotate(
            total=Count("turfs", filter=Q(turfs__is_active=True))
        )[:6],
        "featured_turfs": turfs.filter(is_featured=True)[:6] or turfs[:6],
        "latest_turfs": turfs.order_by("-created_at")[:8],
        "reviews": Review.objects.select_related("user", "turf")
        .filter(rating__gte=4)
        .order_by("-created_at")[:6],
        "stats": {
            "turfs": turfs.count(),
            "bookings": Booking.objects.exclude(status=Booking.CANCELLED).count(),
            "categories": SportCategory.objects.count(),
            "cities": City.objects.filter(turf__isnull=False).distinct().count(),
        },
    }
    return render(request, "pages/home.html", context)


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, "Thanks for reaching out! Our team will reply within 24 hours."
        )
        return redirect("contact")
    return render(request, "pages/contact.html", {"form": form})


def category_list(request):
    categories = SportCategory.objects.annotate(
        total=Count("turfs", filter=Q(turfs__is_active=True))
    )
    return render(request, "pages/categories.html", {"categories": categories})


# ===========================================================================
#  Turf browsing
# ===========================================================================
def turf_list(request):
    turfs = (
        Turf.objects.filter(is_active=True)
        .select_related("category", "city", "state")
        .annotate(avg_rating=Avg("reviews__rating"), total_reviews=Count("reviews"))
    )

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    city = request.GET.get("city", "")
    max_price = request.GET.get("max_price", "")
    sort = request.GET.get("sort", "newest")

    if q:
        turfs = turfs.filter(
            Q(turf_name__icontains=q)
            | Q(description__icontains=q)
            | Q(address__icontains=q)
            | Q(category__category_name__icontains=q)
            | Q(city__name__icontains=q)
        )
    if category.isdigit():
        turfs = turfs.filter(category_id=int(category))
    if city.isdigit():
        turfs = turfs.filter(city_id=int(city))
    if max_price.replace(".", "", 1).isdigit():
        turfs = turfs.filter(price_per_hour__lte=Decimal(max_price))

    sort_map = {
        "newest": "-created_at",
        "price_low": "price_per_hour",
        "price_high": "-price_per_hour",
        "rating": "-avg_rating",
        "name": "turf_name",
    }
    turfs = turfs.order_by(sort_map.get(sort, "-created_at"))

    paginator = Paginator(turfs, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "turfs": page_obj.object_list,
        "categories": SportCategory.objects.all(),
        "cities": City.objects.filter(turf__isnull=False).distinct(),
        "q": q,
        "selected_category": category,
        "selected_city": city,
        "max_price": max_price,
        "sort": sort,
        "total_results": paginator.count,
    }
    return render(request, "pages/turf_list.html", context)


def turf_detail(request, pk):
    turf = get_object_or_404(
        Turf.objects.select_related("category", "city", "state", "country"), pk=pk
    )
    today = timezone.localdate()
    selected_date = request.GET.get("date") or today.isoformat()

    booked = Booking.objects.filter(
        turf=turf,
        booking_date=selected_date,
        status__in=[Booking.PENDING, Booking.CONFIRMED],
    ).values_list("start_time", "end_time")

    slots = []
    for start, end in turf.hourly_slots():
        taken = any(bs < end and be > start for bs, be in booked)
        slots.append({"start": start, "end": end, "taken": taken})

    can_review = False
    my_review = None
    if request.user.is_authenticated:
        can_review = Booking.objects.filter(
            user=request.user, turf=turf, status=Booking.CONFIRMED
        ).exists()
        my_review = Review.objects.filter(user=request.user, turf=turf).first()

    context = {
        "turf": turf,
        "booking_form": BookingForm(turf=turf, initial={"booking_date": selected_date}),
        "review_form": ReviewForm(instance=my_review),
        "reviews": turf.reviews.select_related("user")[:20],
        "related": Turf.objects.filter(category=turf.category, is_active=True)
        .exclude(pk=turf.pk)[:4],
        "slots": slots,
        "selected_date": selected_date,
        "today": today.isoformat(),
        "can_review": can_review,
        "my_review": my_review,
    }
    return render(request, "pages/turf_detail.html", context)


def slot_availability(request, pk):
    """AJAX: returns the booked slots of a turf for a given date."""
    turf = get_object_or_404(Turf, pk=pk)
    date = request.GET.get("date") or timezone.localdate().isoformat()
    booked = Booking.objects.filter(
        turf=turf, booking_date=date,
        status__in=[Booking.PENDING, Booking.CONFIRMED],
    ).values_list("start_time", "end_time")

    data = []
    for start, end in turf.hourly_slots():
        taken = any(bs < end and be > start for bs, be in booked)
        data.append(
            {
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "label": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}",
                "taken": taken,
            }
        )
    return JsonResponse({"date": date, "slots": data,
                         "price_per_hour": float(turf.price_per_hour)})


# ===========================================================================
#  Accounts
# ===========================================================================
def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, f"Welcome to ArenaBook, {user.first_name}!")
        return redirect("home")
    return render(request, "account/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        if not form.cleaned_data.get("remember_me"):
            request.session.set_expiry(0)
        messages.success(request, f"Welcome back, {form.user.first_name}!")
        next_url = request.GET.get("next") or request.POST.get("next")
        return redirect(next_url or "home")
    return render(request, "account/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("home")


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileForm(instance=profile)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            user_form = UserUpdateForm(request.POST, request.FILES,
                                       instance=request.user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Your profile has been updated.")
                return redirect("profile")
            messages.error(request, "Please correct the errors below.")
        elif action == "password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Your password has been changed.")
                return redirect("profile")
            messages.error(request, "Your password could not be changed.")

    for field in password_form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")

    stats = {
        "total": request.user.bookings.count(),
        "confirmed": request.user.bookings.filter(status=Booking.CONFIRMED).count(),
        "pending": request.user.bookings.filter(status=Booking.PENDING).count(),
        "spent": sum(
            p.amount for p in request.user.payments.filter(status=Payment.COMPLETED)
        ),
    }
    return render(
        request,
        "account/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "password_form": password_form,
            "profile": profile,
            "stats": stats,
        },
    )


def load_states(request):
    country_id = request.GET.get("country")
    states = State.objects.filter(country_id=country_id).values("id", "name")
    return JsonResponse(list(states), safe=False)


def load_cities(request):
    state_id = request.GET.get("state")
    cities = City.objects.filter(state_id=state_id).values("id", "name")
    return JsonResponse(list(cities), safe=False)


# ===========================================================================
#  Bookings
# ===========================================================================
@login_required
def booking_create(request, pk):
    turf = get_object_or_404(Turf, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("turf_detail", pk=turf.pk)

    form = BookingForm(request.POST, turf=turf)
    if form.is_valid():
        booking = form.save(commit=False)
        booking.user = request.user
        booking.turf = turf
        booking.total_amount = turf.price_for(booking.start_time, booking.end_time)
        booking.status = Booking.PENDING
        booking.save()
        messages.success(
            request,
            f"Slot held! Complete the payment to confirm booking {booking.reference}.",
        )
        return redirect("payment", pk=booking.pk)

    for error in form.non_field_errors():
        messages.error(request, error)
    for field, errors in form.errors.items():
        if field != "__all__":
            for error in errors:
                messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    return redirect("turf_detail", pk=turf.pk)


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(user=request.user)
        .select_related("turf", "turf__category")
        .prefetch_related("payments")
    )
    status = request.GET.get("status", "")
    if status in dict(Booking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)

    paginator = Paginator(bookings, 8)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "booking/my_bookings.html",
        {
            "page_obj": page_obj,
            "bookings": page_obj.object_list,
            "status": status,
            "status_choices": Booking.STATUS_CHOICES,
        },
    )


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("turf", "user"), pk=pk
    )
    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to view that booking.")
        return redirect("my_bookings")
    payment = booking.payments.order_by("-payment_date").first()
    return render(
        request, "booking/booking_detail.html", {"booking": booking, "payment": payment}
    )


@login_required
@require_POST
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if not booking.can_cancel:
        messages.warning(request, "This booking can no longer be cancelled.")
    else:
        booking.status = Booking.CANCELLED
        booking.save(update_fields=["status"])
        booking.payments.filter(status=Payment.PENDING).update(status=Payment.FAILED)
        messages.success(request, f"Booking {booking.reference} has been cancelled.")
    return redirect("my_bookings")


# ===========================================================================
#  Payment
# ===========================================================================
@login_required
def payment(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.status == Booking.CANCELLED:
        messages.warning(request, "This booking was cancelled.")
        return redirect("my_bookings")
    if booking.is_paid:
        messages.info(request, "This booking is already paid for.")
        return redirect("booking_detail", pk=booking.pk)

    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        pay = form.save(commit=False)
        pay.user = request.user
        pay.booking = booking
        pay.amount = booking.total_amount
        pay.status = Payment.COMPLETED  # demo gateway - always succeeds
        pay.transaction_id = f"TXN{uuid.uuid4().hex[:12].upper()}"
        pay.payment_date = timezone.now()
        pay.save()

        booking.status = Booking.CONFIRMED
        booking.save(update_fields=["status"])

        messages.success(
            request,
            f"Payment successful! Booking {booking.reference} is confirmed.",
        )
        return redirect("booking_success", pk=booking.pk)

    return render(request, "booking/payment.html", {"booking": booking, "form": form})


@login_required
def booking_success(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    payment_obj = booking.payments.order_by("-payment_date").first()
    return render(
        request,
        "booking/success.html",
        {"booking": booking, "payment": payment_obj},
    )


@login_required
def invoice(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not allowed to view that invoice.")
        return redirect("my_bookings")
    return render(
        request,
        "booking/invoice.html",
        {
            "booking": booking,
            "payment": booking.payments.order_by("-payment_date").first(),
            "now": timezone.now(),
        },
    )


# ===========================================================================
#  Reviews
# ===========================================================================
@login_required
@require_POST
def review_submit(request, pk):
    turf = get_object_or_404(Turf, pk=pk)
    has_booking = Booking.objects.filter(
        user=request.user, turf=turf, status=Booking.CONFIRMED
    ).exists()
    if not has_booking:
        messages.warning(
            request, "You can review a venue only after a confirmed booking."
        )
        return redirect("turf_detail", pk=turf.pk)

    instance = Review.objects.filter(user=request.user, turf=turf).first()
    form = ReviewForm(request.POST, instance=instance)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.turf = turf
        review.save()
        messages.success(request, "Thank you! Your review has been posted.")
    else:
        messages.error(request, "Your review could not be saved. Please try again.")
    return redirect("turf_detail", pk=turf.pk)


@login_required
@require_POST
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)
    turf_id = review.turf_id
    review.delete()
    messages.info(request, "Your review has been removed.")
    return redirect("turf_detail", pk=turf_id)
