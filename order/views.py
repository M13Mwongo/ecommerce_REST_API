import os
import stripe

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser


from .filters import OrdersFilter

from .serializers import OrderSerializer

from .models import *

from utils.helpers import get_current_host

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


stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    DOMAIN = get_current_host(request)

    user = request.user
    data = request.data

    order_items = data['orderItems']

    shipping_details = {
        'street': data['street'],
        'city': data['city'],
        'state': data['state'],
        'country': data['country'],
        'zip_code': data['zip_code'],
        'phone_no': data['phone_no'],
        'user': user.id
    }

    checkout_order_items = []
    for item in order_items:
        # adds item to checkout_order_items array
        checkout_order_items.append({
            # required by stripeAPI
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item['name'],
                    'images': [item['image_url']],
                    'metadata': {
                        'product_id': item['product']
                    }
                },
                # pass unit_amount in cents as that is how it is processed by stripe
                'unit_amount': item['price'] * 100,
            },
            'quantity': item['quantity']
        }
        )

    session = stripe.checkout.Session.create(
        line_items=checkout_order_items,
        mode='payment',
        success_url=DOMAIN + '/success/',
        # optional params
        cancel_url=DOMAIN + '/cancel/',
        payment_method_types=['card'],
        metadata=shipping_details,
        customer_email=user.email,
    )

    return Response({'session': session}, status=status.HTTP_200_OK)


@api_view(["POST"])
def stripe_webhook(request):
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    payload = request.body
    signature_header = request.META["HTTP_STRIPE_SIGNATURE"]
    event = None

    # event = stripe.Webhook.construct_event(
    #     payload, signature_header, webhook_secret)

    # print("EVENT:", event.type)

    # return Response({'event\n': event}, status=status.HTTP_200_OK)

    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, webhook_secret)
        print("Webhook event created")
    except ValueError as e:
        return Response({'error': "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.error.SignatureVerificationError as e:
        return Response({'error': "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)

    if event['type'] == "checkout.session.completed":
        session = event['data']['object']
        print("Checkout session created:\n", session)

        line_items = stripe.checkout.Session.list_line_items(session['id'])
        price = session['amount_total'] / 100

        order = Order.objects.create(
            user=User(session.metadata.user),
            street=session.metadata.street,
            city=session.metadata.city,
            state=session.metadata.state,
            country=session.metadata.country,
            zip_code=session.metadata.zip_code,
            phone_no=session.metadata.phone_no,
            total_amount=price,
            payment_mode="CARD",
            payment_status="PAID"
        )

        for item in line_items['data']:
            print('item:', item)

            line_product = stripe.Product.retrieve(item.price.product)
            product_id = line_product.metadata.product_id

            product = Product.objects.get(id=product_id)
            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity=item.quantity,
                price=item.price.unit_amount / 100,
            )
        product.stock -= item.quantity
        product.save()

        return Response({'details': 'Payment Successful'}, status=status.HTTP_200_OK)
