# AccuKnox Django Trainee Take-Home Assessment

## Project Layout

accuknox_assignment/
├── manage.py
├── accuknox_assignment/        # Project settings and URL conf
└── signals_demo/               # App containing all answers
    ├── apps.py                 # Calls import signals inside ready()
    ├── models.py               # MyModel — the save() target for proofs
    ├── signals.py              # Handlers for Q1 (sync) and Q2 (thread)
    ├── rectangle.py            # Custom Rectangle class (+ Option B reference)
    └── tests.py                # One TestCase class per question

Expected result: 8 passed, 0 failed.

## Q1 — Django signals are SYNCHRONOUS

Answer: post_save (and all built-in signals) dispatches handlers synchronously. The call to save() blocks until every registered handler has returned.

Proof: The handler calls time.sleep(2). The test measures wall-clock time around save(). If signals were async, save() would return in approximately 0 seconds. Instead it consistently returns in 2 or more seconds, proving blocking/synchronous execution.

```python
# signals.py
@receiver(post_save, sender=MyModel, dispatch_uid="q1_sync_proof")
def q1_sync_proof_handler(sender, instance, **kwargs):
    time.sleep(2)

# tests.py
start = time.perf_counter()
MyModel.objects.create(name="q1_sync_test")
elapsed = time.perf_counter() - start
assert elapsed >= 2.0
```

## Q2 — Signals run in the SAME THREAD as the caller

Answer: Django dispatches signals on the calling thread. There is no thread pool or background dispatch mechanism.

Proof: The handler stores threading.get_ident() in a module-level variable. After save() returns, the test compares that value against its own thread ID. They are always identical.

```python
# signals.py
thread_id_captured_by_signal = None

@receiver(post_save, sender=MyModel, dispatch_uid="q2_thread_proof")
def q2_thread_proof_handler(sender, instance, **kwargs):
    global thread_id_captured_by_signal
    thread_id_captured_by_signal = threading.get_ident()

# tests.py
caller_thread_id = threading.get_ident()
MyModel.objects.create(name="q2_thread_test")
assert caller_thread_id == sig_module.thread_id_captured_by_signal
```

## Q3 — Signals run inside the SAME DB TRANSACTION as the caller

Answer: By default, post_save fires before the transaction commits, meaning it shares the caller's database transaction.

Proof: A one-shot handler raises an exception. Because the handler runs inside the same atomic() block, the exception unwinds the entire transaction and the row is never persisted.

```python
def rollback_inducing_handler(sender, instance, **kwargs):
    raise Exception("Intentional rollback")

post_save.connect(rollback_inducing_handler, sender=MyModel)

try:
    with transaction.atomic():
        MyModel.objects.create(name="q3_txn_test")
except Exception:
    pass

assert not MyModel.objects.filter(name="q3_txn_test").exists()
```

Senior Note on transaction.on_commit():

The default behaviour creates a race condition in real applications. If the signal enqueues a Celery task or calls an external API, the worker may try to read a row that has not been committed yet. The fix is transaction.on_commit():

```python
@receiver(post_save, sender=MyModel)
def notify_on_commit(sender, instance, **kwargs):
    transaction.on_commit(
        lambda: send_welcome_email_or_enqueue_task(instance.pk)
    )
```

on_commit() callbacks fire only once the outermost atomic block commits successfully. If the transaction rolls back, the callback is silently discarded, eliminating the race condition entirely.

## Custom Class — Rectangle

Chosen approach: generator-based __iter__

```python
class Rectangle:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width

    def __iter__(self):
        yield {"length": self.length}
        yield {"width": self.width}
```

yield inside __iter__ is the cleanest approach. Python turns the method into a generator function which returns a fresh iterator on every call. The rectangle.py file also includes an explicit iterator version as a reference to show the trade-off between the two approaches.
