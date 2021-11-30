from django.contrib import admin
from .models import Book,StudentExtra, Borrower
# Register your models here.
class BookAdmin(admin.ModelAdmin):
    pass
admin.site.register(Book, BookAdmin)


class StudentExtraAdmin(admin.ModelAdmin):
    pass
admin.site.register(StudentExtra, StudentExtraAdmin)


class BorrowerAdmin(admin.ModelAdmin):
    pass
admin.site.register(Borrower, BorrowerAdmin)
