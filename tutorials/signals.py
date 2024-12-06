from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from tutorials.models import Student, Tutor

User = settings.AUTH_USER_MODEL

@receiver(post_save, sender=User)
def create_or_update_profile_for_role(sender, instance, created, **kwargs):
    """
    Automatically create or update a Student or Tutor profile when a UserID's role is assigned or updated.
    """
    if hasattr(instance, "role"):
        if instance.role == "student":
            Student.objects.get_or_create(UserID=instance)
        elif instance.role == "tutor":
            Tutor.objects.get_or_create(UserID=instance)
