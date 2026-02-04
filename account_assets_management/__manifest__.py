# -*- coding: utf-8 -*-
{
    'name': "account_assets_management",

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
    'depends': ['base', 'account'],

    # always loaded
    "data": [
        "data/ir_cron_cron.xml",
        "views/account_asset_group_views.xml",
        "views/account_asset_line_views.xml",
        "views/account_asset_profile_views.xml",
        "views/account_asset_recompute_trigger_views.xml",
        "views/account_asset_views.xml",
        "views/templates.xml",
        "views/views.xml",
        "reports/account_asset_report_report.xml",
        "wizards/account_asset_compute.xml",
        "wizards/account_asset_remove.xml",
        "wizards/asset_modify.xml",
        "#security/ir.model.access.csv"
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
