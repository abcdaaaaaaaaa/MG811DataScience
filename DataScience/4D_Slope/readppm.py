import numpy as np

def interpolate(x, x0, x1, y0, y1):
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def exponential_interpolate(value, min_value, max_value, target_min, target_max):
    log_min = np.log10(target_min)
    log_max = np.log10(target_max)
    ratio = (value - min_value) / (max_value - min_value)
    log_val = log_min + ratio * (log_max - log_min)
    return np.power(10, log_val)

def inverseyaxb(valuea, value, valueb):
    return np.power(value / valuea, 1 / valueb)

def yaxb(valuea, value, valueb):
    return valuea * np.power(value, valueb)

def time(x):
    if 0 <= x <= 1:
        return 325.79
    elif 1 < x <= 2:
        return interpolate(x, 1, 2, 325.79, 326.15)
    elif 2 < x <= 3:
        return interpolate(x, 2, 3, 326.15, 325.05)
    elif 3 < x <= 5:
        return interpolate(x, 3, 5, 325.05, 288.06)
    elif 5 < x <= 7:
        return 285.86 + (3.2 * (x - 4) ** -1.0587 - 1)
    elif 7 < x <= 11:
        return 285.86
    elif 11 < x <= 13:
        return 285.86 + (3.2 * (14 - x) ** -1.0587 - 1)
    elif 13 < x <= 15:
        return interpolate(x, 13, 15, 288.06, 319.93)
    elif 15 < x <= 17:
        return 324.87 - (5.94 * (x - 14) ** -1.6218 - 1)
    elif 17 < x <= 19:
        return 324.87
    elif 19 < x <= 20:
        return interpolate(x, 19, 20, 324.87, 325.79)
    else:
        return np.nan

def interpolate_from_table(x, table):
    keys = sorted(table.keys())
    if x <= keys[0]:
        return table[keys[0]]
    elif x >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= x <= keys[i + 1]:
            a0, b0 = table[keys[i]]
            a1, b1 = table[keys[i + 1]]
            a = interpolate(x, keys[i], keys[i + 1], a0, a1)
            b = interpolate(x, keys[i], keys[i + 1], b0, b1)
            return (a, b)



temp = 55
RH = 65
SensorValue = 0.15
t = 9


temp_data = {
    -10: (522.7202, -0.0843),
    0: (517.0238, -0.0833),
    10: (520.9298, -0.0849),
    20: (523.094, -0.0863),
    30: (527.0596, -0.0879),
    50: (527.0802, -0.0891),
}

rh_data = {
    40: (536.8846, -0.0726),
    65: (538.2376, -0.0733),
    85: (529.1227, -0.0717),
}

gases = {
    'CH4':     (326.7924, -0.0017, 1, 323.217, 324.2145),
    'C2H5OH':  (329.7936, -0.0039, 0.9049, 320.6234, 323.616),
    'CO':      (422.0278, -0.0481, 0.8772, 264.1646, 323.616),
    'CO2':     (499.0689, -0.0722, 1, 303.6658, 324.2145),
}

a_temp, b_temp = interpolate_from_table(temp, temp_data)
a_rh, b_rh = interpolate_from_table(RH, rh_data)

temp_corr_a, temp_corr_b = interpolate_from_table(28, temp_data)

a_corr = (temp_corr_a + 538.2376 + gases['CO2'][0]) / 3
b_corr = (temp_corr_b + -0.0733 + gases['CO2'][1]) / 3

correction = 3500 / inverseyaxb(a_corr, time(t), b_corr)
gas_name = 'CO2'
gas_a, gas_b, R2, min_emf, max_emf = gases[gas_name]
EMF = interpolate(SensorValue, 0, 1, max_emf, min_emf)
a_avg = (a_temp + a_rh + gas_a * R2) / (2 + R2)
b_avg = (b_temp + b_rh + gas_b * R2) / (2 + R2)

ppm = inverseyaxb(a_avg, EMF, b_avg) * correction

print(correction)
print(ppm)
