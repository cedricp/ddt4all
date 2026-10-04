# ============================================================
# Safe session template (DDT2000 .cmd, mod_term format)
# ============================================================
#
# One file per step, in the order that makes the operation reversible.
# The whole session is played as ONE macro (double-click session.cmd):
# the plugin expands the includes, so labels/goto work across the steps.
#
# $addr        : logical address of the ECU (see the ddt4all tables)
# 10C0         : start the diagnostic session
# 1902         : read the fault memory (DTC list)
# 2101         : read the configuration to be modified  <- THE BACKUP
# 2Exxxx       : write the configuration
# 2101         : read the configuration back            <- the verification
# 14           : clear the fault memory
# 1902         : read the fault memory again
#
# The values read in steps 3 and 5 are in the ddt4all journal
# (<ddt4all>/logs/elm_ddt.txt and ecu_ddt.txt): keep them, they are the
# only backup of the original state.
#
# Check the order with:
#     python tools/check_safe_session.py --strict examples/safe_session
# ============================================================

$addr = 26

# --- 1. start the diagnostic session ---------------------------------
include 01_session_start.cmd

# --- 2. read the fault memory (before) -------------------------------
include 02_read_faults.cmd

# --- 3. read the configuration to be modified (BACKUP) ---------------
include 03_read_config.cmd

# --- 4. modify the configuration --------------------------------------
include 04_write_config.cmd

# --- 5. read the current configuration back --------------------------
include 05_read_back.cmd

# --- 6. clear the fault memory ----------------------------------------
include 06_clear_faults.cmd

# --- 7. read the fault memory again -----------------------------------
include 07_read_faults_after.cmd