# Test protocol: triggers volume_overflow heuristic
#
# The bad pattern: dispenses 300 µL total (3 x 100 µL) into a single well of
# a 200 µL plate. The well overflows on the third dispense.
#
# Expected analyzer output:
#   - volume_overflow : FIRES (well 2/A1 receives 300 µL into a 200 µL well)

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Volume Overflow',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate   = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    res     = protocol.load_labware('nest_1_reservoir_195ml', '3')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Pour 300 µL total into a 200 µL well — must overflow.
    p300.pick_up_tip()
    for _ in range(3):
        p300.transfer(100.0, res.wells()[0], plate.wells_by_name()['A1'], new_tip='never')
    p300.drop_tip()
