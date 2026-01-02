from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE users DROP COLUMN IF EXISTS username;",
            reverse_sql="ALTER TABLE users ADD COLUMN username VARCHAR(100);"
        ),
    ]
