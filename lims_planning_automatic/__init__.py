# This file is part of lims_automatic_planning module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import planification
from . import laboratory
from . import entry
from . import sheet
from . import quality


def register():
    Pool.register(
        planification.Planification,
        laboratory.Laboratory,
        entry.Entry,
        sheet.AnalysisSheet,
        module='lims_planning_automatic', type_='model')
    Pool.register(
        quality.QualityTest,
        module='lims_planning_automatic', type_='model',
        depends=['lims_quality_control'])
