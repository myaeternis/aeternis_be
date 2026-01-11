# Generated manually for security app

import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiChallengeToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('secret', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('is_revoked', models.BooleanField(default=False)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'API Challenge Token',
                'verbose_name_plural': 'API Challenge Tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ApiNonce',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nonce', models.CharField(db_index=True, max_length=64, unique=True)),
                ('used_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('expires_at', models.DateTimeField(db_index=True)),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nonces', to='security.apichallengetoken')),
            ],
            options={
                'verbose_name': 'API Nonce',
                'verbose_name_plural': 'API Nonces',
                'ordering': ['-used_at'],
            },
        ),
        migrations.AddIndex(
            model_name='apichallengetoken',
            index=models.Index(fields=['token', 'expires_at'], name='security_ap_token_e8a123_idx'),
        ),
        migrations.AddIndex(
            model_name='apinonce',
            index=models.Index(fields=['nonce', 'expires_at'], name='security_ap_nonce_e8a123_idx'),
        ),
        migrations.AddIndex(
            model_name='apinonce',
            index=models.Index(fields=['token', 'expires_at'], name='security_ap_token_e8a456_idx'),
        ),
    ]
