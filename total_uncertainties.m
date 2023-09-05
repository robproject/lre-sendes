%% Constant Values

% Device Parameters

% adc specs
res_bits = 16;
res_steps = 2^res_bits;
adc_accuracy = .0001; % percent

% caliper tolerance
calipers = .0005; % inches
calipers = convlength(calipers, 'in', 'm');

% transducer accuracy, in total units
transducer = .0025 * 200; % percent * fs range (psi)
transducer = convpres(transducer, 'psi', 'Pa');

vars_const = {
    'rho',    1000, .00001;
    'P1',      convpres(100, 'psi', 'Pa'), transducer;
    'P2',      convpres(0, 'psi', 'Pa'),   transducer; 
    };
syms(vars_const{:,1})

%% Volume Approach

% linear potentiometer specs
vmax = 5;
pot_accuracy = .0001;


% Without decomposed dvolume
% vars = [D2, D1, Di, rho, v,  cP];
% Cd = 4*(Di/2)^2 * v * D2^(-2) * (2* cP * (rho * (1-(D2/D1)^4))^(-1))^(-1/2);

% With decomposed dvolume


% var, nominal, uncertainty
vars = {
    'D2', convlength(.75, 'in', 'm'),  calipers; % 1
    'D1', convlength(.5, 'in', 'm'),   calipers; % 2
    'Di', convlength(5, 'in', 'm'),    calipers; % 3
    'h',  convlength(16, 'in', 'm'),   calipers; % 4
    'v1', 2.5, pot_accuracy * vmax;              % 5
    'v2', 2.6,   pot_accuracy * vmax;            % 6
    'steps1', 2.5/vmax * res_steps, adc_accuracy * res_steps;% 7
    'steps2', 2.6/vmax * res_steps, adc_accuracy * res_steps;% 8
    't1', .05, 0;
    't2', .06, 0;
    };

syms(vars{:,1})

dx = (((v2/vmax) * steps2 / res_steps) - ((v1/vmax) * steps1 / res_steps))*h;

dt = t2 - t1;

Cd = 4*(Di/2)^2 * dx/dt * D2^(-2) * (2* (P1 - P2) * (rho * (1-(D2/D1)^4))^(-1))^(-1/2);
%Cd = subs(Cd, [dx, dt], [dx, dt]);

get_total_uncertainty('Cd', Cd, [vars_const; vars])


%% Mass Approach
syms mf mi tf ti dm dt

% Without decomposed dmass
% vars = [D1, D2, rho, dm, cP, dt];
% Cd =  (4/pi) *  (dm/(dt * rho)) * D2^-2 * (2*(cP) * (rho*(1-(D2/D1)^4))^(-1))^(-1/2);

% With decomposed dmass
vars = [D1, D2, rho, mf, mi, cP, tf, ti];
vars_nominal = [1, .75, 1000, 45, 0, 100, 2.5, 0];
vars_uncertainty = [];
Cd = (4/pi) *  ((mf-mi)/((tf-ti) * rho)) * D2^-2 * (2*(cP) * (rho*(1-(D2/D1)^4))^(-1))^(-1/2);

get_total_uncertainty('Cd', Cd, vars)



%% Functions

function get_total_uncertainty(name, fx, vars)

    fprintf('%s \n', name)
    pretty(fx)
    for k = 1:size(vars, 1)
        if ischar(vars{k, 1})
            vars{k, 1} = str2sym(vars{k, 1});
        end
    end
    ref = subs(fx, [vars{:,1}], [vars{:,2}]);
    disp(ref)
    du_var = 0;
    


    for i=1:length(vars)
        d = diff(fx, vars{i,1});

        if has(d, vars{i,1})
            du_var = du_var + (subs(d, vars(:,1), vars(:,2)) * vars(i,3))^2;
            disp(du_var)
        else
            sub_names = {vars{[1:i-1, i+1:end],1}};
            sub_vals = {vars{[1:i-1, i+1:end],2}};
    
            du_var = du_var + (subs(d, sub_names, sub_vals) * vars{i,3})^2;
            disp(du_var)
        end
    end
    disp(du_var)
    disp(sqrt(du_var));
end
