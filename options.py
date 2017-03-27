
simulation_mode = False
port_speed = 38400
port = ""
promode = False
elm = None
log = "ddt"
opt_cfc0 = False
opt_n1c = True
log_all = False
auto_refresh = False
elm_failed = False
# KWP2000 Slow init
opt_si=False
report_data=True
ecus_dir="ecus/"
last_error=""


def get_last_error():
    global last_error
    err = last_error
    last_error = ""
    return err
