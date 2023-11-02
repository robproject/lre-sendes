%% Stopper Calculations
% ----------------------inputs --------------------------
d2=3; % outter diameter (in)
d1=1; % inner diameter (in)
% --------------------formulas----------------------------
Vessel_Force
F=highForce; % Force acting on the stopper (lbf)
cSA=areaCircle(d2)-areaCircle(d1); % Cross-Sectional Area acted on
stress=F/cSA; % Calculating stress on the stopper in (psi)

% ------------- info & confirmation ----------------------
% PVC can withstand: 
% - stress of 52 MPa = 7542 psi (lbf/in^2)
% - Young's Modulus of 4.00 GPa = 580151 psi (lbf/in^2)
% ABS can withstand:
% - stress of 28.3 MPa = 4100 psi 
% - Young's Modulus of 2.10 GPa = 304,000 psi

if stress < 7542
    disp('PVC OK');
    if stress < 4100
    disp('ABS OK');
    else
        disp('ABS cannot withstand stress');
    end
else
    disp('PVC and ABS cannot withstand stress');
end

