# This file is part of lims_industry module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from sql import Literal
from sql.conditionals import Case

from trytond.model import ModelSQL, ModelView, fields
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Entry(metaclass=PoolMeta):
    __name__ = 'lims.entry'

    @classmethod
    def confirm(cls, entries):
        Sample = Pool().get('lims.sample')
        super().confirm(entries)
        samples = [s for e in entries for s in e.samples]
        Sample._confirm_samples(samples)


class Sample(metaclass=PoolMeta):
    __name__ = 'lims.sample'

    plant = fields.Function(fields.Many2One('lims.plant', 'Plant'),
        'get_plant', searcher='search_plant')
    equipment = fields.Many2One('lims.equipment', 'Equipment',
        domain=['OR', ('id', '=', Eval('equipment')),
            ('party', '=', Eval('party'))],
        depends=['party'], select=True)
    equipment_template = fields.Function(fields.Many2One(
        'lims.equipment.template', 'Equipment Template'),
        'get_equipment_field')
    equipment_model = fields.Function(fields.Char('Equipment Model'),
        'get_equipment_field')
    equipment_serial_number = fields.Function(fields.Char(
        'Equipment Serial Number'), 'get_equipment_field')
    equipment_name = fields.Function(fields.Char(
        'Equipment Name'), 'get_equipment_field')
    component = fields.Many2One('lims.component', 'Component',
        domain=['OR', ('id', '=', Eval('component')),
            ('equipment', '=', Eval('equipment'))],
        depends=['equipment'])
    comercial_product = fields.Many2One('lims.comercial.product',
        'Comercial Product')
    ind_sampling_date = fields.Date('Sampling date')
    ind_volume = fields.Float('Received volume')
    sampling_type = fields.Many2One('lims.sampling.type',
        'Sampling Type')
    ind_operational_detail = fields.Text('Operational detail')
    ind_work_environment = fields.Text('Work environment')
    ind_analysis_reason = fields.Text('Reason for analysis')
    missing_data = fields.Boolean('Missing data')
    attributes_domain = fields.Function(fields.Many2Many(
        'lims.sample.attribute', None, None, 'Attributes domain'),
        'on_change_with_attributes_domain')
    sample_photo = fields.Binary('Sample Photo',
        file_id='sample_photo_id', store_prefix='sample')
    sample_photo_id = fields.Char('Sample Photo ID', readonly=True)
    label_photo = fields.Binary('Label Photo',
        file_id='label_photo_id', store_prefix='sample')
    label_photo_id = fields.Char('Label Photo ID', readonly=True)
    oil_added = fields.Float('Liters Oil added')
    ind_equipment = fields.Integer('Equipment')
    ind_equipment_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    ind_component = fields.Integer('Component')
    ind_component_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    ind_oil = fields.Integer('Oil')
    ind_oil_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    oil_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Oil?', sort=False)
    oil_changed_string = oil_changed.translated('oil_changed')
    oil_filter_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Oil Filter?', sort=False)
    oil_filter_changed_string = oil_filter_changed.translated(
        'oil_filter_changed')
    air_filter_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Air Filter?', sort=False)
    air_filter_changed_string = air_filter_changed.translated(
        'air_filter_changed')
    edition_log = fields.One2Many('lims.sample.edition.log', 'sample',
        'Edition log', readonly=True)

    @classmethod
    def __register__(cls, module_name):
        cursor = Transaction().connection.cursor()
        table_h = cls.__table_handler__(module_name)
        sample = cls.__table__()

        super().__register__(module_name)

        if table_h.column_exist('changed_oil'):
            cursor.execute(*sample.update([sample.oil_changed],
                [Case((sample.changed_oil == Literal(True),
                    'yes'), else_='no')]))
            table_h.drop_column('changed_oil')
        if table_h.column_exist('changed_oil_filter'):
            cursor.execute(*sample.update([sample.oil_filter_changed],
                [Case((sample.changed_oil_filter == Literal(True),
                    'yes'), else_='no')]))
            table_h.drop_column('changed_oil_filter')
        if table_h.column_exist('changed_air_filter'):
            cursor.execute(*sample.update([sample.air_filter_changed],
                [Case((sample.changed_air_filter == Literal(True),
                    'yes'), else_='no')]))
            table_h.drop_column('changed_air_filter')
        if table_h.column_exist('hours_equipment'):
            cursor.execute(*sample.update([sample.ind_equipment],
                [sample.hours_equipment]))
            table_h.drop_column('hours_equipment')
        if table_h.column_exist('hours_component'):
            cursor.execute(*sample.update([sample.ind_component],
                [sample.hours_component]))
            table_h.drop_column('hours_component')
        if table_h.column_exist('hours_oil'):
            cursor.execute(*sample.update([sample.ind_oil],
                [sample.hours_oil]))
            table_h.drop_column('hours_oil')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.product_type.states['readonly'] = Bool(Eval('component'))
        if 'component' not in cls.product_type.depends:
            cls.product_type.depends.append('component')
        cls.matrix.states['readonly'] = Bool(Eval('comercial_product'))
        if 'comercial_product' not in cls.matrix.depends:
            cls.matrix.depends.append('comercial_product')
        cls.attributes.domain = [('id', 'in', Eval('attributes_domain'))]
        if 'attributes_domain' not in cls.attributes.depends:
            cls.attributes.depends.append('attributes_domain')

    @staticmethod
    def default_ind_equipment_uom():
        return 'hs'

    @staticmethod
    def default_ind_component_uom():
        return 'hs'

    @staticmethod
    def default_ind_oil_uom():
        return 'hs'

    @fields.depends('equipment', 'component')
    def on_change_equipment(self):
        if not self.equipment and self.component:
            self.component = None

    @fields.depends('component')
    def on_change_component(self):
        if self.component:
            if self.component.product_type:
                self.product_type = self.component.product_type.id
            if self.component.comercial_product:
                self.comercial_product = self.component.comercial_product.id
                self.on_change_comercial_product()

    @fields.depends('comercial_product')
    def on_change_comercial_product(self):
        if self.comercial_product and self.comercial_product.matrix:
            self.matrix = self.comercial_product.matrix.id

    @fields.depends('product_type', '_parent_product_type.attribute_set')
    def on_change_with_attributes_domain(self, name=None):
        pool = Pool()
        SampleAttributeAttributeSet = pool.get(
            'lims.sample.attribute-attribute.set')
        attribute_set = None
        if self.product_type and self.product_type.attribute_set:
            attribute_set = self.product_type.attribute_set.id
        res = SampleAttributeAttributeSet.search([
            ('attribute_set', '=', attribute_set),
            ])
        return [x.attribute.id for x in res]

    @classmethod
    def get_plant(cls, samples, name):
        result = {}
        for s in samples:
            result[s.id] = s.equipment and s.equipment.plant.id or None
        return result

    @classmethod
    def search_plant(cls, name, clause):
        return [('equipment.plant',) + tuple(clause[1:])]

    def _order_equipment_field(name):
        def order_field(tables):
            Equipment = Pool().get('lims.equipment')
            field = Equipment._fields[name]
            table, _ = tables[None]
            equipment_tables = tables.get('equipment')
            if equipment_tables is None:
                equipment = Equipment.__table__()
                equipment_tables = {
                    None: (equipment, equipment.id == table.equipment),
                    }
                tables['equipment'] = equipment_tables
            return field.convert_order(name, equipment_tables, Equipment)
        return staticmethod(order_field)
    order_plant = _order_equipment_field('plant')

    @classmethod
    def get_equipment_field(cls, samples, names):
        result = {}
        for name in names:
            result[name] = {}
            if cls._fields[name]._type == 'many2one':
                for s in samples:
                    field = getattr(s.equipment, name.replace(
                        'equipment_', ''), None)
                    result[name][s.id] = field.id if field else None
            else:
                for s in samples:
                    result[name][s.id] = getattr(s.equipment, name.replace(
                        'equipment_', ''), None)
        return result

    @classmethod
    def _confirm_samples(cls, samples):
        TaskTemplate = Pool().get('lims.administrative.task.template')
        for sample in samples:
            if not sample.component or not sample.comercial_product:
                continue
            if sample.component.comercial_product != sample.comercial_product:
                sample.component.comercial_product = sample.comercial_product
                sample.component.save()
        TaskTemplate.create_tasks('sample_missing_data',
            cls._for_task_missing_data(samples))
        TaskTemplate.create_tasks('sample_insufficient_volume',
            cls._for_task_required_volume(samples))

    @classmethod
    def _for_task_missing_data(cls, samples):
        AdministrativeTask = Pool().get('lims.administrative.task')
        res = []
        for sample in samples:
            if not sample.missing_data:
                continue
            if AdministrativeTask.search([
                    ('type', '=', 'sample_missing_data'),
                    ('origin', '=', '%s,%s' % (cls.__name__, sample.id)),
                    ('state', 'not in', ('done', 'discarded')),
                    ]):
                continue
            res.append(sample)
        return res

    @classmethod
    def _for_task_required_volume(cls, samples):
        pool = Pool()
        EntryDetailAnalysis = pool.get('lims.entry.detail.analysis')
        AdministrativeTask = pool.get('lims.administrative.task')
        res = []
        for sample in samples:
            received_volume = sample.ind_volume or 0
            analysis_detail = EntryDetailAnalysis.search([
                ('sample', '=', sample.id)])
            for detail in analysis_detail:
                received_volume -= (detail.analysis.ind_volume or 0)
            if received_volume >= 0:
                continue
            if AdministrativeTask.search([
                    ('type', '=', 'sample_insufficient_volume'),
                    ('origin', '=', '%s,%s' % (cls.__name__, sample.id)),
                    ('state', 'not in', ('done', 'discarded')),
                    ]):
                continue
            res.append(sample)
        return res

    @classmethod
    def delete(cls, samples):
        AdministrativeTask = Pool().get('lims.administrative.task')
        for sample in samples:
            tasks = AdministrativeTask.search([
                ('origin', '=', '%s,%s' % (cls.__name__, sample.id)),
                ('state', 'not in', ('done', 'discarded')),
                ])
            if tasks:
                AdministrativeTask.write(tasks, {'state': 'draft'})
                AdministrativeTask.delete(tasks)
        super().delete(samples)


class SampleEditionLog(ModelSQL, ModelView):
    'Sample Edition Log'
    __name__ = 'lims.sample.edition.log'

    create_date2 = fields.Function(fields.DateTime('Created at'),
       'get_create_date2', searcher='search_create_date2')
    sample = fields.Many2One('lims.sample', 'Sample', required=True,
        ondelete='CASCADE', select=True, readonly=True)
    field = fields.Selection([
        ('party', 'Party'),
        ('equipment', 'Equipment'),
        ('component', 'Component'),
        ('product_type', 'Product type'),
        ('comercial_product', 'Comercial Product'),
        ('matrix', 'Matrix'),
        ], 'Field', readonly=True)
    initial_value = fields.Text('Initial value', readonly=True)
    final_value = fields.Text('Final value', readonly=True)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('create_date', 'ASC'))

    def get_create_date2(self, name):
        return self.create_date.replace(microsecond=0)

    @classmethod
    def search_create_date2(cls, name, clause):
        cursor = Transaction().connection.cursor()
        operator_ = clause[1:2][0]
        cursor.execute('SELECT id '
                'FROM "' + cls._table + '" '
                'WHERE create_date' + operator_ + ' %s',
                clause[2:3])
        return [('id', 'in', [x[0] for x in cursor.fetchall()])]

    @classmethod
    def order_create_date2(cls, tables):
        return cls.create_date.convert_order('create_date', tables, cls)


class Fraction(metaclass=PoolMeta):
    __name__ = 'lims.fraction'

    equipment = fields.Function(fields.Many2One('lims.equipment', 'Equipment'),
        'get_sample_field', searcher='search_sample_field')
    component = fields.Function(fields.Many2One('lims.component', 'Component'),
        'get_sample_field', searcher='search_sample_field')
    comercial_product = fields.Function(fields.Many2One(
        'lims.comercial.product', 'Comercial Product'),
        'get_sample_field', searcher='search_sample_field')
    ind_component = fields.Function(fields.Integer('Hs/Km Component'),
        'get_sample_field', searcher='search_sample_field')

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
    order_equipment = _order_sample_field('equipment')
    order_component = _order_sample_field('component')
    order_comercial_product = _order_sample_field('comercial_product')
    order_ind_component = _order_sample_field('ind_component')


class FractionType(metaclass=PoolMeta):
    __name__ = 'lims.fraction.type'

    default_sampling_type = fields.Many2One('lims.sampling.type',
        'Default Sampling Type')


class CreateSampleStart(metaclass=PoolMeta):
    __name__ = 'lims.create_sample.start'

    ind_required = fields.Function(fields.Boolean('Industry required'),
        'on_change_with_ind_required')
    equipment = fields.Many2One('lims.equipment', 'Equipment',
        domain=[('party', '=', Eval('party'))],
        states={'required': Bool(Eval('ind_required'))},
        context={'party': Eval('party')},
        depends=['party', 'ind_required'])
    component = fields.Many2One('lims.component', 'Component',
        domain=[('equipment', '=', Eval('equipment'))],
        states={'required': Bool(Eval('ind_required'))},
        depends=['equipment', 'ind_required'])
    comercial_product = fields.Many2One('lims.comercial.product',
        'Comercial Product', depends=['ind_required'],
        states={'required': Bool(Eval('ind_required'))})
    label = fields.Char('Label')
    ind_sampling_date = fields.Date('Sampling date')
    ind_volume = fields.Float('Received volume', depends=['ind_required'],
        states={'required': Bool(Eval('ind_required'))})
    sampling_type = fields.Many2One('lims.sampling.type',
        'Sampling Type', depends=['ind_required'],
        states={'required': Bool(Eval('ind_required'))})
    ind_operational_detail = fields.Text('Operational detail')
    ind_work_environment = fields.Text('Work environment')
    ind_analysis_reason = fields.Text('Reason for analysis')
    missing_data = fields.Boolean('Missing data')
    attributes_domain = fields.Function(fields.Many2Many(
        'lims.sample.attribute', None, None, 'Attributes domain'),
        'on_change_with_attributes_domain')
    sample_photo = fields.Binary('Sample Photo')
    label_photo = fields.Binary('Label Photo')
    oil_added = fields.Float('Liters Oil added')
    ind_equipment = fields.Integer('Equipment')
    ind_equipment_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    ind_component = fields.Integer('Component')
    ind_component_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    ind_oil = fields.Integer('Oil')
    ind_oil_uom = fields.Selection([
        ('hs', 'Hs.'),
        ('km', 'Km.'),
        ], 'UoM', sort=False)
    oil_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Oil?', sort=False)
    oil_filter_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Oil Filter?', sort=False)
    air_filter_changed = fields.Selection([
        (None, '-'),
        ('yes', 'Yes'),
        ('no', 'No'),
        ], 'Did change Air Filter?', sort=False)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        for field in ('component', 'comercial_product'):
            cls.analysis_domain.on_change_with.add(field)
        cls.product_type.states['readonly'] = Bool(Eval('component'))
        if 'component' not in cls.product_type.depends:
            cls.product_type.depends.append('component')
        cls.matrix.states['readonly'] = Bool(Eval('comercial_product'))
        if 'comercial_product' not in cls.matrix.depends:
            cls.matrix.depends.append('comercial_product')
        cls.attributes.domain = [('id', 'in', Eval('attributes_domain'))]
        if 'attributes_domain' not in cls.attributes.depends:
            cls.attributes.depends.append('attributes_domain')
        cls.sample_client_description.required = False

    @staticmethod
    def default_ind_equipment_uom():
        return 'hs'

    @staticmethod
    def default_ind_component_uom():
        return 'hs'

    @staticmethod
    def default_ind_oil_uom():
        return 'hs'

    @fields.depends('fraction_type')
    def on_change_with_ind_required(self, name=None):
        Config = Pool().get('lims.configuration')
        if self.fraction_type:
            if self.fraction_type == Config(1).mcl_fraction_type:
                return True
        return False

    @fields.depends('component')
    def on_change_component(self):
        if self.component:
            if self.component.product_type:
                self.product_type = self.component.product_type.id
            if self.component.comercial_product:
                self.comercial_product = self.component.comercial_product.id
                self.on_change_comercial_product()

    @fields.depends('comercial_product')
    def on_change_comercial_product(self):
        if self.comercial_product and self.comercial_product.matrix:
            self.matrix = self.comercial_product.matrix.id

    @fields.depends('product_type', 'component',
        '_parent_product_type.attribute_set')
    def on_change_with_attributes_domain(self, name=None):
        pool = Pool()
        SampleAttributeAttributeSet = pool.get(
            'lims.sample.attribute-attribute.set')
        attribute_set = None
        if self.product_type and self.product_type.attribute_set:
            attribute_set = self.product_type.attribute_set.id
        res = SampleAttributeAttributeSet.search([
            ('attribute_set', '=', attribute_set),
            ])
        return [x.attribute.id for x in res]

    @fields.depends('label')
    def on_change_label(self):
        self.labels = self.label

    @fields.depends('packages_quantity', 'package_type')
    def on_change_with_ind_volume(self, name=None):
        if (self.packages_quantity and
                self.package_type and self.package_type.capacity):
            return (self.packages_quantity * self.package_type.capacity)
        return None

    @fields.depends('fraction_type', 'sampling_type')
    def on_change_fraction_type(self):
        super().on_change_fraction_type()
        if not self.fraction_type:
            return
        if (not self.sampling_type and
                self.fraction_type.default_sampling_type):
            self.sampling_type = self.fraction_type.default_sampling_type


class CreateSample(metaclass=PoolMeta):
    __name__ = 'lims.create_sample'

    start = StateView('lims.create_sample.start',
        'lims.lims_create_sample_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Create same Equipment', 'create_continue', 'tryton-ok'),
            Button('Create', 'create_', 'tryton-ok', default=True),
            ])
    create_continue = StateTransition()

    def default_start(self, fields):
        defaults = super().default_start(fields)
        for field in ('storage_location', 'equipment'):
            if (hasattr(self.start, field) and getattr(self.start, field)):
                defaults[field] = getattr(self.start, field).id
        for field in ('ind_equipment', 'ind_equipment_uom'):
            if (hasattr(self.start, field) and getattr(self.start, field)):
                defaults[field] = getattr(self.start, field)
        return defaults

    def _get_samples_defaults(self, entry_id):
        samples_defaults = super()._get_samples_defaults(entry_id)

        equipment_id = None
        if (hasattr(self.start, 'equipment') and
                getattr(self.start, 'equipment')):
            equipment_id = getattr(self.start, 'equipment').id
        component_id = None
        if (hasattr(self.start, 'component') and
                getattr(self.start, 'component')):
            component_id = getattr(self.start, 'component').id
        comercial_product_id = None
        if (hasattr(self.start, 'comercial_product') and
                getattr(self.start, 'comercial_product')):
            comercial_product_id = getattr(self.start, 'comercial_product').id
        sampling_type_id = None
        if (hasattr(self.start, 'sampling_type') and
                getattr(self.start, 'sampling_type')):
            sampling_type_id = getattr(self.start, 'sampling_type').id
        ind_sampling_date = (hasattr(self.start,
            'ind_sampling_date') and getattr(self.start,
            'ind_sampling_date') or None)
        ind_volume = (hasattr(self.start,
            'ind_volume') and getattr(self.start,
            'ind_volume') or None)
        ind_operational_detail = (hasattr(self.start,
            'ind_operational_detail') and getattr(self.start,
            'ind_operational_detail') or None)
        ind_work_environment = (hasattr(self.start,
            'ind_work_environment') and getattr(self.start,
            'ind_work_environment') or None)
        ind_analysis_reason = (hasattr(self.start,
            'ind_analysis_reason') and getattr(self.start,
            'ind_analysis_reason') or None)
        missing_data = (hasattr(self.start, 'missing_data') and
            getattr(self.start, 'missing_data') or False)
        sample_photo = (hasattr(self.start, 'sample_photo') and
            getattr(self.start, 'sample_photo') or None)
        label_photo = (hasattr(self.start, 'label_photo') and
            getattr(self.start, 'label_photo') or None)
        oil_added = (hasattr(self.start, 'oil_added') and
            getattr(self.start, 'oil_added') or None)
        ind_equipment = (hasattr(self.start, 'ind_equipment') and
            getattr(self.start, 'ind_equipment') or None)
        ind_equipment_uom = (hasattr(self.start, 'ind_equipment_uom') and
            getattr(self.start, 'ind_equipment_uom') or None)
        ind_component = (hasattr(self.start, 'ind_component') and
            getattr(self.start, 'ind_component') or None)
        ind_component_uom = (hasattr(self.start, 'ind_component_uom') and
            getattr(self.start, 'ind_component_uom') or None)
        ind_oil = (hasattr(self.start, 'ind_oil') and
            getattr(self.start, 'ind_oil') or None)
        ind_oil_uom = (hasattr(self.start, 'ind_oil_uom') and
            getattr(self.start, 'ind_oil_uom') or None)
        oil_changed = (hasattr(self.start, 'oil_changed') and
            getattr(self.start, 'oil_changed') or None)
        oil_filter_changed = (hasattr(self.start, 'oil_filter_changed') and
            getattr(self.start, 'oil_filter_changed') or None)
        air_filter_changed = (hasattr(self.start, 'air_filter_changed') and
            getattr(self.start, 'air_filter_changed') or None)
        sample_client_description = (hasattr(self.start,
            'sample_client_description') and getattr(self.start,
            'sample_client_description') or ' ')

        for sample_defaults in samples_defaults:
            sample_defaults['equipment'] = equipment_id
            sample_defaults['component'] = component_id
            sample_defaults['comercial_product'] = comercial_product_id
            sample_defaults['ind_sampling_date'] = ind_sampling_date
            sample_defaults['ind_volume'] = ind_volume
            sample_defaults['sampling_type'] = sampling_type_id
            sample_defaults['ind_operational_detail'] = ind_operational_detail
            sample_defaults['ind_work_environment'] = ind_work_environment
            sample_defaults['ind_analysis_reason'] = ind_analysis_reason
            sample_defaults['missing_data'] = missing_data
            sample_defaults['sample_photo'] = sample_photo
            sample_defaults['label_photo'] = label_photo
            sample_defaults['oil_added'] = oil_added
            sample_defaults['ind_equipment'] = ind_equipment
            sample_defaults['ind_equipment_uom'] = ind_equipment_uom
            sample_defaults['ind_component'] = ind_component
            sample_defaults['ind_component_uom'] = ind_component_uom
            sample_defaults['ind_oil'] = ind_oil
            sample_defaults['ind_oil_uom'] = ind_oil_uom
            sample_defaults['oil_changed'] = oil_changed
            sample_defaults['oil_filter_changed'] = oil_filter_changed
            sample_defaults['air_filter_changed'] = air_filter_changed
            sample_defaults['sample_client_description'] = \
                sample_client_description

        return samples_defaults

    def transition_create_continue(self):
        self.transition_create_()
        return 'start'


class EditSampleStart(ModelView):
    'Edit Samples'
    __name__ = 'lims.sample.edit.start'

    party = fields.Many2One('party.party', 'Party')
    plant = fields.Many2One('lims.plant', 'Plant',
        domain=[('party', '=', Eval('party'))],
        depends=['party'])
    equipment = fields.Many2One('lims.equipment', 'Equipment',
        domain=[('plant', '=', Eval('plant'))],
        depends=['plant'])
    component = fields.Many2One('lims.component', 'Component',
        domain=[('equipment', '=', Eval('equipment'))],
        depends=['equipment'])
    comercial_product = fields.Many2One('lims.comercial.product',
        'Comercial Product')

    @fields.depends('component')
    def on_change_component(self):
        if self.component and self.component.comercial_product:
            self.comercial_product = self.component.comercial_product.id


class EditSample(Wizard):
    'Edit Samples'
    __name__ = 'lims.sample.edit'

    start = StateView('lims.sample.edit.start',
        'lims_industry.edit_sample_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Confirm', 'confirm', 'tryton-ok', default=True),
            ])
    confirm = StateTransition()

    def _get_filtered_samples(self):
        Sample = Pool().get('lims.sample')
        samples = Sample.browse(Transaction().context['active_ids'])
        #return [s for s in samples if s.entry.state == 'draft']
        return samples

    def default_start(self, fields):
        samples = self._get_filtered_samples()
        party_id = None
        for sample in samples:
            if not party_id:
                party_id = sample.party.id
            elif party_id != sample.party.id:
                party_id = None
                break
        return {
            'party': party_id,
            }

    def transition_confirm(self):
        SampleEditionLog = Pool().get('lims.sample.edition.log')

        samples = self._get_filtered_samples()
        samples_to_edit_party = {}
        for sample in samples:
            check_typifications = False
            log = []

            sample_party = sample.party
            if (self.start.party and
                    self.start.party != sample.party):
                sample_party = self.start.party
                log.append({
                    'sample': sample.id,
                    'field': 'party',
                    'initial_value': sample.party.rec_name,
                    'final_value': self.start.party.rec_name,
                    })
                if sample.entry.id not in samples_to_edit_party:
                    samples_to_edit_party[sample.entry.id] = []
                samples_to_edit_party[sample.entry.id].append(sample)

            if (self.start.equipment and
                    self.start.equipment != sample.equipment):
                log.append({
                    'sample': sample.id,
                    'field': 'equipment',
                    'initial_value': (sample.equipment and
                        sample.equipment.rec_name or None),
                    'final_value': self.start.equipment.rec_name,
                    })
                sample.equipment = self.start.equipment
            if (sample.equipment and sample.equipment.party != sample_party):
                raise UserError(gettext(
                    'lims_industry.msg_edit_sample_equipment',
                    sample=sample.rec_name))

            if (self.start.component and
                    self.start.component != sample.component):
                log.append({
                    'sample': sample.id,
                    'field': 'component',
                    'initial_value': (sample.component and
                        sample.component.rec_name or None),
                    'final_value': self.start.component.rec_name,
                    })
                sample.component = self.start.component
                if (self.start.component.product_type and
                        self.start.component.product_type !=
                        sample.product_type):
                    check_typifications = True
                    log.append({
                        'sample': sample.id,
                        'field': 'product_type',
                        'initial_value': sample.product_type.rec_name,
                        'final_value': (
                            self.start.component.product_type.rec_name),
                        })
                    sample.product_type = self.start.component.product_type
            if (sample.component and (not sample.equipment or
                    sample.component.equipment != sample.equipment)):
                raise UserError(gettext(
                    'lims_industry.msg_edit_sample_component',
                    sample=sample.rec_name))

            if (self.start.comercial_product and
                    self.start.comercial_product != sample.comercial_product):
                log.append({
                    'sample': sample.id,
                    'field': 'comercial_product',
                    'initial_value': (sample.comercial_product and
                        sample.comercial_product.rec_name),
                    'final_value': self.start.comercial_product.rec_name,
                    })
                sample.comercial_product = self.start.comercial_product
                if (self.start.comercial_product.matrix and
                        self.start.comercial_product.matrix != sample.matrix):
                    check_typifications = True
                    log.append({
                        'sample': sample.id,
                        'field': 'matrix',
                        'initial_value': sample.matrix.rec_name,
                        'final_value': (
                            self.start.comercial_product.matrix.rec_name),
                        })
                    sample.matrix = self.start.comercial_product.matrix

            if check_typifications:
                self.check_typifications(sample)

            sample.save()
            if log:
                SampleEditionLog.create(log)

            if check_typifications:
                self.update_laboratory_notebook(sample)

        for entry_id, samples_to_edit in samples_to_edit_party.items():
            self._edit_entry_party(entry_id, samples_to_edit)
            self._edit_results_report_party(samples_to_edit)

        return 'end'

    def _edit_entry_party(self, entry_id, samples):
        pool = Pool()
        Config = pool.get('lims.configuration')
        PartyRelation = pool.get('party.relation')
        Sample = pool.get('lims.sample')
        Entry = pool.get('lims.entry')

        entry = Entry(entry_id)
        party_id = self.start.party.id

        if entry.multi_party:
            config_ = Config(1)
            party_domain = [entry.invoice_party.id]
            relations = PartyRelation.search([
                ('to', '=', entry.invoice_party),
                ('type', '=', config_.invoice_party_relation_type)
                ])
            party_domain.extend([r.from_.id for r in relations])
            party_domain = list(set(party_domain))
            if party_id not in party_domain:
                raise UserError(gettext('lims_industry.msg_edit_sample_party'))
            Sample.write(samples, {'party': party_id})
            return

        # Check if all samples from the same entry were selected
        if Sample.search_count([
                ('entry', '=', entry.id),
                ('id', 'not in', [s.id for s in samples]),
                ]) == 0:
            entry.party = party_id
            entry.invoice_party = party_id
            entry.ack_report_format = None
            entry.ack_report_cache = None
            entry.ack_report_cache_id = None
            entry.save()
            Sample.write(samples, {'party': party_id})
        else:
            new_vals = {
                'party': party_id,
                'invoice_party': party_id,
                'samples': [],
                'invoice_contacts': [],
                'report_contacts': [],
                'acknowledgment_contacts': [],
                }

            new_entry, = Entry.copy([entry], new_vals)
            new_entry.state = entry.state
            new_entry.save()
            Sample.write(samples, {'entry': new_entry.id, 'party': party_id})

    def _edit_results_report_party(self, samples):
        cursor = Transaction().connection.cursor()
        pool = Pool()
        Fraction = pool.get('lims.fraction')
        Notebook = pool.get('lims.notebook')
        ResultsSample = pool.get('lims.results_report.version.detail.sample')
        ResultsDetail = pool.get('lims.results_report.version.detail')
        ResultsVersion = pool.get('lims.results_report.version')
        ResultsReport = pool.get('lims.results_report')

        party_id = self.start.party.id

        for sample in samples:
            #if sample.has_results_report:
                #raise UserError(gettext(
                    #'lims_industry.msg_edit_results_report_party',
                    #sample=sample.rec_name))

            cursor.execute('SELECT rv.results_report '
                'FROM "' + ResultsVersion._table + '" rv '
                    'INNER JOIN "' + ResultsDetail._table + '" rd '
                    'ON rv.id =  rd.report_version '
                    'INNER JOIN "' + ResultsSample._table + '" rs '
                    'ON rd.id = rs.version_detail '
                    'INNER JOIN "' + Notebook._table + '" n '
                    'ON n.id = rs.notebook '
                    'INNER JOIN "' + Fraction._table + '" f '
                    'ON f.id = n.fraction '
                'WHERE f.sample = %s '
                    'AND rd.state NOT IN (\'released\', \'annulled\')',
                (str(sample.id),))
            reports_ids = [x[0] for x in cursor.fetchall()]
            if not reports_ids:
                continue
            reports = ResultsReport.browse(reports_ids)
            ResultsReport.write(reports, {'party': party_id})

    def check_typifications(self, sample):
        analysis_domain_ids = self._get_analysis_domain(sample)
        for f in sample.fractions:
            for s in f.services:
                if s.analysis.id not in analysis_domain_ids:
                    raise UserError(gettext('lims.msg_not_typified',
                        analysis=s.analysis.rec_name,
                        product_type=sample.product_type.rec_name,
                        matrix=sample.matrix.rec_name))

    def _get_analysis_domain(self, sample):
        cursor = Transaction().connection.cursor()
        pool = Pool()
        Typification = pool.get('lims.typification')
        CalculatedTypification = pool.get('lims.typification.calculated')
        Analysis = pool.get('lims.analysis')

        if not sample.product_type or not sample.matrix:
            return []

        cursor.execute('SELECT DISTINCT(analysis) '
            'FROM "' + Typification._table + '" '
            'WHERE product_type = %s '
                'AND matrix = %s '
                'AND valid',
            (sample.product_type.id, sample.matrix.id))
        typified_analysis = [a[0] for a in cursor.fetchall()]
        if not typified_analysis:
            return []

        cursor.execute('SELECT DISTINCT(analysis) '
            'FROM "' + CalculatedTypification._table + '" '
            'WHERE product_type = %s '
                'AND matrix = %s',
            (sample.product_type.id, sample.matrix.id))
        typified_sets_groups = [a[0] for a in cursor.fetchall()]

        cursor.execute('SELECT id '
            'FROM "' + Analysis._table + '" '
            'WHERE behavior = \'additional\' '
                'AND state = \'active\'')
        additional_analysis = [a[0] for a in cursor.fetchall()]

        return typified_analysis + typified_sets_groups + additional_analysis

    @classmethod
    def update_laboratory_notebook(self, sample):
        pool = Pool()
        NotebookLine = pool.get('lims.notebook.line')
        Typification = pool.get('lims.typification')

        lines_to_update = []
        notebook_lines = NotebookLine.search([
            ('notebook.fraction.sample', '=', sample.id),
            ('annulled', '=', False),
            ('end_date', '=', None),
            ])
        for nl in notebook_lines:
            t = Typification.get_valid_typification(
                sample.product_type.id, sample.matrix.id,
                nl.analysis.id, nl.method.id)
            if not t:
                continue
            nl.initial_concentration = t.initial_concentration
            nl.final_concentration = t.final_concentration
            nl.initial_unit = t.start_uom and t.start_uom.id or None
            nl.final_unit = t.end_uom and t.end_uom.id or None
            nl.detection_limit = t.detection_limit
            nl.quantification_limit = t.quantification_limit
            nl.lower_limit = t.lower_limit
            nl.upper_limit = t.upper_limit
            nl.decimals = t.calc_decimals
            nl.significant_digits = t.significant_digits
            nl.scientific_notation = t.scientific_notation
            nl.report = t.report
            lines_to_update.append(nl)

        if lines_to_update:
            NotebookLine.save(lines_to_update)
