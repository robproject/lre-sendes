close all;
% Number of simulations
N = 10000;

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

% Define nominal values and uncertainties for variables
nominal_values = struct('Dc', piston_dia, 'dx', .609, 'D1', d1, 'D2', d2, 'rho', 1, 'P1', us, 'P2', ds);
uncertainties = struct('Dc', micrometer, 'dx', .001, 'D1', micrometer, 'D2', micrometer, 'rho', 0, 'P1', transducer, 'P2', transducer);

% Generate N random samples for each variable, assuming a normal distribution
fields = fieldnames(nominal_values);
samples = struct();

for i = 1:numel(fields)
    samples.(fields{i}) = normrnd(nominal_values.(fields{i}), uncertainties.(fields{i}), [N, 1]);
end

% Calculate flow rate for each sample
Cd_values = (samples.dx .* (samples.Dc/2).^2 .* pi) ./ (pi / 4 .* samples.D2.^2 .* sqrt(2 .* (samples.P1 - samples.P2) ./ (samples.rho .* (1-(samples.D2-samples.D1).^4))));

% Analyze results
f = figure(1);
set(f, 'Position', [500, 100, 1700, 800])

for i = 1:numel(fields)
    subplot(2, 4, i);
    
    % Compute 2D histogram data
    [counts, xedges, yedges] = histcounts2(samples.(fields{i}), Cd_values, 50);
    
    % Display as a heatmap
    imagesc(xedges, yedges, counts');
    axis xy; % To ensure the y-axis is in increasing order
    colormap('jet');
    colorbar;
    
    xlabel(fields{i});
    ylabel('Cd');
    title(['2D Histogram of ', fields{i}, ' vs. Cd']);
end
