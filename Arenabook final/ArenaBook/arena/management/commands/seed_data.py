"""
Populate the ArenaBook database with realistic demo data.

    python manage.py seed_data
"""

import random
import uuid
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from arena.models import (
    Booking,
    City,
    ContactUs,
    Country,
    Payment,
    Review,
    SportCategory,
    State,
    Turf,
)

User = get_user_model()

LOCATIONS = {
    "India": {
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur"],
        "Karnataka": ["Bengaluru", "Mysuru"],
        "Delhi": ["New Delhi"],
    }
}

CATEGORIES = [
    ("Football", "bi-dribbble",
     "Full-size and 5-a-side floodlit football turfs with premium artificial grass."),
    ("Cricket", "bi-bullseye",
     "Box cricket arenas and practice nets with bowling machines and turf pitches."),
    ("Badminton", "bi-shuffle",
     "Wooden and synthetic indoor badminton courts with tournament-grade lighting."),
    ("Basketball", "bi-basket",
     "Outdoor and indoor half/full courts with shock-absorbing acrylic flooring."),
    ("Tennis", "bi-circle",
     "Clay and hard tennis courts available for singles, doubles and coaching."),
    ("Swimming", "bi-water",
     "Temperature controlled semi-Olympic pools with trained lifeguards on duty."),
    ("Volleyball", "bi-globe",
     "Beach-sand and indoor volleyball courts perfect for evening leagues."),
    ("Table Tennis", "bi-record-circle",
     "Air-conditioned TT halls with ITTF approved tables and robot trainers."),
]

TURFS = [
    ("Victory Arena Football Turf", "Football", "Ahmedabad", 1200,
     "Premium FIFA-grade artificial turf with 30ft nets, floodlights and a covered gallery. "
     "Ideal for 7-a-side matches and corporate tournaments.",
     "Floodlights, Parking, Washroom, Changing Room, Drinking Water, First Aid"),
    ("Kick-Off Sports Club", "Football", "Surat", 950,
     "Community football ground with two 5-a-side pitches, cafeteria and referee on request.",
     "Floodlights, Cafeteria, Parking, Washroom"),
    ("Sixer Box Cricket Arena", "Cricket", "Ahmedabad", 1500,
     "Fully enclosed box cricket arena with bounce-controlled matting, digital scoreboard "
     "and live streaming support.",
     "Scoreboard, Floodlights, Parking, Equipment Rental, Washroom"),
    ("Pavilion Cricket Nets", "Cricket", "Rajkot", 700,
     "Four practice nets with turf, cement and matting surfaces plus a bowling machine.",
     "Bowling Machine, Coach, Parking, Drinking Water"),
    ("SmashPoint Badminton Academy", "Badminton", "Ahmedabad", 500,
     "Six wooden courts with 9-metre ceiling height, AC hall and pro-shop stringing service.",
     "Air Conditioned, Pro Shop, Parking, Locker, Washroom"),
    ("Rally Indoor Courts", "Badminton", "Vadodara", 450,
     "Synthetic mat courts with anti-glare lighting, coaching available morning and evening.",
     "Coach, Locker, Parking, Cafeteria"),
    ("Hoops Basketball Court", "Basketball", "Mumbai", 800,
     "Full-size acrylic court with breakaway rims, night lighting and spectator seating.",
     "Floodlights, Seating, Parking, Washroom"),
    ("Downtown Dunk Arena", "Basketball", "Pune", 650,
     "Indoor half court perfect for 3x3 games, shooting drills and school practice.",
     "Indoor, Air Conditioned, Locker, Drinking Water"),
    ("Grand Slam Tennis Club", "Tennis", "Bengaluru", 900,
     "Two hard courts and one clay court maintained daily, ball machine available on request.",
     "Ball Machine, Coach, Floodlights, Cafeteria, Parking"),
    ("Ace Court Tennis Centre", "Tennis", "New Delhi", 1100,
     "Championship hard courts with umpire chairs and covered viewing deck.",
     "Floodlights, Seating, Locker, Parking"),
    ("AquaSprint Swimming Pool", "Swimming", "Ahmedabad", 400,
     "25-metre semi-Olympic pool with six lanes, filtered water and certified lifeguards.",
     "Lifeguard, Changing Room, Locker, Shower, Coach"),
    ("Blue Wave Aquatic Centre", "Swimming", "Gandhinagar", 350,
     "Heated indoor pool with separate kids section and learn-to-swim batches.",
     "Heated Pool, Lifeguard, Kids Pool, Parking"),
    ("Spike Beach Volleyball", "Volleyball", "Surat", 600,
     "Imported soft-sand beach volleyball court with night lighting and music system.",
     "Floodlights, Music System, Washroom, Parking"),
    ("Topspin Table Tennis Hall", "Table Tennis", "Pune", 300,
     "Eight ITTF approved tables in an air conditioned hall with robot practice machines.",
     "Air Conditioned, Robot Machine, Coach, Locker"),
]

COMMENTS = [
    "Excellent surface and very well maintained. Booking through ArenaBook was effortless.",
    "Great lighting for night games. The staff were helpful and the parking is easy.",
    "Good value for money. Could use a bigger changing room but everything else is solid.",
    "We play here every weekend now. Slots are always accurate and never double booked.",
    "Clean washrooms, punctual timing and a friendly manager. Highly recommended.",
    "The turf quality is top class. Perfect for our corporate tournament.",
    "Nice place, just a little crowded in the evening hours. Book early!",
]


class Command(BaseCommand):
    help = "Seed the database with demo users, venues, bookings, payments and reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing demo records before seeding.",
        )

    def handle(self, *args, **options):
        random.seed(7)

        if options["fresh"]:
            self.stdout.write("Clearing old demo data...")
            Payment.objects.all().delete()
            Booking.objects.all().delete()
            Review.objects.all().delete()
            Turf.objects.all().delete()
            SportCategory.objects.all().delete()
            ContactUs.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # ---------------- locations ----------------
        cities = {}
        for country_name, states in LOCATIONS.items():
            country, _ = Country.objects.get_or_create(name=country_name)
            for state_name, city_names in states.items():
                state, _ = State.objects.get_or_create(
                    name=state_name, country=country
                )
                for city_name in city_names:
                    city, _ = City.objects.get_or_create(name=city_name, state=state)
                    cities[city_name] = city
        self.stdout.write(self.style.SUCCESS(f"  Locations ready ({len(cities)} cities)"))

        # ---------------- categories ----------------
        categories = {}
        for name, icon, description in CATEGORIES:
            category, _ = SportCategory.objects.get_or_create(
                category_name=name,
                defaults={"icon": icon, "description": description},
            )
            if not category.description:
                category.description = description
                category.icon = icon
                category.save()
            categories[name] = category
        self.stdout.write(self.style.SUCCESS(f"  {len(categories)} sport categories"))

        # ---------------- users ----------------
        admin_user, created = User.objects.get_or_create(
            email="admin@arenabook.com",
            defaults={
                "first_name": "Arena",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("Admin@123")
            admin_user.save()

        demo_people = [
            ("Rahul", "Sharma", "rahul@example.com"),
            ("Priya", "Patel", "priya@example.com"),
            ("Aman", "Verma", "aman@example.com"),
            ("Sneha", "Desai", "sneha@example.com"),
            ("Karan", "Mehta", "karan@example.com"),
            ("Neha", "Joshi", "neha@example.com"),
        ]
        users = []
        for first, last, email in demo_people:
            user, made = User.objects.get_or_create(
                email=email, defaults={"first_name": first, "last_name": last}
            )
            if made:
                user.set_password("User@123")
                user.save()
            profile = user.profile
            profile.phone_no = f"9{random.randint(100000000, 999999999)}"
            profile.address = f"{random.randint(1, 99)}, Sports Colony"
            city = random.choice(list(cities.values()))
            profile.city, profile.state, profile.country = (
                city, city.state, city.state.country
            )
            profile.save()
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"  {len(users)} demo users + 1 admin"))

        # ---------------- turfs ----------------
        turfs = []
        for index, (name, cat, city_name, price, desc, amenities) in enumerate(TURFS):
            city = cities.get(city_name)
            turf, _ = Turf.objects.get_or_create(
                turf_name=name,
                defaults={
                    "category": categories[cat],
                    "description": desc,
                    "address": f"{random.randint(1, 120)}, {city_name} Sports Complex Road",
                    "city": city,
                    "state": city.state if city else None,
                    "country": city.state.country if city else None,
                    "price_per_hour": Decimal(price),
                    "open_time": time(6, 0),
                    "close_time": time(23, 0),
                    "capacity": random.choice([10, 12, 14, 16, 22]),
                    "amenities": amenities,
                    "is_featured": index < 6,
                },
            )
            turfs.append(turf)
        self.stdout.write(self.style.SUCCESS(f"  {len(turfs)} sports venues"))

        # ---------------- bookings + payments ----------------
        created_bookings = 0
        today = timezone.localdate()
        if Booking.objects.count() < 20:
            for _ in range(40):
                user = random.choice(users)
                turf = random.choice(turfs)
                day_offset = random.randint(-30, 14)
                booking_date = today + timedelta(days=day_offset)
                start_hour = random.randint(6, 21)
                duration = random.choice([1, 1, 2])
                start = time(start_hour, 0)
                end_hour = min(start_hour + duration, 23)
                if end_hour <= start_hour:
                    continue
                end = time(end_hour, 0)

                if not turf.is_slot_free(booking_date, start, end):
                    continue

                status = random.choices(
                    [Booking.CONFIRMED, Booking.PENDING, Booking.CANCELLED],
                    weights=[7, 2, 1],
                )[0]
                booking = Booking.objects.create(
                    user=user,
                    turf=turf,
                    booking_date=booking_date,
                    start_time=start,
                    end_time=end,
                    total_amount=turf.price_for(start, end),
                    status=status,
                )
                created_bookings += 1

                if status == Booking.CONFIRMED:
                    Payment.objects.create(
                        user=user,
                        booking=booking,
                        amount=booking.total_amount,
                        payment_method=random.choice(
                            [c[0] for c in Payment.PAYMENT_METHOD_CHOICES]
                        ),
                        status=Payment.COMPLETED,
                        transaction_id=f"TXN{uuid.uuid4().hex[:12].upper()}",
                        payment_date=timezone.now() - timedelta(
                            days=random.randint(0, 60)
                        ),
                    )
        self.stdout.write(
            self.style.SUCCESS(f"  {created_bookings} bookings with payments")
        )

        # ---------------- reviews ----------------
        review_count = 0
        for turf in turfs:
            for user in random.sample(users, k=random.randint(2, 4)):
                _, made = Review.objects.get_or_create(
                    user=user,
                    turf=turf,
                    defaults={
                        "rating": random.choices([5, 4, 3], weights=[6, 3, 1])[0],
                        "comment": random.choice(COMMENTS),
                    },
                )
                review_count += int(made)
        self.stdout.write(self.style.SUCCESS(f"  {review_count} reviews"))

        # ---------------- contact messages ----------------
        if not ContactUs.objects.exists():
            ContactUs.objects.bulk_create([
                ContactUs(
                    name="Vivek Anand", email="vivek@example.com",
                    phone="9876543210",
                    message="Do you offer monthly membership packages for football turfs?",
                ),
                ContactUs(
                    name="Ritika Shah", email="ritika@example.com",
                    phone="9812345670",
                    message="I want to list my badminton court on ArenaBook. "
                            "What is the process and commission?",
                ),
                ContactUs(
                    name="Sports Club Ahmedabad", email="info@sportsclub.com",
                    phone="7965432100",
                    message="Requesting a bulk booking quotation for a two-day "
                            "inter-college tournament.",
                ),
            ])
        self.stdout.write(self.style.SUCCESS("  Contact messages added"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 58))
        self.stdout.write(self.style.SUCCESS(" ArenaBook demo data loaded successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 58))
        self.stdout.write("  Admin panel : http://127.0.0.1:8000/dashboard/")
        self.stdout.write("  Admin login : admin@arenabook.com / Admin@123")
        self.stdout.write("  User login  : rahul@example.com  / User@123")
        self.stdout.write(self.style.SUCCESS("=" * 58))
