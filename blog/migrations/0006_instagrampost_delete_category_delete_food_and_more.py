# Generated by Django 4.1.7 on 2023-08-01 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_food'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstagramPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('caption', models.TextField()),
                ('image', models.ImageField(blank=True, upload_to='uploads/')),
                ('scheduled_time', models.DateTimeField()),
            ],
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Food',
        ),
        migrations.DeleteModel(
            name='Recipe',
        ),
    ]
