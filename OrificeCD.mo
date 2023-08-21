model OrificeCD
  // Constants
  import Modelica.Constants.pi;
  import Modelica.Units.SI; // Import the SIunits library
  
  parameter SI.Length D1 = .0254 "Diameter 1"; // 1"
  parameter SI.Length D2 = .01905 "Diameter 2"; // 0.5"
  parameter SI.Density rho = 998 "rho room temp water"; // Density of water at room temperature in kg/m^3
  parameter SI.Area cyl_area = (2.5*2.54/100)^2 * pi "Cylinder Area";

  parameter Real d = D2/D1 "Diameter ratio";

  // Variables
  Real cd(start = 0) "Coefficient of discharge";
  SI.Pressure P1(start = 0) "US reading";
  SI.Pressure P2(start = 0) "DS reading";
  Real potentiometer_reading(start = 0) "Potentiometer reading";
  SI.VolumeFlowRate q(start = 0) "Flow Rate in m3/s";
  
initial equation
  // Initial conditions can be specified here if needed
  potentiometer_reading = 0; // Initial potentiometer reading
  
equation
  // Define the differential equation for potentiometer_reading.
  // For the sake of this model, we'll assume a constant rate of change.
  // You can modify this to simulate different behaviors.
  der(potentiometer_reading) = .609; // m/s
  
  // Coefficient of discharge calculation
  q = der(potentiometer_reading) * cyl_area;
  cd = q / (pi / 4 * D2^2 * (2 * (P1-P2) / (rho * (1-d^4)))^(1/2));

  // Placeholders for P1 and P2, you can replace these with actual equations or 
  // data sources (e.g., other components in a more complex model).
  P1 = 689476; // Placeholder value in Pascals
  P2 = 101697; // Placeholder value in Pascals

end OrificeCD;
