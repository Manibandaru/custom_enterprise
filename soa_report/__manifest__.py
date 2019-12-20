
{
    'name': 'Statement of Account Report',
    'version': '1.0',
    'website' : 'https://www.sidmectech.com',
    'category': 'Base',
    'summary': 'Account Customers statement & Supplier statement & overdue statements',
    'description': """
This module will help you to Print and email Customers & Suppliers with Due Account Statements
""",
    'author': 'Mani Shankar',
    'depends': ['base','sale','purchase','web'],
    'data': [

        'report/acc_statemnt_view.xml',
        'report/report_view.xml',

    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
