%% Main System Run
% -------------------------------------------------------------------------
% This file will run the basic inputs of the system and calculate
% - output fluid flow
% - rate of the piston
% - Force acting on the fluid
% -------------------------------------------------------------------------
% ----------------- Formatting --------------------------------------------
format short
disp('*** Successful Run ***');
% ----------------- Output Fluid Flow -------------------------------------
% _Inputs_
d=0.238; % diameter of the output (in)
P=50; % desired pressure (psi) (lbf/in^2)
density=62.4; % density of fluid (lb/ft^3)
% _Formulas_
rho=density/(12^3); % slug converted to (lb s^2/in^4)
v=sqrt(P/.5/rho);
q=areaCircle(d)*v; % flow (in^3/s)
q=q/231*60; % flow converted to gallons/min
% _Display_
fD=sprintf('Rate of fluid downstream: %g gal/min',q);
disp(fD);
% ----------------- Rate of the Piston ------------------------------------
% _Inputs_
d1=3.505; % diameter of piston
d2=d; % diameter of orifice
% _Formula_
y=pistonRate(d1,d2,v); % in/s
% _Display_
rP=sprintf('Rate of piston: %g in/s',y);
disp(rP);
% ----------------- Force Acting on the Fluid -----------------------------
% _Inputs_
d0=d1; % diameter of the piston
P=P; % desired pressure
% _Formulas_
y=Vessel_Force(d0,P);
% _Display_
pF=sprintf('Piston Force: %g lbf',y);
disp(pF);