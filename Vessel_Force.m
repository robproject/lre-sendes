%% Force acting on the Ram
% This gives the force acting on the fluid from inside the 
% vessel. Nothing needs to be changed.
% -------------------- INPUT -------------------------
P1_lower= 50; % psi % Desired pressure for fluid
P2_higher=100; % psi
d0 = 3.505; % inch % inner diameter of the vessel 
lowForce = P1_lower*areaCircle(d0); % lbf % force needed
highForce = P2_higher*areaCircle(d0); % lbf 