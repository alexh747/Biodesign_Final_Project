# Test protocol: triggers batchable_transfers heuristic
#
# The bad pattern: 5 separate aspirate-dispense cycles from one reservoir,
# each delivering 20 µL. Could be replaced with a single 100 µL aspirate
# followed by 5 small dispenses.
#
# Expected analyzer output:
#   - batchable_transfers : FIRES (5 transfers from same source, total 100 µL
#                                  fits in pipette max)

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Batchable Transfers',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate   = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    res     = protocol.load_labware('nest_1_reservoir_195ml', '3')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # 5 transfers, all from the same reservoir well, each going to a
    # distinct destination — perfect candidate for distribute().
    p300.pick_up_tip()
    for dest in ['A1', 'B1', 'C1', 'D1', 'E1']:
        p300.transfer(20.0, res.wells()[0], plate.wells_by_name()[dest], new_tip='never')
    p300.drop_tip()
