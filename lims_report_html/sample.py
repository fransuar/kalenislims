# This file is part of lims_report_html module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import Pool, PoolMeta


class Fraction(metaclass=PoolMeta):
    __name__ = 'lims.fraction'

    result_template = fields.Function(fields.Many2One(
        'lims.result_report.template', 'Report Template'), 'get_sample_field')

    def _order_sample_field(name):
        def order_field(tables):
            Sample = Pool().get('lims.sample')
            field = Sample._fields[name]
            table, _ = tables[None]
            sample_tables = tables.get('sample')
            if sample_tables is None:
                sample = Sample.__table__()
                sample_tables = {
                    None: (sample, sample.id == table.sample),
                    }
                tables['sample'] = sample_tables
            return field.convert_order(name, sample_tables, Sample)
        return staticmethod(order_field)
    order_result_template = _order_sample_field('result_template')


class Sample(metaclass=PoolMeta):
    __name__ = 'lims.sample'

    result_template = fields.Many2One('lims.result_report.template',
        'Report Template', domain=[('type', 'in', [None, 'base'])])
    resultrange_origin = fields.Many2One('lims.range.type', 'Comparison range',
        domain=[('use', '=', 'result_range')])

    @fields.depends('result_template')
    def on_change_result_template(self):
        if self.result_template and self.result_template.resultrange_origin:
            self.resultrange_origin = (
                self.result_template.resultrange_origin.id)


class CreateSampleStart(metaclass=PoolMeta):
    __name__ = 'lims.create_sample.start'

    result_template = fields.Many2One('lims.result_report.template',
        'Report Template', domain=[('type', 'in', [None, 'base'])])
    resultrange_origin = fields.Many2One('lims.range.type', 'Comparison range',
        domain=[('use', '=', 'result_range')])

    @fields.depends('result_template')
    def on_change_result_template(self):
        if self.result_template and self.result_template.resultrange_origin:
            self.resultrange_origin = (
                self.result_template.resultrange_origin.id)


class CreateSample(metaclass=PoolMeta):
    __name__ = 'lims.create_sample'

    def default_start(self, fields):
        Party = Pool().get('party.party')

        defaults = super().default_start(fields)

        party_id = defaults['party']
        if party_id:
            party = Party(party_id)
            if party.result_template:
                defaults['result_template'] = party.result_template.id
                if party.result_template.resultrange_origin:
                    defaults['resultrange_origin'] = (
                        party.result_template.resultrange_origin.id)
        return defaults

    def _get_samples_defaults(self, entry_id):
        samples_defaults = super()._get_samples_defaults(entry_id)

        result_template_id = None
        if (hasattr(self.start, 'result_template') and
                getattr(self.start, 'result_template')):
            result_template_id = getattr(self.start, 'result_template').id
        result_range_id = None
        if (hasattr(self.start, 'resultrange_origin') and
                getattr(self.start, 'resultrange_origin')):
            result_range_id = getattr(self.start, 'resultrange_origin').id

        for sample in samples_defaults:
            sample['result_template'] = result_template_id
            sample['resultrange_origin'] = result_range_id
        return samples_defaults
