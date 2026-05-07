# Test protocol: triggers tip_waste heuristic
#
# The bad pattern: the loop drops + picks up a fresh tip on every iteration
# even though every transfer aspirates from the same source (the reservoir).
# Each tip change between same-source aspirations is wasted plastic.
#
# Expected analyzer output:
#   - tip_waste     : FIRES (same source, drop_tip between aspirations)
#   - batchable_transfers : may also fire (5 same-source transfers fit one aspirate)

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Tip Waste',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate   = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    res     = protocol.load_labware('nest_1_reservoir_195ml', '3')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Wastefully changes tip between every transfer from the SAME reservoir well
    for dest in ['A1', 'B1', 'C1', 'D1', 'E1']:
        p300.pick_up_tip()
        p300.transfer(50.0, res.wells()[0], plate.wells_by_name()[dest], new_tip='never')
        p300.drop_tip()
