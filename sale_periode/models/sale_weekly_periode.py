import logging
from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SalesWeeklyPeriode(models.Model):
    _name = 'sale.weekly.periode'
    _description = 'Sales Weekly Periode'
    _order = 'company_id, years, start_date asc'
    _rec_name = 'code'
    _inherit = [
        'portal.mixin',
        'mail.thread',
        'mail.activity.mixin',
        'utm.mixin']

    name = fields.Char(string='Name', required=True)
    years = fields.Integer(string='Year', required=True, index=True)
    month = fields.Integer(string='Month', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)
    start_date = fields.Date(string='Start Date', required=True, index=True)
    end_date = fields.Date(string='End Date', required=True, index=True)
    week_no = fields.Integer(string='Week Number', index=True)
    active = fields.Boolean(string='Active', default=True, tracking=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('run', 'Running'),
        ('pending', 'Hold'),
        ('close', 'Closed')
    ], string='State', default='draft', tracking=1)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    description = fields.Text()

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    _sql_constraints = [
        (
            'code_company_unique',
            'unique(code, company_id)',
            'Code must be unique per company!',
        ),
    ]

    @api.constrains('start_date', 'end_date', 'company_id')
    def _check_date_overlap(self):
        """
        Validasi Python untuk mencegah periode tanggal tumpang tindih
        dalam perusahaan yang sama.
        """
        for record in self:
            if (record.start_date and record.end_date and
                    record.start_date > record.end_date):
                raise ValidationError(
                    f"Error pada '{record.name}': "
                    "Start Date tidak boleh melewati End Date!"
                )

            domain = [
                ('id', '!=', record.id),
                ('company_id', '=', record.company_id.id),
                ('start_date', '<=', record.end_date),
                ('end_date', '>=', record.start_date),
            ]

            overlap = self.search(domain, limit=1)

            if overlap:
                raise ValidationError(
                    "Terjadi tumpang tindih tanggal!\n"
                    f"Periode '{record.name}' "
                    f"({record.start_date} s/d {record.end_date}) bentrok "
                    f"dengan periode '{overlap.name}' "
                    f"({overlap.start_date} s/d {overlap.end_date})."
                )

    # =========================================================
    # CORE GENERATOR
    # =========================================================

    @api.model
    def _prepare_weekly_period_vals(self, year, company_id=None):
        """
        Prepare weekly period values for 1 year based on company.
        """
        if not company_id:
            company_id = self.env.company.id

        vals_list = []
        current_date = date(year, 1, 1)
        last_day = date(year, 12, 31)

        short_year = str(year)[2:]
        week_no = 1

        while current_date <= last_day:
            start_week = current_date
            # Monday=0 ... Sunday=6
            days_to_sunday = 6 - current_date.weekday()
            end_week = current_date + timedelta(days=days_to_sunday)

            # Prevent crossing next year
            if end_week > last_day:
                end_week = last_day

            month = start_week.month
            code = f"{short_year}{month:02d}wk{week_no}"

            vals_list.append({
                'name': f'WEEK {week_no} {year}',
                'years': year,
                'month': month,
                'code': code,
                'start_date': start_week,
                'end_date': end_week,
                'week_no': week_no,
                'company_id': company_id,
            })

            current_date = end_week + timedelta(days=1)
            week_no += 1

        return vals_list

    # =========================================================
    # PUBLIC GENERATOR
    # =========================================================

    @api.model
    def generate_weekly_period(self, year=None, company_id=None,
                               replace_existing=True):
        """
        Public method for manual or automated generation per company.
        """
        if not year:
            today = fields.Date.context_today(self)
            year = today.year + 1

        if not company_id:
            company_id = self.env.company.id

        _logger.info(
            "Generating weekly periods for year %s (Company ID: %s)",
            year,
            company_id,
        )

        existing = self.search([
            ('years', '=', year),
            ('company_id', '=', company_id),
        ])

        if existing:
            if replace_existing:
                _logger.info(
                    "Deleting existing weekly periods for year %s "
                    "(Company ID: %s)",
                    year,
                    company_id,
                )
                existing.unlink()
            else:
                _logger.warning(
                    "Weekly periods already exist for year %s "
                    "(Company ID: %s).",
                    year,
                    company_id,
                )
                return False

        vals_list = self._prepare_weekly_period_vals(
            year,
            company_id=company_id,
        )

        if vals_list:
            records = self.create(vals_list)
            _logger.info(
                "Successfully generated %s weekly periods for year %s "
                "(Company ID: %s)",
                len(records),
                year,
                company_id,
            )
            return records

        return False

    # =========================================================
    # CRON JOB
    # =========================================================

    @api.model
    def cron_generate_weekly_period(self):
        """
        Executed every 31 December 23:00.
        Generate next year weekly periods FOR ALL ACTIVE COMPANIES.
        """
        today = fields.Date.context_today(self)
        next_year = today.year + 1

        companies = self.env['res.company'].search([])

        for company in companies:
            self.with_context(
                allowed_company_ids=company.ids
            ).generate_weekly_period(
                year=next_year,
                company_id=company.id,
                replace_existing=True,
            )
