"""Django admin registration (available at /django-admin/)."""

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

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
    User,
    UserProfile,
)


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text="Raw passwords are not stored. Use the change-password form.",
    )

    class Meta:
        model = User
        fields = (
            "email", "password", "first_name", "last_name", "profile_image",
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "first_name", "last_name", "is_staff",
                    "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "profile_image")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )


class StateInline(admin.TabularInline):
    model = State
    extra = 1


class CityInline(admin.TabularInline):
    model = City
    extra = 1


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    inlines = [StateInline]


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    list_filter = ("country",)
    search_fields = ("name",)
    inlines = [CityInline]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state")
    list_filter = ("state__country", "state")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_no", "city", "state", "country")
    search_fields = ("user__email", "phone_no")


@admin.register(SportCategory)
class SportCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_name", "icon", "turf_count")
    search_fields = ("category_name",)
    prepopulated_fields = {"slug": ("category_name",)}


class TurfImageInline(admin.TabularInline):
    model = TurfImage
    extra = 2


@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = ("turf_name", "category", "city", "price_per_hour",
                    "is_featured", "is_active", "created_at")
    list_filter = ("category", "is_active", "is_featured", "city")
    search_fields = ("turf_name", "address")
    list_editable = ("price_per_hour", "is_featured", "is_active")
    inlines = [TurfImageInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "turf", "booking_date", "start_time",
                    "end_time", "total_amount", "status")
    list_filter = ("status", "booking_date", "turf__category")
    search_fields = ("user__email", "turf__turf_name")
    date_hierarchy = "booking_date"
    list_editable = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "booking", "amount",
                    "payment_method", "status", "payment_date")
    list_filter = ("status", "payment_method")
    search_fields = ("transaction_id", "user__email")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "turf", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("user__email", "turf__turf_name", "comment")


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "message")


@admin.register(TurfImage)
class TurfImageAdmin(admin.ModelAdmin):
    list_display = ("turf", "caption")
