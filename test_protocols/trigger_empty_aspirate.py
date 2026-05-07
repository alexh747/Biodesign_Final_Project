# Test protocol: triggers empty_aspirate heuristic
#
# The bad pattern: aspirates 50 µL from a well that is never filled — the
# well's tracked volume is 0 µL, but the protocol asks for 50 µL anyway.
#
# Expected analyzer output:
#   - empty_aspirate : FIRES (aspirate 50 µL from 2/A1 with 0 µL available)

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Empty Aspirate',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate   = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # No source well is ever filled — A1 starts at 0 µL. Aspirating 50 µL is
    # impossible, but the simulator will still emit aspirate/dispense lines.
    p300.pick_up_tip()
    p300.transfer(50.0, plate.wells_by_name()['A1'], plate.wells_by_name()['B1'], new_tip='never')
    p300.drop_tip()
