import subprocess
from pathlib import Path

def xfoil_converged(output_location):
    path = Path(output_location)

    if not path.exists():
        return False

    with path.open("r") as file:
        lines = file.readlines()

    separator_index = next((i for i, line in enumerate(lines)if line.strip().startswith("------")),None,)

    if separator_index is None:
        return False

    return any(line.strip() for line in lines[separator_index + 1:])

# Flight conditions
reynolds_number = 1e6
mach_number = 0.1
angle_of_attack = 2

# Airfoils to analyze
NACA_indices = ["2412","0012","2105"]

for i,NACA_index in enumerate(NACA_indices):
    airfoil_name = f"NACA{NACA_index}"

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
    converged = xfoil_converged(output_location)
    print(airfoil_name)
    print(f"Exit status: {result.returncode}")
    print(f"Converged: {converged}")
    print("-------------------------------------")