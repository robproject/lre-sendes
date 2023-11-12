%% Nominal Values
clearvars; close all; clc;
% UObj(val, absolute_uncertainty) defines an object with properties of
% Value, Uncertainty, and Percentage accessible at UObj.V, UObj.U, and
% UObj.P

% timer and potentiometer uncertainty
timer = 1.6522e-8; % seconds

rho = 1000;

v_in_const = 7.853;
in2m = 1/39.3701;
psi2pa = 6894.76;
p1_slope = .9977953;
p1_offset = -.008752722;
p2_slope = 1.002007;
p2_offset = .1061045;

pd = UObj( 3.505, .002284631); % inches
vx2 = UObj( .000908753, 6.08881e-5); % voltage
vx1 = UObj( .000000001, 6.08881e-5); % voltage
t2 = UObj( 1/267, timer); % 1/267 s = sample period
t1 = UObj( .0000000001, timer *1e-20); % 0s
d2 = UObj( .238, 7.84915e-4); % inches
d1 = UObj( .618, .001129); % inches
vp2 = UObj( 0.471, .007436709); % voltage
vp1 = UObj( 0.9451257, .007120869); % voltage

%% Direct Calculation
% pressure = ((((voltage * 118) - .004) * 12500 * slope) + offset) * psi2pa
% (((volts / ohms) - amps) * psi/amps) * pascals/psi = pascals
pres = @(v_uobj, slope, offset) v_uobj.mul(1/118).add(-.004).mul(12500*slope).add(offset).mul(psi2pa);

p1 = pres(vp1, p1_slope, p1_offset);
p2 = pres(vp2, p2_slope, p2_offset);

% position = voltage * in/v * m/in = m
x1 = vx1.mul(v_in_const).mul(in2m);
x2 = vx2.mul(v_in_const).mul(in2m);

% top left pd/2 ^2 * 4 = m ^2
pd_term = pd.mul(1/2*in2m).pwr(2).mul(4);

% x2-x1, t2-t1, dx/dt = m/s
dx_term = x2.u_sub(x1);
dt_term = t2.u_sub(t1);
dxdt_term = dx_term.u_div(dt_term);


% d2^2 = m^2
d2_term = d2.mul(in2m).pwr(2);

% (p1-p2) * 2 = pa
rad_num = p1.u_sub(p2).mul(2);

% d2/d1 ^ 4 = ratio
beta_term = d2.u_div(d1).pwr(4);
% (1 - beta) * rho
rad_den = UObj(1, 0).u_sub(beta_term).mul(rho);

% sqrt(dp/rho)
rad_term = rad_num.u_div(rad_den).pwr(1/2);

cd_num = pd_term.u_mul(dxdt_term);
cd_den = d2_term.u_mul(rad_term);

CD = cd_num.u_div(cd_den);

fprintf([...
    'Direct CD Value:                  %.3f\n' ...
    'Direct CD Uncertainty:            %.3f\n' ...
    'Direct CD Uncertainty Percentage: %.2f%%\n\n'],...
    CD.V, CD.U, CD.U/CD.V*100)
X1 = x1; X2 = x2; T1 = t1; T2 = t2; P1 = p1; P2 = p2; D1 = d1; D2 = d2; RHO = rho; R = pd.mul(1/2);
vals = [X1.V X2.V T1.V T2.V P1.V P2.V D1.V D2.V RHO R.V];
u_vals = [X1.U X2.U T1.U T2.U P1.U P2.U D1.U D2.U 0 R.U];

figure()
sym_strs = ["x1" "x2" "t1" "t2" "p1" "p2" "d1" "d2" "rho" "r"];
% plotting relative uncertainty per variable
bar(sym_strs,u_vals./vals)
xlabel('Variable')
ylabel('Relative Uncertainty, %')

%% Symbolic Substitution
syms(sym_strs);
sym_chars = [x1 x2 t1 t2 p1 p2 d1 d2 rho r];

umf_syms = sym.empty;
u_propogated = [];

cd = 4 * r^2 * (x2 - x1) / (t2 - t1) * d2^-2 * (2 * (p1 - p2) / (rho * (1- (d2 / d1)^4)))^(-1/2);

for i = 1:length(vals)
    umf_syms(i) = simplify(diff(cd, sym_chars(i)) * sym_chars(i)/cd);
    u_propogated(i) = eval(subs(umf_syms(i), sym_chars, vals)) * u_vals(i)/vals(i);
end



cd_ur = rssq(u_propogated);
cd_v = eval(subs(cd, sym_chars, vals));

fprintf([...
    'Substituted CD Value:             %.3f\n' ...
    'Substituted CD Uncertainty:       %.3f\n' ...
    'Substituted CD Uncertainty Percentage: %.2f%%\n\n'], ...
     cd_v, cd_ur*cd_v, cd_ur*100)

figure()
% plotting relative uncertainty with respect to CD, per variable
bar(sym_strs, u_propogated)
xlabel('Variable')
ylabel('Relative Uncertainty wrt Cd, %')

%% Monte Carlo
cd_vals = zeros(1,10);
iters = 100;
rand_vals = vals + u_vals.*randn(iters,length(vals));
for i=1:iters
    cd_vals(i) = eval(subs(cd, sym_chars, rand_vals(i,:)));
end

fprintf([ ...
    'Monte Carlo CD Value: %.3f\n' ...
    'Monte Carlo CD Uncertainty: %.3f\n' ...
    'Monte Carlo CD Uncertainty Percentage: %.2f%%\n\n'], ...
    mean(cd_vals), std(cd_vals), abs(std(cd_vals)/mean(cd_vals)*100));








