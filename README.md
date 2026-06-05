# AccuKnox Django Trainee Assignment

## Question 1: Are Django signals synchronous or asynchronous?

Django signals are synchronous by default. To prove this, I added a time.sleep(2) inside the post_save handler. The save() call blocked for 2 or more seconds, confirming synchronous execution.

## Question 2: Do Django signals run in the same thread as the caller?

Yes. I captured threading.get_ident() inside the handler and compared it with the caller thread ID. Both were identical, confirming same thread execution.

## Question 3: Do Django signals run in the same database transaction as the caller?

Yes. I connected a handler that raises an exception on purpose. The entire transaction rolled back and the object was not saved, confirming shared transaction.

Note: Using transaction.on_commit() ensures side effects like emails or Celery tasks only run after a successful commit, avoiding race conditions.

## Rectangle Class

Used yield inside __iter__ for clean and Pythonic iteration. rectangle.py also includes an explicit iterator version as reference.
