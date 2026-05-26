import calendar
import logging
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleQuarterlyPeriode(models.Model):
    _name = 'sale.quarterly.periode'
    _description = 'Quarterly Period'
    _order = 'company_id, years, start_date asc'
    _rec_name = 'code'
    _inherit = [
        'portal.mixin',
        'mail.thread',
        'mail.activity.mixin',
        'utm.mixin']

    name = fields.Char(string='Name', required=True)
    years = fields.Integer(string='Year', required=True, index=True)
    quarter = fields.Integer(string='Quarter', required=True, index=True)
    code = fields.Char(string='Code', required=True, index=True)
    start_date = fields.Date(string='Start Date', required=True, index=True)
    end_date = fields.Date(string='End Date', required=True, index=True)
    active = fields.Boolean(string='Active', tracking=1, default=True)

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('run', 'Running'),
        ('pending', 'Hold'),
        ('close', 'Closed')
    ], string='State', default='draft', tracking=1)
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
    # CORE GENERATOR (Logika 3 Bulanan)
    # =========================================================

    @api.model
    def _prepare_quarterly_period_vals(self, year, company_id=None):
        if not company_id:
            company_id = self.env.company.id

        vals_list = []
        short_year = str(year)[2:]

        # Looping 4 Kuartal
        # Q1: Bulan 1 s/d 3
        # Q2: Bulan 4 s/d 6
        # Q3: Bulan 7 s/d 9
        # Q4: Bulan 10 s/d 12
        for q in range(1, 5):
            start_month = (q - 1) * 3 + 1
            end_month = q * 3

            start_date = date(year, start_month, 1)

            # Mendapatkan hari terakhir dari bulan terakhir di kuartal ini
            # Contoh: calendar.monthrange(2026, 3) -> hasil [1] adalah 31
            last_day = calendar.monthrange(year, end_month)[1]
            end_date = date(year, end_month, last_day)

            # Format kode contoh: 26Q1, 26Q2, dst.
            code = f"{short_year}Q{q}"

            vals_list.append({
                'name': f'QUARTER {q} {year}',
                'years': year,
                'quarter': q,
                'code': code,
                'start_date': start_date,
                'end_date': end_date,
                'company_id': company_id,
            })

        return vals_list

    # =========================================================
    # PUBLIC GENERATOR
    # =========================================================

    @api.model
    def generate_quarterly_period(self, year=None, company_id=None,
                                  replace_existing=True):
        if not year:
            today = fields.Date.context_today(self)
            year = today.year + 1

        if not company_id:
            company_id = self.env.company.id

        _logger.info(
            "Generating quarterly periods for year %s (Company: %s)",
            year, company_id
        )

        existing = self.search([
            ('years', '=', year),
            ('company_id', '=', company_id),
        ])

        if existing:
            if replace_existing:
                existing.unlink()
            else:
                return False

        vals_list = self._prepare_quarterly_period_vals(
            year,
            company_id=company_id,
        )

        if vals_list:
            records = self.create(vals_list)
            return records

        return False

    # =========================================================
    # CRON JOB
    # =========================================================

    @api.model
    def cron_generate_quarterly_period(self):
        today = fields.Date.context_today(self)
        next_year = today.year + 1
        companies = self.env['res.company'].search([])

        for company in companies:
            self.with_context(
                allowed_company_ids=company.ids
            ).generate_quarterly_period(
                year=next_year,
                company_id=company.id,
                replace_existing=True,
            )
