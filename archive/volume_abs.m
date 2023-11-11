% Absolute value of sensitivity per variable, volume
gal2m3 = @(gal) gal*0.003785411784;
% piston dims
vol = 5; % gallons
piston_dia = 5; % piston dia inch
piston_dia = convlength(piston_dia, 'in', 'm'); % piston dia m
vol = gal2m3(vol); % vol cubic m
piston_len = vol / (pi * (piston_dia/2)^2); % piston len m
t = 2.46 ; % seconds
dx = piston_len/t;

% accuracies
micrometer = .0005; % inches
transducer = .5; % psi

micrometer = convlength(micrometer, 'in', 'm');
transducer = convpres(transducer, 'psi', 'Pa');
adc = piston_len / 1024; % meters

abs2per = @(nominal, accuracy) accuracy / nominal;

% nominal values and conversions

d1_i = 1; % inch
d2_i = .75; % inch
us_p = 100; % psi
ds_p = 14.75; % psi

piston_dia = convlength(piston_dia, 'in', 'm');
d1 = convlength(d1_i, 'in', 'm');
d2 = convlength(d2_i, 'in', 'm');
us = convpres(us_p, 'psi', 'Pa');
ds = convpres(ds_p, 'psi', 'Pa');



% Define array variable names and their nominal and deviation values
vars = {'piston_dia', 'plunger_v', 'pipe_d', 'orifice_d', 'rho', 'p1', 'p2'};
nominal_values = [piston_dia, dx, d1, d2, 998, us, ds];
deviations = nominal_values .* [abs2per(piston_dia, micrometer), abs2per(dx, adc), abs2per(d1, micrometer), abs2per(d2, micrometer), 0, abs2per(us, transducer), abs2per(ds, transducer)];

% Define function to estimate flow rate
cd = @(piston_dia, v, d1, d2, rho, p1, p2) (pi * (piston_dia/2)^2 * v) / (pi / 4 * d2^2 * (2 * (p1 - p2))/sqrt(rho * (1-(d2/d1)^4)));

% Estimate flow rate at nominal values
cd_nominal = cd(nominal_values(1), nominal_values(2), nominal_values(3), nominal_values(4), nominal_values(5), nominal_values(6), nominal_values(7));
disp(cd_nominal);

% Estimate flow rate at nominal values ± deviation for each variable
cd_p = zeros(1, length(vars));
cd_n = zeros(1, length(vars));

for i = 1:length(vars)
    delta = zeros(1, length(vars));
    delta(i) = deviations(i);
    cd_p(i) = cd(nominal_values(1) + delta(1), nominal_values(2) + delta(2), nominal_values(3) + delta(3), nominal_values(4) + delta(4), nominal_values(5) + delta(5), nominal_values(6) + delta(6), nominal_values(7) + delta(7));
    cd_n(i) = cd(nominal_values(1) - delta(1), nominal_values(2) - delta(2), nominal_values(3) - delta(3), nominal_values(4) - delta(4), nominal_values(5) - delta(5), nominal_values(6) - delta(6), nominal_values(7) - delta(7));
end

% Calculate sensitivity for each variable
sensitivities = cd_p - cd_n;
disp(sensitivities);
disp(cd_p);
disp(cd_n);

% Sort variables by sensitivity
[sensitivities_sorted, indices] = sort(abs(sensitivities), 'descend');
vars_sorted = vars(indices);

% Adjust yticklabels to include deviation values
yticklabels_with_deviation = cell(1, length(vars_sorted));
for i = 1:length(vars_sorted)
    yticklabels_with_deviation{i} = sprintf('%s (%.7f)', vars_sorted{i}, deviations(indices(i)));
end

% Plot tornado diagram
figure;
barh(1:length(vars), sensitivities_sorted, 'FaceColor', [0.1176, 0.5647, 1.0000]);

xlabel('Change in Cd');
title('Tornado Diagram');
yticks(1:length(vars));
yticklabels(yticklabels_with_deviation);

% Adjust text placement for better visualization
text_offset = max(abs(sensitivities_sorted)) * 0.05;


% Add labels to bar ends
for i = 1:length(sensitivities_sorted)
    if sensitivities_sorted(i) > 0
        text(sensitivities_sorted(i) + text_offset, i, sprintf('%.7f', sensitivities_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    else
        text(sensitivities_sorted(i) - text_offset, i, sprintf('%.7f', sensitivities_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    end
end


axis tight;
