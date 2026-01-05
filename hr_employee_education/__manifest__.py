# -*- coding: utf-8 -*-
{
    'name': "hr_employee_education",

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
    'depends': ['base', 'hr', 'hr_skills'],

    # always loaded
    "data": [
        "security/ir.model.access.csvviews/hr_certification_views.xml",
        "views/hr_education_views.xml",
        "views/hr_employee_views.xml",
        "views/hr_skills_views.xml",
        "views/templates.xml",
        "views/views.xml"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
