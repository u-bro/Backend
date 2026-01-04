"""Script to seed test data - run with: python manage.py shell < seed_data.py"""
from django.db import connection
from datetime import datetime, timedelta
import random
import json

def seed_all():
    with connection.cursor() as cursor:
        # Roles
        cursor.execute("""
            INSERT INTO roles (code, name, description, created_at, updated_at)
            VALUES 
                ('client', 'Клиент', 'Пользователь приложения', NOW(), NOW()),
                ('driver', 'Водитель', 'Водитель такси', NOW(), NOW()),
                ('operator', 'Оператор', 'Оператор службы поддержки', NOW(), NOW()),
                ('admin', 'Администратор', 'Администратор системы', NOW(), NOW())
            ON CONFLICT (code) DO NOTHING
        """)
        print('✅ Created roles')
        
        # Users
        cursor.execute("""
            INSERT INTO users (created_at, last_active_at, first_name, last_name, phone, is_active, role_id)
            SELECT 
                NOW() - (RANDOM() * 365)::int * INTERVAL '1 day',
                NOW() - (RANDOM() * 2)::int * INTERVAL '1 day',
                'User' || generate_series,
                'Lastname' || generate_series,
                '+79000' || LPAD(generate_series::text, 6, '0'),
                CASE WHEN RANDOM() > 0.2 THEN true ELSE false END,
                (SELECT id FROM roles WHERE code = CASE WHEN generate_series <= 10 THEN 'client' ELSE 'driver' END)
            FROM generate_series(1, 20)
            ON CONFLICT (phone) DO NOTHING
        """)
        print('✅ Created 20 users')
        
        # Tariff plans
        cursor.execute("""
            INSERT INTO tariff_plans (name, effective_from, effective_to, base_fare, rate_per_meter, multiplier, rules, commission_percentage, created_at, updated_at)
            VALUES 
                ('Эконом', NOW() - INTERVAL '30 days', NULL, 50.0, 8.0, 1.0, '{"min_distance": 500}'::jsonb, 15.0, NOW(), NOW()),
                ('Комфорт', NOW() - INTERVAL '30 days', NULL, 100.0, 12.0, 1.2, '{"min_distance": 500}'::jsonb, 18.0, NOW(), NOW()),
                ('Бизнес', NOW() - INTERVAL '30 days', NULL, 200.0, 20.0, 1.5, '{"min_distance": 500}'::jsonb, 20.0, NOW(), NOW())
        """)
        print('✅ Created 3 tariff plans')
        
        # Driver profiles
        cursor.execute("""
            INSERT INTO driver_profiles (user_id, display_name, first_name, last_name, birth_date, photo_url, 
                                        license_number, license_category, license_issued_at, license_expires_at,
                                        experience_years, approved, approved_by, approved_at, qualification_level,
                                        classes_allowed, documents_status, rating_avg, rating_count, created_at, updated_at)
            SELECT 
                u.id,
                'Driver' || u.id,
                u.first_name,
                u.last_name,
                NOW() - (25 + RANDOM() * 20)::int * INTERVAL '1 year',
                'https://example.com/photo' || u.id || '.jpg',
                'AB' || (1000000 + RANDOM() * 8999999)::int,
                'B',
                NOW() - (2 + RANDOM() * 3)::int * INTERVAL '1 year',
                NOW() + (5 + RANDOM() * 5)::int * INTERVAL '1 year',
                (1 + RANDOM() * 14)::int,
                CASE WHEN RANDOM() > 0.3 THEN true ELSE false END,
                1,
                NOW() - (RANDOM() * 30)::int * INTERVAL '1 day',
                'basic',
                '["economy", "comfort"]'::jsonb,
                'approved',
                4.0 + RANDOM(),
                (10 + RANDOM() * 90)::int,
                NOW() - (RANDOM() * 365)::int * INTERVAL '1 day',
                NOW()
            FROM users u
            WHERE u.role_id = (SELECT id FROM roles WHERE code = 'driver')
            LIMIT 10
            ON CONFLICT (user_id) DO NOTHING
        """)
        print('✅ Created driver profiles')
        
        # Rides
        cursor.execute("""
            INSERT INTO rides (client_id, driver_profile_id, status, pickup_address, pickup_lat, pickup_lng,
                              dropoff_address, dropoff_lat, dropoff_lng, scheduled_at, started_at, completed_at,
                              expected_fare, actual_fare, distance_meters, duration_seconds, tariff_plan_id, 
                              is_anomaly, created_at, updated_at)
            SELECT 
                (SELECT id FROM users WHERE role_id = (SELECT id FROM roles WHERE code = 'client') ORDER BY RANDOM() LIMIT 1),
                (SELECT id FROM driver_profiles ORDER BY RANDOM() LIMIT 1),
                CASE (RANDOM() * 3)::int 
                    WHEN 0 THEN 'completed'
                    WHEN 1 THEN 'cancelled'
                    ELSE 'in_progress'
                END,
                'ул. Ленина, ' || (1 + RANDOM() * 100)::int,
                55.7558 + (RANDOM() - 0.5) * 0.2,
                37.6173 + (RANDOM() - 0.5) * 0.2,
                'ул. Пушкина, ' || (1 + RANDOM() * 100)::int,
                55.7558 + (RANDOM() - 0.5) * 0.2,
                37.6173 + (RANDOM() - 0.5) * 0.2,
                NOW() + (RANDOM() * 60)::int * INTERVAL '1 minute',
                NOW(),
                NOW() + (RANDOM() * 30)::int * INTERVAL '1 minute',
                (200 + RANDOM() * 800)::int,
                (200 + RANDOM() * 800)::int,
                (3000 + RANDOM() * 12000)::int,
                (600 + RANDOM() * 1200)::int,
                (SELECT id FROM tariff_plans ORDER BY RANDOM() LIMIT 1),
                false,
                NOW() - (RANDOM() * 30)::int * INTERVAL '1 day',
                NOW()
            FROM generate_series(1, 30)
        """)
        print('✅ Created 30 rides')
        
        # Transactions
        cursor.execute("""
            INSERT INTO transactions (user_id, is_withdraw, amount, created_at)
            SELECT 
                u.id,
                CASE WHEN RANDOM() > 0.5 THEN true ELSE false END,
                (100 + RANDOM() * 1900)::int,
                NOW() - (RANDOM() * 30)::int * INTERVAL '1 day'
            FROM users u
            CROSS JOIN generate_series(1, 3)
            LIMIT 50
        """)
        print('✅ Created 50 transactions')
        
        # Driver documents  
        cursor.execute("""
            INSERT INTO driver_documents (driver_profile_id, doc_type, file_url, status, reviewed_by, reviewed_at, created_at)
            SELECT 
                dp.id,
                CASE (RANDOM() * 3)::int 
                    WHEN 0 THEN 'passport'
                    WHEN 1 THEN 'license'
                    ELSE 'insurance'
                END,
                'https://example.com/doc_' || dp.id || '_' || generate_series || '.pdf',
                CASE (RANDOM() * 2)::int 
                    WHEN 0 THEN 'approved'
                    WHEN 1 THEN 'pending'
                    ELSE 'rejected'
                END,
                1,
                NOW() - (RANDOM() * 10)::int * INTERVAL '1 day',
                NOW() - (RANDOM() * 30)::int * INTERVAL '1 day'
            FROM driver_profiles dp
            CROSS JOIN generate_series(1, 3)
        """)
        print('✅ Created driver documents')
        
        # Driver ratings
        cursor.execute("""
            INSERT INTO driver_ratings (driver_profile_id, client_id, ride_id, rate, comment, created_at)
            SELECT 
                (SELECT driver_profile_id FROM rides WHERE status = 'completed' ORDER BY RANDOM() LIMIT 1),
                (SELECT client_id FROM rides WHERE status = 'completed' ORDER BY RANDOM() LIMIT 1),
                (SELECT id FROM rides WHERE status = 'completed' ORDER BY RANDOM() LIMIT 1),
                (3 + RANDOM() * 2)::int,
                CASE (RANDOM() * 3)::int
                    WHEN 0 THEN 'Отличная поездка!'
                    WHEN 1 THEN 'Хороший водитель'
                    ELSE 'Все понравилось'
                END,
                NOW() - (RANDOM() * 30)::int * INTERVAL '1 day'
            FROM generate_series(1, 50)
        """)
        print('✅ Created driver ratings')
        
        # Ride status history
        cursor.execute("""
            INSERT INTO ride_status_history (ride_id, from_status, to_status, changed_by, actor_role, reason, created_at)
            SELECT 
                r.id,
                'pending',
                'in_progress',
                r.driver_profile_id,
                'driver',
                'Driver accepted',
                r.created_at + INTERVAL '5 minutes'
            FROM rides r
            WHERE r.status IN ('completed', 'in_progress')
            LIMIT 50
        """)
        print('✅ Created ride status history')
        
        # Chat messages
        cursor.execute("""
            INSERT INTO chat_messages (ride_id, sender_id, receiver_id, text, message_type, is_moderated, created_at)
            SELECT 
                r.id,
                r.client_id,
                (SELECT user_id FROM driver_profiles WHERE id = r.driver_profile_id),
                'Тестовое сообщение ' || generate_series,
                'text',
                false,
                r.created_at + (generate_series * 5)::int * INTERVAL '1 minute'
            FROM rides r
            CROSS JOIN generate_series(1, 5)
            WHERE r.driver_profile_id IS NOT NULL
            LIMIT 100
        """)
        print('✅ Created chat messages')

seed_all()
print('\n🎉 All test data created successfully!')
