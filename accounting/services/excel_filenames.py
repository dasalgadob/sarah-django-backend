"""Shared filename builder for the Excel export endpoints.

Produces names like 'Productos#Acme SAS#2026-06-25.xlsx'.
"""

import re

from django.utils import timezone


def build_dated_filename(prefix, company):
    today = timezone.localdate().isoformat()
    if not company:
        return f'{prefix}#{today}.xlsx'
    company_name = re.sub(r'[\r\n"]', '', str(company)).strip()
    return f'{prefix}#{company_name}#{today}.xlsx'
