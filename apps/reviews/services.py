import pandas as pd
from django.http import HttpResponse


def export_reviews_to_csv(queryset) -> HttpResponse:
    data = [
        {
            'id': rev.id,
            'location_id': rev.location_id,
            'location_name': rev.location.name if rev.location else '',
            'author': rev.author.username if rev.author else '',
            'rating': rev.rating,
            'text': rev.text,
            'likes_count': getattr(rev, 'likes_count', 0),
            'dislikes_count': getattr(rev, 'dislikes_count', 0),
            'created_at': rev.created_at.isoformat() if rev.created_at else '',
        }
        for rev in queryset
    ]
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reviews.csv"'
    return response


def export_reviews_to_json(queryset) -> HttpResponse:
    data = [
        {
            'id': rev.id,
            'location_id': rev.location_id,
            'location_name': rev.location.name if rev.location else '',
            'author': rev.author.username if rev.author else '',
            'rating': rev.rating,
            'text': rev.text,
            'likes_count': getattr(rev, 'likes_count', 0),
            'dislikes_count': getattr(rev, 'dislikes_count', 0),
            'created_at': rev.created_at.isoformat() if rev.created_at else '',
        }
        for rev in queryset
    ]
    df = pd.DataFrame(data)
    json_data = df.to_json(orient='records', indent=2, force_ascii=False)
    response = HttpResponse(json_data, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reviews.json"'
    return response


def notify_author_and_subscribers_on_new_review(review) -> None:
    from django.conf import settings
    from django.core.mail import send_mail

    location = review.location
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@locations.local')
    author = location.author

    if author and author.email and author.id != review.author_id:
        subject = f'New review for your location "{location.name}"'
        message = (
            f'Hi {author.username},\n\n'
            f'User "{review.author.username}" left a new review for your location "{location.name}".\n'
            f'Rating: {review.rating}/5\n'
            f'Comment: {review.text}\n'
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[author.email],
            fail_silently=True,
        )

    subscriptions = (
        location.subscriptions
        .select_related('user')
        .exclude(user_id=review.author_id)
    )
    if author:
        subscriptions = subscriptions.exclude(user_id=author.id)

    for sub in subscriptions:
        if sub.user and sub.user.email:
            subject = f'New review for subscribed location "{location.name}"'
            message = (
                f'Hi {sub.user.username},\n\n'
                f'A new review has been posted on subscribed location "{location.name}".\n'
                f'Reviewer: {review.author.username}\n'
                f'Rating: {review.rating}/5\n'
                f'Comment: {review.text}\n'
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[sub.user.email],
                fail_silently=True,
            )
