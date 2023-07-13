from django.urls import path


from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('my-profile/', views.get_user, name='current_user'),
    path('my-profile/update/', views.update_user, name='update_user'),

]
