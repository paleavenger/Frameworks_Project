from django import forms

from .models import Membership, Team


# TeamFilterForm Принимает фильтры списка команд
class TeamFilterForm(forms.Form):
    ORDERING = {
        "name": ("name", "pk"),
        "project": ("project__title", "name", "pk"),
        "readiness": ("-readiness_percent", "name", "pk"),
    }

    q = forms.CharField(
        label="Название команды или проекта", required=False, max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    project = forms.TypedChoiceField(
        label="Проект", required=False, coerce=int, empty_value=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "Выберите проект из списка."},
    )
    status = forms.ChoiceField(
        label="Состояние команды", required=False,
        choices=(("", "Любое состояние"), *Team.Status.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "Выберите состояние из списка."},
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False,
        choices=(
            ("name", "По названию"),
            ("project", "По проекту"),
            ("readiness", "По готовности"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "Выберите порядок из списка."},
    )

    # __init__ Заполняет список проектов
    def __init__(self, *args, projects, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].choices = [("", "Все проекты"), *projects]


# MembershipForm Редактирует участие в команде
class MembershipForm(forms.ModelForm):
    # Meta Настраивает поля формы участия
    class Meta:
        model = Membership
        fields = ("student", "team", "role")
        labels = {"role": "Роль в команде"}
        widgets = {
            field: forms.Select(attrs={"class": "form-select"})
            for field in fields
        }
        error_messages = {
            "student": {
                "unique": "Студент уже состоит в команде.",
            },
        }

    # __init__ Настраивает выбор студента, команды и роли
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = (
            self.fields["student"].queryset.order_by("name", "pk")
        )
        self.fields["team"].queryset = (
            self.fields["team"].queryset.order_by("name", "pk")
        )
        self.fields["role"].queryset = (
            self.fields["role"].queryset.order_by("name", "pk")
        )
        if self.instance.pk:
            self.fields["student"].disabled = True
