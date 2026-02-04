# -*- coding: utf-8 -*-
import logging
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    """
    Enterprise-grade Fixed Asset model.

    Design goals:
    - Accounting-safe (never touch posted journals)
    - Recompute-friendly for running assets
    - Clear lifecycle (Draft → Running → Closed / Removed)
    - Easy to extend (disposal, impairment, revaluation)
    """
    _name = "account.asset"
    _description = "Fixed Asset"
    _inherit = ["mail.thread", "mail.activity.mixin", "analytic.mixin"]
    _order = "date_start desc, code, name"
    _check_company_auto = True

    # =====================================================
    # BASIC INFORMATION
    # =====================================================
    name = fields.Char(
        string="Asset Name",
        required=True,
        tracking=True,
        help="Nama unik aset tetap, contoh: 'Laptop MacBook Pro 2024 - IT'."
    )

    code = fields.Char(
        string="Asset Reference",
        copy=False,
        tracking=True,
        help="Kode internal atau Asset Tag untuk identifikasi aset."
    )

    barcode = fields.Char(
        string="Barcode",
        copy=False,
        help="Barcode fisik untuk scanning dan inventarisasi aset."
    )

    active = fields.Boolean(
        default=True,
        help="Nonaktifkan untuk mengarsipkan aset tanpa menghapus histori akuntansi."
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Running'),
        ('close', 'Closed'),
        ('removed', 'Removed'),
    ],
        string="Asset Lifecycle Status",
        default='draft',
        readonly=True,
        tracking=True,
        help=(
            "Lifecycle aset:\n"
            "- Draft: Belum divalidasi\n"
            "- Running: Sedang disusutkan\n"
            "- Closed: Sudah habis disusutkan\n"
            "- Removed: Dijual / dihapus"
    )
    )

    asset_status = fields.Selection([
        ('assign', 'Assign'),
        ('return', 'Return'),
        ('in_warehouse', 'In Warehouse'),
        ('repair', 'Repair'),
        ('destroyed', 'Destroyed')
    ],
        string="Physical Asset Status",
        default="assign",
        tracking=True,
        help="Status fisik atau operasional aset."
    )

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="Perusahaan pemilik aset ini."
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Mata uang nilai aset dan jurnal depresiasi."
    )

    vendor_id = fields.Many2one(
        'res.partner',
        string="Vendor",
        help="Vendor atau supplier tempat aset dibeli."
    )

    vendor_name = fields.Char(
        string="Vendor Name",
        help="Nama vendor (opsional, snapshot manual)."
    )

    # =====================================================
    # PROFILE & CLASSIFICATION
    # =====================================================
    profile_id = fields.Many2one(
        'account.asset.profile',
        string="Asset Profile",
        required=True,
        check_company=True,
        ondelete='restrict',  # Prevent deletion of used profiles
        tracking=True,
        help="Profil aset (akun, metode, periode depresiasi)."
    )

    asset_type = fields.Selection([
        ('land', 'Land'),  # Tambahan
        ('vehicle', 'Vehicle'),
        ('electronic', 'Electronic'),
        ('furniture', 'Furniture'),
        ('building', 'Building'),
        ('machinery', 'Machinery'),
        ('other', 'Other')
    ],
        string="Asset Category Type",
        default='other',
        help="Klasifikasi aset untuk pelaporan dan analitik."
    )

    group_id = fields.Many2one(
        'account.asset.group',
        string="Asset Group",
        check_company=True,
        help="Pengelompokan aset (lokasi / departemen)."
    )

    # =====================================================
    # FINANCIAL VALUES
    # =====================================================
    purchase_value = fields.Monetary(
        string="Original Value",
        required=True,
        tracking=True,
        currency_field='currency_id',
        help="Nilai perolehan awal aset."
    )

    salvage_value = fields.Monetary(
        string="Salvage Value",
        currency_field='currency_id',
        help="Nilai sisa aset di akhir masa manfaat."
    )

    purchase_date = fields.Date(
        string="Purchase Date",
        tracking=True,
        help="Tanggal pembelian aset."
    )

    date_start = fields.Date(
        string="Depreciation Start Date",
        required=True,
        default=fields.Date.context_today,
        help="Tanggal mulai perhitungan penyusutan."
    )

    # =====================================================
    # DEPRECIATION PARAMETERS (SNAPSHOT)
    # =====================================================
    method = fields.Selection(
        [('linear', 'Linear'),
         ('degressive', 'Degressive'),
         ('double_declining', 'Double Declining'),
         ('custom', 'Custom Formula')],
        string="Depreciation Method",
        default='linear',
        tracking=True,
        help="Metode perhitungan penyusutan."
    )

    method_number = fields.Integer(
        string="Number of Depreciations",
        default=5,
        help="Total jumlah periode penyusutan."
    )

    method_period = fields.Integer(
        string="Period Length (Months)",
        default=1,
        help="Jarak antar penyusutan (bulan). Default: 1 (Bulanan), 12 (Tahunan)."
    )

    prorata = fields.Boolean(
        string="Prorata Temporis",
        help="Jika aktif, periode pertama dihitung proporsional berdasarkan tanggal mulai."
    )

    # =====================================================
    # RELATIONSHIPS & ACCOUNTING
    # =====================================================

    is_depreciable = fields.Boolean(default=True)

    depreciation_line_ids = fields.One2many(
        'account.asset.line',
        'asset_id',
        string="Depreciation Schedule",
        copy=False,
        help="Jadwal penyusutan aset."
    )

    depreciation_move_ids = fields.One2many(
        'account.move',
        compute='_compute_depreciation_move_ids',
        string="Journal Entries",
        help="Jurnal depresiasi yang sudah diposting."
    )

    move_count = fields.Integer(
        compute='_compute_depreciation_move_ids',
        string="Journal Entry Count"
    )

    recompute_trigger_ids = fields.Many2many(
        'account.asset.recompute.trigger',
        string="Recompute Triggers",
        readonly=True,
        copy=False,
        help="Log otomatis penanda aset perlu dihitung ulang."
    )

    # =====================================================
    # WARRANTY
    # =====================================================
    expired_warranty_date = fields.Date(
        string="Expired Warranty Date",
        tracking=True
    )

    warranty_status = fields.Selection([
        ('expired', 'Expired'),
        ('danger', 'Critical (< 3 Months)'),
        ('warning', 'Warning (3–6 Months)'),
        ('success', 'Safe (> 6 Months)'),
        ('on-going', 'On Going')
    ],
        string="Warranty Status",
        default='on-going',
        compute="_compute_months_left",
        store=True,
        help="Indikator otomatis status garansi berdasarkan tanggal kedaluwarsa."
    )

    remaining_warranty = fields.Char(
        string="Remaining Warranty",
        compute="_compute_months_left",
        store=True,
        help="Sisa masa garansi dalam teks (Tahun/Bulan)."
    )

    # =====================================================
    # VALIDATION & COMPUTATION
    # =====================================================

    @api.constrains('purchase_value', 'salvage_value', 'asset_type')
    def _check_values(self):
        """Pastikan nilai aset logis."""
        for asset in self:
            if asset.purchase_value < 0:
                raise ValidationError(_("Original value cannot be negative."))
            if asset.asset_type == 'land':
                asset.salvage_value = asset.purchase_value
            else:
                if asset.salvage_value >= asset.purchase_value:
                    raise ValidationError(_(
                        "Salvage value must be lower than the original value for depreciable assets."
                    ))

    @api.depends('expired_warranty_date')
    def _compute_months_left(self):
        """
        Menghitung sisa masa garansi dengan akurasi hingga level hari
        untuk menentukan status (danger/warning/success).
        """
        today = fields.Date.today()

        for asset in self:
            # 1. Kasus jika tanggal garansi tidak diisi
            if not asset.expired_warranty_date:
                asset.warranty_status = 'on-going'
                asset.remaining_warranty = False
                continue

            expiry = asset.expired_warranty_date

            # 2. Kasus jika sudah expired (melewati hari ini)
            if expiry < today:
                asset.warranty_status = 'expired'
                asset.remaining_warranty = _("Expired")
                continue

            # 3. Hitung selisih menggunakan relativedelta
            delta = relativedelta(expiry, today)

            # Hitung total bulan dalam bentuk float agar lebih presisi
            # Misal: 2 bulan 20 hari akan dianggap > 2.5 bulan
            total_months = (delta.years * 12) + \
                delta.months + (delta.days / 30.0)

            # Logic penentuan status warna
            if total_months < 3:
                asset.warranty_status = 'danger'   # < 3 bulan
            elif total_months < 6:
                asset.warranty_status = 'warning'  # 3 - 6 bulan
            else:
                asset.warranty_status = 'success'  # > 6 bulan

            # 4. Membangun string tampilan yang user-friendly
            parts = []
            if delta.years:
                parts.append(f"{delta.years}Y")
            if delta.months:
                parts.append(f"{delta.months}M")

            # Tampilkan hari hanya jika belum sampai setahun (agar tidak terlalu panjang)
            if delta.days and not delta.years:
                parts.append(f"{delta.days}D")

            # Jika hari ini adalah tanggal expire-nya
            asset.remaining_warranty = " ".join(parts) or _("Today")

    @api.depends('depreciation_line_ids.move_id')
    def _compute_depreciation_move_ids(self):
        """Menghitung semua journal entry yang berasal dari depresiasi aset."""
        for asset in self:
            moves = asset.depreciation_line_ids.mapped('move_id')
            asset.depreciation_move_ids = moves
            asset.move_count = len(moves)

    @api.onchange('profile_id')
    def _onchange_profile_id(self):
        """
        Menyalin parameter depresiasi dari Asset Profile.
        Snapshot ini memastikan histori tidak berubah walau profil diedit.
        """
        if not self.profile_id:
            return
        p = self.profile_id
        self.method = p.method
        self.method_number = p.method_number
        self.method_period = p.method_period
        self.prorata = p.prorata
        self.is_depreciable = p.is_depreciable

        # Analytic distribution inherit dari mixin jika ada
        if hasattr(p, 'analytic_distribution') and p.analytic_distribution:
            self.analytic_distribution = p.analytic_distribution

    # =====================================================
    # CORE ACCOUNTING ENGINE
    # =====================================================
    def compute_depreciation_board(self):
        """
        Ultimate safe & flexible depreciation engine.
        Guarantees accounting safety by respecting posted entries.
        """
        self.ensure_one()

        # 1. Validation
        if self.state == 'close':
            return True

        if not self.is_depreciable:
            self.write({'state': 'close'})
            return True
        # 2. Separate posted vs draft
        posted_lines = self.depreciation_line_ids.filtered(lambda l: l.move_id)
        draft_lines = self.depreciation_line_ids - posted_lines
        draft_lines.unlink()

        # 3. Base values calculations
        depreciable_base = self.purchase_value - self.salvage_value
        if depreciable_base <= 0:
            # Jika nilai residu >= harga beli, langsung tutup tanpa depresiasi
            self.write({'state': 'close'})
            return True

        already_depreciated = sum(posted_lines.mapped('amount'))
        remaining_amount = depreciable_base - already_depreciated

        # Currency rounding helper
        currency = self.currency_id
        if currency.is_zero(remaining_amount) or remaining_amount < 0:
            self.write({'state': 'close'})
            return True

        # 4. Period Calculation
        # Total periods defined vs periods already consumed
        total_periods = self.method_number
        posted_count = len(posted_lines)
        remaining_periods = total_periods - posted_count

        if remaining_periods <= 0:
            # Case: User changed method_number to be smaller than posted lines
            self.write({'state': 'close'})
            return True

        # Determine start date for the next line
        if posted_lines:
            last_date = max(posted_lines.mapped('line_date'))
            current_date = last_date + relativedelta(months=self.method_period)
        else:
            current_date = self.date_start

        cumulative_depreciated = already_depreciated
        commands = []

        # Factors for non-linear methods
        degressive_factor = getattr(
            self.profile_id, 'method_progress_factor', 0.3)
        double_declining_factor = 2 * degressive_factor
        period_factor = (self.method_period or 1) / 12.0

        # 5. Generate depreciation lines
        for i in range(1, remaining_periods + 1):
            is_last = (i == remaining_periods)
            amount = 0.0

            if self.method == 'linear':
                if is_last:
                    amount = remaining_amount
                else:
                    # Smoothing: Recalculate based on remaining life
                    # This auto-corrects any past rounding anomalies
                    amount = currency.round(
                        remaining_amount / (remaining_periods - i + 1)
                    )

            elif self.method == 'degressive':
                book_value = self.purchase_value - cumulative_depreciated
                amount = currency.round(
                    book_value * degressive_factor * period_factor)
                # Cap amount
                amount = min(amount, remaining_amount)

            elif self.method == 'double_declining':
                book_value = self.purchase_value - cumulative_depreciated
                amount = currency.round(
                    book_value * double_declining_factor * period_factor)
                # Cap amount
                amount = min(amount, remaining_amount)

            elif self.method == 'custom':
                # Custom Formula Execution
                # formula = getattr(self.profile_id, 'custom_formula', '')
                # try:
                #     eval_context = {
                #         'book_value': self.purchase_value - cumulative_depreciated,
                #         'remaining_amount': remaining_amount,
                #         'period_factor': period_factor,
                #         'purchase_value': self.purchase_value,
                #         'salvage_value': self.salvage_value,
                #     }
                #     raw_amount = eval(formula, eval_context)
                #     amount = currency.round(float(raw_amount))
                # except Exception as e:
                #     _logger.error("Asset Custom Formula Error: %s", e)
                #     amount = 0.0
                formula = getattr(self.profile_id, 'custom_formula', '')
                if not formula:
                    amount = 0.0
                else:
                    try:
                        eval_context = {
                            'book_value': self.purchase_value - cumulative_depreciated,
                            'remaining_amount': remaining_amount,
                            'period_factor': period_factor,
                            'purchase_value': self.purchase_value,
                            'salvage_value': self.salvage_value,
                        }
                        # Mengganti eval() menjadi safe_eval()
                        raw_amount = safe_eval(formula, eval_context)
                        amount = currency.round(float(raw_amount))
                    except Exception as e:
                        _logger.error("Asset Custom Formula Error: %s", e)
                        amount = 0.0
                        
                amount = min(amount, remaining_amount)

            # --- Safety Checks ---
            amount = max(amount, 0.0)
            if is_last and amount != remaining_amount:
                # Force balance on last line
                amount = remaining_amount

            # --- Update Accumulations ---
            cumulative_depreciated += amount
            remaining_amount -= amount

            # Create line command
            commands.append((0, 0, {
                'name': f"{self.name} - {posted_count + i}/{total_periods}",
                'amount': amount,
                'depreciated_value': cumulative_depreciated,
                'remaining_value': self.purchase_value - cumulative_depreciated,
                'line_date': current_date,
                'type': 'depreciation',
                'currency_id': currency.id,
            }))

            current_date += relativedelta(months=self.method_period)

        # 6. Write to DB
        self.write({'depreciation_line_ids': commands})
        return True

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_validate(self):
        """Validasi aset dan mengaktifkan penyusutan."""
        for asset in self:
            if asset.state != 'draft':
                continue
            if not asset.depreciation_line_ids:
                asset.compute_depreciation_board()
            asset.state = 'open'
            _logger.info("Asset validated: %s", asset.name)

    def action_post_depreciation(self, date=None):
        """
        Membuat journal entry depresiasi hingga tanggal tertentu.
        """
        if not date:
            date = fields.Date.today()

        lines = self.env['account.asset.line'].search([
            ('asset_id', 'in', self.ids),
            ('line_date', '<=', date),
            ('move_id', '=', False),
            ('type', '=', 'depreciation')
        ])

        # Filter by profile setting: Grouped Entry or One Entry Per Asset
        # Assumes account.asset.line has create_grouped_move and create_move methods
        grouped = lines.filtered(lambda l: l.asset_id.profile_id.group_entries)
        individual = lines - grouped

        if grouped:
            grouped.create_grouped_move()
        if individual:
            individual.create_move()

        return True

    def action_view_asset_moves(self):
        """Smart button untuk melihat journal entry depresiasi."""
        self.ensure_one()
        return {
            'name': _("Asset Entries"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.depreciation_move_ids.ids)],
            'context': {'create': False}
        }
