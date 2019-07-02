
{
    'name': 'a2NSoft Essentials',
    'version': '1.0',
    'author': 'Mani Shankar',
    'category': 'Productivity',
    'description': """
        This module helps to do avoid quick creation of the products, customers, vendors, analytical accounts 
    """,

    'summary': 'This module helps to avoid Human Mistakes',
    'depends': ['base', 'sale'],

    'data': [
		'views/custom_sale_order.xml'


    ],

    'installable': True,
    'auto_install': False,
}