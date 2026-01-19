# -*- coding: utf-8 -*-
{
    'name': "hr_employee_termination",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'hr',
                'hr_contract',
                'hr_payroll',
                'survey',],

    # always loaded
    "data": [
        "views/hr_config_notification_views.xml",
        "views/hr_employee_termination_views.xml",
        "views/templates.xml",
        "views/views.xml",
        "wizards/wis_employee_child_ids.xml",
        "wizards/wiz_hr_paklaring.xml",
        "#security/ir.model.access.csv"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

