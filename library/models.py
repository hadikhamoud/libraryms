from django.db import models
from django.contrib.auth.models import User
from datetime import datetime,timedelta,timezone




class StudentExtra(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    enrollment = models.CharField(max_length=40)
    branch = models.CharField(max_length=40)
    #used in issue book
    def __str__(self):
        return self.user.first_name+'['+str(self.enrollment)+']'
    @property
    def get_name(self):
        return self.user.first_name
    @property
    def getuserid(self):
        return self.user.id

def get_expiry():
    return datetime.today() - timedelta(days=7)




# + timedelta(days=30)

class Borrower(models.Model):
    student=models.ForeignKey('StudentExtra', on_delete=models.CASCADE,null=True)
    book = models.ForeignKey('Book', on_delete=models.CASCADE,null=True)
    issue_date = models.DateTimeField(auto_now=True,null=True)
    return_date = models.DateTimeField(default=get_expiry())
    status = models.CharField(max_length=40,null=True)
    Renewed = models.BooleanField(default=False)
    Fine = models.PositiveIntegerField(default = 0)
    Fined = models.PositiveIntegerField(default = 0)



    def __str__(self):
        return str(self.student.user)+" borrowed "+str(self.book)

    def dayMonthYearIssue(self):
        return self.issue_date.strftime("%d-%m-%Y")
    def dayMonthYearReturn(self):
        return self.return_date.strftime("%d-%m-%Y")
    def getreturnday(self):
        return self.return_date




class Book(models.Model):
    catchoice= [
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('comics', 'Comics'),
        ('biography', 'Biographie'),
        ('history', 'History'),
        ]
    name=models.CharField(max_length=30)
    isbn=models.PositiveIntegerField(unique=True)
    author=models.CharField(max_length=40)
    category=models.CharField(max_length=30,choices=catchoice,default='education')
    Active=models.BooleanField(default = True)
    def __str__(self):
        return str(self.name)+"["+str(self.isbn)+']'
