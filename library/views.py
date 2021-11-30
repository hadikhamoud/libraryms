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
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import token_generator
from django.shortcuts import redirect
from itertools import chain



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


#creates Admin account, to be deleted (script to be written for adding
#admins directly to db)
def adminsignup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()

            #groups to distinguish between admins and Student
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return HttpResponseRedirect('adminlogin')
    return render(request,'library/adminsignup.html',{'form':form})



#creates student account
def studentsignup_view(request):
    #form1 for user and form2 to add enrollment and branch
    form1=forms.StudentUserForm()
    form2=forms.StudentExtraForm()
    mydict={'form1':form1,'form2':form2}
    if request.method=='POST':
        form1=forms.StudentUserForm(request.POST)
        form2=forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user=form1.save()
            user.set_password(user.password)
            #deactivate account until verified by user
            user.is_active=False
            user.save()
            f2=form2.save(commit=False)
            f2.user=user
            user2=f2.save()
            #add to 'student group'
            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)
            #Process Of Sending the verification email(linked to VerificationEmail.views down):


            #security id
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            #domain to be displayed on the verification link
            domain = get_current_site(request).domain
            #create link containing the uid and a security token
            #this command is linked to a specific path in urls.py
            link = reverse('activate',kwargs={'uidb64':uidb64,'token':token_generator.make_token(user)})
            #final email to be sent
            activate_url = "http://"+domain+link
            #email content
            email_subject = 'Activate your account'
            email_body = 'Hi '+user.first_name+"\nPlease use this link to verify your account\n"+activate_url
            #use EmailMessage class to construct email object
            email = EmailMessage(
            email_subject,
            email_body,
            'noreplylibms@gmail.com',
            [user.email]
            )
            #use EmailMessage built in method send to send email
            email.send(fail_silently=False)

        return render(request,'library/PleaseVerify.html')
    return render(request,'library/studentsignup.html',context=mydict)



#checks if user is admin or not by searching for his object in the ADMIN group
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()

def afterlogin_view(request):
    #if admin show admin after login
    if is_admin(request.user):
        return render(request,'library/adminafterlogin.html')
    #else show student after log in
    else:
        #reminder function for books with one day left or no days:
        BooksComingUp = []
        #query to check the status of all the books that are issued by student
        BorrowedBooks = models.Borrower.objects.filter(student__user__id=request.user.id).filter(status="Issued")
        print(BorrowedBooks)
        for ib in BorrowedBooks:
            #iterate through books and check the return date and match it with today
            return_date_days = ib.return_date.date()
            d = date.today()-return_date_days
            d=d.days
            print(d)
            #if there is more than one day left, then remove from query since we don't need it
            if int(d)<-1:
                BorrowedBooks = BorrowedBooks.exclude(id=ib.id)
            #if some books remain in the query, then there are some books close to expiry
            #therefore, send a True flag to html frontend to show reminder link on mainpage
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
    #query that shows all books for admin
    books=models.Book.objects.filter(Active = True).order_by('category')
    return render(request,'library/viewbook.html',{'books':books})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def searchbooksadmin(request):
    if request.method == "POST":
        searched = request.POST['searched']
        Books = models.Book.objects.filter(name__contains = searched).filter(Active =True)
        try:
            Booksbyisbn = models.Book.objects.filter(isbn__contains = int(searched)).filter(Active =True)
            print(Booksbyisbn)
        except:
            Booksbyisbn = models.Book.objects.none()

        Books = list(chain(Books,Booksbyisbn))
        print("books",Books)
        return render(request, 'library/searchbooksadmin.html',{'books':Books})


def checkavailablebooks(books,studentID):

    #iterate through books and if you find a book that has been "Issued" by another student
    #remove the book from the query
    for ib in books:
        #Borrower removes the book if the student has it already or has already requested it
        Borrower = models.Borrower.objects.filter(book=ib).filter(student__user_id=studentID).filter(status="Pending")
        #Availability removes the book if anyone else has it issued
        Availability = models.Borrower.objects.filter(book=ib).filter(status="Issued")

        #exlude both from the main query
        if Borrower.exists():

            books = books.exclude(isbn=ib.isbn)
        if Availability.exists():
            books = books.exclude(isbn=ib.isbn)
    return books

#(could be enhanced)
@login_required(login_url='studentlogin')
def booksAvailable_view(request):
    #view to show the available books for student, first query all books
    tempbooks = models.Book.objects.filter(Active = True).order_by('category')
    books=checkavailablebooks(tempbooks,request.user.id)

    #get all the checkboxes that the student has submitted into id_list
    if request.method =="POST":
        id_list = request.POST.getlist("choices")
        print(id_list)
        #id list contains all the isbns of the books chosen
        for ib in id_list:
            #iterate through isbns and create Borrower objects with status "pending"
            obj = models.Borrower()
            SelectedBook=models.Book.objects.filter(isbn=ib)
            if SelectedBook.exists():
                #assign book of Borrower object
                obj.book=SelectedBook[0]

            tempstudent=models.StudentExtra.objects.filter(user_id=request.user.id)
            if tempstudent.exists():
                #assign student of Borrower object
                obj.student=tempstudent[0]
            #status "pending" means that the book has been requested and not yet approved
            obj.status="Pending"
            obj.save()
            print(obj.status)
            #exlude the book that has been ordered now
            books = books.exclude(id=obj.book.id)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def todaycheckouthistory(request):

    today = datetime.today()
    ReturnersToday = models.Borrower.objects.filter(status = "Returned").filter(return_date__date = datetime(today.year,today.month,today.day))
    print(today)
    print(ReturnersToday)
    return render(request, "library/todaycheckouthistory.html",{'li':ReturnersToday})


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

#to be fixed
def issuebook_view(request):
    form=forms.IssuedBookForm()
    issuedBefore = []
    if request.method=='POST':
        #now this form have data from html
        form=forms.IssuedBookForm(request.POST)
        if form.is_valid():
            obj=models.Borrower()
            username = form.cleaned_data['username2']
            isbn = form.cleaned_data['isbn2']
            selectedStudent = models.StudentExtra.objects.filter(user__username = username)
            selectedBook = models.Book.objects.filter(isbn = isbn)
            if selectedStudent.exists() and selectedBook.exists():
                obj.student=selectedStudent[0]
                obj.book=selectedBook[0]
                obj.status="Issued"

                temp2 = models.Borrower.objects.filter(book = obj.book).filter(status="Pending").delete()
                temp3 = models.Borrower.objects.filter(book = obj.book).filter(status="Issued")
                print(temp3)
                if temp3.exists():
                    issuedBefore.append(True)
                    return render(request,'library/bookissued.html',{"issuedBefore":issuedBefore})
                obj.save()


                return render(request,'library/bookissued.html',{"issuedBefore":issuedBefore})
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


#used to view the book requests by student on the admin side
#could be enhanced
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewissuedbook_view(request):
    #deletes all the duplicate requests
    deleteDuplicateBorrowers()
    #checkss all the "pending" requests
    li=models.Borrower.objects.filter(status="Pending").distinct()
    if request.method =="POST":
        #gets the choices from frontend in the form of a list from input checkboxes
        id_list = request.POST.getlist("choices")
        print(id_list)
        for ib in id_list:
           #get the suitable borrower object
           Selected=models.Borrower.objects.filter(id = ib)
           if Selected.exists():
               #change the status to "Issued"
               print(Selected)
               Selected=Selected[0]
               Selected.status = "Issued"
               Selected.save()
               #delete all the requests for this book from other users since he has gotten it
               #(could be modified if we add multiple copies)
               models.Borrower.objects.filter(book__isbn=Selected.book.isbn).exclude(student__user__username = Selected.student.user.username).delete()
               print(Selected.issue_date)
               print(Selected.status)
    return render(request,'library/viewissuedbook.html',{'li':li})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def searchbookrequests(request):
    deleteDuplicateBorrowers()

    if request.method == "POST":

            try:
                searched = request.POST['searched']
                print(searched)
                BorrowerBystudent = models.Borrower.objects.filter(student__user__username__contains = searched).filter(status="Pending")
                BorrowerBybookname = models.Borrower.objects.filter(book__name__contains = searched).filter(book__Active=True).filter(status="Pending")
                try:
                    Borrowersbyisbn =  models.Borrower.objects.filter(book__isbn__contains = int(searched)).filter(book__Active=True).filter(status="Pending")
                    print(Borrowersbyisbn)
                except:
                    Borrowersbyisbn = models.Book.objects.none()
                Requests = set(chain(BorrowerBystudent,BorrowerBybookname,Borrowersbyisbn))
                print(Requests)
            except:
                Requests = models.Borrower.objects.filter(status = "Pending")




            #return render(request, 'library/searchbookrequests.html',{'li':Requests})



            id_list = request.POST.getlist("choices")
            print(id_list)
            for ib in id_list:
               #get the suitable borrower object
               Selected=models.Borrower.objects.filter(id = ib)
               if Selected.exists():
                   #change the status to "Issued"
                   print(Selected)
                   Selected=Selected[0]
                   Selected.status = "Issued"
                   Selected.save()
                   #delete all the requests for this book from other users since he has gotten it
                   #(could be modified if we add multiple copies)
                   models.Borrower.objects.filter(book__isbn=Selected.book.isbn).exclude(student__user__username = Selected.student.user.username).delete()
                   print(Selected.issue_date)
                   print(Selected.status)

            return render(request, 'library/searchbookrequests.html',{'li':Requests})
    return render(request, 'library/searchbookrequests.html')


@login_required(login_url='studentlogin')
def searchbooksavailable(request):
    if request.method == "POST":
            try:
                searched = request.POST['searched']
                Books = models.Book.objects.filter(name__contains = searched).filter(Active =True)
                print('contains',Books)
                Books = checkavailablebooks(Books,request.user.id)
                try:
                    Booksbyisbn = models.Book.objects.filter(isbn__contains = int(searched)).filter(Active =True)
                    Booksbyisbn = checkavailablebooks(Booksbyisbn,request.user.id)
                    print("byisbn",Booksbyisbn)
                except:
                    Booksbyisbn = models.Book.objects.none()

                Books = set(chain(Books,Booksbyisbn))
                print("chain",Books)
            except:
                Books = models.Book.objects.filter(Active = True)
                Books = checkavailablebooks(Books,request.user.id)

            id_list = request.POST.getlist("choices")

            #id list contains all the isbns of the books chosen
            for ib in id_list:
                #iterate through isbns and create Borrower objects with status "pending"
                obj = models.Borrower()
                SelectedBook=models.Book.objects.filter(isbn=ib)
                if SelectedBook.exists():
                    #assign book of Borrower object
                    obj.book=SelectedBook[0]

                tempstudent=models.StudentExtra.objects.filter(user_id=request.user.id)
                if tempstudent.exists():
                    #assign student of Borrower object
                    obj.student=tempstudent[0]
                #status "pending" means that the book has been requested and not yet approved
                obj.status="Pending"
                obj.save()

                #exlude the book that has been ordered now
                Books = Books.exclude(id=obj.book.id)

    #return to html the query of books
            return render(request, 'library/searchbooksavailable.html',{'books':Books})
    return render(request,'library/searchbooksavailable.html')





#views all the student

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def viewstudent_view(request):
    #query all the students and return
    students=models.StudentExtra.objects.all()
    return render(request,'library/viewstudent.html',{'students':students})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def searchstudent(request):
    if request.method == "POST":
        searched = request.POST['searched']
        Students = models.StudentExtra.objects.filter(user__username__contains = searched)
        return render(request,'library/searchstudent.html',{'students':Students})
    return render(request,'library/searchstudent.html')




#check all the books that are coming up
#could be enhanced (books could be replaced by ib)
@login_required(login_url='studentlogin')
def ComingUp(request):
    #query student
    student=models.StudentExtra.objects.filter(user_id=request.user.id)
    #query all his current books (borrower objects that are issued)
    issuedbook=models.Borrower.objects.filter(student=student[0]).filter(status="Issued")
    #prepare two lists to send to frontend
    li1=[]
    li2=[]
    for ib in issuedbook:
        #for each of his current books:
        #get the Borrower object
        print(ib)
        books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
        #check the return date
        return_date_days = ib.return_date.date()
        d = date.today()-return_date_days
        d=d.days
        #if it is not coming up in 1 day or already expired, then forget it
        if int(d)<-1:
             continue
        if len(books)>0:
            #prepare to send info to frontend
            t=(ib.student.user.username,ib.student.enrollment,ib.student.branch,ib.book.name,ib.book.author)
            li1.append(t)
            issdate=str(ib.issue_date.day)+'-'+str(ib.issue_date.month)+'-'+str(ib.issue_date.year)
            expdate=str(ib.return_date.day)+'-'+str(ib.return_date.month)+'-'+str(ib.return_date.year)
            #expdate=0
        #fine calculation
            print(ib.return_date)
            timeTemp = date.today() - ib.return_date.date()
            if int(timeTemp.days)>0:
                ib.Fine = CalculateFine(ib.return_date.date())
                ib.save()

            fine = "$" + str(ib.Fine)
            borrowerID = ib.id
            t=(issdate,expdate,fine,borrowerID)
            li2.append(t)

    return render(request,'library/viewissuedbookbystudent.html',{'li1':li1,'li2':li2})


#view all the issued books for the student
#same process as before but without the 1 day left or less condition
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
            t=(ib.student.user.username,ib.student.enrollment,ib.student.branch,ib.book.name,ib.book.author)
            li1.append(t)
            issdate=str(ib.issue_date.day)+'-'+str(ib.issue_date.month)+'-'+str(ib.issue_date.year)
            expdate=str(ib.return_date.day)+'-'+str(ib.return_date.month)+'-'+str(ib.return_date.year)
            #expdate=0
        #fine calculation
            timeTemp = date.today() - ib.return_date.date()
            if int(timeTemp.days)>0:
                ib.Fine = CalculateFine(ib.return_date.date())
                ib.save()

            fine = "$" + str(ib.Fine)
            borrowerID = ib.id

            t=(issdate,expdate,fine,borrowerID)
            li2.append(t)

    return render(request,'library/viewissuedbookbystudent.html',{'li1':li1,'li2':li2})

@login_required(login_url='studentlogin')
def userhistory(request):
    student=models.StudentExtra.objects.filter(user_id=request.user.id)
    issuedbook=models.Borrower.objects.filter(student=student[0]).exclude(status="Pending").order_by('status')
    li1=[]
    li2=[]
    for ib in issuedbook:
        t=(ib.student.user.username,ib.student.enrollment,ib.student.branch,ib.book.name,ib.book.author)
        li1.append(t)
        issdate=str(ib.issue_date.day)+'-'+str(ib.issue_date.month)+'-'+str(ib.issue_date.year)
        expdate=str(ib.return_date.day)+'-'+str(ib.return_date.month)+'-'+str(ib.return_date.year)
        print(ib.return_date)
        timeTemp = date.today() - ib.return_date.date()
        if int(timeTemp.days)>0:
            ib.Fine = CalculateFine(ib.return_date.date())
            ib.save()

        fine = "$" + str(ib.Fine)
        borrowerID = ib.id
        Status = ib.status
        t=(issdate,expdate,fine,borrowerID,Status)

        li2.append(t)
    return render(request,'library/userhistory.html',{'li1':li1,'li2':li2})








#gives admin a list of all the users that have books close to deadline
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def CloseToDeadline(request):
    #querys  all the issued books that are close to deadline
    Borrowers = models.Borrower.objects.filter(status="Issued").order_by('return_date')
    #same process as viewissuedbooksbystudent and ComingUp
    li1=[]
    li2=[]
    for ib in Borrowers:
            print(ib)
            books=models.Borrower.objects.filter(student=ib.student,book=ib.book)
            print(books)

            if len(books)>0:
                t=(ib.student.user.username,ib.student.enrollment,ib.student.branch,ib.book.name,ib.book.author)
                li1.append(t)
                issdate=str(ib.issue_date.day)+'-'+str(ib.issue_date.month)+'-'+str(ib.issue_date.year)
                expdate=str(ib.return_date.day)+'-'+str(ib.return_date.month)+'-'+str(ib.return_date.year)
                #expdate=0
            #fine calculation
                print(ib.return_date)
                timeTemp = date.today() - ib.return_date.date()
                if int(timeTemp.days)>0:
                    ib.Fine = CalculateFine(ib.return_date.date())
                    ib.save()

                fine = "$" + str(ib.Fine)
                borrowerID = ib.id
                t=(issdate,expdate,fine,borrowerID)
                li2.append(t)
    if request.method =="POST":
            id_list = request.POST.getlist("choices")
            print(id_list)
                #id list contains all the isbns of the books chosen
            for ib in id_list:
                    #iterate through isbns and create Borrower objects with status "pending"
                  #set variables for username and id
                 #get the suitable borrower object
                Selected=models.Borrower.objects.filter(id=ib).filter(status="Issued")
                if Selected.exists():
                     #change the status to "Issued"
                    print(Selected)
                    Selected=Selected[0]
                    Selected.status = "Returned"
                    Selected.return_date = datetime.today()
                    Selected.Fine = 0
                    Selected.save()
            return redirect('CloseToDeadline')

    return render(request, 'library/CloseToDeadline.html', {'li1':li1,'li2':li2})


#view the book log of every student
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def userbooklog(request,username):
    #take from the previous session page the user name of the user
    student=models.StudentExtra.objects.filter(user__username=username)
    #get all his issued books
    issuedbook=models.Borrower.objects.filter(student=student[0]).exclude(status="Pending").order_by("status")
    li1=[]
    li2=[]
    #also same process as before in viewissuedbooksbystudent
    if not issuedbook.exists():
        return render(request, 'library/userbooklog.html', {'li1':li1,'li2':li2})

    for ib in issuedbook:

        books=models.Borrower.objects.filter(student=ib.student,book=ib.book)


        if len(books)>0:
            t=(ib.student.user.username,ib.student.enrollment,ib.student.branch,ib.book.name,ib.book.author)
            li1.append(t)
            issdate=str(ib.issue_date.day)+'-'+str(ib.issue_date.month)+'-'+str(ib.issue_date.year)
            expdate=str(ib.return_date.day)+'-'+str(ib.return_date.month)+'-'+str(ib.return_date.year)


            timeTemp = date.today() - ib.return_date.date()
            if int(timeTemp.days)>0:
                ib.Fine = CalculateFine(ib.return_date.date())
                ib.save()

            fine = "$" + str(ib.Fine)
            BorrowerID = ib.id
            Status = ib.status
            t=(issdate,expdate,fine,BorrowerID,Status)
            li2.append(t)
    if request.method =="POST":
        id_list = request.POST.getlist("choices")

        #id list contains all the isbns of the books chosen
        for ib in id_list:
            #iterate through isbns and create Borrower objects with status "pending"
          #set variables for username and id
         #get the suitable borrower object
            Selected=models.Borrower.objects.filter(id=ib).filter(status="Issued")
            if Selected.exists():
             #change the status to "Issued"

                Selected=Selected[0]
                Selected.status = "Returned"
                Selected.return_date = datetime.today()
                Selected.Fine = 0
                Selected.save()
        return HttpResponseRedirect(username)




    return render(request, 'library/userbooklog.html', {'li1':li1,'li2':li2})


#student can renew books
@login_required(login_url='studentlogin')
def RenewBook(request,borrowerID):
    #borrowerID is sent with each Borrower object in the
    print(borrowerID,type(borrowerID))
    response =[]
    #get the borrower object
    BorrowedBook = models.Borrower.objects.get(id=borrowerID)
    if request.method=='POST':
        #dumb way to distinguish navbar
        #(to be changed if time allows)
        navbar=[]
        if is_admin(request.user):
            navbar.append(True)

        if not BorrowedBook.Renewed:
            #renew the book if not renewed before and send True flag to alert
            #front end that the book has been renewed
            BorrowedBook.return_date += timedelta(days = 30)
            BorrowedBook.Renewed = True
            BorrowedBook.save()
            response.append(True)
        #else if response is empty, tell frontend that the book has already been renewed
        return render(request,'library/renewed.html',{'response': response,'navbar': navbar})
    return render(request,'library/RenewBook.html',{'li': BorrowedBook})








#modify book information
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def modifybook(request,isbn):
    #get isbn from previous page in same session
    Book = models.Book.objects.filter(isbn=isbn).filter(Active = True)
    #fill the form initially with the old information
    form=forms.BookForm(initial={"name":Book[0].name,"isbn":Book[0].isbn,"author":Book[0].author,"category":Book[0].category})
    if request.method=='POST':
        #now this form have data from html
        form=forms.BookForm(request.POST)
        print(form)
        if form.is_valid():
            #modify information and send form
            tempBook = form.save()
            #update book object with new infromation
            Book.update(name=tempBook.name,isbn=tempBook.isbn,author=tempBook.author,category=tempBook.category)
            #delete the temp book form
            tempBook.delete()
            return redirect('viewbook')

    return render(request, 'library/modifybook.html',{'form':form})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def deletebook(request,isbn):
    #check all the active books
    Book = models.Book.objects.filter(isbn=isbn).filter(Active = True)
    print(Book)
    if request.method=='POST':
        #once you want to delete the book
        Selected = Book[0]
        #Sets the active as false which means it is hidden
        #we're doing this to preserve the user history borrower objects
        Selected.Active = False
        Selected.save()
        #delete all the requests and the issures for this book
        BorrowersOfSelected = models.Borrower.objects.filter(book = Selected).exclude(status = "Returned").delete()
        print(Selected.Active,"Post")
        return render(request,'library/deleted.html')
    return render(request, 'library/deletebook.html',{'li':Book})






def aboutus_view(request):
    return render(request,'library/aboutus.html')

#send an email for contact us view
def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, EMAIL_HOST_USER, ['noreplylibms@gmail.com'], fail_silently = False)
            return render(request, 'library/contactussuccess.html')
    return render(request, 'library/contactus.html', {'form':sub})

#takes the link received in email and redirects the user to a login page
#changes his status to activate his account
def VerificationEmail(request,uidb64,token):
    id = force_text(urlsafe_base64_decode(uidb64))
    user=models.StudentExtra.objects.get(user__pk=id)
    print(user)
    if user.user.is_active:
        #if already active dont do anything just redirect him
        return redirect('studentlogin')
    user.user.is_active=True
    user.user.save()
    return redirect('studentlogin')


#function to check for duplicate requests of book by student
def ifrequestedbefore(isbn,stid):
    Borrower = models.Borrower.objects.filter(book__isbn=isbn).filter(student__user__username=stid)
    if Borrower.exists():
        return True
    return False


#used for admin to not view any duplicate Borrower objects since the
#student can go back to the page and resubmit the form
#this duplicate handling system could be used everywhere
def deleteDuplicateBorrowers():
    #order books by issue date in a query
    BorrowerObjects = models.Borrower.objects.filter(status="Pending").order_by('issue_date')
    #check all the books from bottom to top
    for rows in BorrowerObjects.reverse():
        #if we find a matching one when iterating from bottom to top
        temp = models.Borrower.objects.filter(student=rows.student).filter(book=rows.book).filter(status="Pending")
        #remove the bottom one since we want the first instance of the Borrower object
        if temp.count()>1:
            rows.delete()


#function that substracts the dates and calculate fines at 1$ per day
#capped at 15$
def CalculateFine(returndate):
    days=date.today() - returndate
    d=days
    fine=0
    d=d.days
    if int(d)>0:
        fine=d*1
    if fine>15:
        return 15
    return fine
