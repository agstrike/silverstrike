from . import dkb, dkb_visa, pc_mastercard, volksbank

IMPORTERS = [
    dkb,
    dkb_visa,
    pc_mastercard,
    volksbank,
]

IMPORTER_NAMES = [
    'DKB Giro',
    'DKB Visa',
    'PC MasterCard',
    'Volksbank',
]

try:
    from . import ofx
    IMPORTERS.append(ofx)
    IMPORTER_NAMES.append('OFX Importer')
except ImportError:
    pass
