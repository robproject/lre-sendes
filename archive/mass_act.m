% Actual value of sensitivity per variable, mass

% Define variables and their nominal and deviation values
vars = {'dm', 'pipe_d', 'orifice_d', 'rho', 'p1', 'p2'};
nominal_values = [3, 1, 0.5, 1, 50, 10];
deviations = nominal_values .* [1, 0.0005, 0.0005, 0, 0.5, 0.5];

% Define function to estimate flow rate
cd = @(dm, d1, d2, rho, p1, p2) (rho * dm) / (pi / 4 * d2^2 * (2 * (p1 - p2))/sqrt(rho * (1-(d2/d1)^4)));

cd_nominal = cd(nominal_values(1), nominal_values(2), nominal_values(3), nominal_values(4), nominal_values(5), nominal_values(6));

cd_p = zeros(1, length(vars));
cd_n = zeros(1, length(vars));

for i = 1:length(vars)
    delta = zeros(1, length(vars));
    delta(i) = deviations(i);
    cd_p(i) = cd(nominal_values(1) + delta(1), nominal_values(2) + delta(2), nominal_values(3) + delta(3), nominal_values(4) + delta(4), nominal_values(5) + delta(5), nominal_values(6) + delta(6));
    cd_n(i) = cd(nominal_values(1) - delta(1), nominal_values(2) - delta(2), nominal_values(3) - delta(3), nominal_values(4) - delta(4), nominal_values(5) - delta(5), nominal_values(6) - delta(6));
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

% Adjusting the x limits to better visualize bars
xlim([-max(abs(sensitivities_neg_sorted)) * 1.1, max(abs(sensitivities_pos_sorted)) * 1.1]);
xlabel('Change in Cd');
title('Tornado Diagram');
yticks(1:length(vars));
yticklabels(vars_sorted);

% Add labels to bar ends for positive sensitivities
for i = 1:length(sensitivities_pos_sorted)
    if sensitivities_pos_sorted(i) > 1
        text(sensitivities_pos_sorted(i), i, sprintf('%.3f', sensitivities_pos_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    else
        text(sensitivities_pos_sorted(i), i, sprintf('%.3f', sensitivities_pos_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    end
end

% Add labels to bar ends for negative sensitivities
for i = 1:length(sensitivities_neg_sorted)
    if sensitivities_neg_sorted(i) > 1
        text(-sensitivities_neg_sorted(i), i, sprintf('-%.3f', sensitivities_neg_sorted(i)), 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
    else
        text(-sensitivities_neg_sorted(i), i, sprintf('-%.3f', sensitivities_neg_sorted(i)), 'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle');
    end
end

legend('Positive', 'Negative');
hold off;
