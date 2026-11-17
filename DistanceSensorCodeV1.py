import time
from collections import deque
import smbus2
import matplotlib.pyplot as plt
import matplotlib.animation as animation

I2C_BUS = 1          # Bus 1 on Raspberry Pi (use bus 1 or 7 on Jetson Orin)
VCNL_ADDR = 0x60     # 7-bit I2C address of VCNL36825T

# Register command codes (confirm exact values in VCNL36825T datasheet Table 1)
REG_PS_CONF1_2 = 0x03
REG_PS_CONF3_4 = 0x04
REG_PS_DATA    = 0xF8  # 16-bit word containing 12-bit proximity count

bus = smbus2.SMBus(I2C_BUS)

def init_sensor():
    # Power on proximity sensor & enable VCSEL current (check datasheet for exact bitmask)
    bus.write_word_data(VCNL_ADDR, REG_PS_CONF1_2, 0x0000)
    bus.write_word_data(VCNL_ADDR, REG_PS_CONF3_4, 0x0800)

def read_proximity():
    raw = bus.read_word_data(VCNL_ADDR, REG_PS_DATA)
    return raw & 0x0FFF  # Mask 12-bit ADC value (0-4095)

init_sensor()

# Rolling buffer of last 100 samples for live plot
history = deque([0]*100, maxlen=100)
fig, ax = plt.subplots()
line, = ax.plot(history, lw=2, label="Proximity Reflection (12-bit)")
ax.axhline(y=500, color='r', linestyle='--', label="Trigger Threshold")
ax.set_ylim(0, 4100)
ax.set_title("Proximity 14 Click (VCNL36825T) Live Link Detection")
ax.set_ylabel("ADC Counts (0 - 4095)")
ax.legend(loc="upper right")

def update(frame):
    val = read_proximity()
    history.append(val)
    line.set_ydata(history)
    return line,

ani = animation.FuncAnimation(fig, update, interval=20, blit=True)
plt.show()