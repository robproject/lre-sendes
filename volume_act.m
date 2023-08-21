% Actual value of sensitivity per variable
% accuracies
micrometer = .0005; % inches
transducer = .5; % psi

micrometer = convlength(micrometer, 'in', 'm');
transducer = convpres(transducer, 'psi', 'Pa');

abs2per = @(nominal, accuracy) accuracy / nominal;
% nominal values and conversions
piston_dia = 2.5; %inch
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
nominal_values = [piston_dia, .609, d1, d2, 998, us, ds];
deviations = nominal_values .* [abs2per(piston_dia, micrometer), 0, abs2per(d1, micrometer), abs2per(d2, micrometer), 0, abs2per(us, transducer), abs2per(ds, transducer)];

% Define function to estimate flow rate
cd = @(piston_dia, v, d1, d2, rho, p1, p2) (pi * (piston_dia/2)^2 * v) / (pi / 4 * d2^2 * (2 * (p1 - p2))/sqrt(rho * (1-(d2/d1)^4)));

cd_nominal = cd(nominal_values(1), nominal_values(2), nominal_values(3), nominal_values(4), nominal_values(5), nominal_values(6), nominal_values(7));

cd_p = zeros(1, length(vars));
cd_n = zeros(1, length(vars));

for i = 1:length(vars)
    delta = zeros(1, length(vars));
    delta(i) = deviations(i);
    cd_p(i) = cd(nominal_values(1) + delta(1), nominal_values(2) + delta(2), nominal_values(3) + delta(3), nominal_values(4) + delta(4), nominal_values(5) + delta(5), nominal_values(6) + delta(6), nominal_values(7) + delta(7));
    cd_n(i) = cd(nominal_values(1) - delta(1), nominal_values(2) - delta(2), nominal_values(3) - delta(3), nominal_values(4) - delta(4), nominal_values(5) - delta(5), nominal_values(6) - delta(6), nominal_values(7) - delta(7));
end

sensitivities_pos = cd_p - cd_nominal;
sensitivities_neg = cd_nominal - cd_n;

[~, indices] = sort(abs(sensitivities_pos + sensitivities_neg), 'descend');
vars_sorted = vars(indices);
sensitivities_pos_sorted = sensitivities_pos(indices);
sensitivities_neg_sorted = sensitivities_neg(indices);

disp(sensitivities_pos_sorted);
disp(sensitivities_neg_sorted);

figure;
hold on;

% Plot positive and negative sensitivities separately
bars_pos = barh(1:length(vars), sensitivities_pos_sorted, 'FaceColor', [0.1176, 0.5647, 1.0000]);
bars_neg = barh(1:length(vars), -sensitivities_neg_sorted, 'FaceColor', 'red');

% Adjust yticklabels to include deviation values
yticklabels_with_deviation = cell(1, length(vars_sorted));
for i = 1:length(vars_sorted)
    yticklabels_with_deviation{i} = sprintf('%s (%.7f)', vars_sorted{i}, deviations(indices(i)));
end



% Adjusting the x limits to better visualize bars
xlim([-max(abs(sensitivities_neg_sorted)) * 1.1, max(abs(sensitivities_pos_sorted)) * 1.1]);
xlabel('Change in Cd');
title('Tornado Diagram');
yticks(1:length(vars));
yticklabels(yticklabels_with_deviation);

text_offset = max(abs(sensitivities_pos_sorted)) * 0.05;

% Add labels to bar ends for positive sensitivities
for i = 1:length(sensitivities_pos_sorted)
    if sensitivities_pos_sorted(i) > 1
        text(sensitivities_pos_sorted(i) + text_offset, i, sprintf('%.7f', sensitivities_pos_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    else
        text(sensitivities_pos_sorted(i) - text_offset, i, sprintf('%.7f', sensitivities_pos_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    end
end

% Add labels to bar ends for negative sensitivities
for i = 1:length(sensitivities_neg_sorted)
    if sensitivities_neg_sorted(i) > 1
        text(-sensitivities_neg_sorted(i) - text_offset, i, sprintf('-%.7f', sensitivities_neg_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    else
        text(-sensitivities_neg_sorted(i) + text_offset, i, sprintf('-%.7f', sensitivities_neg_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    end
end


legend('Positive', 'Negative');
hold off;
