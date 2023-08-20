# celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'post_insta_task': {
        'task': 'blog.management.commands.post_insta',
        'schedule': crontab(minute='*'),  # Run the task every minute
    },
}
