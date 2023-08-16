model OrificeCD
  // Constants
  import Modelica.Constants.pi;
  parameter Real D1 = 1 "Diameter 1";
  parameter Real D2 = 0.5 "Diameter 2";
  parameter Real rho = 62.4/12^3 "Density";
  parameter Real cyl_area = 2.5^2 * pi "Cylinder Area";

  parameter Real d = D2/D1 "Diameter ratio";

  // Variables
  Real q(start = 0) "Rate of change of potentiometer";
  Real cd(start = 0) "Coefficient of discharge";
  Real P1(start = 0) "US reading";
  Real P2(start = 0) "DS reading";
  Real potentiometer_reading(start = 0) "Potentiometer reading";
  
initial equation
  // Initial conditions can be specified here if needed
  potentiometer_reading = 0; // Initial potentiometer reading
  
equation
  // Define the differential equation for potentiometer_reading.
  // For the sake of this model, we'll assume a constant rate of change.
  // You can modify this to simulate different behaviors.
  der(potentiometer_reading) = .3; // 1 unit/s for demonstration purposes
  
  // Coefficient of discharge calculation
  q = der(potentiometer_reading) * cyl_area;
  cd = q / (pi / 4 * D2^2 * (2 * (P1-P2) / (rho * (1-d^4)))^(1/2));

  // Placeholders for P1 and P2, you can replace these with actual equations or 
  // data sources (e.g., other components in a more complex model).
  P1 = 50; // Placeholder value
  P2 = 14.75; // Placeholder value

end OrificeCD;
