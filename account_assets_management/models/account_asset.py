# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    _name = "account.asset"
    _inherit = ["mail.thread", "mail.activity.mixin", "analytic.mixin"]
    _description = "Asset"
    _order = "date_start desc, code, name"
    _check_company_auto = True

    # =====================================================
    # BASIC INFORMATION
    # =====================================================
    name = fields.Char(
        string="Asset Name",
        required=True,
        tracking=True,
        help="Nama spesifik aset tetap (contoh: 'Laptop MacBook Pro 2024 - IT')."
    )
    code = fields.Char(
        string="Reference",
        copy=False,
        tracking=True,
        help="Nomor identifikasi unik atau label inventaris (Asset Tag)."
    )
    barcode = fields.Char(
        string="Barcode",
        copy=False,
        help="Barcode for asset identification and scanning")
    vendor_id = fields.Many2one(
        'res.partner',
        string="Associated Vendor",
        help="Select the vendor or supplier of this asset")
    vendor_name = fields.Char(
        string="Vendor Name",
        help="Select the vendor or supplier of this asset")
    active = fields.Boolean(
        default=True,
        help="Jika dinonaktifkan, aset ini akan diarsipkan tanpa menghapus data historisnya."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Running'),
        ('close', 'Closed'),
        ('removed', 'Removed'),
    ], string='Status', default='draft', readonly=True, tracking=True,
        help="Lifecycle Aset: \n"
             "- Draft: Belum divalidasi, jadwal penyusutan belum terbentuk.\n"
             "- Running: Sedang dalam masa penyusutan aktif.\n"
             "- Closed: Masa manfaat habis atau sudah lunas disusutkan.\n"
             "- Removed: Aset dijual atau dihapus sebelum masa manfaat habis."
    )

    asset_status = fields.Selection([
        ('assign', 'Assign'),
        ('return', 'Return'),
        ('in_warehouse', 'In Warehouse'),
        ('repair', 'Repair'),
        ('destroyed', 'Destroyed')
    ], string="Status", default="assign")

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
        help="Perusahaan pemilik aset ini (Multi-company aware)."
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id,
        help="Mata uang yang digunakan untuk nilai perolehan dan penyusutan."
    )

    # =====================================================
    # PROFILE & VALUE
    # =====================================================
    profile_id = fields.Many2one(
        'account.asset.profile', string='Asset Profile',
        required=True, check_company=True,
        help="Template konfigurasi yang menentukan akun akuntansi dan metode penyusutan aset ini."
    )

    asset_type = fields.Selection([
        ('vehicle', 'Vehicle (Kendaraan)'),
        ('electronic', 'Electronic (Elektronik)'),
        ('furniture', 'Furniture (Mebel)'),
        ('building', 'Building (Bangunan)'),
        ('machinery', 'Machinery (Mesin)'),
        ('other', 'Other (Lainnya)')
    ], string="Asset Category Type", default='other', help="Klasifikasi jenis barang untuk pelaporan.")

    purchase_value = fields.Monetary(
        string='Original Value', required=True, currency_field='currency_id',
        help="Nilai harga beli awal aset yang akan menjadi dasar perhitungan penyusutan."
    )
    purchase_date = fields.Date(
        string='Purchase Date',
        tracking=True,
        help="Tanggal pembelian aset berdasarkan Vendor Bill."
    )
    salvage_value = fields.Monetary(
        string='Salvage Value', currency_field='currency_id',
        help="Nilai sisa aset di akhir masa manfaat (tidak ikut disusutkan)."
    )
    date_start = fields.Date(
        string='Start Date', required=True, default=fields.Date.context_today,
        help="Tanggal mulai aset digunakan dan dimulainya perhitungan penyusutan."
    )

    # Depreciation Snapshot fields (Salinan dari Profile)
    method = fields.Selection(
        [('linear', 'Linear'), ('degressive', 'Degressive')],
        string='Method',
        help="Metode perhitungan: Linear (nilai tetap) atau Degressive (saldo menurun)."
    )
    method_number = fields.Integer(
        string='Number of Depreciations',
        help="Jumlah total periode penyusutan yang direncanakan."
    )
    method_period = fields.Integer(
        string='Period Length (Months)', default=1,
        help="Interval waktu antar penyusutan dalam satuan bulan (misal: 1 untuk bulanan)."
    )
    prorata = fields.Boolean(
        string='Prorata Temporis',
        help="Jika aktif, penyusutan periode pertama dihitung proporsional berdasarkan jumlah hari sejak tanggal mulai."
    )

    # Relationships
    depreciation_line_ids = fields.One2many(
        'account.asset.line', 'asset_id', string='Depreciation Lines', copy=False,
        help="Daftar jadwal penyusutan yang dihasilkan secara otomatis oleh sistem."
    )
    depreciation_move_ids = fields.One2many(
        'account.move', compute='_compute_depreciation_move_ids', string='Journal Entries',
        help="Daftar entri jurnal akuntansi yang telah diposting untuk aset ini."
    )
    move_count = fields.Integer(
        compute='_compute_depreciation_move_ids', string='Journal Entries Count')
    group_id = fields.Many2one(
        'account.asset.group',
        string='Asset Group',
        check_company=True,
        help="Gunakan ini untuk pengelompokan lokasi atau departemen secara hirarkis."
    )

    recompute_trigger_ids = fields.Many2many(
        'account.asset.recompute.trigger',
        string='Recompute Triggers',
        readonly=True,
        help="Log otomatis jika aset ini membutuhkan hitung ulang akibat perubahan sistem."
    )

    # Warranty Information
    expired_warranty_date = fields.Date(
        string="Expired Warranty Date", tracking=True)
    warranty_status = fields.Selection([
        ('expired', 'Expired'),
        ('danger', 'Critical (Below 3 Months)'),
        ('warning', 'Warning (3-6 Months)'),
        ('success', 'Safe (Above 6 Months)'),
        ('on-going', 'On Going')
    ], string='Warranty Status', default='on-going', compute="_compute_months_left", store=True)

    remaining_warranty = fields.Char(
        string="Remaining Warranty",
        compute="_compute_months_left",
        store=True,
        tracking=True,
        help="Menampilkan sisa waktu garansi dalam tahun/bulan/hari."
    )
    # =====================================================
    # COMPUTE & ONCHANGE
    # =====================================================

    @api.depends('depreciation_line_ids.move_id')
    def _compute_depreciation_move_ids(self):
        for asset in self:
            moves = asset.depreciation_line_ids.mapped('move_id')
            asset.depreciation_move_ids = moves
            asset.move_count = len(moves)

    @api.onchange('profile_id')
    def _onchange_profile_id(self):
        """Menyalin pengaturan default dari profil aset yang dipilih."""
        if not self.profile_id:
            return
        p = self.profile_id
        self.method = p.method
        self.method_number = p.method_number
        self.method_period = p.method_period
        self.prorata = p.prorata
        if p.analytic_distribution:
            self.analytic_distribution = p.analytic_distribution

    # =====================================================
    # CORE LOGIC (ENGINE)
    # =====================================================
    def compute_depreciation_board(self):
        """Engine penyusutan Linear dengan penanganan pembulatan dan sisa nilai."""
        self.ensure_one()
        # Bersihkan baris draft yang lama
        self.depreciation_line_ids.filtered(lambda l: not l.move_id).unlink()

        if self.method != 'linear':
            raise UserError(
                _("Saat ini sistem hanya mendukung metode penyusutan Linear."))

        amount_to_depreciate = self.purchase_value - self.salvage_value
        if amount_to_depreciate <= 0:
            return True

        total_periods = self.method_number or 1
        # Gunakan pembulatan mata uang agar balance di jurnal
        depreciation_amount = self.currency_id.round(
            amount_to_depreciate / total_periods)

        commands = []
        cumulative_depr = 0.0
        current_date = self.date_start
        period_interval = int(
            self.method_period) if self.method_period > 0 else 1

        for i in range(1, total_periods + 1):
            # Baris terakhir menyesuaikan selisih pembulatan (rounding difference)
            if i == total_periods:
                depreciation_amount = amount_to_depreciate - cumulative_depr

            cumulative_depr += depreciation_amount

            commands.append((0, 0, {
                'name': f"{self.name} - {i}/{total_periods}",
                'amount': depreciation_amount,
                'depreciated_value': cumulative_depr,
                'remaining_value': self.purchase_value - cumulative_depr,
                'line_date': current_date,
                'type': 'depreciation',
            }))
            current_date += relativedelta(months=period_interval)

        self.write({'depreciation_line_ids': commands})
        return True

    @api.depends('expired_warranty_date')
    def _compute_months_left(self):
        today = fields.Date.today()
        for record in self:
            if record.expired_warranty_date:
                if record.expired_warranty_date < today:
                    record.remaining_warranty = _('Expired')
                    record.warranty_status = 'expired'
                elif record.expired_warranty_date == today:
                    record.remaining_warranty = _('Today')
                    record.warranty_status = 'danger'
                else:
                    rd = relativedelta(record.expired_warranty_date, today)
                    # Hitung total bulan untuk menentukan status warna (badge)
                    total_months = rd.years * 12 + rd.months

                    if total_months > 6:
                        record.warranty_status = 'success'
                    elif 3 <= total_months <= 6:
                        record.warranty_status = 'warning'
                    else:
                        record.warranty_status = 'danger'

                    # Logika penyusunan teks yang lebih rapi
                    parts = []
                    if rd.years > 0:
                        parts.append(
                            f"{rd.years} year{'s' if rd.years > 1 else ''}")
                    if rd.months > 0:
                        parts.append(
                            f"{rd.months} month{'s' if rd.months > 1 else ''}")
                    if rd.days > 0 and not parts:  # Tampilkan hari hanya jika tahun & bulan 0
                        parts.append(
                            f"{rd.days} day{'s' if rd.days > 1 else ''}")

                    record.remaining_warranty = ', '.join(
                        parts) if parts else _("Expiring Soon")
            else:
                record.remaining_warranty = _('No warranty')
                record.warranty_status = 'expired'

    def action_validate(self):
        """Memvalidasi aset dan membuat jadwal penyusutan."""
        for asset in self:
            if asset.state != 'draft':
                continue
            asset.compute_depreciation_board()
            asset.state = 'open'
            _logger.info("Aset %s divalidasi.", asset.name)

    def action_post_depreciation(self, date=None):
        """Memicu pembuatan jurnal. Mendukung Grouping jika diatur di Profil."""
        if not date:
            date = fields.Date.today()

        domain = [
            ('asset_id', 'in', self.ids),
            ('line_date', '<=', date),
            ('move_id', '=', False)
        ]
        lines = self.env['account.asset.line'].search(domain)

        # Logika Grouping seperti Odoo 11
        grouped_lines = lines.filtered(
            lambda l: l.asset_id.profile_id.group_entries)
        individual_lines = lines.filtered(
            lambda l: not l.asset_id.profile_id.group_entries)

        if grouped_lines:
            grouped_lines.create_grouped_move()

        if individual_lines:
            individual_lines.create_move()

        return True

    # =====================================================
    # SMART BUTTON ACTIONS
    # =====================================================
    def action_view_sales_moves(self):
        """Membuka daftar Journal Entries terkait aset ini."""
        self.ensure_one()
        return {
            'name': _("Journal Entries"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.depreciation_move_ids.ids)],
            'context': {'create': False}
        }
