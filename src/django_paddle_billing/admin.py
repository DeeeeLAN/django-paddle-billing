import typing

from django.conf import settings
from django.contrib import admin
from django.db import models

from django_paddle_billing import settings as app_settings
from django_paddle_billing.models import Address, Business, Customer, Price, Product, Subscription, Transaction

# Check if unfold is in installed apps
if "unfold" in settings.INSTALLED_APPS:
    from unfold.admin import ModelAdmin, StackedInline, TabularInline
else:
    from django.contrib.admin import ModelAdmin, StackedInline, TabularInline


class AddressInline(StackedInline):
    model = Address
    extra = 1


class BusinessInline(StackedInline):
    model = Business
    extra = 1


class PriceInline(StackedInline):
    model = Price
    extra = 1


class ProductInline(TabularInline):
    model = Product.subscriptions.through
    extra = 1
    show_change_link = True


class CustomerInline(StackedInline):
    model = Customer
    extra = 1


class SubscriptionInline(StackedInline):
    model = Subscription
    extra = 1


class TransactionInline(TabularInline):
    model = Transaction
    extra = 1
    show_change_link = True


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ["id", "customer_email", "country_code", "postal_code", "status"]
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return app_settings.ADMIN_READONLY

    def customer_email(self, obj=None):
        if obj and obj.customer:
            return obj.customer.email
        return ""

    def postal_code(self, obj=None):
        if obj and obj.data:
            return obj.data.get("postal_code", "")
        return ""

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""


@admin.register(Business)
class BusinessAdmin(ModelAdmin):
    inlines = (SubscriptionInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        "name",
        "status",
        "created_at",
    ]
    search_fields = ["id", "name"]
    inlines = (PriceInline,)
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Price)
class PriceAdmin(ModelAdmin):
    list_display = [
        "name",
        "unit_price",
        "description",
        "status",
        "trial_period",
        "billing_cycle",
    ]
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def billing_cycle(self, obj=None):
        if obj and obj.data and obj.data.get("billing_cycle"):
            return f'{obj.data["billing_cycle"]["frequency"]} {obj.data["billing_cycle"]["interval"]}'
        return ""

    def description(self, obj=None):
        if obj and obj.data:
            return obj.data.get("description", "")

    def name(self, obj=None):
        if obj and obj.data:
            return obj.data.get("name", "")

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")

    def trial_period(self, obj=None):
        if obj and obj.data and obj.data.get("trial_period"):
            return f'{obj.data["trial_period"]["frequency"]} {obj.data["trial_period"]["interval"]}'
        return ""

    def unit_price(self, obj=None):
        if obj and obj.data and obj.data.get("unit_price"):
            return f'{int(obj.data["unit_price"]["amount"]) / 100} {obj.data["unit_price"]["currency_code"]}'
        return ""


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    inlines = (
        TransactionInline,
        ProductInline,
    )
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    exclude = ["products"]

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = [
        "email",
        "name",
        "status",
        "created_at",
    ]
    inlines = (
        AddressInline,
        BusinessInline,
        SubscriptionInline,
        TransactionInline,
    )
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ["customer_email", "payment_amount", "payment_method", "date_paid", "products", "status"]
    formfield_overrides: typing.ClassVar = {
        models.JSONField: {"widget": app_settings.ADMIN_JSON_EDITOR_WIDGET},
    }

    def has_change_permission(self, request, obj=None):
        return not app_settings.ADMIN_READONLY

    def customer_email(self, obj=None):
        if obj and obj.customer:
            return obj.customer.email
        return ""

    def payment_amount(self, obj=None):
        if obj and obj.data:
            try:
                return int(obj.data["details"]["totals"]["total"]) / 100
            except Exception:
                return ""
        return ""

    def payment_method(self, obj=None):
        if obj and obj.data:
            try:
                return (
                    f'{obj.data["payments"][0]["method_details"]["card"]["type"]} '
                    f'{obj.data["payments"][0]["method_details"]["card"]["last4"]}'
                )
            except Exception:
                return ""
        return ""

    def date_paid(self, obj=None):
        if obj and obj.data:
            try:
                return obj.data["payments"][0]["captured_at"]
            except Exception:
                return ""
        return ""

    def products(self, obj=None):
        if obj and obj.data:
            items = obj.data.get("items", [])
            # return items
            products = Product.objects.filter(id__in=[item["price"]["product_id"] for item in items])
            return ", ".join([product.name for product in products])
        return ""

    products.short_description = "Product(s)"

    def status(self, obj=None):
        if obj and obj.data:
            return obj.data.get("status", "")
        return ""
