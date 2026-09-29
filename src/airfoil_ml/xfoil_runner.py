import subprocess
from pathlib import Path
import pandas as pd
import warnings

def read_xfoil_result(output_location):
    path = Path(output_location)

    if not path.exists():
        return None

    with path.open("r", encoding="ascii", errors="ignore") as file:
        lines = file.readlines()

    separator_index = next(
        (i for i, line in enumerate(lines)
         if line.strip().startswith("------")),
        None,
    )

    if separator_index is None:
        return None

    data_lines = [
        line.strip()
        for line in lines[separator_index + 1:]
        if line.strip()
    ]

    if not data_lines:
        return None

    values = data_lines[-1].split()

    return {
        "alpha": float(values[0]),
        "CL": float(values[1]),
        "CD": float(values[2]),
        "CDp": float(values[3]),
        "CM": float(values[4]),
        "Top_Xtr": float(values[5]),
        "Bot_Xtr": float(values[6]),
    }

# Flight conditions
reynolds_number = 1e6
mach_number = 0.1
angle_of_attack = 2

# Geometric limits
min_camber = 0             # [%]
max_camber = 9             # [%]
min_camber_position = 1    # [10% chord]
max_camber_position = 9    # [10% chord]
min_thickness = 1          # [%]
max_thickness = 40         # [%]

NACA_indices = []

# Symmetric airfoils
if min_camber == 0:
    for t in range(min_thickness, max_thickness + 1):
        NACA_indices.append(f"00{t:02d}")

# Cambered airfoils
for m in range(max(1, min_camber), max_camber + 1):
    for p in range(min_camber_position, max_camber_position + 1):
        for t in range(min_thickness, max_thickness + 1):
            NACA_indices.append(f"{m}{p}{t:02d}")

# Define entities required for simulation loops
results = []

for i,NACA_index in enumerate(NACA_indices, start=1):
    airfoil_name = f"NACA{NACA_index}"

    print(
        f"[{i}/{len(NACA_indices)}] "
        f"({i / len(NACA_indices) * 100:.1f}%) "
        f"{airfoil_name}")

    output_location = f"data/{airfoil_name}.txt"
    output_path = Path(output_location)

    # Delete old temp file
    if output_path.exists():
        output_path.unlink()

    xfoil_commands = [
        "PLOP",
        "G F",
        "",
        airfoil_name,
        "OPER",
        "VISCOUS",
        str(reynolds_number),
        "MACH",
        str(mach_number),
        "PACC",
        output_location,
        "",
        f"ALFA {angle_of_attack}",
        "",
        "QUIT"
        ]


    xfoil_input = "\n".join(xfoil_commands) # Puts new line between every element -> Empty string becomes empty line -> xfoil sees empty line as pressing enter
    result = subprocess.run(["./xfoil/xfoil.exe"],input=xfoil_input, text=True, capture_output=True)
    xfoil_result = read_xfoil_result(output_location)

    if xfoil_result is None:
        warnings.warn(f"XFOIL did not converge for {airfoil_name}")

    m = int(NACA_index[0]) / 100
    p = int(NACA_index[1]) / 10
    t_c = int(NACA_index[2:4]) / 100

    observation = {
        "naca": NACA_index,
        "m": m,
        "p": p,
        "t_c": t_c,
        "Re": reynolds_number,
        "Mach": mach_number,
        "alpha": angle_of_attack,
        "converged": xfoil_result is not None,
    }

    if xfoil_result is not None:
        observation.update({
            "CL": xfoil_result["CL"],
            "CD": xfoil_result["CD"],
            "CDp": xfoil_result["CDp"],
            "CM": xfoil_result["CM"],
            "Top_Xtr": xfoil_result["Top_Xtr"],
            "Bot_Xtr": xfoil_result["Bot_Xtr"],
        })
    else:
        observation.update({
            "CL": float("nan"),
            "CD": float("nan"),
            "CDp": float("nan"),
            "CM": float("nan"),
            "Top_Xtr": float("nan"),
            "Bot_Xtr": float("nan"),
        })

    results.append(observation)

    # XFOIL file is no longer needed
    output_path.unlink(missing_ok=True)

df = pd.DataFrame(results)
df.to_csv("data/airfoil_data.csv", index=False)

print('Finished')