from django.shortcuts import render, redirect
import stripe, json
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from Homepage.models import CustomUser, UserProfile
from cart.models import Cart, CartItem
from django.contrib import messages
from checkout.models import Payment, Refund

stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckOutView(View):
    template_name = "checkout.html"

    def get_user_from_cookie(self):
        user_id = self.request.session["user_id"]
        user = CustomUser.objects.get(id=user_id)
        return user

    def get_cart_for_user(self):
        user = self.get_user_from_cookie()
        cart = Cart.objects.get(user=user)
        return cart

    def get_userprofile_for_user(self):
        user_id = self.request.session["user_id"]
        phone = UserProfile.objects.get(user__id=user_id).phone_number.as_e164
        full_name = UserProfile.objects.get(user__id=user_id).full_name
        shipping_address = UserProfile.objects.get(user__id=user_id).shipping_address
        return phone, full_name, shipping_address

    def cart_total(self):
        try:
            user = self.get_user_from_cookie()
            cart = Cart.objects.get(user=user)
            return cart.total
        except Exception as e:
            pass

    def get(self, request, *kwargs):
        context = {"stripe_publication_key": settings.PUBLISHABLE_KEY}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.method == "POST":
            stripe_token = request.POST.get("stripeToken")
            [phone, name, shipping_address] = self.get_userprofile_for_user()

            try:
                email = self.get_user_from_cookie().email

                query = f"email:'{email}' AND phone:'{phone}' AND name:'{name}'"

                customers = stripe.Customer.search(query=query)
                stripe_customer = None
                # the stripe.CustomerList class internally parses the JSON response received from
                # the Stripe API and provides an interface to work with the data as if it
                # were a Python object.
                try:
                    if "data" in customers and customers["data"]:
                        for customer in customers["data"]:
                            if (
                                customer["email"] == email
                                and customer["phone"] == phone
                                and customer["name"] == name
                                and "user_id" in customer["metadata"]
                                and "cart_id" in customer["metadata"]
                                and customer["metadata"]["user_id"]
                                == str(self.request.session["user_id"])
                                and customer["metadata"]["cart_id"]
                                == str(self.get_cart_for_user().id)
                            ):
                                stripe_customer = customer
                                break
                    else:
                        try:
                            stripe_customer = stripe.Customer.create(
                                source=stripe_token,
                                phone=phone,
                                email=email,
                                name=name,
                                metadata={
                                    "user_id": self.request.session["user_id"],
                                    "cart_id": self.get_cart_for_user().id,
                                },
                            )
                        except Exception as e:
                            return JsonResponse({"error": str(e)})

                    try:
                        if stripe_customer and "id" in stripe_customer:
                            charge = stripe.Charge.create(
                                customer=stripe_customer.get("id"),
                                amount=int(self.cart_total()),
                                currency="usd",
                                description="Example Charge",
                                metadata={
                                    "user_id": self.request.session["user_id"],
                                    "cart_id": self.get_cart_for_user().id,
                                },
                            )
                            Payment.objects.create(
                                user=self.get_user_from_cookie(),
                                cart=self.get_cart_for_user(),
                                stripe_charge_id=charge["id"],
                                stripe_customer_id=stripe_customer["id"],
                            )
                            messages.success(
                                self.request, "You have successfully payed for items"
                            )
                            return redirect("/")
                    except Exception as e:
                        return JsonResponse({f"Error": str(e)})
                except Exception as e:
                    return JsonResponse({f"Error": str(e)})
            except Exception as e:
                return JsonResponse({f"Error": str(e)})
        return JsonResponse(
            {"Error": "Invalid request method"}, status=HttpResponse.status_code
        )


@csrf_exempt
def stripe_webhook(request):
    event = None
    charge = {}
    payload = request.body
    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle the event
    if event["type"] == "charge.captured":
        charge = event["data"]["object"]
    elif event["type"] == "charge.expired":
        charge = event["data"]["object"]
    elif event["type"] == "charge.failed":
        charge = event["data"]["object"]
    elif event["type"] == "charge.pending":
        charge = event["data"]["object"]

    elif event["type"] == "charge.refunded":
        refund = event["data"]["object"]
        updating_refund_status(refund, request)
        return JsonResponse({"event": event, "refund": event["data"]["object"]})

    elif event["type"] == "charge.succeeded":
        charge = event["data"]["object"]
        user_id = charge["metadata"]["user_id"]
        cart_id = charge["metadata"]["cart_id"]
        charge_status(charge["id"], user_id, cart_id)
        return JsonResponse({"message": f"stripe created"})

    elif event["type"] == "charge.updated":
        charge = event["data"]["object"]

    elif event["type"] == "customer.created":
        customer = event["data"]["object"]
        return JsonResponse(
            {"message": f"stripe customer with id: {customer['id']} is created"}
        )

    elif event["type"] == "customer.deleted":
        customer = event["data"]["object"]
        return JsonResponse(
            {"message": f"stripe customer with id: {customer['id']} is deleted"}
        )

    elif event["type"] == "customer.updated":
        customer = event["data"]["object"]
    elif event["type"] == "issuing_card.created":
        issuing_card = event["data"]["object"]
    elif event["type"] == "issuing_card.updated":
        issuing_card = event["data"]["object"]
    elif event["type"] == "payment_method.attached":
        payment_method = event["data"]["object"]
    # ... handle other event types
    else:
        print("Unhandled event type {}".format(event["type"]))
    return JsonResponse(charge)


def charge_status(charge_id, user_id, cart_id):
    try:
        payment_object = Payment.objects.get(
            cart__id=cart_id, user__id=user_id, stripe_charge_id=charge_id
        )
        payment_object.payment_status = Payment.CHARGE_STATUS[0][0]
        payment_object.save()
        print(f"*********************{payment_object.payment_status}")

        print(f"payment_object______________{payment_object}")

    except Payment.DoesNotExist:
        return JsonResponse(
            {"error": "Payment object not found for the specified user and cart."}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)})


def updating_refund_status(refund, request):
    try:
        cartitem_id = refund["metadata"]["cartitem_id"]
        cart_item = CartItem.objects.get(id=cartitem_id)
        cart = cart_item.cart
        refund_object = Refund.objects.create(
            cart=cart,
            stripe_refund_id=refund["id"],
            refund_status=Refund.REFUND_CHOICES[0][0],
            cart_item_id=cartitem_id,
        )
        refund_object.save()
    except Exception as e:
        print(f"______________________{str(e)}")
        return JsonResponse({"error": str(e)})


class Charge_Refund(View):
    def get_user_from_cookie(self):
        user_id = self.request.session["user_id"]
        user = CustomUser.objects.get(id=user_id)
        return user

    def get_amount_refunded(self):
        cart_item = CartItem.objects.get(id=self.kwargs["id"])
        return cart_item.price

    def get_stripe_charge_id(self):
        cart = CartItem.objects.get(id=self.kwargs["id"]).cart
        payment = Payment.objects.get(cart=cart)
        return payment.stripe_charge_id

    def get(self, request, *args, **kwargs):
        charge_id = self.get_stripe_charge_id()
        try:
            charge = stripe.Charge.retrieve(charge_id)
            charge_modify = stripe.Charge.modify(
                charge_id, metadata={"cartitem_id": self.kwargs["id"]}
            )
            try:
                refund = stripe.Refund.create(
                    charge=charge_id,
                    amount=int(self.get_amount_refunded()),
                    metadata={
                        "user_id": self.get_user_from_cookie().id,
                        "cartitem_id": self.kwargs["id"],
                    },
                )
                messages.success(
                    request, f"Refund successful. Refund ID: {refund['id']}"
                )
                return JsonResponse({"success": True, "refund": refund})
            except stripe.error.StripeError as e:
                messages.error(request, f"Error refunding charge: {str(e)}")
                return JsonResponse({"success": False, "error": str(e)})
        except stripe.error.StripeError as e:
            messages.error(request, f"Error retrieving charge from Stripe: {str(e)}")
            return JsonResponse({"success": False, "error": str(e)})


class View_Orders(View):
    def get(self, request, **kwargs):
        user_id = self.request.session["user_id"]
        # get the cart for which user has confirmed Checkout
        carts = Cart.objects.filter(
            user__id=user_id, cart_payment__stripe_charge_id__isnull=False
        )
        print(f"^^^^^^^^^^^^^^^^^^{carts}")
        payment_object = Payment.objects.filter(user__id=user_id)
        if payment_object:
            payment = payment_object[0]
        else:
            payment = None
        context = {
            "carts": carts,
            "payment": payment,
        }
        return render(self.request, "view_orders.html", context=context)
