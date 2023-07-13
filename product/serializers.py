from rest_framework import serializers
from django.utils import timezone

from .models import Product, ProductImages, Review


class ReadableDateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        value = timezone.localtime(value)
        return value.strftime("%Z %d-%m-%Y %I:%M %p")
        # return value.strftime("%Y-%m-%d %H:%M:%S %Z")


class ReviewSerializer(serializers.ModelSerializer):
    createdAt = ReadableDateTimeField(read_only=True)

    class Meta:
        model = Review
        fields = "__all__"


class ProductImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImages
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    createdAt = ReadableDateTimeField(read_only=True)
    # Showing images in the list of products
    images = ProductImagesSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField(
        method_name='get_reviews', read_only=True)

    class Meta:
        model = Product
        fields = ('id', "name", "description", "price", "brand",
                  "category", "ratings", "stock", "images", "reviews", "createdAt", 'user')
        extra_kwargs = {
            "name": {"required": True, "allow_blank": False},
            "brand": {"required": True, "allow_blank": False},
            "description": {"required": True, "allow_blank": False},
        }

    def get_reviews(self, instance):
        """
        Retrieves all the reviews associated with the given product (instance).

        Parameters:
            instance (object): The instance for which to retrieve the reviews.

        Returns:
            list: A list of serialized review data.
        """
        reviews = instance.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return serializer.data
