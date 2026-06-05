# AccuKnox Django Trainee Take-Home Assessment

## Project Layout

    accuknox_assignment/
        manage.py
        accuknox_assignment/
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

## Q2: Signals run in the SAME THREAD as the caller

Answer: Django dispatches signals on the calling thread. There is no thread pool or background dispatch mechanism.

Proof: threading.get_ident() is captured inside the handler and compared with the caller thread ID. They are always identical.

## Q3: Signals run in the SAME DB TRANSACTION as the caller

Answer: By default, post_save fires before the transaction commits, meaning it shares the caller's database transaction.

Proof: A handler raises an exception inside atomic(). The entire transaction rolls back and the row is never saved to the database.

Senior Note: Using transaction.on_commit() ensures side effects like emails or Celery tasks only run after a successful commit, avoiding race conditions entirely.

## Custom Class: Rectangle

Used yield inside __iter__ for clean Pythonic iteration. rectangle.py also includes an explicit iterator version as reference.
