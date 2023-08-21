%% SenDes Main
%=================================================================
% _Constant Values_
g  = 32.17405*12; % gravity (in/s^2)  
d1 = 1; % pipe size (in)
rho = 62.4/(12*12*12); % density of the fluid (lbs/in^3)
%------------------------------------------------------------------
%_Input values_
prompt = {'Orifice Size:','Pressure 1:','Pressure 2:','fluid flow:'};
dlgtitle = 'Variables';
dims = [1 35];
definputs = {'','','',''}
answer = inputdlg(prompt,dlgtitle,dims,definputs);
UD_Input = cell2struct(answer)
Approach = 'Volume' ;
d2 = 0.25; % orifice size (in) [0.25 & 0.75]
P1 = answer(2,1); % Pressure before orifice (Psi)
P2 = answer(3,1); % Pressure after orifice (Psi) (atmospheric pressure)
v  = 10;    % velocity of fluid
q  = answer(4,1);
%------------------------------------------------------------------
% _Theoretical_
if d2==0.25
    Cd_t=0.60; % engineering toolbox
elseif d2==0.75
    Cd_t=0.75; % engineering toolbox
end
%------------------------------------------------------------------
% Area calculated through a Function
a1 = calcArea(d1);
a2 = calcArea(d2);
bR = a2/a1 ;
%------------------------------------------------------------------
%_flow rates Theoretical_
qDot_t = Cd_t*a2*sqrt((2*(P1-P2))/(rho*(1-bR*bR*bR*bR))); % 'volume'
mDot_t = Cd_t*a2*sqrt((2*g*(P1-P2))/(rho*(1-bR*bR*bR*bR))); % 'mass'
%------------------------------------------------------------------
%_Calculations_
qDot= v*a1; % actual volumetric flow rate (in^3/s) (693 = 3 gal/s)
mDot= v*a1*rho ; % actual mass flow rate
%------------------------------------------------------------------
%_Calculating Cd_
if Approach == 'Volume'
    Cd=(4*q*sqrt(rho*(1-bR*bR*bR*bR)))/(pi*d2*d2*sqrt(2*(P1-P2)));
elseif Approach == 'Mass'
    Cd=(4*m_dot*sqrt(rho*(1-bR*bR*bR*bR)))/(pi*d2*d2*g*sqrt(2*(P1-P2)));
else
    print('enter volume or mass');
end