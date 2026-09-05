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
