from django.core.paginator import Paginator

MAX_POSTS = 10


def pages(post_list):
    return Paginator(post_list, MAX_POSTS)
