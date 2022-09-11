from django.db import models


class CreationDateModel(models.Model):
    """Абстрактная модель для добавления даты в наследуемые классы."""
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True
