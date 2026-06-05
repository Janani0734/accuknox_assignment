import time
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MyModel

# Mutable container to capture thread ID (avoids primitive global reset issues)
thread_tracker = {"id": None}

@receiver(post_save, sender=MyModel, dispatch_uid="q1_sync_proof")
def q1_sync_proof_handler(sender, instance, **kwargs):
    if instance.name == "q1_sync_test":
        time.sleep(2)

@receiver(post_save, sender=MyModel, dispatch_uid="q2_thread_proof")
def q2_thread_proof_handler(sender, instance, **kwargs):
    thread_tracker["id"] = threading.get_ident()
