# Test protocol: triggers tip_rack_exhaustion heuristic
#
# The bad pattern: only one 96-tip rack is loaded, but the protocol asks
# for 100 fresh-tip transfers. The robot would run out of tips at #97.
#
# Expected analyzer output:
#   - tip_rack_exhaustion : SHOULD fire (100 pickups requested, 96 available)
#
# KNOWN LIMITATION: opentrons_simulate stops emitting log lines as soon as
# it raises OutOfTipsError, which means the resulting log file may contain
# only 96 (or fewer) pickup events. The heuristic counts pickups in the
# parsed log, so it sees 96 ≤ 96 and stays silent. To meaningfully test
# this heuristic, you may need to read the raw simulator stderr for an
# "OutOfTipsError" string instead of counting log lines.

from opentrons import protocol_api

metadata = {
    'protocolName': 'Test - Tip Rack Exhaustion',
    'apiLevel': '2.15',
}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    plate1  = protocol.load_labware('nest_96_wellplate_200ul_flat', '2')
    plate2  = protocol.load_labware('nest_96_wellplate_200ul_flat', '4')
    res     = protocol.load_labware('nest_1_reservoir_195ml', '3')
    p300    = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tiprack])

    # Touch every well of plate1 (96) plus the first 4 of plate2 → 100 pickups
    targets = plate1.wells() + plate2.wells()[:4]
    for well in targets:
        p300.transfer(20.0, res.wells()[0], well, new_tip='always')
