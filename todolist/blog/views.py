from django.shortcuts import render, redirect
from .models import Post, Comment, Like, Select
import datetime
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth.decorators import login_required

from todolist.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME
import boto3
from boto3.session import Session
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
# Create your views here.
def home(request):
    posts = Post.objects.all().order_by('deadline')
    return render(request, 'home.html', {'posts' : posts})

def signup(request):
    if (request.method == 'POST'):
        found_user = User.objects.filter(username=request.POST['username'])
        if (len(found_user) > 0):
            error = 'username이 이미 존재합니다'
            return render(request, 'registration/signup.html', {'error': error})

        new_user = User.objects.create_user(
            username = request.POST['username'],
            password = request.POST['password']
        )
        auth.login(
            request,
            new_user,
            backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')

    return render(request, 'registration/signup.html')

def login(request):
    if (request.method == 'POST'):
        found_user = auth.authenticate(
            username = request.POST['username'],
            password = request.POST['password']
        )
        if (found_user is None):
            error = '아이디 또는 비밀번호가 틀렸습니다'
            return render(request, 'registration/login.html', {'error': error })

        auth.login(
            request, 
            found_user,
            backend='django.contrib.auth.backends.ModelBackend'
        )
        return redirect(request.GET.get('next', '/'))
    return render(request, 'registration/login.html')

def logout(request):
    auth.logout(request)
    return redirect('home')

@login_required(login_url='/registration/login')
def new(request):
    if request.method == 'POST':
        file_to_upload = request.FILES.get('img')
        print(file_to_upload)
        session = Session(
            aws_access_key_id= AWS_ACCESS_KEY_ID,
            aws_secret_access_key= AWS_SECRET_ACCESS_KEY,
            region_name= AWS_S3_REGION_NAME
        )
        s3 = session.resource('s3')
        now = datetime.now().strftime('%Y%H%M%S')
        img_object = s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(
            Key = str(request.user.pk)+'/'+now+file_to_upload.name,
            Body = file_to_upload
        )
        s3_url = 'https://connie-bucket.s3.ap-northeast-2.amazonaws.com/'
        new_post = Post.objects.create(
            title = request.POST['title'],
            content = request.POST['content'],
            deadline = request.POST['deadline'],
            author = request.user,
            img = s3_url +str(request.user.pk)+'/' + now + file_to_upload.name
        )
        return redirect('detail', new_post.pk)
    return render(request, 'new.html')

def detail(request, post_pk):
    post = Post.objects.get(pk=post_pk)

    if request.method == "POST":
        Comment.objects.create(
            post = post,
            content = request.POST['content'],
            author = request.user
            )
        return redirect('detail', post_pk)

    return render(request, 'detail.html', {'post': post})

def delete_comment(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    comment.delete()
    return redirect('detail', post_pk)

def edit(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.method == 'POST':
        Post.objects.filter(pk=post_pk).update(
            title = request.POST['title'],
            content = request.POST['content'],
            deadline = request.POST['deadline']
        )
        return redirect('detail', post_pk)
    return render(request, 'edit.html',)

def delete(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    post.delete()
    return redirect('home')

@csrf_exempt
def like(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        post_pk = request_body['post_pk']

        existing_like = Like.objects.filter(
            post = Post.objects.get(pk=post_pk),
            user = request.user
        )

        if existing_like.count() > 0:
            existing_like.delete()

        else:
            Like.objects.create(
                post = Post.objects.get(pk=post_pk),
                user = request.user
            )

        post_likes = Like.objects.filter(
            post = Post.objects.get(pk=post_pk)
        )

        likeCheck = Like.objects.filter(
            post = Post.objects.get(pk=post_pk),
            user = request.user
        )
        response = {
            'like_count' : post_likes.count(),
            "likeCheck" : likeCheck.count()
        }

        return HttpResponse(json.dumps(response))

@csrf_exempt
def select(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        post_pk = request_body['post_pk']

        existing_select = Select.objects.filter(
            post = Post.objects.get(pk=post_pk),
            user = request.user
        )

        if existing_select.count() > 0:
            existing_select.delete()

        else:
            Select.objects.create(
                post = Post.objects.get(pk=post_pk),
                user = request.user
            )
        post_select = Select.objects.filter(
            post = Post.objects.get(pk=post_pk)
        )

        selectCheck = Select.objects.filter(
            post = Post.objects.get(pk=post_pk),
            user = request.user
        )
        response = {
            'select_count': post_select.count(),
            'selectCheck': selectCheck.count()
        }
        
        return HttpResponse(json.dumps(response))


def mypage(request):
    posts = Post.objects.all()
    likes = Like.objects.filter(
        user = request.user 
    )
    selects = Select.objects.filter(
        user = request.user
    )
    return render(request, 'mypage.html', {'posts': posts, 'likes': likes, 'selects': selects})