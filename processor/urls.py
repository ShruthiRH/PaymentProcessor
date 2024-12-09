from django.urls import path
from .views import initiate_payment

urlpatterns = [
    path('initiate-payment/',initiate_payment, name='checking')
]