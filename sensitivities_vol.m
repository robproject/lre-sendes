
% Device parameters 
% Number of simulations
N = 10000;

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
adc = piston_len / 1024; % meters

micrometer = convlength(micrometer, 'in', 'm');
transducer = convpres(transducer, 'psi', 'Pa');

% nominal values and conversions


d1_i = 1; % pipe dia inch
d2_i = .75; % orifice dia inch
us_p = 100; % upstream transducer pressure psi
ds_p = 14.75; % downstream transducer pressure psi


d1 = convlength(d1_i, 'in', 'm');
d2 = convlength(d2_i, 'in', 'm');
us = convpres(us_p, 'psi', 'Pa');
ds = convpres(ds_p, 'psi', 'Pa');


% Define nominal values and uncertainties for variables
nominal_values = struct('Dc', piston_dia, 'dx', dx, 'D1', d1, 'D2', d2, 'rho', 1000, 'P1', us, 'P2', ds);
uncertainties = struct('Dc', micrometer, 'dx', adc, 'D1', micrometer, 'D2', micrometer, 'rho', 0, 'P1', transducer, 'P2', transducer);

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

function [m3] = gal2m3(gal)
% Convert volume from US liquid gallons to cubic meters. 
% Chad Greene 2012
m3 = gal*0.003785411784;
end
