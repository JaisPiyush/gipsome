from rest_framework.pagination import PageNumberPagination


class StandardResultSetPagination(PageNumberPagination):
    page_size = 12
    page_query_param = 'page_size'
    max_page_size = 120


