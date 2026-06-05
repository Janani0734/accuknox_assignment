import time
import threading
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.db.models.signals import post_save
from .models import MyModel
from . import signals as sig_module
from .rectangle import Rectangle


# Q1 — Django signals are SYNCHRONOUS
class Q1SynchronousSignalTest(TestCase):
    """
    Proof: The handler sleeps 2 seconds only when triggered by this test.
    save() blocks for >= 2s, proving synchronous execution.
    If signals were async, save() would return instantly (~0s).
    """
    def test_signals_are_synchronous(self):
        start = time.perf_counter()
        MyModel.objects.create(name="q1_sync_test")
        elapsed = time.perf_counter() - start
        self.assertGreaterEqual(elapsed, 2.0)


# Q2 — Signals run in the SAME THREAD as the caller
class Q2SameThreadSignalTest(TestCase):
    """
    Proof: threading.get_ident() is captured inside the handler and compared
    with the caller's thread ID. They are always identical.
    """
    def setUp(self):
        sig_module.thread_tracker["id"] = None

    def test_signals_run_in_same_thread(self):
        caller_thread_id = threading.get_ident()
        MyModel.objects.create(name="q2_thread_test")
        self.assertIsNotNone(sig_module.thread_tracker["id"])
        self.assertEqual(caller_thread_id, sig_module.thread_tracker["id"])


# Q3 — Signals run in the SAME DB TRANSACTION as the caller
class Q3SameTransactionSignalTest(TransactionTestCase):
    """
    Proof: A handler raises an exception inside atomic(). The entire
    transaction rolls back — the row is never persisted.
    If signals had a separate transaction, the row would still exist.

    Senior note — transaction.on_commit():
    In production, signals fire BEFORE the transaction commits. This creates
    a race condition where an external worker (e.g. Celery) tries to read a
    row that hasn't been committed yet. The fix is transaction.on_commit():

        @receiver(post_save, sender=MyModel)
        def notify_on_commit(sender, instance, **kwargs):
            transaction.on_commit(
                lambda: send_email_or_enqueue_task(instance.pk)
            )

    on_commit() fires only after a successful commit. If the transaction
    rolls back, the callback is silently discarded — eliminating the race.
    """
    def test_signals_run_in_same_transaction(self):
        def rollback_inducing_handler(sender, instance, **kwargs):
            raise Exception("Intentional rollback")

        post_save.connect(rollback_inducing_handler, sender=MyModel)

        try:
            with transaction.atomic():
                MyModel.objects.create(name="q3_txn_test")
        except Exception:
            pass
        finally:
            post_save.disconnect(rollback_inducing_handler, sender=MyModel)

        self.assertFalse(MyModel.objects.filter(name="q3_txn_test").exists())

    def test_on_commit_does_not_fire_on_rollback(self):
        on_commit_fired = []

        def on_commit_handler(sender, instance, **kwargs):
            transaction.on_commit(lambda: on_commit_fired.append(instance.pk))

        post_save.connect(on_commit_handler, sender=MyModel)

        try:
            with transaction.atomic():
                MyModel.objects.create(name="q3_on_commit_test")
                raise Exception("Forced rollback")
        except Exception:
            pass
        finally:
            post_save.disconnect(on_commit_handler, sender=MyModel)

        self.assertEqual(on_commit_fired, [])


# Custom Class — Rectangle (iterable)
class RectangleTest(TestCase):

    def test_iteration_order_and_keys(self):
        rect = Rectangle(10, 5)
        items = list(rect)
        self.assertEqual(items[0], {"length": 10})
        self.assertEqual(items[1], {"width": 5})

    def test_iteration_via_unpacking(self):
        length_dict, width_dict = Rectangle(7, 3)
        self.assertEqual(length_dict, {"length": 7})
        self.assertEqual(width_dict, {"width": 3})

    def test_multiple_iterations_are_independent(self):
        rect = Rectangle(4, 2)
        self.assertEqual(list(rect), list(rect))
