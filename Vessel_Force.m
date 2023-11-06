%% Piston Force on the fluid
% d0 = diameter
% P = pressure 
function y=Vessel_Force(d0,P)
y=P*areaCircle(d0);
end