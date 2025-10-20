from django.core.mail import send_mail
from django.conf import settings


def send_registration_confirmation(user):
    subject = 'Добро пожаловать в Ordering App!'
    message = f'Здравствуйте, {user.username}! Ваша регистрация прошла успешно.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    send_mail(subject, message, email_from, recipient_list)


def send_order_confirmation(order):
    subject = f'Ваш заказ #{order.id} подтвержден!'
    message = (f'Здравствуйте, {order.user.username}!\n\n'
               f'Ваш заказ №{order.id} на сумму {order.total_amount} был успешно подтвержден. '
               f'Адрес доставки: {order.shipping_address}')
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [order.user.email]

    send_mail(subject, message, email_from, recipient_list)