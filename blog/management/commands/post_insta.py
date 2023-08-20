from django.core.management.base import BaseCommand
from blog.views import post_insta

class Command(BaseCommand):
    help = 'Runs the post_insta function continuously'

    def handle(self, *args, **options):
        post_insta()
