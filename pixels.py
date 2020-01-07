# Copyright public licence and also I don't care.
# 2020 Josh "NeverCast" Lloyd.

from esp32 import RMT

# The peripheral clock is 80MHz or 12.5 nanoseconds per clock.
# The smallest precision of timing requried for neopixels is
# 0.35us, but I've decided to go with 0.05 microseconds or
# 50 nanoseconds. 50 nanoseconds = 12.5 * 4 clocks.
# By dividing the 80MHz clock by 4 we get a clock every 50 nanoseconds.

# Neopixel timing in RMT clock counts.
T_0H = 35 // 5 # 0.35 microseconds / 50 nanoseconds
T_1H = 70 // 5 # 0.70 microseconds / 50 nanoseconds
T_0L = 80 // 5 # 0.80 microseconds / 50 nanoseconds
T_1L = 60 // 5 # 0.60 microseconds / 50 nanoseconds

# Encoded timings for bits 0 and 1.
D_ZERO = (T_0H, T_0L)
D_ONE = (T_1H, T_1L)

# Reset signal is low for longer than 50 microseconds.
T_RST = 510 // 5 # > 50 microseconds / 50 nanoseconds

class Pixels:
    def __init__(self, pin, pixel_count, rmt_channel=1):
        self.rmt = RMT(rmt_channel, pin, clock_div=4)
        # pixels stores the data sent out via RMT
        self.pixels = [self.encode_pixel(0, 0, 0)] * pixel_count
        # colors is only used for __getitem__
        self.colors = [(0, 0, 0)] * pixel_count

    def encode_pixel(self, r, g, b):
        i_24 = (g & 0xFF) << 16 | (r & 0xFF) << 8 | (b & 0xFF)
        # This can probably be faster or better or something. #VersionZeroPointZero.
        bits = '{0:024b}'.format(i_24)
        bits = map(lambda i: D_ZERO if i == '0' else D_ONE, bits)
        return tuple(clocks for bit in bits for clocks in bit)

    def set(self, pixel, r, g, b):
        self.colors[pixel] = (r, g, b)
        self.pixels[pixel] = self.encode_pixel(r, g, b)

    def write(self):
        # The bus should be idle low ( I think... )
        # So we finish low and start high.
        pulses = tuple()
        for pixel in self.pixels:
            pulses += pixel
        pulses = pulses[:-1] + (T_RST,) # The last low should be long.
        self.rmt.write_pulses(pulses, start=1)

    # pixels[0] = (r, g, b)
    def __setitem__(self, pixel_index, pixel_set):
        self.set(pixel_index, *pixel_set)

    def __getitem__(self, pixel_index):
        return self.colors[pixel_index]
