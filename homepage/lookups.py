from django.db.models import TextField, Transform


# Casefold Нормализует регистр текста в SQL
@TextField.register_lookup
class Casefold(Transform):
    function = "unicode_casefold"
    lookup_name = "casefold"
    output_field = TextField()
