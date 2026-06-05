from django.db import models


class MyModel(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'signals_demo'
