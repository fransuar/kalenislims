# This file is part of lims module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .formula_parser import *
from .configuration import *
from .lims import *
from .stock import *
from .product import *
from .party import *
from report import *
from wizard import *


def register():
    Pool.register(
        FormulaParser,
        LimsLaboratory2,
        LimsNotebookView,
        LimsNotebookViewColumn,
        LimsUserRole,
        LimsUserRoleGroup,
        LimsPrinter,
        User,
        LimsUserLaboratory,
        LimsConfiguration,
        LimsConfigurationLaboratory,
        LimsLabWorkYear,
        LimsLabWorkYearSequence,
        LimsLaboratoryProfessional,
        LimsLaboratory,
        LimsLabMethod,
        LimsLabDeviceType,
        LimsLabDevice,
        LimsLabDeviceLaboratory,
        LimsProductType,
        LimsMatrix,
        LimsFormula,
        LimsFractionType,
        LimsLaboratoryCVCorrection,
        LimsFormulaVariable,
        LimsAnalysis,
        LimsTypification,
        LimsTypificationAditional,
        LimsTypificationReadOnly,
        LimsCalculatedTypification,
        LimsCalculatedTypificationReadOnly,
        LimsPackagingType,
        LimsAnalysisIncluded,
        LimsAnalysisDevice,
        LimsCertificationType,
        LimsTechnicalScope,
        LimsTechnicalScopeVersion,
        LimsTechnicalScopeVersionLine,
        LimsPackagingIntegrity,
        LimsEntrySuspensionReason,
        LimsEntry,
        LimsZone,
        LimsVariety,
        LimsSampleProducer,
        LimsSample,
        LimsFraction,
        LimsService,
        LimsConcentrationLevel,
        LimsEntryDetailAnalysis,
        LimsNotebook,
        LimsResultsReport,
        LimsPlanification,
        LimsNotebookLine,
        LimsNotebookLineAllFields,
        LimsNotebookLineProfessional,
        LimsRangeType,
        LimsResultsReportVersion,
        LimsResultsReportVersionDetail,
        LimsResultsReportVersionDetailLine,
        LimsAnalysisFamily,
        LimsAnalysisFamilyCertificant,
        LimsMatrixVariety,
        LimsLabDeviceTypeLabMethod,
        LimsAnalysisLaboratory,
        LimsAnalysisLabMethod,
        LimsNotebookLineLaboratoryProfessional,
        LimsEntryInvoiceContact,
        LimsEntryReportContact,
        LimsEntryAcknowledgmentContact,
        LimsVolumeConversion,
        LimsUomConversion,
        LimsRange,
        LimsControlTendency,
        LimsControlTendencyDetail,
        LimsControlTendencyDetailRule,
        LimsDuplicateSampleStart,
        LimsDuplicateSampleFromEntryStart,
        LimsCopyTypificationStart,
        LimsCopyCalculatedTypificationStart,
        LimsRelateAnalysisStart,
        LimsNotebookInitialConcentrationCalcStart,
        LimsNotebookResultsConversionStart,
        LimsNotebookLimitsValidationStart,
        LimsNotebookInternalRelationsCalc1Start,
        LimsNotebookInternalRelationsCalc1Relation,
        LimsNotebookInternalRelationsCalc1Variable,
        LimsNotebookInternalRelationsCalc2Start,
        LimsNotebookInternalRelationsCalc2Result,
        LimsNotebookInternalRelationsCalc2Relation,
        LimsNotebookInternalRelationsCalc2Variable,
        LimsNotebookInternalRelationsCalc2Process,
        LimsNotebookLoadResultsFormulaStart,
        LimsNotebookLoadResultsFormulaEmpty,
        LimsNotebookLoadResultsFormulaResult,
        LimsNotebookLoadResultsFormulaLine,
        LimsNotebookLoadResultsFormulaAction,
        LimsNotebookLoadResultsFormulaProcess,
        LimsNotebookLoadResultsFormulaVariable,
        LimsNotebookLoadResultsFormulaBeginning,
        LimsNotebookLoadResultsFormulaConfirm,
        LimsNotebookLoadResultsFormulaSit1,
        LimsNotebookLoadResultsFormulaSit2,
        LimsNotebookLoadResultsFormulaSit2Detail,
        LimsNotebookLoadResultsFormulaSit2DetailLine,
        LimsNotebookLoadResultsManualStart,
        LimsNotebookLoadResultsManualEmpty,
        LimsNotebookLoadResultsManualResult,
        LimsNotebookLoadResultsManualLine,
        LimsNotebookLoadResultsManualSit1,
        LimsNotebookLoadResultsManualSit2,
        LimsNotebookAddInternalRelationsStart,
        LimsNotebookAcceptLinesStart,
        LimsNotebookLineRepeatAnalysisStart,
        FractionsByLocationsStart,
        LimsNotebookResultsVerificationStart,
        LimsUncertaintyCalcStart,
        LimsNotebookPrecisionControlStart,
        LimsMeansDeviationsCalcStart,
        LimsMeansDeviationsCalcEmpty,
        LimsMeansDeviationsCalcResult,
        LimsControlResultLine,
        LimsControlResultLineDetail,
        LimsMeansDeviationsCalcResult2,
        LimsTendenciesAnalysisStart,
        LimsTendenciesAnalysisResult,
        LimsDivideReportsResult,
        LimsDivideReportsDetail,
        LimsDivideReportsProcess,
        LimsGenerateResultsReportStart,
        LimsGenerateResultsReportEmpty,
        LimsGenerateResultsReportResultAut,
        LimsGenerateResultsReportResultAutNotebook,
        LimsGenerateResultsReportResultAutNotebookLine,
        LimsGenerateResultsReportResultAutExcludedNotebook,
        LimsGenerateResultsReportResultAutExcludedNotebookLine,
        LimsGenerateResultsReportResultMan,
        LimsDuplicateAnalysisFamilyStart,
        LimsResultsReportAnnulationStart,
        LimsCountersampleStorageStart,
        LimsCountersampleStorageEmpty,
        LimsCountersampleStorageResult,
        LimsCountersampleStorageRevertStart,
        LimsCountersampleStorageRevertEmpty,
        LimsCountersampleStorageRevertResult,
        LimsCountersampleDischargeStart,
        LimsCountersampleDischargeEmpty,
        LimsCountersampleDischargeResult,
        LimsFractionDischargeStart,
        LimsFractionDischargeEmpty,
        LimsFractionDischargeResult,
        LimsFractionDischargeRevertStart,
        LimsFractionDischargeRevertEmpty,
        LimsFractionDischargeRevertResult,
        LimsCreateSampleStart,
        LimsCreateSampleService,
        LimsChangeInvoicePartyStart,
        LimsChangeInvoicePartyError,
        AddTypificationsStart,
        RemoveTypificationsStart,
        ChangeEstimatedDaysForResultsStart,
        LimsCountersampleStoragePrintStart,
        LimsCountersampleDischargePrintStart,
        PrintAnalysisPendingInformStart,
        Location,
        Move,
        ShipmentInternal,
        InventoryLine,
        Uom,
        UomCategory,
        Template,
        Party,
        Address,
        Company,
        PrintAnalysisCheckedPendingInformStart,
        module='lims', type_='model')
    Pool.register(
        LimsPrintAcknowledgmentOfReceipt,
        LimsEntryLabelsPrinter,
        LimsSampleLabelsPrinter,
        LimsPrintControlChart,
        LimsCountersampleStoragePrint,
        LimsCountersampleDischargePrint,
        PrintAnalysisPendingInform,
        LimsDuplicateSample,
        LimsDuplicateSampleFromEntry,
        LimsForwardAcknowledgmentOfReceipt,
        LimsCopyTypification,
        LimsCopyCalculatedTypification,
        LimsRelateAnalysis,
        LimsManageServices,
        LimsCompleteServices,
        LimsNotebookInitialConcentrationCalc,
        LimsNotebookLineInitialConcentrationCalc,
        LimsNotebookResultsConversion,
        LimsNotebookLineResultsConversion,
        LimsNotebookLimitsValidation,
        LimsNotebookLineLimitsValidation,
        LimsNotebookInternalRelationsCalc1,
        LimsNotebookLineInternalRelationsCalc1,
        LimsNotebookInternalRelationsCalc2,
        LimsNotebookLineInternalRelationsCalc2,
        LimsNotebookLoadResultsFormula,
        LimsNotebookLoadResultsManual,
        LimsNotebookAddInternalRelations,
        LimsNotebookAcceptLines,
        LimsNotebookLineAcceptLines,
        LimsNotebookLineUnacceptLines,
        LimsNotebookLineRepeatAnalysis,
        FractionsByLocations,
        LimsNotebookResultsVerification,
        LimsNotebookLineResultsVerification,
        LimsUncertaintyCalc,
        LimsNotebookLineUncertaintyCalc,
        LimsNotebookPrecisionControl,
        LimsNotebookLinePrecisionControl,
        LimsMeansDeviationsCalc,
        LimsTendenciesAnalysis,
        LimsDivideReports,
        LimsGenerateResultsReport,
        LimsPrintResultsReport,
        LimsDuplicateAnalysisFamily,
        LimsServiceResultsReport,
        LimsFractionResultsReport,
        LimsSampleResultsReport,
        LimsResultsReportSample,
        LimsResultsReportAnnulation,
        LimsCountersampleStorage,
        LimsCountersampleStorageRevert,
        LimsCountersampleDischarge,
        LimsFractionDischarge,
        LimsFractionDischargeRevert,
        LimsCreateSample,
        OpenNotebookLines,
        LimsCreateAnalysisProduct,
        LimsChangeInvoiceParty,
        OpenTypifications,
        AddTypifications,
        RemoveTypifications,
        ChangeEstimatedDaysForResults,
        PrintAnalysisCheckedPendingInform,
        module='lims', type_='wizard')
    Pool.register(
        LimsAcknowledgmentOfReceipt,
        LimsEntryDetail,
        LimsEntryLabels,
        LimsControlChartReport,
        LimsResultReport,
        LimsResultReportTranscription,
        LimsGlobalResultReport,
        LimsCountersampleStorageReport,
        LimsCountersampleDischargeReport,
        AnalysisPendingInform,
        AnalysisCheckedPendingInform,
        module='lims', type_='report')
