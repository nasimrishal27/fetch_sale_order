# -*- coding: utf-8 -*-
{
    'name': "Fetch Sale Order: V17 - V18",
    'version': '1.0',
    'depends': ['base', 'sale'],
    'sequence': 2,
    'author': "Suni",
    'category': 'All',
    'description': """
    Property Management
    """,
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'wizard/fetch_sale_order_wizard_views.xml',
        'views/sale_order_menu_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}

