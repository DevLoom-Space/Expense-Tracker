from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_deleted=False)


class TransactionQuerySet(ActiveQuerySet):
    def for_user(self, user):
        return self.active().filter(owner=user)

    def expenses(self):
        return self.filter(t_type="EXPENSE")

    def income(self):
        return self.filter(t_type="INCOME")


class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def active(self):
        return self.get_queryset().active()
