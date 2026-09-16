"""
ArenaBook database models.

Every table from the project specification is implemented here:
User, Country, State, City, UserProfile, SportCategory, Turf,
TurfImage, Booking, Payment, Review and ContactUs.
"""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# ===========================================================================
#  Table: User
# ===========================================================================
class UserManager(BaseUserManager):
    """Manager for the e-mail based custom user model."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60, blank=True)
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(
        default=False, help_text="Allows access to the ArenaBook admin panel."
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    # -- helpers -----------------------------------------------------------
    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email.split("@")[0]

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]

    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.full_name[:2].upper()

    @property
    def avatar_url(self):
        if self.profile_image:
            return self.profile_image.url
        try:
            if self.profile.image:
                return self.profile.image.url
        except Exception:
            pass
        return ""


# ===========================================================================
#  Table: Country / State / City
# ===========================================================================
class Country(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["name"]
        unique_together = ("country", "name")

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    name = models.CharField(max_length=80)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ["name"]
        unique_together = ("state", "name")

    def __str__(self):
        return f"{self.name}, {self.state.name}"


# ===========================================================================
#  Table: User Profile
# ===========================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    address = models.TextField(blank=True)
    phone_no = models.CharField(max_length=15, blank=True)
    image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self):
        return f"Profile of {self.user.full_name}"

    @property
    def location(self):
        bits = [b.name for b in (self.city, self.state, self.country) if b]
        return ", ".join(bits)


# ===========================================================================
#  Table: Sport Category
# ===========================================================================
class SportCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    icon = models.CharField(
        max_length=50,
        default="bi-trophy",
        help_text="Bootstrap icon class, e.g. bi-dribbble",
    )
    slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        verbose_name = "Sport category"
        verbose_name_plural = "Sport categories"
        ordering = ["category_name"]

    def __str__(self):
        return self.category_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.category_name) or "category"
            slug, counter = base, 2
            while SportCategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('turf_list')}?category={self.pk}"

    @property
    def turf_count(self):
        return self.turfs.filter(is_active=True).count()


# ===========================================================================
#  Table: Turf  (sports venue / ground)
# ===========================================================================
class Turf(models.Model):
    turf_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        SportCategory, on_delete=models.CASCADE, related_name="turfs"
    )
    address = models.TextField()
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    open_time = models.TimeField(default=time(6, 0))
    close_time = models.TimeField(default=time(23, 0))
    image = models.ImageField(upload_to="turfs/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # extra convenience fields (not required, but make the site feel real)
    capacity = models.PositiveIntegerField(default=10)
    amenities = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma separated, e.g. Parking, Floodlights, Washroom",
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.turf_name

    def get_absolute_url(self):
        return reverse("turf_detail", args=[self.pk])

    # -- computed ----------------------------------------------------------
    @property
    def amenity_list(self):
        return [a.strip() for a in self.amenities.split(",") if a.strip()]

    @property
    def location(self):
        bits = [b.name for b in (self.city, self.state, self.country) if b]
        return ", ".join(bits)

    @property
    def average_rating(self):
        result = self.reviews.aggregate(avg=models.Avg("rating"))["avg"]
        return round(result, 1) if result else 0

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def rating_stars(self):
        """List of 5 items: 'full' / 'half' / 'empty' - used by the template."""
        avg = self.average_rating
        stars = []
        for i in range(1, 6):
            if avg >= i:
                stars.append("full")
            elif avg >= i - 0.5:
                stars.append("half")
            else:
                stars.append("empty")
        return stars

    def hourly_slots(self):
        """Every bookable 1-hour slot between open_time and close_time."""
        today = datetime.today().date()
        start = datetime.combine(today, self.open_time)
        end = datetime.combine(today, self.close_time)
        if end <= start:
            end += timedelta(days=1)
        slots, cursor = [], start
        while cursor + timedelta(hours=1) <= end:
            nxt = cursor + timedelta(hours=1)
            slots.append((cursor.time(), nxt.time()))
            cursor = nxt
        return slots

    def is_slot_free(self, booking_date, start_time, end_time, exclude_pk=None):
        qs = self.bookings.filter(
            booking_date=booking_date,
            status__in=[Booking.PENDING, Booking.CONFIRMED],
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
        return not qs.exists()

    def price_for(self, start_time, end_time):
        today = datetime.today().date()
        start = datetime.combine(today, start_time)
        end = datetime.combine(today, end_time)
        if end <= start:
            end += timedelta(days=1)
        hours = Decimal((end - start).total_seconds()) / Decimal(3600)
        return (self.price_per_hour * hours).quantize(Decimal("0.01"))


# ===========================================================================
#  Table: Turf Images
# ===========================================================================
class TurfImage(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="turfs/")
    caption = models.CharField(max_length=120, blank=True)

    class Meta:
        verbose_name = "Turf image"
        verbose_name_plural = "Turf images"

    def __str__(self):
        return f"Image of {self.turf.turf_name}"


# ===========================================================================
#  Table: Booking
# ===========================================================================
class Booking(models.Model):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name="bookings")
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.turf.turf_name} - {self.booking_date}"

    def get_absolute_url(self):
        return reverse("booking_detail", args=[self.pk])

    @property
    def reference(self):
        return f"ARB{self.pk:05d}"

    @property
    def duration_hours(self):
        today = datetime.today().date()
        start = datetime.combine(today, self.start_time)
        end = datetime.combine(today, self.end_time)
        if end <= start:
            end += timedelta(days=1)
        return round((end - start).total_seconds() / 3600, 1)

    @property
    def is_paid(self):
        return self.payments.filter(status=Payment.COMPLETED).exists()

    @property
    def is_past(self):
        return self.booking_date < timezone.localdate()

    @property
    def can_cancel(self):
        return self.status != self.CANCELLED and not self.is_past

    @property
    def status_class(self):
        return {
            self.PENDING: "warning",
            self.CONFIRMED: "success",
            self.CANCELLED: "danger",
        }.get(self.status, "secondary")


# ===========================================================================
#  Table: Payment
# ===========================================================================
class Payment(models.Model):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    OTHER = "other"
    PAYMENT_METHOD_CHOICES = [
        (CREDIT_CARD, "Credit Card"),
        (DEBIT_CARD, "Debit Card"),
        (PAYPAL, "PayPal"),
        (OTHER, "Other"),
    ]

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default=CREDIT_CARD
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    payment_date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.transaction_id or self.pk} - {self.get_status_display()}"

    @property
    def status_class(self):
        return {
            self.PENDING: "warning",
            self.COMPLETED: "success",
            self.FAILED: "danger",
        }.get(self.status, "secondary")


# ===========================================================================
#  Table: Review
# ===========================================================================
class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "turf")

    def __str__(self):
        return f"{self.user.full_name} -> {self.turf.turf_name} ({self.rating}/5)"

    @property
    def star_range(self):
        return range(self.rating)

    @property
    def empty_range(self):
        return range(5 - self.rating)


# ===========================================================================
#  Table: ContactUs
# ===========================================================================
class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Contact message"
        verbose_name_plural = "Contact messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.email}"
