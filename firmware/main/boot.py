# boot.py -- run on boot-up
import esp
import gc

esp.osdebug(None)
gc.collect()