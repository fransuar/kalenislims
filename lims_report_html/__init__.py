# This file is part of lims_report_html module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import action
from . import html_template
from . import configuration
from . import laboratory
from . import party
from . import sample
from . import analysis
from . import results_report
from . import notebook


def register():
    Pool.register(
        action.ActionReport,
        html_template.ReportTemplate,
        html_template.ReportTemplateTranslation,
        html_template.ReportTemplateSection,
        html_template.ReportTemplateTrendChart,
        configuration.Configuration,
        laboratory.Laboratory,
        party.Party,
        sample.Fraction,
        sample.Sample,
        sample.CreateSampleStart,
        analysis.Analysis,
        results_report.ResultsReportVersionDetail,
        results_report.ResultsReportVersionDetailSection,
        results_report.ResultsReportVersionDetailTrendChart,
        results_report.ResultsReportVersionDetailSample,
        results_report.GenerateReportStart,
        notebook.Notebook,
        module='lims_report_html', type_='model')
    Pool.register(
        action.ReportTranslationSet,
        sample.CreateSample,
        results_report.GenerateReport,
        module='lims_report_html', type_='wizard')
    Pool.register(
        results_report.ResultReport,
        module='lims_report_html', type_='report')
