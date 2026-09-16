"""Values that every template can use."""
from .models import ContactUs, SportCategory


def site_context(request):
    unread = 0
    if request.user.is_authenticated and request.user.is_staff:
        unread = ContactUs.objects.filter(is_read=False).count()
    return {
        "SITE_NAME": "ArenaBook",
        "SITE_TAGLINE": "Book your game. Own the ground.",
        "nav_categories": SportCategory.objects.all()[:8],
        "unread_messages": unread,
    }
