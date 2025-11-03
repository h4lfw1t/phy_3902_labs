def output_power_to_physical_power(output_power, v_supply=12.0, r_heater=15.7):
    """
    Convert output_power (0-255) to actual power in Watts.
    """
    v = output_power * v_supply / 255.0
    i = v / r_heater
    p = v * i
    return p

def calc_specific_heat(energy_joules, mass_grams, delta_t=1.0):
    """
    Calculate specific heat capacity in J/(g*C).
    """
    return energy_joules / (mass_grams * delta_t)