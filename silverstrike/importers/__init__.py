from . import dkb, dkb_visa, volksbank, pc_mastercard, ofx

IMPORTERS = [
    pc_mastercard,
    ofx,
    dkb,
    dkb_visa,
    volksbank,
]

IMPORTER_NAMES = [
    'PC MasterCard',
    'OFX Importer',
    'DKB Giro',
    'DKB Visa',
    'Volksbank',
]
