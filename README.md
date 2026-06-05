# AccuKnox Django Trainee Take-Home Assessment

## Project Layout

    accuknox_assignment/ 
    manage.py accuknox_assignment/ 
        signals_demo/ 
        apps.py 
        models.py 
        signals.py 
        rectangle.py 
        tests.py 
    Expected result: 7 passed, 0 failed.

## Q1: Django signals are SYNCHRONOUS

Answer: post_save dispatches handlers synchronously. The call to save() blocks until every registered handler has returned.

Proof: The handler calls time.sleep(2). If signals were async, save() would return in 0 seconds. Instead it takes 2 or more seconds, proving synchronous execution.

```python
@receiver(post_save, sender=MyModel, dispatch_uid="q1_sync_proof")
def q1_sync_proof_handler(sender, instance, **kwargs):
    time.sleep(2)

start = time.perf_counter()
MyModel.objects.create(name="q1_sync_test")
elapsed = time.perf_counter() - start
assert elapsed >= 2.0
```

## Q2: Signals run in the SAME THREAD as the caller

Answer: Django dispatches signals on the calling thread. There is no thread pool or background dispatch mechanism.

Proof: threading.get_ident() is captured inside the handler and compared with the caller thread ID. They are always identical.

```python
@receiver(post_save, sender=MyModel, dispatch_uid="q2_thread_proof")
def q2_thread_proof_handler(sender, instance, **kwargs):
    thread_tracker["id"] = threading.get_ident()

caller_thread_id = threading.get_ident()
MyModel.objects.create(name="q2_thread_test")
assert caller_thread_id == sig_module.thread_tracker["id"]
```

## Q3: Signals run in the SAME DB TRANSACTION as the caller

Answer: By default, post_save fires before the transaction commits, meaning it shares the caller's database transaction.

Proof: A handler raises an exception inside atomic(). The entire transaction rolls back and the row is never saved to the database.

```python
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

assert not MyModel.objects.filter(name="q3_txn_test").exists()
```

Senior Note on transaction.on_commit():

The default behaviour creates a race condition in real applications. If a signal enqueues a Celery task, the worker may try to read a row that has not been committed yet. The fix is transaction.on_commit() which ensures the callback only runs after a successful commit. If the transaction rolls back, the callback is silently discarded.

```python
@receiver(post_save, sender=MyModel)
def notify_on_commit(sender, instance, **kwargs):
    transaction.on_commit(
        lambda: send_welcome_email_or_enqueue_task(instance.pk)
    )
```

## Custom Class: Rectangle

Chosen approach: generator-based __iter__ using yield.

```python
class Rectangle:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        yield {"length": self.length}
        yield {"width": self.width}
```

yield inside __iter__ is the cleanest approach. Python turns the method into a generator function which returns a fresh iterator on every call. The rectangle.py file also includes an explicit iterator version as a reference.
