% Calculator to get total value of uncertainty, given device specifications
%% Constant Values

% Device Parameters

% adc specs
res_bits = 16;
res_steps = 2^res_bits;
adc_accuracy = .0001; % percent
resolution_uncertainty = .5/res_steps;
A = 1;

% caliper tolerance
calipers = .0005; % inches
calipers = convlength(calipers, 'in', 'm');

% transducer accuracy, in total units
transducer = .0025 * 200; % percent * fs range (psi)
transducer = convpres(transducer, 'psi', 'Pa');

vars_const = {
    'rho',   1000,                              0; % kg/m3
    'P1',    convpres(50, 'psi', 'Pa'),    transducer;
    'P2',    convpres(15, 'psi', 'Pa'),      transducer; 
    'D2',    convlength(.25, 'in', 'm'),      calipers;
    'D1',    convlength(  1, 'in', 'm'),      calipers;
    };
syms(vars_const{:,1})

%% Volume Approach

% linear potentiometer specs
vmax = 5;  % volts (vref)
pot_accuracy = .0001; % percent

%    var,                    nominal,               uncertainty
vars_vol = {

    "Di", convlength(  8, 'in', 'm'),                  calipers; 
    "L",  convlength( 22.97, 'in', 'm'),               calipers; 
    "v1", 2.5000,                           pot_accuracy * vmax; 
    "v2", 2.5203,                           pot_accuracy * vmax; 
    "A", 1, rssq([adc_accuracy, resolution_uncertainty]); 
    "t1", .05, 0;
    "t2", .06, 0;
    "vref", vmax, .0001*vmax;
    };

syms(vars_vol{:,1})

dx = v2 - v1;

dt = t2 - t1;

Cd = 4*(Di/2)^2 * dx/dt * A*L/vref* D2^(-2) * (2* (P1 - P2) * (rho * (1-(D2/D1)^4))^(-1))^(-1/2);

[u, ref] = get_total_uncertainty('Cd', Cd, [vars_const; vars_vol]);
fprintf('Cd with Uncertainty: %1.4f +/-%1.4f \n', [ref, u/2]);

%% Mass Approach
syms mf mi tf ti dm dt

% load cell specs
vmax = 5; % volts (vref)
cell_accuracy = .001; % percent

% catch and weigh uncertainty
water_loss = 1; % kg

% time uncertainty for weight
t_valve = .05;

% reference weight uncertainty
W_max = convmass(50, 'lbm', 'kg'); % reference weight for load cell calibration
W_accuracy = .00023 ; % .023g accuracy of 50lb reference weight

water_loss_accuracy = water_loss / W_max; % accuracy scalar for final voltage reading



%    var,                    nominal,               uncertainty
vars_mass = {
    'v1', 0 , cell_accuracy * vmax;
    'v2', 4.175 , rssq([cell_accuracy * vmax, water_loss_accuracy * vmax]);
    't1', 0, t_valve;
    't2', 2.4, t_valve;
    'W',  W_max, W_accuracy ;
    'A', 1, rssq([adc_accuracy, resolution_uncertainty]);
    "vref", vmax, .0001*vmax;
    };

syms(vars_mass{:,1});

dm = v2 - v1;
dt = t2 - t1;

Cd = (4/pi) *  dm/(dt * rho) * A * W / vref * D2^-2 * (2*(P1-P2) * (rho*(1-(D2/D1)^4))^(-1))^(-1/2);


[u, ref] = get_total_uncertainty('Cd', Cd, [vars_const; vars_mass]);
fprintf('Cd with Uncertainty: %1.4f +/-%1.4f \n', [ref, u/2]);


%% Functions

function [u, ref] = get_total_uncertainty(name, fx, vars)

    fprintf('%s \n', name)
    pretty(vpa(simplify(fx),4))
    latex(fx)

    % covert to syms
    for k = 1:size(vars, 1)
        if ischar(vars{k, 1})
            vars{k, 1} = str2sym(vars{k, 1});
        end
    end
    
    % get reference Cd based on nominal values
    ref = subs(fx, [vars{:,1}], [vars{:,2}]);
    % convert from symbolic equation
    ref = double(ref);
    
    % initialize sum of uncertainties to be square rooted
    du_var = 0;

    for i=1:length(vars)
        % partial diff according to current variable
        d = diff(fx, vars{i,1});
        
        % if equation still has current variable after diff
        if has(d, vars{i,1})
            % substitute all nominal values and mulitply by uncertainty
            du_var = du_var + (subs(d, vars(:,1), vars(:,2)) * vars(i,3))^2;
        else
            % if missing partial variable, skip that variable for
            % substitution by creating new substitution objects ommitting
            % the variable
            sub_names = {vars{[1:i-1, i+1:end],1}};
            sub_vals = {vars{[1:i-1, i+1:end],2}};
            % substitute and multiply
            du_var = du_var + (subs(d, sub_names, sub_vals) * vars{i,3})^2;
        end
    end

    u = double(sqrt(du_var));
end
