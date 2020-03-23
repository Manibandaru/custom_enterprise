
{
    'name': 'Logistics Addon',
    'version': '1.0',
    'author': 'Mani Shankar',
    'category': 'Productivity',
    'description': """
        This module includes the a2NSoft solution for the logistic companies""",

    'summary': 'This module includes the a2NSoft solution for the logistic companies',
    'depends': ['base', 'sale','account'],

    'data': [
        'security/ir.model.access.csv',
        'views/so_job_type_view.xml',
        'views/custom_sale_order_view.xml',
        'views/custom_res_company_view.xml',
        'views/custom_account_invoice.xml'


    ],

    'installable': True,
    'auto_install': False,
}