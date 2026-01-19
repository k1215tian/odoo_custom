# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrConfigNotification(models.Model):
    """ This model represents hr.config.notification."""
    _name = 'hr.config.notification'
    _description = 'Configuration Notification Contract'
    _order = "calculate_notif"

    @api.depends('days_notif','interval_notif')
    def calculate_date(self):
        for line in self:
            if line.interval_notif =='days' and line.days_notif:
                line.calculate_notif=line.days_notif
            elif line.interval_notif == 'weeks' and line.days_notif:
                line.calculate_notif=line.days_notif*7
            elif line.interval_notif == 'months' and line.days_notif:
                line.calculate_notif=line.days_notif*30
            else:
                line.calculate_notif=1


    days_notif = fields.Integer(
        string='Length of the notification contract',
        store=True, change_default=True, default=1,required=True)
    interval_notif = fields.Selection([('days','Days'),('weeks','Weeks'),('months','Months')],
        string='Interval of the notification contract',default='days',required=True)
    calculate_notif = fields.Integer(
        string='Lenth of days of', compute = "calculate_date",store=True)
    active = fields.Boolean(
        string='Active',default=True)

    @api.onchange('days_notif','interval_notif')
    def _calculate_date(self):
        self.calculate_date()