from django.db import models

class InstagramPost(models.Model):
    user_name = models.TextField(blank=True)
    caption = models.TextField()
    image = models.ImageField(blank=True)
    scheduled_time = models.DateTimeField()

    def __str__(self):
        return self.caption[:50]  # Return the first 50 characters of the caption for display purposes

class InstagramLogin(models.Model):
    user_name = models.TextField()
    pass_word = models.CharField(max_length=255)

    def __str__(self):
        return self.user_name