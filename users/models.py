# users/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class UserManager(models.Manager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.password = ''
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

    # Add this method so Django authentication works
    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    # Django authentication expects these
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name
