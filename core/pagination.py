"""
Custom pagination classes for the Sarah Project API.

Provides standardized pagination response format across all endpoints.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
import math


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that returns:
    - 'data' instead of 'results'
    - Includes 'total_pages' in response
    - Provides current page info
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """Override response format to use 'data' instead of 'results' and add total_pages."""
        total_pages = math.ceil(self.page.paginator.count / self.page_size) if self.page_size else 1
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', total_pages),
            ('current_page', self.page.number),
            ('page_size', self.page_size),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)  # Changed from 'results' to 'data'
        ]))

    def get_paginated_response_schema(self, schema):
        """Override schema for OpenAPI documentation."""
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': 'Total number of items'
                },
                'total_pages': {
                    'type': 'integer',
                    'description': 'Total number of pages'
                },
                'current_page': {
                    'type': 'integer',
                    'description': 'Current page number'
                },
                'page_size': {
                    'type': 'integer',
                    'description': 'Number of items per page'
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri',
                    'description': 'URL to next page'
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'format': 'uri', 
                    'description': 'URL to previous page'
                },
                'data': schema  # Changed from 'results' to 'data'
            }
        }


class LargeResultsSetPagination(CustomPageNumberPagination):
    """Pagination class for endpoints with potentially large datasets."""
    page_size = 50
    max_page_size = 200


class SmallResultsSetPagination(CustomPageNumberPagination):
    """Pagination class for endpoints with smaller datasets."""
    page_size = 10
    max_page_size = 50