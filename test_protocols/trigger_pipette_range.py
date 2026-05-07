# Test protocol: triggers pipette_range heuristic
#
# The bad pattern: a P300 pipette (accurate range ~20–300 µL) is asked to
# transfer 5 µL — well below its minimum reliable volume.
#
# Expected analyzer output:
#   - pipette_range : SHOULD fire (5 µL is below the P300's 20 µL minimum)
#
# KNOWN BUG: pipette_range.py infers the pipette range from tiprack name
# substrings like "300ul" — but real Opentrons log labware names are
# "Opentrons OT-2 96 Tip Rack 300 µL" (with µ and a space). The current
# regex misses these, so this heuristic may stay silent until the matching
# is fixed. If silent, it confirms the v2 bug.

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Pipette Range',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate   = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    res     = protocol.load_labware('nest_1_reservoir_195ml', '3')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # 5 µL is far below the P300's accurate range of 20–300 µL.
    p300.pick_up_tip()
    p300.transfer(5.0, res.wells()[0], plate.wells_by_name()['A1'], new_tip='never')
    p300.drop_tip()
