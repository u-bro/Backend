from django.db import migrations, transaction
from django.utils import timezone
import random


def create_test_data(apps, schema_editor):
    # Import models directly since some are managed=False
    from admin_users.models import User
    from admin_drivers.models import DriverProfile
    from admin_tariffs.models import TariffPlan
    from admin_rides.models import Ride
    from admin_roles.models import Role
    from admin_driver_documents.models import DriverDocument
    from admin_chat_messages.models import ChatMessage
    from admin_commissions.models import Commission
    from admin_transactions.models import Transaction
    from admin_ride_status_history.models import RideStatusHistory

    with transaction.atomic():
        # Create Roles
        admin_role, _ = Role.objects.get_or_create(
            code='admin',
            defaults={
                'name': 'Administrator',
                'description': 'Admin role',
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        driver_role, _ = Role.objects.get_or_create(
            code='driver',
            defaults={
                'name': 'Driver',
                'description': 'Driver role',
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        client_role, _ = Role.objects.get_or_create(
            code='client',
            defaults={
                'name': 'Client',
                'description': 'Client role',
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )

        # Create Users
        admin_user, _ = User.objects.get_or_create(
            phone='+1234567890',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True,
                'role_id': admin_role.id,
                'created_at': timezone.now(),
                'last_active_at': timezone.now()
            }
        )
        driver_user1, _ = User.objects.get_or_create(
            phone='+1234567891',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'is_active': True,
                'role_id': driver_role.id,
                'created_at': timezone.now(),
                'last_active_at': timezone.now()
            }
        )
        driver_user2, _ = User.objects.get_or_create(
            phone='+1234567892',
            defaults={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_active': True,
                'role_id': driver_role.id,
                'created_at': timezone.now(),
                'last_active_at': timezone.now()
            }
        )
        client_user1, _ = User.objects.get_or_create(
            phone='+1234567893',
            defaults={
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'is_active': True,
                'role_id': client_role.id,
                'created_at': timezone.now(),
                'last_active_at': timezone.now()
            }
        )
        client_user2, _ = User.objects.get_or_create(
            phone='+1234567894',
            defaults={
                'first_name': 'Bob',
                'last_name': 'Brown',
                'is_active': True,
                'role_id': client_role.id,
                'created_at': timezone.now(),
                'last_active_at': timezone.now()
            }
        )

        # Create Driver Profiles
        driver_profile1, _ = DriverProfile.objects.get_or_create(
            user_id=driver_user1.id,
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'display_name': 'John Driver',
                'birth_date': timezone.now() - timezone.timedelta(days=365*30),
                'photo_url': 'https://example.com/photo1.jpg',
                'license_number': 'DL123456',
                'license_category': 'B',
                'license_issued_at': timezone.now() - timezone.timedelta(days=365*5),
                'license_expires_at': timezone.now() + timezone.timedelta(days=365*2),
                'experience_years': 5,
                'approved': True,
                'approved_by': admin_user.id,
                'approved_at': timezone.now(),
                'qualification_level': 'Standard',
                'classes_allowed': ['economy', 'comfort'],
                'documents_status': 'approved',
                'documents_review_notes': 'All documents verified',
                'rating_avg': 4,
                'rating_count': 10,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )
        driver_profile2, _ = DriverProfile.objects.get_or_create(
            user_id=driver_user2.id,
            defaults={
                'first_name': 'Jane',
                'last_name': 'Smith',
                'display_name': 'Jane Driver',
                'birth_date': timezone.now() - timezone.timedelta(days=365*28),
                'photo_url': 'https://example.com/photo2.jpg',
                'license_number': 'DL654321',
                'license_category': 'B',
                'license_issued_at': timezone.now() - timezone.timedelta(days=365*3),
                'license_expires_at': timezone.now() + timezone.timedelta(days=365*3),
                'experience_years': 3,
                'approved': True,
                'approved_by': admin_user.id,
                'approved_at': timezone.now(),
                'qualification_level': 'Premium',
                'classes_allowed': ['comfort', 'business'],
                'documents_status': 'approved',
                'documents_review_notes': 'Verified',
                'rating_avg': 5,
                'rating_count': 15,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )

        # Create Tariff Plans
        tariff1, _ = TariffPlan.objects.get_or_create(
            name='Economy',
            defaults={
                'updated_at': timezone.now(),
                'created_at': timezone.now(),
                'effective_from': timezone.now(),
                'effective_to': None,
                'base_fare': 5.0,
                'rate_per_meter': 0.01,
                'multiplier': 1.0,
                'rules': {'min_fare': 10.0},
                'commission_percentage': 10.0
            }
        )
        tariff2, _ = TariffPlan.objects.get_or_create(
            name='Comfort',
            defaults={
                'updated_at': timezone.now(),
                'created_at': timezone.now(),
                'effective_from': timezone.now(),
                'effective_to': None,
                'base_fare': 10.0,
                'rate_per_meter': 0.015,
                'multiplier': 1.2,
                'rules': {'min_fare': 15.0},
                'commission_percentage': 12.0
            }
        )

        # Create Commissions
        commission1, _ = Commission.objects.get_or_create(
            name='Standard Commission',
            defaults={
                'percentage': 10.0,
                'fixed_amount': 0.0,
                'currency': 'USD',
                'valid_from': timezone.now(),
                'valid_to': None,
                'created_at': timezone.now()
            }
        )
        commission2, _ = Commission.objects.get_or_create(
            name='Premium Commission',
            defaults={
                'percentage': 12.0,
                'fixed_amount': 0.0,
                'currency': 'USD',
                'valid_from': timezone.now(),
                'valid_to': None,
                'created_at': timezone.now()
            }
        )

        # Create Rides
        ride1, _ = Ride.objects.get_or_create(
            client_id=client_user1.id,
            pickup_address='123 Main St',
            defaults={
                'driver_profile_id': driver_profile1.id,
                'status': 'completed',
                'status_reason': None,
                'pickup_lat': 40.7128,
                'pickup_lng': -74.0060,
                'dropoff_address': '456 Elm St',
                'dropoff_lat': 40.7589,
                'dropoff_lng': -73.9851,
                'scheduled_at': None,
                'started_at': timezone.now() - timezone.timedelta(hours=2),
                'completed_at': timezone.now() - timezone.timedelta(hours=1),
                'canceled_at': None,
                'cancellation_reason': None,
                'expected_fare': 25.0,
                'expected_fare_snapshot': {'base': 5.0, 'distance': 20.0},
                'driver_fare': 22.5,
                'actual_fare': 25.0,
                'distance_meters': 5000,
                'duration_seconds': 3600,
                'transaction_id': None,
                'commission_id': commission1.id,
                'is_anomaly': False,
                'anomaly_reason': None,
                'ride_metadata': {'notes': 'Smooth ride'},
                'created_at': timezone.now() - timezone.timedelta(hours=2),
                'updated_at': timezone.now() - timezone.timedelta(hours=1),
                'tariff_plan_id': tariff1.id
            }
        )
        ride2, _ = Ride.objects.get_or_create(
            client_id=client_user2.id,
            pickup_address='789 Oak St',
            defaults={
                'driver_profile_id': driver_profile2.id,
                'status': 'in_progress',
                'status_reason': None,
                'pickup_lat': 40.7505,
                'pickup_lng': -73.9934,
                'dropoff_address': '101 Pine St',
                'dropoff_lat': 40.7614,
                'dropoff_lng': -73.9776,
                'scheduled_at': None,
                'started_at': timezone.now() - timezone.timedelta(minutes=30),
                'completed_at': None,
                'canceled_at': None,
                'cancellation_reason': None,
                'expected_fare': 30.0,
                'expected_fare_snapshot': {'base': 10.0, 'distance': 20.0},
                'driver_fare': None,
                'actual_fare': None,
                'distance_meters': 0,
                'duration_seconds': 0,
                'transaction_id': None,
                'commission_id': commission2.id,
                'is_anomaly': False,
                'anomaly_reason': None,
                'ride_metadata': {},
                'created_at': timezone.now() - timezone.timedelta(minutes=30),
                'updated_at': timezone.now(),
                'tariff_plan_id': tariff2.id
            }
        )

        # Create Transactions
        transaction1, _ = Transaction.objects.get_or_create(
            user_id=driver_user1.id,
            amount=22.5,
            is_withdraw=False,
            defaults={
                'created_at': timezone.now() - timezone.timedelta(hours=1)
            }
        )
        transaction2, _ = Transaction.objects.get_or_create(
            user_id=client_user1.id,
            amount=25.0,
            is_withdraw=True,
            defaults={
                'created_at': timezone.now() - timezone.timedelta(hours=1)
            }
        )

        # Create Driver Documents
        doc1, _ = DriverDocument.objects.get_or_create(
            driver_profile_id=driver_profile1.id,
            doc_type='license',
            defaults={
                'file_url': 'https://example.com/license1.pdf',
                'status': 'approved',
                'reviewed_by': admin_user.id,
                'reviewed_at': timezone.now(),
                'created_at': timezone.now()
            }
        )
        doc2, _ = DriverDocument.objects.get_or_create(
            driver_profile_id=driver_profile2.id,
            doc_type='insurance',
            defaults={
                'file_url': 'https://example.com/insurance2.pdf',
                'status': 'approved',
                'reviewed_by': admin_user.id,
                'reviewed_at': timezone.now(),
                'created_at': timezone.now()
            }
        )

        # Create Chat Messages
        msg1, _ = ChatMessage.objects.get_or_create(
            ride_id=ride1.id,
            text='Hello, I am on my way.',
            sender_id=driver_user1.id,
            defaults={
                'receiver_id': client_user1.id,
                'message_type': 'text',
                'attachments': None,
                'is_moderated': False,
                'created_at': timezone.now() - timezone.timedelta(hours=1, minutes=30),
                'edited_at': None,
                'deleted_at': None
            }
        )
        msg2, _ = ChatMessage.objects.get_or_create(
            ride_id=ride1.id,
            text='Thank you!',
            sender_id=client_user1.id,
            defaults={
                'receiver_id': driver_user1.id,
                'message_type': 'text',
                'attachments': None,
                'is_moderated': False,
                'created_at': timezone.now() - timezone.timedelta(hours=1, minutes=20),
                'edited_at': None,
                'deleted_at': None
            }
        )

        # Create Ride Status History
        history1, _ = RideStatusHistory.objects.get_or_create(
            ride_id=ride1.id,
            from_status='requested',
            to_status='accepted',
            defaults={
                'changed_by': driver_user1.id,
                'actor_role': 'driver',
                'reason': None,
                'meta': {},
                'created_at': timezone.now() - timezone.timedelta(hours=2)
            }
        )
        history2, _ = RideStatusHistory.objects.get_or_create(
            ride_id=ride1.id,
            from_status='accepted',
            to_status='started',
            defaults={
                'changed_by': driver_user1.id,
                'actor_role': 'driver',
                'reason': None,
                'meta': {},
                'created_at': timezone.now() - timezone.timedelta(hours=2)
            }
        )
        history3, _ = RideStatusHistory.objects.get_or_create(
            ride_id=ride1.id,
            from_status='started',
            to_status='completed',
            defaults={
                'changed_by': driver_user1.id,
                'actor_role': 'driver',
                'reason': None,
                'meta': {},
                'created_at': timezone.now() - timezone.timedelta(hours=1)
            }
        )


def noop_reverse(apps, schema_editor):
    # Do not remove test data on reverse
    return


class Migration(migrations.Migration):
    dependencies = [
        ('admin_users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_test_data, noop_reverse),
    ]