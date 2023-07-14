from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .filters import OrdersFilter

from .serializers import OrderSerializer

from .models import *

# Create your views here.


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_orders(request):
    orders = Order.objects.all()

    filterset = OrdersFilter(
        request.GET, queryset=orders.order_by('id')).qs

    count = filterset.count()
    # Pagination
    resPerPage = 2
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage

    page = paginator.paginate_queryset(filterset, request)

    serializer = OrderSerializer(page, many=True)

    return Response({
        "Total Orders": count,
        "Results per page": resPerPage,
        "Orders": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    orders = get_object_or_404(Order, id=pk)

    serializer = OrderSerializer(orders, many=False)

    return Response({"Order": serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_order(request):
    user = request.user
    data = request.data

    order_items = data['orderItems']

    if order_items and len(order_items) == 0:
        return Response({"error": "No items have been ordered."}, status=status.HTTP_400_BAD_REQUEST)

    else:

        # Create order
        total_amount = 0
        order = Order.objects.create(
            user=user,
            street=data['street'],
            city=data['city'],
            state=data['state'],
            country=data['country'],
            zip_code=data['zip_code'],
            phone_no=data['phone_no'],
            total_amount=total_amount
        )

        # Creates order items & sets order to order items
        for ord in order_items:
            product = Product.objects.get(id=ord['product'])

            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                price=product.price,
                quantity=ord['quantity']
            )

            # Update product stock
            product.stock -= item.quantity
            product.save()

            # Calculate total amount
            total_amount += item.price * item.quantity

        # Update total amount
        order.total_amount = total_amount
        order.save()

        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def process_order(request, pk):
    order = get_object_or_404(Order, id=pk)

    order.status = request.data['status']
    order.save()

    serializer = OrderSerializer(order, many=False)

    return Response({"Updated Order": serializer.data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_order(request, pk):
    order = get_object_or_404(Order, id=pk)

    order.delete()
    return Response({"Your order has been deleted"}, status=status.HTTP_200_OK)
