% Number of simulations
N = 10000;

% Define nominal values and uncertainties for variables
nominal_values = struct('Dc', 3, 'dx', 4, 'D1', 1, 'D2', 0.5, 'rho', 1, 'P1', 50, 'P2', 14.75);
uncertainties = struct('Dc', 0.0005, 'dx', 0.1, 'D1', 0.0005, 'D2', 0.0005, 'rho', 0, 'P1', 0.5, 'P2', 0.5);

% Generate N random samples for each variable, assuming a normal distribution
fields = fieldnames(nominal_values);
samples = struct();

for i = 1:numel(fields)
    samples.(fields{i}) = normrnd(nominal_values.(fields{i}), uncertainties.(fields{i}), [N, 1]);
end

% Calculate flow rate for each sample
Cd_values = (samples.dx .* (samples.Dc/2).^2 .* pi) ./ (pi / 4 .* samples.D2.^2 .* sqrt(2 .* (samples.P1 - samples.P2) ./ (samples.rho .* (1-(samples.D2-samples.D1).^4))));

% Analyze results
figure;

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
