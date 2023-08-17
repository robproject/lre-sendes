% Absolute value of sensitivity per variable

% Define variables and their nominal and deviation values
vars = {'piston_dia', 'plunger_v', 'pipe_d', 'orifice_d', 'rho', 'p1', 'p2'};
%       in, in/s, in, in, density, psi, psit

nominal_values = [3, 3, 1, 0.5, 1, 50, 10];
deviations = nominal_values .* [0.0005, 1, 0.0005, 0.0005, 0, 0.5, 0.5];

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

% Plot tornado diagram
figure;
barh(1:length(vars), sensitivities_sorted, 'FaceColor', [0.1176, 0.5647, 1.0000]);

xlabel('Change in Cd');
title('Tornado Diagram');
yticks(1:length(vars));
yticklabels(vars_sorted);

% Add labels to bar ends
for i = 1:length(sensitivities_sorted)
    if sensitivities_sorted(i) > 0
        text(sensitivities_sorted(i), i, sprintf('%.3f', sensitivities_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    else
        text(sensitivities_sorted(i), i, sprintf('%.3f', sensitivities_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    end
end

axis tight;
