from django import forms
from django.contrib.auth.models import User
from . import models

def AvailableBooksOnly():
    books=models.Book.objects.all()
    print(books)
    for ib in books:
        Availability = models.Borrower.objects.filter(book=ib).filter(status="Issued")
        if Availability.exists():
            print(Availability)
            books = books.exclude(isbn=ib.isbn)
    print(books)
    return books


class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))




class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']



class StudentUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password','email']

class StudentExtraForm(forms.ModelForm):
    class Meta:
        model=models.StudentExtra
        fields=['enrollment','branch']
class BorrowForm(forms.ModelForm):
    class Meta:
        model=models.Borrower
        exclude=[]

class BookForm(forms.ModelForm):
    class Meta:
        model=models.Book
        fields=['name','isbn','author','category']

class IssuedBookForm(forms.Form):
    #to_field_name value will be stored when form is submitted.....__str__ method of book model will be shown there in html
    booksAvailable = AvailableBooksOnly()
    isbn2=forms.ModelChoiceField(queryset=booksAvailable,empty_label="Name and isbn",label='Name and Isbn')
    enrollment2=forms.ModelChoiceField(queryset=models.StudentExtra.objects.all(),empty_label="Name and enrollment",label='Name and enrollment')
