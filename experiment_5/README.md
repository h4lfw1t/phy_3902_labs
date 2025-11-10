
# TODO:
 - Create data processing module for converting csv data to plottable data
    - Functions for converting ldr adc_value to voltage, followed by voltage to intensity, with error (move from intensity_plot.py)
    - Functions for converting stepper motor steps to linear position (move from intensity_plot.py)
    - Transform position data based on calculated center fringe position, to align center fringe at position 0 before plotting
    - Update intensity_plot.py to use data processing module
    - Add method to get distance between fringes based on center fringe position
    - Add method to calculate angle based on fringe distance and experimental setup

 - Create logging module or add detailed console outputs
    - Print fringe regions to console, including center fringe and outer fringes detected
    - Print calculated center fringe position to console
    - Print calculated distance between fringes to console
    - Print calculated angles to console
