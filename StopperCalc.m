%% Stopper Calculations
% -------------------------------------------------------------------------
% This file shows whether the material chosen to be the stopper will hold
% given the highest force requested by the customer, the material strength,
% and the cross sectional area of the material in contact with the system.
% -------------------------------------------------------------------------
% ---------------------------Vessel Force----------------------------------
% _Inputs_
d0=3.505; % diameter of the piston (in)
P=50; % highest desired Pressure(psi) (lbf/in^2)
% _Formulas_
y=Vessel_Force(d0,P);
% _Display_
vF=sprintf('Force of piston on fluid: %g lbf',y);
disp(vF);
% --------------------- Stopper Calculations ------------------------------
% _inputs_
d2=3; % outter diameter of stopper (in)
d1=1; % inner diameter of stopper (in)
% _formulas_
highForce=y; % Force acting on the stopper (lbf)
cSA=areaCircle(d2)-areaCircle(d1); % Cross-Sectional Area acted on
stress=y/cSA; % Calculating stress on the stopper in (psi)
% _display_
if stress < 7542
    disp('PVC is OK to use');
    if stress < 4100
    disp('ABS is OK to use');
    else
        disp('ABS cannot withstand stress');
    end
else
    disp('PVC and ABS cannot withstand stress');
end

% ------------- info used for confirmation ----------------------
% PVC can withstand: 
% - stress of 52 MPa = 7542 psi (lbf/in^2)
% - Young's Modulus of 4.00 GPa = 580151 psi (lbf/in^2)
% ABS can withstand:
% - stress of 28.3 MPa = 4100 psi 
% - Young's Modulus of 2.10 GPa = 304,000 psi