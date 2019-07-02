
{
    'name': 'Checklist Report',
    'version': '1.0',
    'author': 'Mani Shankar',
    'category': 'Productivity',
    'description': """
        This module helps to do checklist on the each job assigned.
    """,

    'summary': 'This module helps to do checklist on the each job assigned',
    'depends': ['base', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/checklist_menu.xml',
        'views/custom_action.xml',
        'report/report_so_checklist.xml'


    ],

    'installable': True,
    'auto_install': False,
}