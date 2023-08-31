% Uncertainties in the variables using syms

syms Cd D2 D1 Di B rho v xf xi q cP

% Where D2 = orifice diameter, D1 = provided pipe diameter, Di = vessel diameter
% and cP = change in pressure.

Cd = (4/pi)*sqrt(rho/2)*q*D2^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2);
q_sensitivity = (diff(Cd,q)/Cd*q)^2
D2_sensitivity = (diff(Cd,D2)/Cd*D2)^2
B_sensitivity = (diff(Cd,B)/Cd*B)^2
c_P_sensitivity = (diff(Cd,cP)/Cd*cP)^2
rho_sensitivity = (diff(Cd,rho)/Cd*rho)^2
%----------------------------------------------------
% Where q = v * (Area of the vessel)
Cd = sqrt(rho/2)*Di^2*v*D2^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2);
Di_sensitivity = (diff(Cd,Di)/Cd*Di)^2
v_sensitivity = (diff(Cd,v)/Cd*v)^2
%----------------------------------------------------
% Trying the change in positions | Invalid answers
Cd = xf*(Di^2*sqrt(rho/2)*D2^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2))...
    - xi*(Di^2*sqrt(rho/2)*D2^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2));

xf_sensitivity = (diff(Cd,xf)/Cd*xf)^2;
xi_sensitivity = (diff(Cd,xi)/Cd*xi)^2;
simplify(xf_sensitivity)
simplify(xi_sensitivity)
