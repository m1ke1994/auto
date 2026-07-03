from datetime import timedelta

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

from subscriptions.models import Subscription, SubscriptionPayment, SubscriptionPlan, SubscriptionSettings, TelegramLink


class SubscriptionAdminForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") == Subscription.Status.ACTIVE and not cleaned_data.get("plan"):
            self.add_error("plan", "Для активной подписки необходимо выбрать тариф.")
        return cleaned_data


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "old_price",
        "discount_percent",
        "period_months",
        "is_active",
        "recommended",
        "sort_order",
    )
    list_filter = ("period_months", "is_active", "recommended", "currency")
    list_editable = ("is_active", "recommended", "sort_order")
    search_fields = ("name", "slug", "short_description")
    ordering = ("period_months", "sort_order", "price")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    form = SubscriptionAdminForm
    list_display = ("id", "client", "plan", "status", "paid_until", "admin_override", "updated_at")
    list_filter = ("status", "plan", "admin_override")
    search_fields = ("client__name", "client__owner__email", "plan__name", "plan__slug")
    list_editable = ("plan", "status", "paid_until", "admin_override")
    list_select_related = ("client", "plan")
    fieldsets = (
        ("Клиент и тариф", {"fields": ("client", "plan")}),
        ("Доступ", {"fields": ("status", "paid_until", "is_trial", "admin_override", "auto_renew")}),
    )
    actions = ("activate_subscription",)

    @admin.action(description="Активировать подписку")
    def activate_subscription(self, request, queryset):
        now = timezone.now()
        updated = 0
        skipped = 0
        for subscription in queryset.select_related("plan"):
            if not subscription.plan_id:
                skipped += 1
                continue
            duration_days = subscription.plan.duration_days
            subscription.status = Subscription.Status.ACTIVE
            subscription.paid_until = now + timedelta(days=duration_days)
            subscription.is_trial = False
            subscription.save(update_fields=["status", "paid_until", "is_trial", "updated_at"])
            updated += 1

        self.message_user(request, f"Активировано подписок: {updated}")
        if skipped:
            self.message_user(
                request,
                f"Пропущено без выбранного тарифа: {skipped}",
                level=messages.WARNING,
            )


@admin.register(TelegramLink)
class TelegramLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_user_id", "client", "updated_at")
    search_fields = ("telegram_user_id", "client__name", "client__owner__email")


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "plan", "yookassa_payment_id", "status", "activated_at", "updated_at")
    list_filter = ("status", "plan")
    search_fields = ("yookassa_payment_id", "client__name", "client__owner__email")


@admin.register(SubscriptionSettings)
class SubscriptionSettingsAdmin(admin.ModelAdmin):
    list_display = ("demo_enabled", "demo_days")

    def has_add_permission(self, request):
        if SubscriptionSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        settings_obj = SubscriptionSettings.get_solo()
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[settings_obj.pk],
        )
        return HttpResponseRedirect(url)
