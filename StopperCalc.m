%% Stopper Calculations

d2=0.0762; % outter diameter m
d1=0.0254 ; % inner diameter m
F=2669 ; % Force acting on the stopper (N)
cSA=areaCircle(d2)-areaCircle(d1); % Cross-Sectional Area
stress=F/cSA; % Calculating stress 

