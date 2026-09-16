"""Forms used by the public site and the ArenaBook admin panel."""

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

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
    UserProfile,
)

User = get_user_model()

TEXT = {"class": "form-control"}
SELECT = {"class": "form-select"}


class StyledFormMixin:
    """Adds bootstrap classes + placeholders to every widget automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "form-control")
            else:
                widget.attrs.setdefault("class", "form-control")
            widget.attrs.setdefault("placeholder", field.label or name.title())


# ===========================================================================
#  Authentication
# ===========================================================================
class RegisterForm(StyledFormMixin, forms.ModelForm):
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, min_length=6
    )
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)
    phone_no = forms.CharField(label="Phone number", max_length=15, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "profile_image"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this e-mail already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"phone_no": self.cleaned_data.get("phone_no", "")},
            )
        return user


class LoginForm(StyledFormMixin, forms.Form):
    email = forms.EmailField(label="E-mail address")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label="Remember me", required=False)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email, password = cleaned.get("email"), cleaned.get("password")
        if email and password:
            user = authenticate(self.request, username=email.lower().strip(),
                                password=password)
            if user is None:
                raise forms.ValidationError("Invalid e-mail or password.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            self.user = user
        return cleaned


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "profile_image"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("That e-mail is already in use.")
        return email


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone_no", "address", "image", "country", "state", "city"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].queryset = Country.objects.all()
        self.fields["state"].queryset = State.objects.none()
        self.fields["city"].queryset = City.objects.none()

        data = self.data if self.is_bound else {}
        country_id = data.get("country") or getattr(self.instance.country, "pk", None)
        state_id = data.get("state") or getattr(self.instance.state, "pk", None)

        if country_id:
            self.fields["state"].queryset = State.objects.filter(country_id=country_id)
        if state_id:
            self.fields["city"].queryset = City.objects.filter(state_id=state_id)


# ===========================================================================
#  Booking / payment / review / contact
# ===========================================================================
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "start_time", "end_time"]
        widgets = {
            "booking_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "start_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control", "step": "1800"}
            ),
            "end_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control", "step": "1800"}
            ),
        }

    def __init__(self, *args, turf=None, **kwargs):
        self.turf = turf
        super().__init__(*args, **kwargs)
        self.fields["booking_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("booking_date")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if not (date and start and end):
            return cleaned

        if date < timezone.localdate():
            self.add_error("booking_date", "You cannot book a date in the past.")

        if end <= start:
            self.add_error("end_time", "End time must be after the start time.")
            return cleaned

        if self.turf:
            if start < self.turf.open_time or end > self.turf.close_time:
                self.add_error(
                    None,
                    f"{self.turf.turf_name} is open from "
                    f"{self.turf.open_time.strftime('%I:%M %p')} to "
                    f"{self.turf.close_time.strftime('%I:%M %p')}.",
                )
            elif not self.turf.is_slot_free(date, start, end):
                self.add_error(
                    None,
                    "That slot is already booked. Please pick a different time.",
                )
        return cleaned


class PaymentForm(StyledFormMixin, forms.ModelForm):
    card_name = forms.CharField(label="Name on card", max_length=80, required=False)
    card_number = forms.CharField(label="Card number", max_length=19, required=False)
    expiry = forms.CharField(label="Expiry (MM/YY)", max_length=5, required=False)
    cvv = forms.CharField(label="CVV", max_length=4, required=False)

    class Meta:
        model = Payment
        fields = ["payment_method"]

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("payment_method")
        if method in (Payment.CREDIT_CARD, Payment.DEBIT_CARD):
            number = (cleaned.get("card_number") or "").replace(" ", "")
            if not number.isdigit() or not (12 <= len(number) <= 19):
                self.add_error("card_number", "Enter a valid card number (12-19 digits).")
            if not cleaned.get("card_name"):
                self.add_error("card_name", "Card holder name is required.")
            cvv = cleaned.get("cvv") or ""
            if not cvv.isdigit() or len(cvv) not in (3, 4):
                self.add_error("cvv", "Enter a valid CVV.")
            if not cleaned.get("expiry"):
                self.add_error("expiry", "Expiry date is required.")
        return cleaned


class ReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Share your experience..."}
            ),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if not rating or int(rating) < 1 or int(rating) > 5:
            raise forms.ValidationError("Please select a rating between 1 and 5 stars.")
        return rating


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ["name", "email", "phone", "message"]
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 5, "placeholder": "How can we help you?"}
            )
        }


# ===========================================================================
#  Admin panel forms
# ===========================================================================
class TurfForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Turf
        fields = [
            "turf_name", "category", "description", "address",
            "country", "state", "city", "price_per_hour", "capacity",
            "open_time", "close_time", "amenities", "image",
            "is_featured", "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "open_time": forms.TimeInput(attrs={"type": "time"}),
            "close_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["state"].queryset = State.objects.all()
        self.fields["city"].queryset = City.objects.all()

    def clean(self):
        cleaned = super().clean()
        open_time, close_time = cleaned.get("open_time"), cleaned.get("close_time")
        if open_time and close_time and close_time <= open_time:
            self.add_error("close_time", "Closing time must be after opening time.")
        price = cleaned.get("price_per_hour")
        if price is not None and price <= 0:
            self.add_error("price_per_hour", "Price must be greater than zero.")
        return cleaned


class TurfImageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TurfImage
        fields = ["image", "caption"]


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SportCategory
        fields = ["category_name", "description", "icon", "image"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class BookingStatusForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["status"]


class AdminUserForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active", "is_staff"]


class LocationForm(StyledFormMixin, forms.Form):
    """Quick add form for Country / State / City in the admin panel."""

    country_name = forms.CharField(label="New country", required=False)
    state_country = forms.ModelChoiceField(
        label="Country", queryset=Country.objects.all(), required=False
    )
    state_name = forms.CharField(label="New state", required=False)
    city_state = forms.ModelChoiceField(
        label="State", queryset=State.objects.all(), required=False
    )
    city_name = forms.CharField(label="New city", required=False)
