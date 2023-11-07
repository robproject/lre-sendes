%% Stopper Calculations
% -------------------------------------------------------------------------
% This file shows whether the material chosen to be the stopper will hold
% given the highest force requested by the customer, the material strength,
% and the cross sectional area of the material in contact with the system.
% -------------------------------------------------------------------------
% ---------------------------Vessel Force----------------------------------
% _Inputs_
d0=3.505; % diameter of the piston (in)
P=100; % highest desired Pressure(psi) (lbf/in^2)
% _Formulas_
y=Vessel_Force(d0,P);
% _Display_
vF=sprintf('Force of piston on fluid: %g lbf',y);
disp(vF);
% ----------------------- Max Deformation ---------------------------------
% ------------- info used for confirmation ----------------------
% PVC can withstand: 
% - stress of 52 MPa = 7542 psi (lbf/in^2)
% - stress of 14.3 MPa = 2080 psi (lbf/in^2) lowest
% - Young's Modulus of 4.00 GPa = 580151 psi (lbf/in^2)
% ABS can withstand:
% - stress of 28.3 MPa = 4100 psi 
% - Young's Modulus of 2.10 GPa = 304,000 psi
% ---------------------------------------------------------------
% _inputs_
stressPVC=2080; % (psi)
L_PVC=5; % axial length of PVC (in)
E_PVC=580151; % Young's Modulus (psi)
% _Formulas_
PVC_maxDeformation=stressPVC*L_PVC/E_PVC; % (in)

% _inputs_
stressABS=4100; % (psi)
L_ABS=5.75; % axial length of ABS (in)
E_ABS=304000; % Young's modulus (psi)
% _Formulas_
ABS_maxDeformation=stressABS*L_ABS/E_ABS; % (in)

% --------------------- Stopper Calculations ------------------------------
% _inputs_ (PVC)
d2_p=1.33; % outer diameter (in)
d1_p=1.03; % inner diameter (in)
% _formulas_
cSA_p=areaCircle(d2_p)-areaCircle(d1_p); % Cross-Sectional Area acted on
deformation_PVC=y*L_PVC/cSA_p/E_PVC; % deformation of PVC

% _display_
if deformation_PVC < PVC_maxDeformation
    disp('PVC is OK to use');
else
    disp('PVC cannot withstand stress');
end

% _inputs_ (ABS)
d2_a=3; % outer diameter (in)
d1_a=1; % inner diameter (in)
% _formulas_
cSA_a=areaCircle(d2_a)-areaCircle(d1_a); % Cross-Sectional Area acted on
deformation_ABS=y*L_ABS/cSA_a/E_ABS; % deformation of ABS
% _display_
if deformation_ABS < ABS_maxDeformation
    disp('ABS is OK to use');
else
    disp('ABS cannot withstand stress');
end