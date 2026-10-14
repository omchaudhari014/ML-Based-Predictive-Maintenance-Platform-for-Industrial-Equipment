import sys

with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace FACTOR_MAPPING
old_map = '''FACTOR_MAPPING = {
    'Torque [Nm]': {'label': 'Torque', 'interpretation': 'Elevated mechanical load', 'area': 'drive_assembly', 'area_label': 'Drive / Tool Assembly'},
    'Rotational speed [rpm]': {'label': 'Rotational speed', 'interpretation': 'Rotational stress', 'area': 'spindle', 'area_label': 'Spindle'},
    'Tool wear [min]': {'label': 'Tool wear', 'interpretation': 'Tool degradation', 'area': 'tool_holder', 'area_label': 'Tool Holder'},
    'Air temperature [K]': {'label': 'Air temperature', 'interpretation': 'Ambient thermal stress', 'area': 'coolant_line', 'area_label': 'Coolant Line'},
    'Process temperature [K]': {'label': 'Process temperature', 'interpretation': 'Process thermal stress', 'area': 'motor', 'area_label': 'Drive Motor'}
}'''

new_map = '''FACTOR_MAPPING = {
    'Torque [Nm]': {'label': 'Torque', 'interpretation': 'Elevated mechanical load', 'area': 'drive_assembly', 'area_label': 'Drive / Tool Assembly'},
    'Rotational speed [rpm]': {'label': 'Rotational speed', 'interpretation': 'Rotational stress', 'area': 'spindle', 'area_label': 'Spindle'},
    'Tool wear [min]': {'label': 'Tool wear', 'interpretation': 'Tool degradation', 'area': 'tool_holder', 'area_label': 'Tool Holder'},
    'Air temperature [K]': {'label': 'Air temperature', 'interpretation': 'Ambient thermal stress', 'area': 'coolant_line', 'area_label': 'Coolant Line'},
    'Process temperature [K]': {'label': 'Process temperature', 'interpretation': 'Process thermal stress', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Machine_Family': {'label': 'Machine Type', 'interpretation': 'Inherent design risk', 'area': 'system', 'area_label': 'General System'},
    'Age_Days': {'label': 'Operating Age', 'interpretation': 'General wear and tear', 'area': 'system', 'area_label': 'General System'},
    'Power_kW': {'label': 'Rated Power', 'interpretation': 'Heavy electrical load', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Sensor_Vibration_mm_s': {'label': 'Vibration (mm/s)', 'interpretation': 'Mechanical imbalance or bearing wear', 'area': 'bearing', 'area_label': 'Bearings'},
    'Sensor_Temperature_C': {'label': 'Temperature (C)', 'interpretation': 'Thermal overload', 'area': 'cooling', 'area_label': 'Cooling System'},
    'Sensor_Pressure_bar': {'label': 'Pressure (bar)', 'interpretation': 'Fluid dynamic issues like cavitation', 'area': 'impeller', 'area_label': 'Impeller / Compressor Element'},
    'Sensor_Current_A': {'label': 'Current (A)', 'interpretation': 'Electrical overload', 'area': 'motor', 'area_label': 'Drive Motor'},
    'Sensor_Speed_RPM': {'label': 'Speed (RPM)', 'interpretation': 'Rotational anomaly', 'area': 'shaft', 'area_label': 'Main Shaft'}
}'''
content = content.replace(old_map, new_map)

# Fix analyze loop
old_loop1 = '''        for i, col in enumerate(FEATURE_COLS):
            s_val = float(s_vals[i])
            actual_val = float(row[col])
            
            factors.append({
                "feature": col,
                "label": FACTOR_MAPPING[col]['label'],'''

new_loop1 = '''        for i, col in enumerate(FEATURE_COLS):
            s_val = float(s_vals[i])
            try: actual_val = float(row[col])
            except: actual_val = row[col]
            
            factors.append({
                "feature": col,
                "label": FACTOR_MAPPING.get(col, {}).get('label', col),'''
content = content.replace(old_loop1, new_loop1)

# Fix another analyze loop
old_loop2 = '''        for i, col in enumerate(FEATURE_COLS):
            s_val = float(s_vals[i])
            factors.append({
                "feature": col,
                "label": FACTOR_MAPPING[col]['label'],'''

new_loop2 = '''        for i, col in enumerate(FEATURE_COLS):
            s_val = float(s_vals[i])
            factors.append({
                "feature": col,
                "label": FACTOR_MAPPING.get(col, {}).get('label', col),'''
content = content.replace(old_loop2, new_loop2)

# Fix dictionary accesses
content = content.replace("FACTOR_MAPPING[top_factor['feature']]['interpretation']", "FACTOR_MAPPING.get(top_factor['feature'], {}).get('interpretation', 'Unknown issue')")
content = content.replace("FACTOR_MAPPING[top_factor['feature']]['area']", "FACTOR_MAPPING.get(top_factor['feature'], {}).get('area', 'unknown')")
content = content.replace("FACTOR_MAPPING[top_factor['feature']]['area_label']", "FACTOR_MAPPING.get(top_factor['feature'], {}).get('area_label', 'Unknown Area')")

# Fix values float casting
content = content.replace('"{col: float(row[col]) for col in FEATURE_COLS}"', '"{col: (float(row[col]) if pd.api.types.is_numeric_dtype(type(row[col])) else row[col]) for col in FEATURE_COLS}"')

# Also for simulate float casting:
content = content.replace('"{col: float(df_features[col].iloc[0]) for col in FEATURE_COLS}"', '"{col: (float(df_features[col].iloc[0]) if pd.api.types.is_numeric_dtype(type(df_features[col].iloc[0])) else df_features[col].iloc[0]) for col in FEATURE_COLS}"')

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
