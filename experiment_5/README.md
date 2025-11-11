
# TODO:
 - Swap wavelength calculation for refractive index calculation
    - Implement refractive index calculation method in DataProcessing class
    - Use existing fringe data to compute refractive index instead of wavelength
    - Use baseline measurement in air to determine the difference between known refractive index of air, and that of the air + cuvette. From there, calculate refractive index of cuvette, to then use in further calculations.

 - Create logging module or add detailed console outputs
    - Print fringe regions to console, including center fringe and outer fringes detected
    - Print calculated center fringe position to console
    - Print calculated distance between fringes to console
    - Print calculated angles to console
