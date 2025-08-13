import numpy as np
import plotly.graph_objs as go
import plotly.io as pio

def interpolate(x, x0, x1, y0, y1):
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)

def inverseyaxb(valuea, value, valueb):
    return np.power(value / valuea, 1 / valueb)

def vals(minval, maxval, count):
    return np.linspace(minval, maxval, count)

def limit(value, minlim, maxlim):
    return np.minimum(np.maximum(value, minlim), maxlim)

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

def calculate_correction(t):
    corr_temp, _ = interpolate_from_table(28, temp_data)
    corr_rh, _ = interpolate_from_table(65, rh_data)
    a_corr = (corr_temp + corr_rh + gases['CO2'][0]) / 3
    b_corr = (-0.0863 + -0.0733 + gases['CO2'][1]) / 3
    return 3500 / inverseyaxb(a_corr, time(t), b_corr)

def emf_from_ppm(temp, rh, ppm, gas_name, t):
    a_temp, b_temp = interpolate_from_table(temp, temp_data)
    a_rh, b_rh = interpolate_from_table(rh, rh_data)
    gas_a, gas_b, R2, _, _, _, _ = gases[gas_name]
    a_avg = (a_temp + a_rh + gas_a * R2) / (2 + R2)
    b_avg = (b_temp + b_rh + gas_b * R2) / (2 + R2)
    correction = calculate_correction(t)
    EMF = a_avg * ((ppm / correction) ** b_avg)
    return EMF

def Sensorppm(temp, rh, EMF, gas_name, t):
    a_temp, b_temp = interpolate_from_table(temp, temp_data)
    a_rh, b_rh = interpolate_from_table(rh, rh_data)
    gas_a, gas_b, R2, _, _, _, _ = gases[gas_name]
    a_avg = (a_temp + a_rh + gas_a * R2) / (2 + R2)
    b_avg = (b_temp + b_rh + gas_b * R2) / (2 + R2)
    correction = calculate_correction(t)
    ppm = inverseyaxb(a_avg, EMF, b_avg) * correction
    return ppm

temp_data = {
    -10: (522.7202, -0.0843),
    0: (517.0238, -0.0833),
    10: (520.9298, -0.0849),
    20: (523.094, -0.0863),
    30: (527.0596, -0.0879),
    50: (527.0802, -0.0891),
}

rh_data = {
    20: (540, -0.07),
    40: (536.8846, -0.0726),
    65: (538.2376, -0.0733),
    85: (529.1227, -0.0717),
}

gases = {
    'CH4':     (326.7924, -0.0017, 1, 100, 1000, 323.217, 324.2145),
    'C2H5OH':  (329.7936, -0.0039, 0.9049, 100, 1000, 320.6234, 323.616),
    'CO':      (422.0278, -0.0481, 0.8772, 100, 10000, 264.1646, 323.616),
    'CO2':     (499.0689, -0.0722, 1, 400, 1000, 303.6658, 324.2145)
}

temp_min, temp_max = -10, 50
rh_min, rh_max = 20, 85

temps = vals(temp_min, temp_max, 30)
rhs = vals(rh_min, rh_max, 30)
T, RH = np.meshgrid(temps, rhs)

scene_camera = dict(eye=dict(x=1.5, y=1.5, z=0.01))

t_slider_values = vals(0, 20, 101)

for gas_name in gases:
    fig = go.Figure()
    all_surfaces = []

    for t in t_slider_values:
        EMF_low = limit(emf_from_ppm(temp_min, rh_min, gases[gas_name][3], gas_name, t), gases[gas_name][5], gases[gas_name][6])
        EMF_high = limit(emf_from_ppm(temp_max, rh_max, gases[gas_name][4], gas_name, t), gases[gas_name][5], gases[gas_name][6])
        
        if EMF_low >= EMF_high:
            EMF_low = gases[gas_name][5]

        EMF_values = vals(EMF_low, EMF_high, 30)
        ppm_stack = []

        for emf in EMF_values:
            ppm_grid = np.zeros_like(T)
            for i in range(T.shape[0]):
                for j in range(T.shape[1]):
                    ppm_grid[i, j] = Sensorppm(T[i, j], RH[i, j], emf, gas_name, t)
            ppm_stack.append(ppm_grid)

        all_surfaces.append(ppm_stack)

    initial_z = all_surfaces[0]

    for idx, ppm_grid in enumerate(initial_z):
        emf_min = gases[gas_name][5]
        emf_max = gases[gas_name][6]
        emf = EMF_values[idx]
        SensorValue = interpolate(emf, emf_max, emf_min, 0, 1)
        fig.add_trace(go.Surface(x=T, y=RH, z=ppm_grid, colorscale='Viridis', showscale=False, name=f"Sensor: {SensorValue:.4f}"))

    frames = []
    for idx, t in enumerate(t_slider_values):
        frame_data = []
        ppm_stack = all_surfaces[idx]
        for ppm_grid in ppm_stack:
            frame_data.append(go.Surface(x=T, y=RH, z=ppm_grid, colorscale='Viridis', showscale=False))
        frames.append(go.Frame(data=frame_data, name=str(idx)))

    fig.frames = frames

    steps = []
    for i in range(len(t_slider_values)):
        steps.append(dict(method="animate", args=[[str(i)], {"frame": {"duration": 200, "redraw": True}, "mode": "immediate"}], label=str(round(t_slider_values[i], 1))))

    sliders = [dict(active=0, currentvalue={"prefix": "Time (t): "}, pad={"t": 50}, steps=steps)]
    
    fig.update_layout(
        title=f'MG811: 4D PPM Surface Diagram for {gas_name}',
        scene=dict(
            xaxis_title="Temperature (°C)",
            yaxis_title="RH (%)",
            zaxis_title="PPM Values",
            aspectmode="cube",
            camera=scene_camera
        ),
        sliders=sliders,
        updatemenus=[dict(
            type="buttons",
            direction="left",
            x=0.085,
            y=1.1,
            showactive=False,
            buttons=[
                dict(label="Play",
                     method="animate",
                     args=[None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True, "mode": "immediate"}]),
                dict(label="Pause",
                     method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
            ]
        )],
        template='plotly_dark'
    )

    print(f"{gas_name} html file completed.")

    pio.write_html(fig, file=f"MG811_{gas_name}_ppm.html")
