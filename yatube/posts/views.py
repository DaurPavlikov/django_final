from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import pages

CACHE_DELAY = 20


@cache_page(CACHE_DELAY, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group')
    page_number = request.GET.get('page')
    page_obj = pages(post_list).get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.select_related(
        'author'
    ).filter(
        group=group
    )
    page_number = request.GET.get('page')
    page_obj = pages(post_list).get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user_posts = Post.objects.select_related(
        'group'
    ).filter(
        author=author
    )
    count_posts = user_posts.count()
    page_number = request.GET.get('page')
    page_obj = pages(user_posts).get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user
    ).filter(
        author=author
    ).exists()
    context = {
        'author': author,
        'following': following,
        'page_obj': page_obj,
        'count': count_posts,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post.pk).select_related('author')
    comment_form = CommentForm(request.POST or None)
    count_posts = (
        Post.objects.select_related(
            'group'
        ).filter(
            author=post.author
        ).count()
    )
    context = {
        'post': post,
        'count': count_posts,
        'comments': comments,
        'form': comment_form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    username = request.user.username
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.user.username != post.author.username:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id,)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    no_subscriptions = not Follow.objects.filter(user=request.user).exists()
    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related(
        'author', 'group'
    )
    page_number = request.GET.get('page')
    page_obj = pages(post_list).get_page(page_number)
    context = {
        'no_subscriptions': no_subscriptions,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    subscriber = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    user_not_subscribed = not Follow.objects.filter(
        user=request.user
    ).filter(
        author=author
    ).exists()
    if request.user.username != author.username and user_not_subscribed:
        Follow.objects.create(user=subscriber, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    subscriber = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=subscriber
    ).filter(
        author=author
    ).delete()
    return redirect('posts:profile', username=author.username)
