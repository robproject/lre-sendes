%% Nominal Values ---------------------------------------------------------
clearvars; close all; clc;
% UObj(val, absolute_uncertainty) defines an object with properties of
% Value, Uncertainty, and Percentage accessible at UObj.V, UObj.U, and
% UObj.P

piston_rate = 2.89; % period s, rate in/s

% Array Setup for plotting ------------\
%sample_periods = flip([1/5 1/10 1/20 1/40 1/80 1/160 1/267]); % sample period array
sample_periods = 1./2.^(0:.25:10); % sample period array, generated
percent_cont_array_all = zeros(10, length(sample_periods));
percent_cont_array_x = zeros(1, length(sample_periods));
percent_cont_array_t = percent_cont_array_x;
cd_u_array = percent_cont_array_x;
rel_cont_array_all = percent_cont_array_all;
umf_vals_array = percent_cont_array_all;
urel_array = umf_vals_array;
% -------------------------------------/
for iter=1:length(sample_periods) 
fprintf("Iter: %g \n", iter)

% constants
rho = 1000; % kg/m3
in2m = 0.0254;  % meters per inch
psi2pa = 6894.76;  % pascals per psi

% calibration constants
pot_slope = 7.853; % inches per volt potentiometer calibration

p1_slope = .9977953; % xducer cal sheet - C01AB psi slope
p1_offset = -.008752722; % xducer cal sheet - C01AB psi offset
p1_u = rssq([.000226, .000635]); % linearity and hysteresis
p2_slope = 1.002007; % xducer cal sheet - C30AB psi slope
p2_offset = .1061045; % xducer cal sheet - C30AB psi offset
p2_u = rssq([.000697, .000436]);
xducer_read_range = 200; % psi
xducer_output_range = .020 - .004; % 4-20mA
xducer_nominal_slope = xducer_read_range / xducer_output_range; % 12.5psi/mA

ljtick_gain = 20; % op-amp on ljtick
ljtick_shunt = 5.9; % ohms
ljtick_scalar = ljtick_gain * ljtick_shunt; % resistance; V/I = 118

% sample_period = 1/267; piston_rate = .242637;
%sample_period = 1/267; 


sample_period = sample_periods(iter); piston_rate = 2.89; % simulate multiple periods
fprintf('Sample Rate: %.1f\n', 1/sample_period)
% nominal pot voltage given piston rate and desired sample period
% volts traveled = s * in/s * v/in
pot_dv = @(period, rate) period * rate * 1/pot_slope;
potentiometer_distance_per_sample_as_voltage = pot_dv(sample_period, piston_rate);  
fprintf('Potentiometer dV per sample: %g\n\n', potentiometer_distance_per_sample_as_voltage)

p1_pressure = 50; p2_pressure = 6;
% nominal potentiometer voltages given desired pressures
% ((psi - psi)/scalar * A/psi + A) * V/A
xducer_reading = @(psi, slope, offset) ((psi-offset)/slope /xducer_nominal_slope + .004) * ljtick_scalar;
p1_read = xducer_reading(p1_pressure, p1_slope, p1_offset);
p2_read = xducer_reading(p2_pressure, p2_slope, p2_offset);

% clock tick uncertainty
% u_clock_tick = 1.6522e-8; % for sample period of 1/267 seconds
% UMF for clock tick given sample rate, 
u_clock_scalar = sqrt(sample_period/(1/267));
u_clock_tick = u_clock_scalar *1.6552e-8;

% parameter object initialization: nominal and absolute uncertain values
pd  = UObj( 3.505, .002284631).mul(in2m); % inches -> meters
% voltage, as in middle of range (+.4v) for less relative uncertainty
vx_mxl = 6.08881e-5; % potentiometer uncertainty reading as calced in excel
vx_test = .00011/sqrt(2); % potentiometer uncertainty reading from test
vx2 = UObj( .4+potentiometer_distance_per_sample_as_voltage, vx_test); 
vx1 = UObj( .4, vx_test); % voltage, uses same uncertainty as x1
t2  = UObj( .2+2*sample_period, u_clock_tick); % sample period
t1  = UObj( .2+sample_period, u_clock_tick *1e-20); % 0s
d2  = UObj( .238, 7.84915e-4).mul(in2m); % inches -> meters
d1  = UObj( .618, .001129).mul(in2m); % inches -> meters
p1_mxl = .007120869; % xducer 1 u reading as calc from excel
p1_test = .0017; % xducer 1 u from test
vp1 = UObj( p1_read, p1_test); % voltage

p2_mxl = .007436709; % xducer 2 u from excel
p2_test = .0021; % xducer 2 from test
vp2 = UObj( p2_read, p2_test); % voltage

% pressure = ((((voltage * 118) - .004) * 12500 * slope) + offset) * psi2pa
% (((volts / ohms) - amps) * psi/amps*psi_scalar) + psi_offset * pascals/psi = pascals
pres = @(v_uobj, slope, offset, p_u) v_uobj.mul(1/ljtick_scalar).add(-.004).mul(xducer_nominal_slope).mul(slope).add(offset).u_mul(UObj(1, p_u)).mul(psi2pa);
p1 = pres(vp1, p1_slope, p1_offset, p1_u);
p2 = pres(vp2, p2_slope, p2_offset, p2_u);

% position = voltage * in/v * m/in = m
x1 = vx1.mul(pot_slope).mul(in2m);
x2 = vx2.mul(pot_slope).mul(in2m);

%  Direct Calculation -----------------------------------------------------

% top left pd/2 ^2 * 4 = m ^2
pd_term = pd.mul(1/2).pwr(2).mul(4);

% x2-x1, t2-t1, dx/dt = m/s
dx_term = x2.u_sub(x1);
dt_term = t2.u_sub(t1);
dxdt_term = dx_term.u_div(dt_term);

% d2^2 = m^2
d2_term = d2.pwr(2);

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

% finished CD value 
CD = cd_num.u_div(cd_den);

fprintf('Direct CD:      %.3f ±%.2f%%\n', CD.V, CD.U/CD.V*100)

% Save values to other variables so lowercase can be used in syms
X1 = x1; X2 = x2; T1 = t1; T2 = t2; P1 = p1; P2 = p2; D1 = d1; D2 = d2; RHO = rho; R = pd.mul(1/2);

% save nominal values
vals = [X1.V X2.V T1.V T2.V P1.V P2.V D1.V D2.V RHO R.V];
% save abs uncertain values
u_vals = [X1.U X2.U T1.U T2.U P1.U P2.U D1.U D2.U 0 R.U];


sym_strs = ["x1" "x2" "t1" "t2" "p1" "p2" "d1" "d2" "rho" "r"];


% Symbolic Substitution --------------------------------------------------
syms(sym_strs);
sym_chars = [x1 x2 t1 t2 p1 p2 d1 d2 rho r];

umf_syms = sym.empty;

cd = ...
    4 * r^2 * ...               pd term   \ numerator
    (x2 - x1) / (t2 - t1) / ... dxdt term /
    (...                                                 \denominator
        d2^2 * ...                 d2 term                |
        sqrt(...                                          |
                2 * (p1 - p2) / ...     rad num term      |     
            (...                                          |
                rho * (1 - (d2 / d1)^4)... rad den term   |
            )...                                          |
        )...                                              |
    );                                                   %/

for i = 1:length(vals)
    % find partial derivative of cd with respect to variable and multiply
    % by variable and divide by cd to find UMF equation, and store in array
    umf_syms(i) = simplify(diff(cd, sym_chars(i)) * sym_chars(i)/cd);
end

% substitute variables in UMF equation with their nominal values to get
% numerical UMF,
umf_vals =  eval(subs(umf_syms, sym_chars, vals));

urels = u_vals./vals;
u_propagated = umf_vals .* urels;
% find nominal cd value
cd_v = eval(subs(cd, sym_chars, vals));
% find CD uncertainty from rssq of all variable relative uncertainties
cd_ur = rssq(u_propagated);

fprintf('Substituted CD: %.3f ±%.2f%%\n', cd_v, cd_ur*100)

%%total relative uncertainties wrt CD
sum_urel_wrt_cd = sum(abs(u_propagated));
%%total relative uncertainty wrt CD of var
total_x = sum(abs(u_propagated(1,1:2)));
total_t = sum(abs(u_propagated(1,3:4)));
fprintf('Potentiometer Reading Uncertainty Contribution: %.1f%%\n\n', total_x/sum_urel_wrt_cd*100)
percent_cont_array_x(iter) = total_x/sum_urel_wrt_cd*100;
percent_cont_array_t(iter) = total_t/sum_urel_wrt_cd*100;
percent_cont_array_all(:,iter) = abs(u_propagated)/sum_urel_wrt_cd;
rel_cont_array_all(:,iter) = percent_cont_array_all(:,iter) .* cd_ur;
cd_u_array(iter) = cd_ur*100;
umf_vals_array(:,iter) = umf_vals;
urel_array(:,iter) = u_vals./vals;

% iter = 18 = 19 samples / s , 1.75s test * 19sa/s = 33samples
if iter==18
    u_prop_14 = u_propagated;
    u_vals_14 = u_vals;
    vals_14 = vals;
end

end

figure('Name', 'Sample Rate Range Variation and Relative Uncertainties at Low Range')
sp_row = 3;
sp_col = 3;

subplot(sp_row,sp_col,6)
% % plotting each variable's relative uncertainty
bar(sym_strs,u_vals_14./vals_14*100)
title('Relative Uncertainty per Parameter at 19 sa/s');
xlabel('Variable')
ylabel('Relative Uncertainty, %')

subplot(sp_row,sp_col,5)
bar(sym_strs, abs(u_prop_14)/sum(abs(u_prop_14))*100)
title('Normalized Relative Uncertainty wrt CD at 19 sa/s');
xlabel('Variable')
ylabel('Relative Uncertainty Contribution to CD, %')

subplot(sp_row,sp_col,4)
semilogx(1./sample_periods, percent_cont_array_x)
title('Uncertainty Percentage Contribution of X to CD');
grid on
xlabel('Sample Rate')
ylabel('X Uncertainty Contribution, %')


subplot(sp_row,sp_col,3)
semilogx(1./sample_periods, percent_cont_array_t);
title('Uncertainty Percentage Contribution of t to CD');
grid on
xlabel('Sample Rate')
ylabel('t Uncertainty Contribution, %')

subplot(sp_row,sp_col,2)
percent_cont_array_all(2,:) = sum(percent_cont_array_all(1:2,:));
semilogx(1./sample_periods, percent_cont_array_all(2:end,:)*100)
legend(['dx' sym_strs(1,3:end)])
title('Normalized Relative Uncertainty wrt CD');
xlabel('Sample Rate')
ylabel('Relative Uncertainty wrtCd, %')
grid on

subplot(sp_row,sp_col,1)
semilogx(1./sample_periods, cd_u_array);
title('CD Relative Uncertainty');
xlabel('Sample Rate')
ylabel('Relative Uncertainy of CD, %')
grid on

subplot(sp_row,sp_col,7)
loglog(1./sample_periods, abs(umf_vals_array));
legend(sym_strs)
title('UMF Per Variable')
xlabel('Sample Rate')
ylabel('UMF')
grid on

subplot(sp_row,sp_col,8)
loglog(1./sample_periods, urel_array)
legend(sym_strs)
title('Relative Uncertainty Per Variable')
xlabel('Sample Rate')
ylabel('Relative Uncertainty, %')

subplot(sp_row,sp_col,9)
area(1./sample_periods, rel_cont_array_all'*100)
set(gca, 'XScale', 'log')
set(gca, 'YScale', 'log')
legend(sym_strs)
title('Relative Uncertainty wrt CD');
xlabel('Sample Rate')
ylabel('Relative Uncertainty wrt Cd, %')
grid on

% %% Monte Carlo ------------------------------------------------------------
% cd_vals = zeros(1,10);
% iters = 100;
% rand_vals = vals + u_vals.*randn(iters,length(vals));
% for i=1:iters
%     cd_vals(i) = eval(subs(cd, sym_chars, rand_vals(i,:)));
% end
% 
% stdcdmc = std(cd_vals);
% mcdmc = mean(cd_vals);
% fprintf('Monte Carlo CD: %.3f ±%.2f%%\n\n',...
%    mcdmc, stdcdmc/mcdmc*100);
