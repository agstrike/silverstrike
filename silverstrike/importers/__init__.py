from . import dkb, dkb_visa, pc_mastercard, volksbank, boa, chase

IMPORTERS = [
    dkb,
    dkb_visa,
    pc_mastercard,
    volksbank,
    boa,
    chase,
]

IMPORTER_NAMES = [
    'DKB Giro',
    'DKB Visa',
    'PC MasterCard',
    'Volksbank',
    'Bank of America',
    'Chase',
]

try:
    from . import ofx
    IMPORTERS.append(ofx)
    IMPORTER_NAMES.append('OFX Importer')
except ImportError:
    pass
