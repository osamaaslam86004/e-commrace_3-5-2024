from django import forms
from book_.models import BookAuthorName, BookFormat, Rating, Review
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.widgets import CKEditorWidget


class BookAuthorNameForm(forms.ModelForm):
    class Meta:
        model = BookAuthorName
        fields = ["author_name", "book_name", "about_author", "language"]
        labels = {
            "author_name": "Author Name",
            "book_name": "Book Name",
            "about_author": "About Author",
            "language": "Language",
        }
        widgets = {
            "author_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter the name of the author",
                }
            ),
            "book_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter the name of the book",
                }
            ),
            "about_author": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter previous work of author",
                }
            ),
            "language": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter the language"}
            ),
        }


class BookFormatForm(forms.ModelForm):
    is_active = forms.TypedChoiceField(
        coerce=lambda x: x == "True",
        choices=[(True, "Active"), (False, "In Active")],
        widget=forms.RadioSelect(),
        required=False,
        initial=True,
        label="Choose the status of the book",
    )

    class Meta:
        model = BookFormat
        fields = [
            "format",
            "is_active",
            "image_1",
            "image_2",
            "image_3",
            "is_new_available",
            "is_used_available",
            "publisher_name",
            "edition",
            "length",
            "narrator",
            "price",
            "publishing_date",
        ]

        labels = {
            "book_author_name": "Author Name",
            "format": "Format",
            "is_new_available": "Is New Available",
            "is_used_available": "Is Used Available",
            "publisher_name": "Publisher Name",
            "edition": "Edition",
            "length": "Length",
            "narrator": "Narrator",
            "price": "Price",
            "publishing_date": "Publishing Date",
        }

        widgets = {
            "format": forms.Select(attrs={"class": "form-control"}),
            "is_new_available": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "enter the number of available new books",
                }
            ),
            "is_used_available": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "enter the number of available used books",
                }
            ),
            "publisher_name": forms.TextInput(attrs={"class": "form-control"}),
            "edition": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Rebound version / 2012"}
            ),
            "length": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "enter the number of pages of a book",
                }
            ),
            "narrator": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "placeholder": "Price must be between 1 and 999999.99.",
                }
            ),
            "publishing_date": forms.DateInput(attrs={"format": "%Y-%m-%d"}),
        }


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = [
            "rating",
        ]
        labels = {
            "rating": "Rating (1-5)",
        }


class ReviewForm(forms.ModelForm):
    rating = RatingForm()

    class Meta:
        model = Review
        fields = ["image_1", "image_2", "title", "content"]
        exclude = ["book_format"]
        labels = {
            "title": "Title",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter the review title"}
            ),
        }


class CustomBookFormatFilterForm(forms.Form):
    FORMAT_CHOICES = [
        ("", "Any Format"),
        ("AUDIO_CD", "Audio CD"),
        ("SPIRAL_BOUND", "Spiral Bound"),
        ("PAPER_BACK", "Paperback"),
        ("HARDCOVER", "Hardcover"),
    ]

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    book_name = forms.CharField(
        max_length=100,
        required=False,
        label="Book Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    author_name = forms.CharField(
        max_length=50,
        required=False,
        label="Author Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    price_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Minimum Price",
        validators=[MinValueValidator(1)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    price_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Maximum Price",
        validators=[MaxValueValidator(999999.99)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    is_new_available = forms.BooleanField(
        required=False,
        label="Is New Available",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    is_used_available = forms.BooleanField(
        required=False,
        label="Is Used Available",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    publisher_name = forms.CharField(
        max_length=100,
        required=False,
        label="Publisher Name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    rating_min = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        required=False,
        label="Minimum Rating",
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    rating_max = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        required=False,
        label="Maximum Rating",
        validators=[MaxValueValidator(5)],
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
