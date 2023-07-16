from datetime import datetime, timedelta
from os import link

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from .serializers import SignUpSerializer, UserSerializer
from utils.helpers import get_current_host
# Create your views here.


@api_view(["POST"])
def register(request):
    """
    Registers a new user.

    Parameters:
        - request: The HTTP request object containing user registration data.

    Returns:
        - If the user is registered successfully:
            - A JSON response with a message: "User created successfully" and status code 201 (HTTP_201_CREATED).
        - If the user already exists:
            - A JSON response with an error message: "User already exists" and status code 400 (HTTP_400_BAD_REQUEST).
        - If the user data is invalid:
            - A JSON response with the validation errors.
    """
    data = request.data

    user = SignUpSerializer(data=data)
    if user.is_valid(raise_exception=True):
        if not User.objects.filter(username=data["email"]).exists():
            # Extract the characters before '@'
            usernameSplit = data['email'].split('@')[0]

            user = User.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                username=usernameSplit,
                password=make_password(data['password']),
            )
            # user = User.objects.create(**data)
            user.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(user.errors)


@api_view(['GET'])
# The permission classes decorator ensures that a token is passed in the header for the request to be carried out/ endpoint to be accessed.
@permission_classes([IsAuthenticated])
def get_user(request):
    """
    Retrieves the details of the current authenticated user.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        Response: The serialized user data.
    """
    user = UserSerializer(request.user)

    return Response(user.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user
    data = request.data

    # Update product fields
    usernameSplit = data['email'].split('@')[0]
    data['username'] = usernameSplit

    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.username = request.data.get('username', user.username)

    if data['password'] != "":
        user.password = make_password(data['password'])

    user.save()

    serializer = UserSerializer(user, many=False)

    return Response(serializer.data)


@api_view(['POST'])
def forgot_password(request):
    data = request.data

    user = get_object_or_404(User, email=data['email'])

    # Generates random string token and expiry date
    token = get_random_string(length=40)
    expire_date = now() + timedelta(minutes=30)

    # Saves the token and expiry date to the profile model
    user.profile.reset_password_token = token
    user.profile.reset_password_expire = expire_date
    user.profile.save()

    current_host = get_current_host(request)

    link = "{current_host}/api/reset-password/{token}".format(
        current_host=current_host,
        token=token
    )
    email_body = f"Your password reset link is: {link}".format(link=link)

    send_mail(
        subject="Password reset",
        message=email_body,
        from_email="noreply@eshop.com",
        recipient_list=[data['email']]
    )

    return Response({"details": "Password reset link sent to {email}".format(email=data['email'])}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request, token):
    data = request.data

    user = get_object_or_404(User, profile__reset_password_token=token)

    # tzinfo is used to avoid timezone issues
    reset_password_expire = user.profile.reset_password_expire

    if reset_password_expire < now():
        return Response({"error": "Reset password link has expired"}, status=status.HTTP_400_BAD_REQUEST)

    if data['password'] != data['confirmPassword']:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    user.password = make_password(data['password'])
    user.profile.reset_password_token = ""
    user.profile.reset_password_expire = None

    user.profile.save()
    user.save()

    return Response({"details": "Password reset successfully"}, status=status.HTTP_200_OK)
