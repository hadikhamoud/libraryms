from django.shortcuts import render
from django.http import HttpResponseRedirect
from . import forms,models
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.contrib import auth
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime, timedelta, date

from django.core.mail import send_mail
from librarymanagement.settings import EMAIL_HOST_USER
from datetime import datetime, timezone
from django.contrib.auth import get_user_model



def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/index.html')

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/studentclick.html')

#for showing signup/login button for teacher
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'library/adminclick.html')



def adminsignup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()


            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request,'library/adminsignup.html',{'form':form})


def ifrequestedbefore(isbn,stid):
    Borrower = models.Borrower.objects.filter(book__isbn=isbn).filter(student__user__username=stid)
    if Borrower.exists():
        return True
    return False

def studentsignup_view(request):
    form1=forms.StudentUserForm()
    form2=forms.StudentExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST)
        form2=forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            user.save()
            f2=form2.save(commit=False)
            f2.user=user
            user2=f2.save()
            print(user)
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            print(my_student_group[0])
            my_student_group[0].user_set.add(user)
            print(my_student_group[0])

        return HttpResponseRedirect('studentlogin')
    return render(request,'library/studentsignup.html',context=mydict)




def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()

def afterlogin_view(request):
    if is_admin(request.user):
        return render(request,'library/adminafterlogin.html')
    else:
        BooksComingUp = []
        BorrowedBooks = models.Borrower.objects.filter(student__user__id=request.user.id).filter(status="Issued")
        print(BorrowedBooks)
        for ib in BorrowedBooks:
            return_date_days = ib.return_date.date()
            d = date.today()-return_date_days
            d=d.days
            print(d)
            if int(d)<-1:
                BorrowedBooks = BorrowedBooks.exclude(id=ib.id)
        if BorrowedBooks.exists():
            BooksComingUp.append(True)
        print(BorrowedBooks)
        return render(request,'library/studentafterlogin.html',{"ComingUp": BooksComingUp})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def addbook_view(request):
    #now it is empty book form for sending to html
    form=forms.BookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.BookForm(request.POST)
        if form.is_valid():
            user=form.save()
            return render(request,'library/bookadded.html')
    return render(request,'library/addbook.html',{'form':form})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewbook_view(request):
    books=models.Book.objects.all()
    return render(request,'library/viewbook.html',{'books':books})

@login_required(login_url='studentlogin')
def booksAvailable_view(request):
    books=models.Book.objects.all()
    for ib in books:
        Borrower = models.Borrower.objects.filter(book=ib).filter(student__user_id=request.user.id)
        Availability = models.Borrower.objects.filter(book=ib).filter(status="Issued")
        print(Borrower)
        if Borrower.exists():
            print(True)
            books = books.exclude(isbn=ib.isbn)
        if Availability.exists():
            books = books.exclude(isbn=ib.isbn)


    if request.method =="POST":
        id_list = request.POST.getlist("choices")
        print(id_list)

        for ib in id_list:
            obj = models.Borrower()
            SelectedBook=models.Book.objects.filter(isbn=ib)
            if SelectedBook.exists():
                obj.book=SelectedBook[0]

            tempstudent=models.StudentExtra.objects.filter(user_id=request.user.id)
            if tempstudent.exists():
                obj.student=tempstudent[0]

            obj.status="Pending"
            obj.save()
            print(obj.status)
            books = books.exclude(id=obj.book.id)


        return HttpResponseRedirect('BooksAvailable')
    return render(request,'library/BooksAvailable.html',{'books':books})

'''
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def issuebook_view(request):
    form=forms.IssuedBookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.IssuedBookForm(request.POST)
        if form.is_valid():
            obj=models.IssuedBook()
            obj.enrollment=request.POST.get('enrollment2')
            obj.isbn=request.POST.get('isbn2')
            obj.save()
            return render(request,'library/bookissued.html')
    return render(request,'library/issuebook.html',{'form':form})
'''
def issuebook_view(request):
    form=forms.IssuedBookForm()
    if request.method=='POST':
        #now this form have data from html
        form=forms.IssuedBookForm(request.POST)
        if form.is_valid():
            obj=models.Borrower()
            student = form.cleaned_data['enrollment2']
            book = form.cleaned_data['isbn2']
            #student = models.StudentExtra.objects.get(pk=form.enrollment2)
            #book = models.Book.objects.get(isbn = 'isbn2')
            obj.student=student
            obj.book=book
            obj.status="Issued"
            obj.save()
            print(obj.status,obj.student,obj.book)
            return render(request,'library/bookissued.html')
    return render(request,'library/issuebook.html',{'form':form})


'''
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    issuedbooks=models.IssuedBook.objects.all()
    li=[]
    for ib in issuedbooks:
        issdate=str(ib.issuedate.day)+'-'+str(ib.issuedate.month)+'-'+str(ib.issuedate.year)
        expdate=str(ib.expirydate.day)+'-'+str(ib.expirydate.month)+'-'+str(ib.expirydate.year)
        #fine calculation
        days=(date.today()-ib.issuedate)
        print(date.today())
        d=days.days
        fine=0
        if d>15:
            day=d-15
            fine=day*10

        i=0
        books=list(models.Book.objects.filter(isbn=ib.isbn))
        students=list(models.StudentExtra.objects.filter(enrollment=ib.enrollment))
        for l in books:
            t=(students[i].get_name,students[i].enrollment,books[i].name,books[i].author,issdate,expdate,fine)
            i=i+1
            li.append(t)

    return render(request,'library/viewissuedbook.html',{'li':li})

'''
def deleteDuplicateBorrowers():
    BorrowerObjects = models.Borrower.objects.all().order_by('issue_date')
    for rows in BorrowerObjects.reverse():
        temp = models.Borrower.objects.filter(student=rows.student,book=rows.book)
        if temp.count()>1:
            rows.delete()

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    deleteDuplicateBorrowers()
    li=models.Borrower.objects.filter(status="Pending").distinct()
    if request.method =="POST":
        id_list = request.POST.getlist("choices")
        print(id_list)
        for ib in id_list:
           ib=ib.split("///")
           if ib[1]=='':
            ib[1]=0
           username = ib[0]
           isbn=int(ib[1])
           print(isbn,username)
           Selected=models.Borrower.objects.filter(student__user__username = username).filter(book__isbn=isbn)
           if Selected.exists():
               print(Selected)
               Selected=Selected[0]
               Selected.status = "Issued"
               Selected.save()
               models.Borrower.objects.filter(book__isbn=isbn).exclude(student__user__username = username).delete()
               print(Selected.issue_date)
               print(Selected.status)
    return render(request,'library/viewissuedbook.html',{'li':li})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    students=models.StudentExtra.objects.all()
    return render(request,'library/viewstudent.html',{'students':students})

@login_required(login_url='studentlogin')
def ComingUp(request):
    student=models.StudentExtra.objects.filter(user_id=request.user.id)
    issuedbook=models.Borrower.objects.filter(student=student[0]).filter(status="Issued")
    li1=[]
    li2=[]
    for ib in issuedbook:
        print(ib)
        books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
        return_date_days = books[0].return_date.date()
        d = date.today()-return_date_days
        d=d.days
        if int(d)<-1:
             continue
        if len(books)>0:
            t=(books[0].student.user.username,books[0].student.enrollment,books[0].student.branch,books[0].book.name,books[0].book.author)
            li1.append(t)
            issdate=str(books[0].issue_date.day)+'-'+str(books[0].issue_date.month)+'-'+str(books[0].issue_date.year)
            expdate=str(books[0].return_date.day)+'-'+str(books[0].return_date.month)+'-'+str(books[0].return_date.year)
            #expdate=0
        #fine calculation
            print(books[0].return_date)
            fine = CalculateFine(books[0].return_date.date())
            fine = "$" + str(fine)
            borrowerID = books[0].id
            t=(issdate,expdate,fine,borrowerID)
            li2.append(t)

    return render(request,'library/viewissuedbookbystudent.html',{'li1':li1,'li2':li2})


@login_required(login_url='studentlogin')
def viewissuedbookbystudent(request):
    student=models.StudentExtra.objects.filter(user_id=request.user.id)
    issuedbook=models.Borrower.objects.filter(student=student[0]).filter(status="Issued")
    li1=[]
    li2=[]
    for ib in issuedbook:
        print(ib)
        books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
        print(books)

        if len(books)>0:
            t=(books[0].student.user.username,books[0].student.enrollment,books[0].student.branch,books[0].book.name,books[0].book.author)
            li1.append(t)
            issdate=str(books[0].issue_date.day)+'-'+str(books[0].issue_date.month)+'-'+str(books[0].issue_date.year)
            expdate=str(books[0].return_date.day)+'-'+str(books[0].return_date.month)+'-'+str(books[0].return_date.year)
            #expdate=0
        #fine calculation
            print(books[0].return_date)
            fine = CalculateFine(books[0].return_date.date())
            fine = "$" + str(fine)
            borrowerID = books[0].id
            t=(issdate,expdate,fine,borrowerID)
            li2.append(t)

    return render(request,'library/viewissuedbookbystudent.html',{'li1':li1,'li2':li2})

def CalculateFine(returndate):
    days=date.today() - returndate
    d=days

    print(type(d))
    fine=0
    d=d.days
    print(type(d))
    if int(d)>0:
        fine=d*1
    return fine

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def CloseToDeadline(request):
    Borrowers = models.Borrower.objects.filter(status="Issued").order_by('return_date')

    li1=[]
    li2=[]
    for ib in Borrowers:
            print(ib)
            books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
            print(books)

            if len(books)>0:
                t=(books[0].student.user.username,books[0].student.enrollment,books[0].student.branch,books[0].book.name,books[0].book.author)
                li1.append(t)
                issdate=str(books[0].issue_date.day)+'-'+str(books[0].issue_date.month)+'-'+str(books[0].issue_date.year)
                expdate=str(books[0].return_date.day)+'-'+str(books[0].return_date.month)+'-'+str(books[0].return_date.year)
                #expdate=0
            #fine calculation
                print(books[0].return_date)
                fine = CalculateFine(books[0].return_date.date())
                fine = "$" + str(fine)
                borrowerID = books[0].id
                t=(issdate,expdate,fine,borrowerID)
                li2.append(t)

    return render(request, 'library/CloseToDeadline.html', {'li1':li1,'li2':li2})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def userbooklog(request,username):
    student=models.StudentExtra.objects.filter(user__username=username)
    issuedbook=models.Borrower.objects.filter(student=student[0]).filter(status="Issued")
    li1=[]
    li2=[]
    for ib in issuedbook:
        print(ib)
        books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
        print(books)

        if len(books)>0:
            t=(books[0].student.user.username,books[0].student.enrollment,books[0].student.branch,books[0].book.name,books[0].book.author)
            li1.append(t)
            issdate=str(books[0].issue_date.day)+'-'+str(books[0].issue_date.month)+'-'+str(books[0].issue_date.year)
            expdate=str(books[0].return_date.day)+'-'+str(books[0].return_date.month)+'-'+str(books[0].return_date.year)


            fine = CalculateFine(books[0].return_date.date())
            fine = "$" + str(fine)
            BorrowerID = books[0].id
            t=(issdate,expdate,fine,BorrowerID)
            li2.append(t)
    return render(request, 'library/userbooklog.html', {'li1':li1,'li2':li2})

@login_required(login_url='studentlogin')
def RenewBook(request,borrowerID):
    print(borrowerID,type(borrowerID))
    response =[]
    BorrowedBook = models.Borrower.objects.get(id=borrowerID)
    if request.method=='POST':
        #dumb way to distinguish navbar
        #(to be changed if time allows)
        navbar=[]
        if is_admin(request.user):
            navbar.append(True)

        if not BorrowedBook.Renewed:
            BorrowedBook.return_date += timedelta(days = 30)
            BorrowedBook.Renewed = True
            BorrowedBook.save()
            response.append(True)
        return render(request,'library/renewed.html',{'response': response,'navbar': navbar})
    return render(request,'library/RenewBook.html',{'li': BorrowedBook})






@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def modifybook(request,isbn):
    Book = models.Book.objects.filter(isbn=isbn)
    form=forms.BookForm(initial={"name":Book[0].name,"isbn":Book[0].isbn,"author":Book[0].author,"category":Book[0].category})
    if request.method=='POST':
        #now this form have data from html
        form=forms.BookForm(request.POST)
        print(form)
        if form.is_valid():
            tempBook = form.save()
            Book.update(name=tempBook.name,isbn=tempBook.isbn,author=tempBook.author,category=tempBook.category)
            tempBook.delete()
            return render(request,'library/bookadded.html')

    return render(request, 'library/modifybook.html',{'form':form})

def aboutus_view(request):
    return render(request,'library/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, EMAIL_HOST_USER, ['wapka1503@gmail.com'], fail_silently = False)
            return render(request, 'library/contactussuccess.html')
    return render(request, 'library/contactus.html', {'form':sub})
