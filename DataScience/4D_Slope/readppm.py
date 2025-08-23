import numpy as np
from scipy.optimize import curve_fit
import pandas as pd

df = pd.read_excel("4D_Datas.xlsx")

selected_gas = input("MG811 gas name (CO2 / C2H5OH / CO / CH4): ")

def roundf(*args):
    return tuple(round(x, 4) for x in args)

def round2(value):
    return round(value, 2)

def yaxb(a, x, b):
    return a * np.power(x, b)

def inverseyaxb(valuea, value, valueb):
    return np.power(value / valuea, 1 / valueb)

def interpolate(x, x0, x1, y0, y1):
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

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

def vals(minval, maxval, count):
    return np.linspace(minval, maxval, count)

def limit(value, minlim, maxlim):
    return np.minimum(np.maximum(value, minlim), maxlim)

def time_curve(x):
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
    
def correction_time(t):
    return t if t < 20 else t % 20.0

def calculate_correction(t):
    temp_corr_a, temp_corr_b = interpolate_from_table(28, temp_data)
    a_corr = (temp_corr_a + 538.2376 + gases['CO2'][0]) / 3
    b_corr = (temp_corr_b + -0.0733 + gases['CO2'][1]) / 3
    return 3500 / inverseyaxb(a_corr, time_curve(t), b_corr)

def emf_from_ppm(temp, rh, ppm, gas_name, t_corr):
    if np.isscalar(temp):
        a_temp, b_temp = interpolate_from_table(temp, temp_data)
    else:
        temp_interp = np.array([interpolate_from_table(t, temp_data) for t in temp])
        a_temp, b_temp = temp_interp[:, 0], temp_interp[:, 1]

    if np.isscalar(rh):
        a_rh, b_rh = interpolate_from_table(rh, rh_data)
    else:
        rh_interp = np.array([interpolate_from_table(r, rh_data) for r in rh])
        a_rh, b_rh = rh_interp[:, 0], rh_interp[:, 1]

    gas_a, gas_b, R2, *_ = gases[gas_name]

    a_avg = (a_temp + a_rh + gas_a * R2) / (2 + R2)
    b_avg = (b_temp + b_rh + gas_b * R2) / (2 + R2)

    if np.isscalar(t_corr):
        correction = calculate_correction(correction_time(t_corr))
    else:
        correction = np.array([calculate_correction(correction_time(t)) for t in t_corr])

    EMF = a_avg * ((ppm / correction) ** b_avg)
    return EMF


def Sensorppm(temp, rh, EMF, gas_name, t_corr, cr_mode):
    if np.isscalar(temp):
        a_temp, b_temp = interpolate_from_table(temp, temp_data)
    else:
        temp_interp = np.array([interpolate_from_table(t, temp_data) for t in temp])
        a_temp, b_temp = temp_interp[:, 0], temp_interp[:, 1]

    if np.isscalar(rh):
        a_rh, b_rh = interpolate_from_table(rh, rh_data)
    else:
        rh_interp = np.array([interpolate_from_table(r, rh_data) for r in rh])
        a_rh, b_rh = rh_interp[:, 0], rh_interp[:, 1]

    gas_a, gas_b, R2, *_ = gases[gas_name]

    a_avg = (a_temp + a_rh + gas_a * R2) / (2 + R2)
    b_avg = (b_temp + b_rh + gas_b * R2) / (2 + R2)

    if (cr_mode):
        if np.isscalar(t_corr):
            correction = calculate_correction(correction_time(t_corr))
        else:
            correction = np.array([calculate_correction(correction_time(t)) for t in t_corr])
    else:
        correction = 1.5371654620976198
    
    ppm = inverseyaxb(a_avg, EMF, b_avg) * correction
    return ppm

def calculate_r2(y, y_pred):
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    return r2

def fit_time_with_r2(x, y):
    popt, _ = curve_fit(lambda x, a, b: yaxb(a, x, b), x, y)
    a, b = popt
    y_pred = yaxb(a, x, b)
    r2 = calculate_r2(y, y_pred)
    return a, b, r2

def fit_daily_sine(t_sec, temps, period=86400.0):
    w = 2*np.pi/period
    t_sec = np.array(t_sec, dtype=float)
    temps = np.array(temps, dtype=float)
    X = np.column_stack([np.ones_like(t_sec), np.sin(w*t_sec), np.cos(w*t_sec)])
    coeffs, *_ = np.linalg.lstsq(X, temps, rcond=None)
    return coeffs[0], coeffs[1], coeffs[2], w

def predict_temp(t, M, C, D, w):
    return M + C*np.sin(w*t) + D*np.cos(w*t)

temp_data = {
    -10: (522.7202, -0.0843),
    0: (517.0238, -0.0833),
    10: (520.9298, -0.0849),
    20: (523.094, -0.0863),
    30: (527.0596, -0.0879),
    50: (527.0802, -0.0891)
}

rh_data = {
    20: (540, -0.07),
    40: (536.8846, -0.0726),
    65: (538.2376, -0.0733),
    85: (529.1227, -0.0717)
}

gases = {
    'CH4':     (326.7924, -0.0017, 1, 100, 1000, 323.217, 324.2145),
    'C2H5OH':  (329.7936, -0.0039, 0.9049, 100, 1000, 320.6234, 323.616),
    'CO':      (422.0278, -0.0481, 0.8772, 100, 10000, 264.1646, 323.616),
    'CO2':     (499.0689, -0.0722, 1, 400, 1000, 303.6658, 324.2145)
}

emf_min = gases[selected_gas][5]
emf_max = gases[selected_gas][6]

time, percentile, temperature, rh = np.array(df["Time"], dtype=float), np.array(df["Per"], dtype=float), np.array(df["Temp"], dtype=float), np.array(df["Rh"], dtype=float)
percentile, temperature, rh = limit(percentile, 0, 100), limit(temperature, -10, 50), limit(rh, 0, 100)
M, C, D, w = fit_daily_sine(time, temperature)
SensorValue = percentile / 100
correction_coefficient = np.array([calculate_correction(correction_time(t)) for t in time])
corrected_time = time if min(time)==1 else (time - min(time)) / 20 + 1
temp_time = np.array([predict_temp(t, M, C, D, w) for t in time])
r2_temp_time = calculate_r2(temperature, temp_time)

a_rh_time, b_rh_time, r2_rh_time = fit_time_with_r2(corrected_time, rh)
a_percentile_time, b_percentile_time, r2_percentile_time = fit_time_with_r2(corrected_time, percentile)

a_rh_time, b_rh_time, r2_rh_time, r2_temp_time = roundf(a_rh_time, b_rh_time, r2_rh_time, r2_temp_time)
a_percentile_time, b_percentile_time, r2_percentile_time = roundf(a_percentile_time, b_percentile_time, r2_percentile_time)

time_surface = vals(min(time), max(time)*2 if min(time)==1 else (max(time)-min(time))*2+min(time), 200)
corrected_time_surface = time_surface if min(time)==1 else (time_surface - min(time)) / 20 + 1
temperature_surface = limit(np.array([predict_temp(t, M, C, D, w) for t in time_surface]), -10, 50)
rh_surface = limit(yaxb(a_rh_time, corrected_time_surface, b_rh_time), 0, 100)
correction_coefficient_surface = np.array([calculate_correction(correction_time(t)) for t in time_surface])
percentile_surface = limit(yaxb(a_percentile_time, corrected_time_surface, b_percentile_time), 0, 100)
SensorValue_surface = percentile_surface / 100

ppm = Sensorppm(temperature, rh, interpolate(SensorValue, 0, 1, emf_max, emf_min), selected_gas, time, True)
false_ppm = Sensorppm(temperature, rh, interpolate(SensorValue, 0, 1, emf_max, emf_min), selected_gas, time, False)
ppm_surface = Sensorppm(temperature_surface, rh_surface, interpolate(SensorValue_surface, 0, 1, emf_max, emf_min), selected_gas, time_surface, True)
false_ppm_surface = Sensorppm(temperature_surface, rh_surface, interpolate(SensorValue_surface, 0, 1, emf_max, emf_min), selected_gas, time_surface, False)

print(f"Gas: {selected_gas} | R²_Per={r2_percentile_time} | R²_Temp={r2_temp_time} | R²_Rh={r2_rh_time}")

for t_val, temp_val, rh_val, sv_val, corr_val in zip(time_surface, temperature_surface, rh_surface, SensorValue_surface, correction_coefficient_surface):
    EMF_input = interpolate(sv_val, 0, 1, emf_max, emf_min)
    ppm_val = Sensorppm(temp_val, rh_val, EMF_input, selected_gas, t_val, True)
    EMF_val = emf_from_ppm(temp_val, rh_val, ppm_val, selected_gas, t_val)
    print(f"t={t_val:.4f}s Sensor={sv_val:.4f} temp={temp_val:.4f} rh={rh_val:.4f} corr={corr_val:.4f} EMF={EMF_val:.4f} ppm={ppm_val:.4f}")
print("")
