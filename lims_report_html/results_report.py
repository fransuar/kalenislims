# This file is part of lims_report_html module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import os
import operator
from mimetypes import guess_type as mime_guess_type
from binascii import b2a_base64
from functools import partial
from decimal import Decimal
from datetime import date, datetime
from lxml import html as lxml_html
from base64 import b64encode
from babel.support import Translations as BabelTranslations
from jinja2 import contextfilter, Markup
from jinja2 import Environment, FunctionLoader
from io import BytesIO
from PyPDF2 import PdfFileMerger
from PyPDF2.utils import PdfReadError

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Not, Bool
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.tools import file_open
from .generator import PdfGenerator


class ResultsReportVersionDetail(metaclass=PoolMeta):
    __name__ = 'lims.results_report.version.detail'

    template = fields.Many2One('lims.result_report.template',
        'Report Template', domain=[('type', 'in', [None, 'base'])],
        states={'readonly': Eval('state') != 'draft'}, depends=['state'])
    template_type = fields.Function(fields.Selection([
        (None, ''),
        ('base', 'HTML'),
        ('header', 'HTML - Header'),
        ('footer', 'HTML - Footer'),
        ], 'Report Template Type'), 'get_template_type')
    sections = fields.One2Many('lims.results_report.version.detail.section',
        'version_detail', 'Sections')
    previous_sections = fields.Function(fields.One2Many(
        'lims.results_report.version.detail.section', 'version_detail',
        'Previous Sections', domain=[('position', '=', 'previous')]),
        'get_previous_sections', setter='set_previous_sections')
    following_sections = fields.Function(fields.One2Many(
        'lims.results_report.version.detail.section', 'version_detail',
        'Following Sections', domain=[('position', '=', 'following')]),
        'get_following_sections', setter='set_following_sections')
    trend_charts = fields.One2Many(
        'lims.results_report.version.detail.trend.chart',
        'version_detail', 'Trend Charts')
    charts_x_row = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ], 'Charts per Row')
    comments_html = fields.Function(fields.Text('Comments',
        states={'readonly': ~Eval('state').in_(['draft', 'revised'])},
        depends=['state']), 'get_comments', setter='set_comments')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        if 'invisible' in cls.resultrange_origin.states:
            del cls.resultrange_origin.states['invisible']
        if 'required' in cls.resultrange_origin.states:
            del cls.resultrange_origin.states['required']

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//page[@id="comments_html"]', 'states', {
                    'invisible': Not(Bool(Eval('template_type'))),
                    }),
            ('//page[@id="comments"]', 'states', {
                    'invisible': Eval('template_type') == 'base',
                    }),
            ]

    @staticmethod
    def default_charts_x_row():
        return '1'

    def get_template_type(self, name):
        return self.template and self.template.type or None

    @fields.depends('template', '_parent_template.trend_charts',
        '_parent_template.sections', 'sections', 'resultrange_origin')
    def on_change_template(self):
        if (self.template and self.template.resultrange_origin and
                not self.resultrange_origin):
            self.resultrange_origin = self.template.resultrange_origin.id
        if self.template and self.template.trend_charts:
            self.trend_charts = [{
                'chart': c.chart.id,
                'order': c.order,
                } for c in self.template.trend_charts]
            self.charts_x_row = self.template.charts_x_row
        if self.template and self.template.sections:
            sections = {}
            for s in self.sections + self.template.sections:
                sections[s.name] = {
                    'name': s.name,
                    'data': s.data,
                    'data_id': s.data_id,
                    'position': s.position,
                    'order': s.order,
                    }
            self.sections = sections.values()

    def get_previous_sections(self, name):
        return [s.id for s in self.sections if s.position == 'previous']

    @classmethod
    def set_previous_sections(cls, sections, name, value):
        if not value:
            return
        cls.write(sections, {'sections': value})

    def get_following_sections(self, name):
        return [s.id for s in self.sections if s.position == 'following']

    @classmethod
    def set_following_sections(cls, sections, name, value):
        if not value:
            return
        cls.write(sections, {'sections': value})

    @classmethod
    def _get_fields_from_samples(cls, samples, generate_report_form=None):
        pool = Pool()
        Notebook = pool.get('lims.notebook')

        detail_default = super()._get_fields_from_samples(samples,
            generate_report_form)

        result_template = None
        if generate_report_form and generate_report_form.template:
            result_template = generate_report_form.template
        resultrange_origin = None

        for sample in samples:
            nb = Notebook(sample['notebook'])
            if not result_template:
                result_template = cls._get_result_template_from_sample(nb)
            if not resultrange_origin:
                resultrange_origin = nb.fraction.sample.resultrange_origin

        if result_template:
            detail_default['template'] = result_template.id
            if not resultrange_origin:
                resultrange_origin = result_template.resultrange_origin
            if result_template.trend_charts:
                detail_default['trend_charts'] = [('create', [{
                    'chart': c.chart.id,
                    'order': c.order,
                    } for c in result_template.trend_charts])]
                detail_default['charts_x_row'] = (
                    result_template.charts_x_row)
            if result_template.sections:
                detail_default['sections'] = [('create', [{
                    'name': s.name,
                    'data': s.data,
                    'data_id': s.data_id,
                    'position': s.position,
                    'order': s.order,
                    } for s in result_template.sections])]

        if resultrange_origin:
            detail_default['resultrange_origin'] = resultrange_origin.id

        return detail_default

    @classmethod
    def _get_result_template_from_sample(cls, notebook):
        pool = Pool()
        Service = pool.get('lims.service')
        Laboratory = pool.get('lims.laboratory')
        Configuration = pool.get('lims.configuration')

        result_template = notebook.fraction.sample.result_template
        if not result_template:
            ok = True
            services = Service.search([
                ('fraction', '=', notebook.fraction),
                ('analysis.type', '=', 'group'),
                ('annulled', '=', False),
                ])
            for service in services:
                if service.analysis.result_template:
                    if not result_template:
                        result_template = service.analysis.result_template
                    elif result_template != service.analysis.result_template:
                        ok = False
                elif result_template:
                    ok = False
            if not ok:
                result_template = None

        if not result_template:
            laboratory_id = Transaction().context.get(
                'samples_pending_reporting_laboratory', None)
            if laboratory_id:
                laboratory = Laboratory(laboratory_id)
                result_template = laboratory.result_template

        if not result_template:
            config_ = Configuration(1)
            result_template = config_.result_template

        return result_template

    @classmethod
    def _get_fields_not_overwrite(cls):
        fields = super()._get_fields_not_overwrite()
        fields.extend(['template', 'trend_charts', 'charts_x_row',
            'sections', 'resultrange_origin'])
        return fields

    @classmethod
    def _get_fields_from_detail(cls, detail):
        detail_default = super()._get_fields_from_detail(detail)
        if detail.template:
            detail_default['template'] = detail.template.id
        if detail.trend_charts:
            detail_default['trend_charts'] = [('create', [{
                'chart': c.chart.id,
                'order': c.order,
                } for c in detail.trend_charts])]
            detail_default['charts_x_row'] = detail.charts_x_row
        if detail.sections:
            detail_default['sections'] = [('create', [{
                'name': s.name,
                'data': s.data,
                'data_id': s.data_id,
                'position': s.position,
                'order': s.order,
                } for s in detail.sections])]
        return detail_default


class ResultsReportVersionDetailSection(ModelSQL, ModelView):
    'Results Report Version Detail Section'
    __name__ = 'lims.results_report.version.detail.section'
    _order_name = 'order'

    version_detail = fields.Many2One('lims.results_report.version.detail',
        'Report Detail', ondelete='CASCADE', select=True, required=True)
    name = fields.Char('Name', required=True)
    data = fields.Binary('File', filename='name', required=True,
        file_id='data_id', store_prefix='results_report_section')
    data_id = fields.Char('File ID', readonly=True)
    position = fields.Selection([
        ('previous', 'Previous'),
        ('following', 'Following'),
        ], 'Position', required=True)
    order = fields.Integer('Order')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order.insert(0, ('order', 'ASC'))

    @classmethod
    def validate(cls, sections):
        super().validate(sections)
        merger = PdfFileMerger(strict=False)
        for section in sections:
            filedata = BytesIO(section.data)
            try:
                merger.append(filedata)
            except PdfReadError:
                raise UserError(gettext('lims_report_html.msg_section_pdf'))


class ResultsReportVersionDetailTrendChart(ModelSQL, ModelView):
    'Results Report Version Detail Trend Chart'
    __name__ = 'lims.results_report.version.detail.trend.chart'
    _order_name = 'order'

    version_detail = fields.Many2One('lims.results_report.version.detail',
        'Report Detail', ondelete='CASCADE', select=True, required=True)
    chart = fields.Many2One('lims.trend.chart', 'Trend Chart',
        required=True, domain=[('active', '=', True)])
    order = fields.Integer('Order')


class ResultsReportVersionDetailSample(metaclass=PoolMeta):
    __name__ = 'lims.results_report.version.detail.sample'

    trend_charts = fields.Function(fields.Text('Trend Charts'),
        'get_trend_charts')
    attachments = fields.Function(fields.Text('Attachments'),
        'get_attachments')

    def get_trend_charts(self, name):
        pool = Pool()
        OpenTrendChart = pool.get('lims.trend.chart.open', type='wizard')
        ResultReport = pool.get('lims.result_report', type='report')

        if not self.version_detail.trend_charts:
            return ''

        charts = []
        for tc in self.version_detail.trend_charts:
            session_id, _, _ = OpenTrendChart.create()
            open_chart = OpenTrendChart(session_id)
            open_chart.start.chart = tc.chart
            open_chart.start.notebook = self.notebook
            open_chart.transition_compute()
            plot = tc.chart.get_plot(session_id)
            charts.append(plot)

        div_row = '<div style="clear:both;">'
        charts_x_row = int(self.version_detail.charts_x_row) or 1
        if charts_x_row == 1:
            div_col = '<div style="float:left; width:100%;">'
        elif charts_x_row == 2:
            div_col = '<div style="float:left; width:50%;">'
        end_div = '</div>'

        content = '<div>'
        count = 0
        for chart in charts:
            if count == 0:
                content += div_row

            content += div_col
            content += ('<img src="' +
                ResultReport.get_image(chart) +
                '" alt="" style="width:100%;">')
            content += end_div

            count += 1
            if count == charts_x_row:
                content += end_div
                count = 0
        if count != 0:
            content += end_div

        content += end_div
        return content

    def get_trend_charts_odt(self):
        pool = Pool()
        OpenTrendChart = pool.get('lims.trend.chart.open', type='wizard')

        if not self.version_detail.trend_charts:
            return []

        charts = []
        for tc in self.version_detail.trend_charts:
            session_id, _, _ = OpenTrendChart.create()
            open_chart = OpenTrendChart(session_id)
            open_chart.start.chart = tc.chart
            open_chart.start.notebook = self.notebook
            open_chart.transition_compute()
            plot = tc.chart.get_plot(session_id)
            charts.append(plot)
        return charts

    def _get_resource(self, obj):
        return '%s,%s' % (obj.__name__, obj.id)

    def get_attachments(self, name):
        pool = Pool()
        Attachment = pool.get('ir.attachment')
        ResultReport = pool.get('lims.result_report', type='report')

        resources = []
        resources.append(self._get_resource(self))
        resources.append(self._get_resource(self.notebook))
        resources.append(self._get_resource(self.notebook.fraction))
        resources.append(self._get_resource(
            self.notebook.fraction.sample))
        resources.append(self._get_resource(
            self.notebook.fraction.sample.entry))
        for line in self.notebook_lines:
            resources.append(self._get_resource(line))
            resources.append(self._get_resource(line.notebook_line))

        attachments = Attachment.search([
            ('resource', 'in', resources),
            ])

        div_row = '<div>'
        div_col = '<div style="float:left; width:50%;">'
        end_div = '</div>'

        content = '<div>'
        count = 0
        extensions = ['png', 'jpg']
        for attachment in attachments:
            if not any(x in attachment.name.lower() for x in extensions):
                continue

            if count == 0:
                content += div_row

            content += div_col

            if attachment.title:
                content += '<p style="font-size: 6pt;font-family: arial,\
                    helvetica, sans-serif;">%s</p>' % (
                        attachment.title, )

            content += ('<img src="' +
                ResultReport.get_image(attachment.data) +
                '" alt="" style="width:100%;">')
            content += end_div

            count += 1
            if count == 2:
                content += end_div
                count = 0
        if count != 0:
            content += end_div

        content += end_div
        return content


class ResultReport(metaclass=PoolMeta):
    __name__ = 'lims.result_report'

    @classmethod
    def execute(cls, ids, data):
        if len(ids) > 1:
            raise UserError(gettext('lims.msg_multiple_reports'))

        pool = Pool()
        ResultsDetail = pool.get('lims.results_report.version.detail')
        CachedReport = pool.get('lims.results_report.cached_report')

        results_report = ResultsDetail(ids[0])
        if results_report.state == 'annulled':
            raise UserError(gettext('lims.msg_annulled_report'))

        if data is None:
            data = {}
        current_data = data.copy()
        current_data['alt_lang'] = results_report.report_language.code

        template = results_report.template
        if template and template.type == 'base':  # HTML
            result = cls.execute_html_results_report(ids, current_data)
        else:
            current_data['action_id'] = None
            if template and template.report:
                current_data['action_id'] = template.report.id
            result = cls.execute_custom_results_report(ids, current_data)

        cached_reports = CachedReport.search([
            ('version_detail', '=', results_report.id),
            ('report_language', '=', results_report.report_language.id),
            ['OR',
                ('report_cache', '!=', None),
                ('report_cache_id', '!=', None)],
            ])
        if cached_reports:
            result = (cached_reports[0].report_format,
                cached_reports[0].report_cache) + result[2:]

        else:
            if current_data.get('save_cache', False):
                cached_reports = CachedReport.search([
                    ('version_detail', '=', results_report.id),
                    ('report_language', '=',
                        results_report.report_language.id),
                    ])
                if cached_reports:
                    CachedReport.write(cached_reports, {
                        'report_cache': result[1],
                        'report_format': result[0],
                        })
                else:
                    CachedReport.create([{
                        'version_detail': results_report.id,
                        'report_language': results_report.report_language.id,
                        'report_cache': result[1],
                        'report_format': result[0],
                        }])

        return result

    @classmethod
    def execute_custom_results_report(cls, ids, data):
        pool = Pool()
        ActionReport = pool.get('ir.action.report')
        cls.check_access()

        action_id = data.get('action_id')
        if action_id is None:
            action_reports = ActionReport.search([
                ('report_name', '=', cls.__name__),
                ('template_extension', '!=', 'results'),
                ])
            assert action_reports, '%s not found' % cls
            action = action_reports[0]
        else:
            action = ActionReport(action_id)

        records = []
        model = action.model or data.get('model')
        if model:
            records = cls._get_records(ids, model, data)
        oext, content = cls._execute(records, [], data, action)
        if not isinstance(content, str):
            content = bytearray(content) if bytes == str else bytes(content)
        return (oext, content, action.direct_print, action.name)

    @classmethod
    def execute_html_results_report(cls, ids, data):
        pool = Pool()
        ActionReport = pool.get('ir.action.report')
        cls.check_access()

        action_reports = ActionReport.search([
            ('report_name', '=', cls.__name__),
            ('template_extension', '=', 'results'),
            ])
        assert action_reports, '%s not found' % cls
        action = action_reports[0]

        records = []
        model = action.model or data.get('model')
        if model:
            records = cls._get_records(ids, model, data)
        oext, content = cls._execute_html_results_report(records, data, action)
        if not isinstance(content, str):
            content = bytearray(content) if bytes == str else bytes(content)
        return (oext, content, action.direct_print, action.name)

    @classmethod
    def _execute_html_results_report(cls, records, data, action):
        record = records[0]
        template_id, tcontent, theader, tfooter = (
            cls.get_results_report_template(action, record.id))
        context = Transaction().context
        context['template'] = template_id
        if not template_id:
            context['default_translations'] = os.path.join(
                os.path.dirname(__file__), 'report', 'translations')
        with Transaction().set_context(**context):
            content = cls.render_results_report_template(action,
                tcontent, record=record, records=[record],
                data=data)
            header = theader and cls.render_results_report_template(action,
                theader, record=record, records=[record],
                data=data)
            footer = tfooter and cls.render_results_report_template(action,
                tfooter, record=record, records=[record],
                data=data)

        stylesheets = cls.parse_stylesheets(tcontent)
        if theader:
            stylesheets += cls.parse_stylesheets(theader)
        if tfooter:
            stylesheets += cls.parse_stylesheets(tfooter)

        page_orientation = (record.template and
            record.template.page_orientation or 'portrait')

        document = PdfGenerator(content,
            header_html=header, footer_html=footer,
            side_margin=1, extra_vertical_margin=30,
            stylesheets=stylesheets,
            page_orientation=page_orientation).render_html().write_pdf()

        if record.previous_sections or record.following_sections:
            merger = PdfFileMerger(strict=False)
            # Previous Sections
            for section in record.previous_sections:
                filedata = BytesIO(section.data)
                merger.append(filedata)
            # Results Report
            filedata = BytesIO(document)
            merger.append(filedata)
            # Following Sections
            for section in record.following_sections:
                filedata = BytesIO(section.data)
                merger.append(filedata)
            output = BytesIO()
            merger.write(output)
            document = output.getvalue()

        return 'pdf', document

    @classmethod
    def get_results_report_template(cls, action, detail_id):
        ResultsDetail = Pool().get('lims.results_report.version.detail')
        template_id, content, header, footer = None, None, None, None
        detail = ResultsDetail(detail_id)
        if detail.template:
            template_id = detail.template
            content = '<body>%s</body>' % detail.template.content
            header = (detail.template.header and
                '<header id="header">%s</header>' %
                    detail.template.header.content)
            footer = (detail.template.footer and
                '<footer id="footer">%s</footer>' %
                    detail.template.footer.content)
        if not content:
            content = (action.report_content and
                action.report_content.decode('utf-8'))
            if not content:
                raise UserError(gettext('lims_report_html.msg_no_template'))
        return template_id, content, header, footer

    @classmethod
    def render_results_report_template(cls, action, template_string,
            record=None, records=None, data=None):
        User = Pool().get('res.user')
        user = User(Transaction().user)

        if data and data.get('alt_lang'):
            locale = data['alt_lang']
        elif user.language:
            locale = user.language.code
        else:
            locale = Transaction().language
        with Transaction().set_context(locale=locale):
            env = cls.get_results_report_environment()

        report_template = env.from_string(template_string)
        context = cls.get_context(records, [], data)
        context.update({
            'report': action,
            'get_image': cls.get_image,
            'operation': cls.operation,
            })
        res = report_template.render(**context)
        res = cls.parse_images(res)
        # print('TEMPLATE:\n', res)
        return res

    @classmethod
    def get_results_report_environment(cls):
        extensions = ['jinja2.ext.i18n', 'jinja2.ext.autoescape',
            'jinja2.ext.with_', 'jinja2.ext.loopcontrols', 'jinja2.ext.do']
        env = Environment(extensions=extensions,
            loader=FunctionLoader(lambda name: ''))

        env.filters.update(cls.get_results_report_filters())

        locale = Transaction().context.get('locale').split('_')[0]
        translations = TemplateTranslations(locale)
        env.install_gettext_translations(translations)
        return env

    @classmethod
    def get_results_report_filters(cls):
        Lang = Pool().get('ir.lang')

        def module_path(name):
            module, path = name.split('/', 1)
            with file_open(os.path.join(module, path)) as f:
                return 'file://%s' % f.name

        def render(value, digits=2, lang=None, filename=None):
            if value is None or value == '':
                return ''

            if isinstance(value, (float, Decimal)):
                return lang.format('%.*f', (digits, value), grouping=True)

            if isinstance(value, int):
                return lang.format('%d', value, grouping=True)

            if isinstance(value, bool):
                if value:
                    return gettext('lims_report_html.msg_yes')
                return gettext('lims_report_html.msg_no')

            if hasattr(value, 'rec_name'):
                return value.rec_name

            if isinstance(value, date):
                return lang.strftime(value)

            if isinstance(value, datetime):
                return '%s %s' % (lang.strftime(value),
                    value.strftime('%H:%M:%S'))

            if isinstance(value, str):
                return value.replace('\n', '<br/>')

            if isinstance(value, bytes):
                b64_value = b2a_base64(value).decode('ascii')
                mimetype = 'image/png'
                if filename:
                    mimetype = mime_guess_type(filename)[0]
                return ('data:%s;base64,%s' % (mimetype, b64_value)).strip()
            return value

        @contextfilter
        def subrender(context, value, subobj=None):
            _template = context.eval_ctx.environment.from_string(value)
            if subobj:
                new_context = {'subobj': subobj}
                new_context.update(context)
            else:
                new_context = context
            result = _template.render(**new_context)
            if context.eval_ctx.autoescape:
                result = Markup(result)
            return result

        locale = Transaction().context.get('locale').split('_')[0]
        lang, = Lang.search([('code', '=', locale or 'en')])

        return {
            'modulepath': module_path,
            'render': partial(render, lang=lang),
            'subrender': subrender,
            }

    @classmethod
    def parse_images(cls, template_string):
        Attachment = Pool().get('ir.attachment')
        root = lxml_html.fromstring(template_string)
        for elem in root.iter('img'):
            # get image from attachments
            if 'id' in elem.attrib:
                img = Attachment.search([('id', '=', int(elem.attrib['id']))])
                if img:
                    elem.attrib['src'] = cls.get_image(img[0].data)
            # get image from TinyMCE widget
            elif 'data-mce-src' in elem.attrib:
                elem.attrib['src'] = elem.attrib['data-mce-src']
                del elem.attrib['data-mce-src']
            # set width and height in style attribute
            style = elem.attrib.get('style', '')
            if 'width' in elem.attrib:
                style += ' width: %spx;' % str(elem.attrib['width'])
            if 'height' in elem.attrib:
                style += ' height: %spx;' % str(elem.attrib['height'])
            elem.attrib['style'] = style
        return lxml_html.tostring(root).decode()

    @classmethod
    def get_image(cls, image):
        if not image:
            return ''
        b64_image = b64encode(image).decode()
        return 'data:image/png;base64,%s' % b64_image

    @classmethod
    def operation(cls, function, value1, value2):
        return getattr(operator, function)(value1, value2)

    @classmethod
    def parse_stylesheets(cls, template_string):
        Attachment = Pool().get('ir.attachment')
        root = lxml_html.fromstring(template_string)
        res = []
        # get stylesheets from attachments
        elems = root.xpath("//div[@id='tryton_styles_container']/div")
        for elem in elems:
            css = Attachment.search([('id', '=', int(elem.attrib['id']))])
            if not css:
                continue
            res.append(css[0].data)
        return res


class TemplateTranslations:

    def __init__(self, lang='en'):
        self.cache = {}
        self.env = None
        self.current = None
        self.language = lang
        self.template = None
        self.set_language(lang)

    def set_language(self, lang='en'):
        self.language = lang
        if lang in self.cache:
            self.current = self.cache[lang]
            return
        context = Transaction().context
        if context.get('default_translations'):
            default_translations = context['default_translations']
            if os.path.isdir(default_translations):
                self.current = BabelTranslations.load(
                    dirname=default_translations, locales=[lang])
                self.cache[lang] = self.current
        else:
            self.template = context.get('template', -1)

    def ugettext(self, message):
        ReportTemplate = Pool().get('lims.result_report.template')
        if self.current:
            return self.current.ugettext(message)
        elif self.template:
            return ReportTemplate.gettext(self.template, message,
                self.language)
        return message

    def ngettext(self, singular, plural, n):
        ReportTemplate = Pool().get('lims.result_report.template')
        if self.current:
            return self.current.ugettext(singular, plural, n)
        elif self.template:
            return ReportTemplate.gettext(self.template, singular,
                self.language)
        return singular


class GenerateReportStart(metaclass=PoolMeta):
    __name__ = 'lims.notebook.generate_results_report.start'

    template = fields.Many2One('lims.result_report.template',
        'Report Template', domain=[('type', 'in', [None, 'base'])],
        states={'readonly': Bool(Eval('report'))},
        depends=['report'])


class GenerateReport(metaclass=PoolMeta):
    __name__ = 'lims.notebook.generate_results_report'

    def default_start(self, fields):
        pool = Pool()
        Notebook = pool.get('lims.notebook')

        res = super().default_start(fields)
        res['template'] = None

        if res['report']:
            return res

        template = None
        for notebook in Notebook.browse(Transaction().context['active_ids']):
            if not notebook.fraction.sample.result_template:
                continue
            if not template:
                template = notebook.fraction.sample.result_template.id
            elif template != notebook.fraction.sample.result_template.id:
                return res

        res['template'] = template
        return res
