from django.db import models
from Homepage.models import CustomUser
from cart.models import Cart


class Payment(models.Model):
    CHARGE_STATUS = (("SUCCESSFUL", "Successful"), ("PENDING", "Pending"))

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="user_payment", null=True
    )
    cart = models.OneToOneField(
        Cart, on_delete=models.CASCADE, related_name="cart_payment", null=True
    )

    stripe_charge_id = models.CharField(max_length=150, blank=False)
    stripe_customer_id = models.CharField(max_length=150, blank=False)
    payment_status = models.CharField(
        max_length=25, choices=CHARGE_STATUS, default="PENDING"
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Refund(models.Model):
    REFUND_CHOICES = (("REFUNDED", "Refund"), ("NO_REFUND", "No Refund"))
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_refund", null=True
    )
    stripe_refund_id = models.CharField(max_length=150, null=True, default=0)
    refund_status = models.CharField(
        max_length=25, choices=REFUND_CHOICES, default="NO_REFUND"
    )
    cart_item_id = models.PositiveIntegerField(null=True)
