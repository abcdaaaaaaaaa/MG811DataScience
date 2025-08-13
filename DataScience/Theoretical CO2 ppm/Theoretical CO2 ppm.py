import numpy as np
from decimal import Decimal, getcontext
import plotly.graph_objects as go

getcontext().prec = 200

def interpolate(value, min_value, max_value, target_min, target_max):
    return target_min + (value - min_value) * (target_max - target_min) / (max_value - min_value)

def exponential_interpolate(value, min_value, max_value, target_min, target_max):
    log_min = Decimal(target_min).log10()
    log_max = Decimal(target_max).log10()
    ratio = (value - min_value) / (max_value - min_value)
    log_val = log_min + ratio * (log_max - log_min)
    return (Decimal(10) ** log_val)

E_c = Decimal(6.0)
T = Decimal(298.15)
R = Decimal(8.314)
F = Decimal(96485.0)

coeff = (R * T) / (Decimal(2) * F)

P_co2_min = ((E_c - Decimal(0.1)) / coeff).exp()
P_co2_max = (E_c / coeff).exp()

min_ppm = P_co2_min * Decimal(1e6)
max_ppm = P_co2_max * Decimal(1e6)

min_sensor_value = Decimal(0)
max_sensor_value = Decimal(1)

min_co2_ppm = Decimal(400)
max_co2_ppm = Decimal(1000)

sensor_values = []
ppm_values = []

for sv in np.linspace(0, 1, 1000):
    sensor_value = Decimal(sv)
    V_out = sensor_value / Decimal(10)
    P_co2 = ((E_c - V_out) / coeff).exp()
    ppm = P_co2 * Decimal(1e6)

    current_ppm = round(exponential_interpolate(interpolate(ppm, min_ppm, max_ppm, max_sensor_value, min_sensor_value), min_sensor_value, max_sensor_value, min_co2_ppm, max_co2_ppm))
    if (current_ppm != min_co2_ppm and current_ppm != max_co2_ppm): 
        current_ppm = round(exponential_interpolate(interpolate(ppm, min_ppm, max_ppm, max_sensor_value, min_sensor_value), min_sensor_value, max_sensor_value, min_co2_ppm, max_co2_ppm), 4)

    sensor_values.append(float(sensor_value))
    ppm_values.append(float(current_ppm))

    if current_ppm >= 1000:
        break

fig = go.Figure()
fig.add_trace(go.Scatter(x=sensor_values, y=ppm_values, mode='lines', name="CO₂ PPM"))

fig.update_layout(
    title="MG811 Theoretical CO₂ Analyses",
    xaxis=dict(title='X: SensorValue'),
    yaxis=dict(title='Y: Theoretical CO₂ ppm'),
    template="plotly_dark"
)

fig.write_html("MG811_Theoretical_CO2.html")
