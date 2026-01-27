from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta


class HRContract(models.Model):
    _inherit = 'hr.contract'

    PERMANENT_TYPES = ['Employee', 'Permanent', 'Full-Time']
    TEMPORARY_TYPES = ['Temporary', 'Seasonal', 'Intern', 'Part-Time']
    # --- Field Definitions ---

    type_contract = fields.Char(
        string='Contract Type Name',
        related='contract_type_id.name',
        store=True,
        readonly=True,
        help="Technical field that stores the name of the contract type for easier filtering and computation logic."
    )

    sch_review_date = fields.Date(
        string='Scheduling Date to Review',
        compute="_compute_sch_review",
        store=True,
        help="Calculated date for contract review. If duration > 5 months, set 3 months before end_date. Otherwise, 1 month before."
    )

    review_contract = fields.Char(
        string='Result Review',
        tracking=True,
        help="Manual entry for the summary or outcome of the contract review process."
    )

    review_date = fields.Date(
        string='Date Review',
        tracking=True,
        help="The actual date when the contract review was conducted."
    )

    length_of_service_contract = fields.Float(
        string='Months of Service',
        compute='_compute_months_service',
        store=True,
        help="Total duration of the contract in months (Float), calculated from start date to end date or today."
    )

    text_length_of_service_contract = fields.Char(
        string='Length of Service',
        compute='_compute_months_service',
        translate=True,
        help="Human-readable format of the service length (e.g., '2 Years 3 Months')."
    )

    reminder_status = fields.Boolean(
        string='Reminder',
        compute="_compute_reminder_status",
        store=True,
        readonly=False,
        tracking=True,
        help="If checked, the system will include this contract in renewal notifications. Automatically set based on Contract Type."
    )

    working_hours_id = fields.Many2one(
        'resource.calendar',
        string='Working Schedule',
        related='resource_calendar_id',
        readonly=False,
        tracking=True,
        help="Link to the employee's working calendar. Synchronized with the standard resource_calendar_id field."
    )
    # --- Business Logic ---

    @api.depends('contract_type_id', 'state')
    def _compute_reminder_status(self):
        for record in self:
            type_name = record.contract_type_id.name
            # Gunakan konstanta yang sudah didefinisikan di atas
            if record.state == 'close' or type_name in self.PERMANENT_TYPES:
                record.reminder_status = False
            elif type_name in self.TEMPORARY_TYPES:
                record.reminder_status = True
            else:
                # Default fallback jika tipe tidak terdaftar
                record.reminder_status = False

    @api.depends('contract_type_id', 'contract_type_id.name', 'date_start', 'date_end')
    def _compute_sch_review(self):
        for contract in self:
            # Default value
            contract.sch_review_date = False

            # Safety check: pastikan contract_type_id, start, end, dan tipe kontrak sesuai
            if not (contract.date_start and contract.date_end and contract.contract_type_id and contract.contract_type_id.name in self.TEMPORARY_TYPES):
                continue

            # Hitung total bulan kontrak
            delta = relativedelta(contract.date_end, contract.date_start)
            total_months = delta.years * 12 + delta.months

            # Tentukan jarak review: 3 bulan jika > 5 bulan, 1 bulan jika <= 5
            months_before = 3 if total_months > 5 else 1
            calculated_date = contract.date_end - \
                relativedelta(months=months_before)

            # Batas bawah agar tidak lebih awal dari start date
            target_date = max(calculated_date, contract.date_start)

            # Koreksi akhir pekan: Saturday=5, Sunday=6 → geser ke Monday
            weekday = target_date.weekday()
            if weekday > 4:
                # Tambahkan (7 - weekday) hari untuk pindah ke Senin
                target_date += relativedelta(days=(7 - weekday))

            contract.sch_review_date = target_date

    @api.depends('date_start', 'date_end')
    def _compute_months_service(self):
        for contract in self:
            if not contract.date_start:
                contract.length_of_service_contract = 0.0
                contract.text_length_of_service_contract = _(
                    "0 Years 0 Months")
                continue

            # Gunakan hari ini jika kontrak masih aktif (Running)
            end_date = contract.date_end or fields.Date.context_today(self)
            delta = relativedelta(end_date, contract.date_start)

            total_months = (delta.years * 12) + delta.months

            contract.length_of_service_contract = float(total_months)

            # Gunakan mapping dictionary untuk translasi yang lebih aman
            contract.text_length_of_service_contract = _("%(years)s Years %(months)s Months") % {
                'years': delta.years,
                'months': delta.months
            }
