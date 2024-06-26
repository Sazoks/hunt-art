from rest_framework.pagination import PageNumberPagination


class ChatPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class ChatMessagePagination(PageNumberPagination):
    page_size = 50
    page_query_param = "page_size"
    max_page_size = 200
