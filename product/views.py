from django.shortcuts import get_object_or_404
from django.db.models import Avg

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination

from .serializers import ProductSerializer, ProductImagesSerializer

from .models import Product, ProductImages, Review

from .filters import ProductsFilter

# Create your views here.


@api_view(['GET'])
def get_products(request):
    """
    Get a list of all products.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - A Response object containing a dictionary with a key "products" and the serialized data of all products.
    """

    products = Product.objects.all().order_by('id')

    # Defining the filterset
    filterset = ProductsFilter(request.GET, queryset=products).qs

    # Defining the pagination params
    resultsPerPage = 2
    paginator = PageNumberPagination()
    paginator.page_size = resultsPerPage
    queryset = paginator.paginate_queryset(filterset, request)

    # Specifying the count of items returned
    count = paginator.page.paginator.num_pages
    totalCount = filterset.count()
    # Defining the serializer
    serializer = ProductSerializer(queryset, many=True)

    return Response(
        {"Total Products": totalCount, "Number of pages": count,
            "products": serializer.data}
    )


@api_view(['GET'])
def get_product(request, pk):
    """
    Get a product by its ID.

    Parameters:
    - request: The request object.
    - pk: The ID of the product.

    Returns:
    - A Response object containing the serialized product data.
    """

    product = get_object_or_404(Product, id=pk)

    serializer = ProductSerializer(product, many=False)

    return Response({"product": serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def new_product(request):
    """
    Create a product.

    Parameters:
    - request: The request object.

    Returns:
    - A Response object containing the serialized product data.
    """
    data = request.data

    serializer = ProductSerializer(data=data)

    # Checks whether the serializer is valid as per the requirements
    if serializer.is_valid():
        product = Product.objects.create(**data, user=request.user)
        res = ProductSerializer(product, many=False)
        return Response({"product": res.data})
    else:
        return Response(serializer.errors)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def upload_product_images(request):
    """
    Uploads product images to the server.

    Parameters:
    - request: The request object containing the images to be uploaded.

    Returns:
    - Response object containing the serialized data of the uploaded images.
    """
    data = request.data
    files = request.FILES.getlist('images')

    # creates a new object and saves it to database
    images = []
    for f in files:
      # passes the product id and image as arguments when creating a new image
        image = ProductImages.objects.create(
            product=Product(data['product']), image=f)
        images.append(image)
    serializer = ProductImagesSerializer(images, many=True)

    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_product(request, pk):
    """
    Update a product with the given ID.

    Parameters:
        request (Request): The HTTP request object.
        pk (int): The ID of the product to update.

    Returns:
        Response: The HTTP response containing the updated product data.
    """
    product = get_object_or_404(Product, id=pk)

    # if product.user is not request.user:
    #     return Response({"error": "You are not authorized to update this product."}, status=status.HTTP_403_FORBIDDEN)

    # Update product fields
    product.name = request.data.get('name', product.name)
    product.description = request.data.get('description', product.description)
    product.price = request.data.get('price', product.price)
    product.brand = request.data.get('brand', product.brand)
    product.category = request.data.get('category', product.category)
    product.ratings = request.data.get('ratings', product.ratings)
    product.stock = request.data.get('stock', product.stock)

    product.save()

    serializer = ProductSerializer(product)

    return Response({"product": serializer.data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_product(request, pk):
    """
    Delete a product.

    Parameters:
        request (HttpRequest): The request object.
        pk (int): The primary key of the product to be deleted.

    Returns:
        Response: The response message indicating the status of the deletion.
    """
    product = get_object_or_404(Product, id=pk)

    if product.user is not request.user:
        return Response({"error": "You are not authorized to update this product."}, status=status.HTTP_403_FORBIDDEN)

    args = {'product': pk}
    images = ProductImages.objects.filter(**args)

    for i in images:
        i.delete()

    product.delete()

    return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, pk):
    user = request.user
    product = get_object_or_404(Product, id=pk)
    data = request.data

    review = product.reviews.filter(user=user)

    if data['rating'] <= 0 or data['rating'] > 5:
        return Response({"error": "Rating must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

    # update a review if it already exists to prevent multiple reviews of the same product by one user
    elif review.exists():
        new_review = {
            'rating': data['rating'],
            'comment': data["comment"]
        }
        review.update(**new_review)

        # Retrieves the average rating for a product by aggregating the ratings from its related reviews.
        rating = product.reviews.aggregate(
            avg_ratings=Avg('rating'))['avg_ratings']
        product.ratings = rating
        product.save()

        return Response({"message": "You have updated your review for this product."}, status=status.HTTP_200_OK)
    else:
        Review.objects.create(
            user=user,
            product=product,
            rating=data['rating'],
            comment=data['comment']
        )
        # Retrieves the average rating for a product by aggregating the ratings from its related reviews.
        rating = product.reviews.aggregate(
            avg_ratings=Avg('rating'))['avg_ratings']
        product.ratings = rating
        product.save()
        return Response({"message": "Review created successfully"}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, pk):
    user = request.user
    product = get_object_or_404(Product, id=pk)

    review = product.reviews.filter(user=user)

    if review.exists():
        review.delete()

        rating = product.reviews.aggregate(
            avg_ratings=Avg('rating'))['avg_ratings']

        if rating is None:
            rating = 0

        product.ratings = rating
        product.save()

        return Response({"message": "Review deleted successfully"}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)
