from rest_framework import serializers
from django.utils import timezone

from .models import Order, OrderItem


class ReadableDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return value.strftime("%Z %d-%m-%Y %I:%M %p")


class OrderItemsSerializer(serializers.ModelSerializer):
    createdAt = ReadableDateTimeField(read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):

    createdAt = ReadableDateTimeField(read_only=True)
    orderItems = serializers.SerializerMethodField(
        method_name='get_order_Items', read_only=True)
    address = serializers.SerializerMethodField(
        method_name='get_address', read_only=True)
    ordered_by = serializers.SerializerMethodField(
        method_name='get_user_email', read_only=True)

    class Meta:
        model = Order
        # fields = '__all__'
        fields = ('id', 'orderItems', 'address', 'phone_no',
                  'total_amount', 'payment_status', 'status', 'payment_mode', 'ordered_by', 'createdAt')

    def get_order_Items(self, obj):
        order_items = obj.orderitems.all()
        serializer = OrderItemsSerializer(order_items, many=True)
        return serializer.data

    def get_user_email(self, obj):
        return obj.user.email

    def get_address(self, obj):
        return f"{obj.street}, {obj.city}, {obj.state}, {obj.country}, {obj.zip_code}"
