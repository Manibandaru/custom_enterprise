{
    'name': 'a2NSoft PDC Module',
    'version': '1.0',
    'website' : 'https://www.sidmectech.com',
    'category': 'Base',
    'summary': 'Manage your company Current and Post Dated Cheques',
    'description': """
Manage your company Current and Post Dated Cheques
""",
    'author': 'Mani Shankar',
    'depends': ['base','account','sale','purchase','web','soa_report'],
    'data': [
        'views/account_payment_view.xml',
        'views/account_config_view.xml',
        'views/soa_report_view.xml'
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}