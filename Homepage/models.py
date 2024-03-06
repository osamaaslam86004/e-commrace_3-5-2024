from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from django_countries.fields import CountryField


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Create a UserProfile for the user
        UserProfile.objects.create(
            user=user,
            full_name="",
            age=18,
            gender="",
            phone_number="",
            city="",
            country="",
            postal_code="",
        )

        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ("CUSTOMER", "Customer"),
        ("SELLER", "Seller"),
        ("CUSTOMER REPRESENTATIVE", "Customer Service Representative"),
        ("MANAGER", "Manager"),
        ("ADMINISTRATOR", "Administrator"),
    )

    email = models.EmailField(
        verbose_name="email address", max_length=255, unique=True, blank=False
    )
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES)
    image = models.ImageField(
        upload_to="images/",
        blank=True,
        default="https://res.cloudinary.com/dh8vfw5u0/image/upload/v1702231959/rmpi4l8wsz4pdc6azeyr.ico",
    )
    user_google_id = models.IntegerField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    # do not use direct import strategy => circular imports error
    # direct import meaning => import at the top of any file
    # why circular imports?
    #  we are importing ProductCategory to Homepage.models and Customuser to i.models


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, name="user")
    full_name = models.CharField(max_length=50, blank=False)
    age = models.IntegerField(blank=False, default=18)
    gender = models.CharField(max_length=30, blank=False)
    phone_number = PhoneNumberField(null=False, blank=False, unique=False)
    city = models.CharField(max_length=100, blank=False)
    country = CountryField(
        multiple=False, blank_label="(select country)", blank=False, null="NZ"
    )
    postal_code = models.CharField(max_length=20, blank=False)
    shipping_address = models.CharField(max_length=1000, null=True, blank=False)


class CustomerProfile(models.Model):
    custumer_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, name="customer_profile", default=None
    )
    customuser_type_1 = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, name="customuser_type_1", default=None
    )
    shipping_address = models.CharField(
        max_length=255, blank=False, null=True, default=None
    )
    wishlist = models.IntegerField(blank=True, null=True, default=None)


class SellerProfile(models.Model):
    seller_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, name="seller_profile", default=None
    )
    customuser_type_2 = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, name="customuser_type_2", default=None
    )
    address = models.CharField(max_length=100, null=True, blank=False)


class CustomerServiceProfile(models.Model):
    csr_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, name="csr_profile", default=None
    )
    customuser_type_3 = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, name="customuser_type_3", default=None
    )
    department = models.CharField(max_length=50, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(blank=False, null=True)


class ManagerProfile(models.Model):
    manager_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, name="manager_profile", default=None
    )
    customuser_type_4 = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, name="customuser_type_4", default=None
    )
    team = models.CharField(max_length=50, null=True, blank=True)
    reports = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(blank=False, null=True)


class AdministratorProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="customuser_type_5",
        null=True,
    )
    admin_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, name="admin_profile", default=None
    )
    bio = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(blank=False, null=True)


class SocialAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    access_token = models.TextField(max_length=500)
    user_info = models.TextField(max_length=1000)
    token_created_at = models.DateTimeField(auto_now_add=True)
    code = models.TextField(max_length=500, null=True)
    refresh_token = models.TextField(max_length=500, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"
