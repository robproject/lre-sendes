%% Piston Rate 
% d1 diameter of piston
% d2 is diameter of pipe
% v2 rate of the fluid flow
function y = pistonRate(d1,d2,v2) 
y=areaCircle(d2)/areaCircle(d1)*v2; 
end
