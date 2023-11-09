%% Stopper Calculations
% -------------------------------------------------------------------------
% This file shows whether the material chosen to be the stopper will hold
% given the highest force requested by the customer, the material strength,
% and the cross sectional area of the material in contact with the system.
% -------------------------------------------------------------------------
% ---------------------------Vessel Force----------------------------------
format short
disp('*** Stopper Calculation Completed ***');
% _Inputs_
d0=3.505; % diameter of the piston (in)
P=50; % highest desired Pressure(psi) (lbf/in^2)
% _Formulas_
y=Vessel_Force(d0,P);
% _Display_
vF=sprintf('Force of piston on fluid: %g lb',y);
disp(vF);
% ----------------------- Max Allowable Force -----------------------------
% ------------- info used for confirmation ----------------------
% PVC can withstand: 
% - Young's Modulus of 441000 psi (lbf/in^2)
% - Poisson's Ratio = 0.4
% ABS can withstand:
% - Young's Modulus of 304,000 psi
% - Poisson's Ratio = 0.37
% Euler's Formula for buckling was used
% ---------------------------------------------------------------
%_ inputs_ (PVC)
d1_p=1.03; % inner diameter (in)
d2_p=1.33; % outer diameter (in)
L=5; % Length of the column
E=441000; % Young's modulus given (matweb)
% _constants_
K=1; % assumed as both ends are fixed
ri=d1_p/2; % inner radius
ro=d2_p/2; % outer radius
% _formula_
I=pi/4*(ro^4-ri^4); % moment of inertia of a hoop
P_cr_PVC=pi^2*E*I/((K*L)^2); % Max force allowable
% _display_
P_cr_P=sprintf('PVC max allowable force: %g lb',P_cr_PVC);
disp(P_cr_P);

%_ inputs_ (ABS)
d1_a=1; % inner diameter (in)
d2_a=3; % outer diameter (in)
L=3; % Length of the column
E=145000; % Young's modulus given (matweb)
% _constants_
K=1; % assumed as both ends are fixed
ri=d1_a/2; % inner radius
ro=d2_a/2; % outer radius
% _formula_
I=pi/4*(ro^4-ri^4); % moment of inertia of a hoop
P_cr_ABS=pi^2*E*I/((K*L)^2); % Max force allowable
% _display_
P_cr_A=sprintf('ABS max allowable force: %g lb',P_cr_ABS);
disp(P_cr_A);

% --------------------- Stopper Calculations ------------------------------

% _display_
if y < P_cr_PVC
    disp('PVC is OK to use');
else
    disp('PVC cannot withstand stress');
end

% _display_
if y < P_cr_ABS
    disp('ABS is OK to use');
else
    disp('ABS cannot withstand stress');
end