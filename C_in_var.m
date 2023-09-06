% Coefficient in Uncertainties of variables

syms Cd D2 D1 Di B rho v xf xi q cP

% Where D2 = orifice diameter, D1 = provided pipe diameter, Di = vessel diameter
% and cP = change in pressure.
% ----------- VOLUME APPROACH -----------------------------
Cd = (4/pi)*sqrt(rho/2)*q*D2^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2);
q_sensitivity = (diff(Cd,q)/Cd*q)^2
D2_sensitivity = (diff(Cd,D2)/Cd*D2)^2
B_sensitivity = (diff(Cd,B)/Cd*B)^2
c_P_sensitivity = (diff(Cd,cP)/Cd*cP)^2
rho_sensitivity = (diff(Cd,rho)/Cd*rho)^2
%--------------------------Beta -----------------------------
B = (D2^2)/(D1^2);
B_sensitivity = (4*B^8)/(B^4 - 1)^2
D1_sensitivity = (diff(B_sensitivity,D1)/B*D1)
D2_sensitivity = (diff(B_sensitivity,D2)/B*D2)

%----------------------------------------------------
% Where q = v * (Area of the vessel)
Cd = sqrt(rho/2)*Di^2*v*D1^(-2)*sqrt(1-(B)^4)*(cP)^(-1/2);
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
%%
%% Volume Approach
syms Cd D2 D1 Di B rho v xf xi q cP tf ti

% Without decomposed dvolume
% vars = [D2, D1, Di, rho, v,  cP];
% Cd = 4(Di/2)^2 v * D2^(-2) * (2* cP * (rho * (1-(D2/D1)^4))^(-1))^(-1/2);

% With decomposed dvolume
vars = [D2, D1, Di, rho, cP, xf, xi, tf, ti];
 Cd = 4*(Di/2)^2 *(xf-xi)/(tf-ti) * D2^(-2) * (2* cP * (rho * (1-(D2/D1)^4))^(-1))^(-1/2);

get_elasticities('Cd', Cd, vars)

