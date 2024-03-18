# Generated by Django 4.0.3 on 2024-03-17 23:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('newsApp', '0006_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='category',
            name='status',
            field=models.CharField(choices=[('1', 'Active'), ('2', 'Inactive')], default=1, max_length=20),
        ),
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='newsApp.category'),
        ),
        migrations.AlterField(
            model_name='post',
            name='status',
            field=models.CharField(choices=[('pending', 'En attente de validation'), ('approved', 'Approuvé'), ('rejected', 'Rejeté')], default='pending', max_length=20),
        ),
    ]