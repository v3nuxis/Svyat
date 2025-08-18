from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_activation_email(email: str, activation_link: str):
    subject = 'User Activation'
    message = f'Please, activate your account: {activation_link}'
    from_email = settings.DEFAULT_FROM_EMAIL or 'admin@catering.com'
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list)
        print(f"Activation email sent to {email}")
    except Exception as e:
        print(f"Failed to send activation email to {email}: {str(e)}")
        raise